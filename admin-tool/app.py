#!/usr/bin/env python3
"""Dick Wray Portfolio — Admin Tool

A Flask-based admin interface for managing the Dick Wray memorial art website.
Local-only tool, no authentication required.
"""

import os
import sys
import json
import uuid
import subprocess
import webbrowser
import threading
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify, send_from_directory,
    redirect, url_for, abort
)
from werkzeug.utils import secure_filename
from PIL import Image as PILImage

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # DickWrayWebsite root
DATA_DIR = os.path.join(SITE_DIR, '_data')
IMAGES_DIR = os.path.join(SITE_DIR, 'assets', 'images', 'collections')

COLLECTIONS = {
    'watercolors': 'Watercolors',
    'black-and-whites': 'Black & Whites',
    'early-works': 'Early Works',
    'large-works': 'Large Works',
    'splash': 'Splash / Hero',
    'homepage': 'Homepage Cards',
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates',
)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB upload limit


@app.context_processor
def inject_globals():
    """Make collections dict available in every template for sidebar nav."""
    return {'collections': COLLECTIONS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_json(filepath, default=None):
    if default is None:
        default = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_image_info(filepath):
    """Return dict with file size and dimensions."""
    info = {
        'size': os.path.getsize(filepath),
        'size_human': _human_size(os.path.getsize(filepath)),
        'width': None,
        'height': None,
    }
    try:
        with PILImage.open(filepath) as img:
            info['width'], info['height'] = img.size
    except Exception:
        pass
    return info


def _human_size(nbytes):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def collection_images(slug):
    """Return list of image dicts for a collection."""
    folder = os.path.join(IMAGES_DIR, slug)
    if not os.path.isdir(folder):
        return []
    images = []
    for fname in sorted(os.listdir(folder)):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath) and allowed_file(fname):
            info = get_image_info(fpath)
            images.append({
                'filename': fname,
                'path': f'/site-assets/images/collections/{slug}/{fname}',
                **info,
            })
    return images


# ---------------------------------------------------------------------------
# Static / asset serving
# ---------------------------------------------------------------------------

@app.route('/site-assets/<path:filename>')
def serve_site_assets(filename):
    """Serve assets from the main site directory."""
    return send_from_directory(os.path.join(SITE_DIR, 'assets'), filename)


@app.route('/preview')
@app.route('/preview/<path:filename>')
def preview_site(filename='index.html'):
    """Serve the built site for preview."""
    return send_from_directory(SITE_DIR, filename)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route('/')
def dashboard():
    collections_data = []
    for slug, name in COLLECTIONS.items():
        imgs = collection_images(slug)
        collections_data.append({
            'slug': slug,
            'name': name,
            'count': len(imgs),
            'thumbnail': imgs[0]['path'] if imgs else None,
        })

    interviews = read_json(os.path.join(DATA_DIR, 'interviews.json'))
    publications = read_json(os.path.join(DATA_DIR, 'publications.json'))

    return render_template('admin/dashboard.html',
                           collections=collections_data,
                           interviews=interviews,
                           publications=publications)


@app.route('/images/<collection>')
def images_page(collection):
    if collection not in COLLECTIONS:
        abort(404)
    imgs = collection_images(collection)
    return render_template('admin/images.html',
                           collection=collection,
                           collection_name=COLLECTIONS[collection],
                           images=imgs,
                           collections=COLLECTIONS)


@app.route('/interviews')
def interviews_page():
    interviews = read_json(os.path.join(DATA_DIR, 'interviews.json'))
    return render_template('admin/interviews.html', interviews=interviews)


@app.route('/publications')
def publications_page():
    publications = read_json(os.path.join(DATA_DIR, 'publications.json'))
    return render_template('admin/publications.html', publications=publications)


@app.route('/settings')
def settings_page():
    settings = read_json(os.path.join(DATA_DIR, 'settings.json'), default={})
    return render_template('admin/settings.html', settings=settings)


# ---------------------------------------------------------------------------
# API — Images
# ---------------------------------------------------------------------------

@app.route('/api/images/<collection>', methods=['GET'])
def api_list_images(collection):
    if collection not in COLLECTIONS:
        return jsonify({'error': 'Unknown collection'}), 404
    return jsonify(collection_images(collection))


@app.route('/api/images/<collection>/upload', methods=['POST'])
def api_upload_images(collection):
    if collection not in COLLECTIONS:
        return jsonify({'error': 'Unknown collection'}), 404

    folder = os.path.join(IMAGES_DIR, collection)
    os.makedirs(folder, exist_ok=True)

    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No files provided'}), 400

    uploaded = []
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            fname = secure_filename(f.filename)
            dest = os.path.join(folder, fname)
            # Avoid overwriting — append number if exists
            base, ext = os.path.splitext(fname)
            counter = 1
            while os.path.exists(dest):
                fname = f"{base}_{counter}{ext}"
                dest = os.path.join(folder, fname)
                counter += 1
            f.save(dest)
            info = get_image_info(dest)
            uploaded.append({
                'filename': fname,
                'path': f'/site-assets/images/collections/{collection}/{fname}',
                **info,
            })

    return jsonify({'uploaded': uploaded, 'count': len(uploaded)})


@app.route('/api/images/<collection>/<filename>', methods=['DELETE'])
def api_delete_image(collection, filename):
    if collection not in COLLECTIONS:
        return jsonify({'error': 'Unknown collection'}), 404
    filepath = os.path.join(IMAGES_DIR, collection, secure_filename(filename))
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    os.remove(filepath)
    return jsonify({'success': True, 'deleted': filename})


# ---------------------------------------------------------------------------
# API — Interviews
# ---------------------------------------------------------------------------

def _interviews_path():
    return os.path.join(DATA_DIR, 'interviews.json')


@app.route('/api/interviews', methods=['GET'])
def api_list_interviews():
    return jsonify(read_json(_interviews_path()))


@app.route('/api/interviews', methods=['POST'])
def api_add_interview():
    data = request.get_json(force=True)
    interviews = read_json(_interviews_path())
    entry = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'url': data.get('url', ''),
        'date': data.get('date', ''),
        'description': data.get('description', ''),
    }
    interviews.append(entry)
    write_json(_interviews_path(), interviews)
    return jsonify(entry), 201


@app.route('/api/interviews/<entry_id>', methods=['PUT'])
def api_update_interview(entry_id):
    data = request.get_json(force=True)
    interviews = read_json(_interviews_path())
    for item in interviews:
        if item.get('id') == entry_id:
            item.update({k: v for k, v in data.items() if k != 'id'})
            write_json(_interviews_path(), interviews)
            return jsonify(item)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/interviews/<entry_id>', methods=['DELETE'])
def api_delete_interview(entry_id):
    interviews = read_json(_interviews_path())
    interviews = [i for i in interviews if i.get('id') != entry_id]
    write_json(_interviews_path(), interviews)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# API — Publications
# ---------------------------------------------------------------------------

def _publications_path():
    return os.path.join(DATA_DIR, 'publications.json')


@app.route('/api/publications', methods=['GET'])
def api_list_publications():
    return jsonify(read_json(_publications_path()))


@app.route('/api/publications', methods=['POST'])
def api_add_publication():
    # Handle multipart form (cover image) or JSON
    if request.content_type and 'multipart' in request.content_type:
        data = request.form.to_dict()
        cover = request.files.get('cover_image')
    else:
        data = request.get_json(force=True)
        cover = None

    publications = read_json(_publications_path())
    entry = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'url': data.get('url', ''),
        'date': data.get('date', ''),
        'description': data.get('description', ''),
        'cover_image': '',
    }

    if cover and cover.filename:
        covers_dir = os.path.join(SITE_DIR, 'assets', 'images', 'publications')
        os.makedirs(covers_dir, exist_ok=True)
        fname = secure_filename(cover.filename)
        cover.save(os.path.join(covers_dir, fname))
        entry['cover_image'] = f'/site-assets/images/publications/{fname}'

    publications.append(entry)
    write_json(_publications_path(), publications)
    return jsonify(entry), 201


@app.route('/api/publications/<entry_id>', methods=['PUT'])
def api_update_publication(entry_id):
    if request.content_type and 'multipart' in request.content_type:
        data = request.form.to_dict()
        cover = request.files.get('cover_image')
    else:
        data = request.get_json(force=True)
        cover = None

    publications = read_json(_publications_path())
    for item in publications:
        if item.get('id') == entry_id:
            item.update({k: v for k, v in data.items() if k != 'id'})
            if cover and cover.filename:
                covers_dir = os.path.join(SITE_DIR, 'assets', 'images', 'publications')
                os.makedirs(covers_dir, exist_ok=True)
                fname = secure_filename(cover.filename)
                cover.save(os.path.join(covers_dir, fname))
                item['cover_image'] = f'/site-assets/images/publications/{fname}'
            write_json(_publications_path(), publications)
            return jsonify(item)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/publications/<entry_id>', methods=['DELETE'])
def api_delete_publication(entry_id):
    publications = read_json(_publications_path())
    publications = [p for p in publications if p.get('id') != entry_id]
    write_json(_publications_path(), publications)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# API — Settings
# ---------------------------------------------------------------------------

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    return jsonify(read_json(os.path.join(DATA_DIR, 'settings.json'), default={}))


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    data = request.get_json(force=True)
    settings_path = os.path.join(DATA_DIR, 'settings.json')
    settings = read_json(settings_path, default={})
    settings.update(data)
    write_json(settings_path, settings)
    return jsonify(settings)


# ---------------------------------------------------------------------------
# Build & Deploy
# ---------------------------------------------------------------------------

@app.route('/build', methods=['POST'])
def build_site():
    try:
        # Try to import build module from the site root
        sys.path.insert(0, SITE_DIR)
        # Reload if already imported
        if 'build' in sys.modules:
            del sys.modules['build']
        from build import build_site as do_build
        result = do_build()
        return jsonify({
            'success': True,
            'message': 'Site built successfully',
            'files': result if isinstance(result, list) else [],
        })
    except ImportError:
        # Fallback: try running build.py as a script
        build_script = os.path.join(SITE_DIR, 'build.py')
        if not os.path.isfile(build_script):
            return jsonify({
                'success': False,
                'message': 'build.py not found in site directory',
            }), 404
        try:
            proc = subprocess.run(
                [sys.executable, build_script],
                cwd=SITE_DIR,
                capture_output=True, text=True, timeout=120,
            )
            return jsonify({
                'success': proc.returncode == 0,
                'message': proc.stdout or proc.stderr,
                'files': [],
            })
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'message': 'Build timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/deploy', methods=['POST'])
def deploy_site():
    try:
        git_dir = os.path.join(SITE_DIR, '.git')

        # Initialize git if needed
        if not os.path.isdir(git_dir):
            subprocess.run(['git', 'init'], cwd=SITE_DIR,
                           capture_output=True, text=True)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"Site update via admin tool - {timestamp}"

        # Stage all changes
        r1 = subprocess.run(['git', 'add', '-A'], cwd=SITE_DIR,
                            capture_output=True, text=True)

        # Commit
        r2 = subprocess.run(['git', 'commit', '-m', commit_msg], cwd=SITE_DIR,
                            capture_output=True, text=True)

        # Push
        r3 = subprocess.run(['git', 'push'], cwd=SITE_DIR,
                            capture_output=True, text=True, timeout=60)

        output = '\n'.join(filter(None, [r1.stdout, r2.stdout, r3.stdout, r3.stderr]))

        success = r3.returncode == 0
        if r2.returncode != 0 and 'nothing to commit' in (r2.stdout + r2.stderr).lower():
            return jsonify({
                'success': True,
                'message': 'Nothing to commit — site is up to date.',
                'output': r2.stdout,
            })

        return jsonify({
            'success': success,
            'message': 'Deployed successfully' if success else 'Deploy had issues',
            'output': output,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Git push timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def open_browser():
    """Open browser after a short delay to let Flask start."""
    import time
    time.sleep(1.2)
    webbrowser.open('http://localhost:5555')


if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Create default data files if missing
    for fname, default in [
        ('interviews.json', []),
        ('publications.json', []),
        ('settings.json', {
            'site_title': 'Dick Wray | Abstract Expressionist Artist',
            'site_description': 'Official website for abstract expressionist artist Dick Wray',
            'email': 'contact@dickwray.com',
        }),
    ]:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.isfile(fpath):
            write_json(fpath, default)

    print('\n\U0001f3a8 Dick Wray Admin — http://localhost:5555\n')

    # Auto-open browser
    threading.Thread(target=open_browser, daemon=True).start()

    app.run(host='0.0.0.0', port=5555, debug=True, use_reloader=False)

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


def read_json_list(filepath):
    """Read a JSON file that may be an array or {items: [...]}."""
    data = read_json(filepath, default=[])
    if isinstance(data, dict) and 'items' in data:
        return data['items']
    if isinstance(data, list):
        return data
    return []


def write_json_list(filepath, items):
    """Write a list back as {items: [...]} format (compatible with Decap CMS)."""
    write_json(filepath, {'items': items})


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


# ---------------------------------------------------------------------------
# Gallery data files (_data/galleries/<slug>.json)
# Shared with the web editor (Decap CMS) and used by build.py for ordering
# and captions. Kept in sync here whenever images are added/removed/edited.
# ---------------------------------------------------------------------------

def _gallery_path(slug):
    return os.path.join(DATA_DIR, 'galleries', f'{slug}.json')


def _gallery_public_path(slug, fname):
    return f'/assets/images/collections/{slug}/{fname}'


def read_gallery(slug):
    data = read_json(_gallery_path(slug), default=None)
    if isinstance(data, dict) and isinstance(data.get('images'), list):
        return data['images']
    return None


def write_gallery(slug, images):
    os.makedirs(os.path.dirname(_gallery_path(slug)), exist_ok=True)
    write_json(_gallery_path(slug), {'images': images})


def gallery_add(slug, fname):
    images = read_gallery(slug)
    if images is None:
        return  # no gallery file yet -> build.py falls back to folder scan
    public = _gallery_public_path(slug, fname)
    if not any(i.get('image') == public for i in images):
        images.append({'image': public, 'title': '', 'year': '',
                       'medium': '', 'dimensions': '', 'notes': ''})
        write_gallery(slug, images)


def gallery_remove(slug, fname):
    images = read_gallery(slug)
    if images is None:
        return
    public = _gallery_public_path(slug, fname)
    kept = [i for i in images if i.get('image') != public]
    if len(kept) != len(images):
        write_gallery(slug, kept)


def gallery_set_meta(slug, fname, meta):
    images = read_gallery(slug)
    if images is None:
        return
    public = _gallery_public_path(slug, fname)
    for i in images:
        if i.get('image') == public:
            i.update(meta)
            write_gallery(slug, images)
            return


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


# Serve site CSS, JS, and assets at root paths so preview links work
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(SITE_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(SITE_DIR, 'js'), filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(SITE_DIR, 'assets'), filename)

# Serve site HTML pages (for preview nav links like interviews.html)
@app.route('/<page>.html')
def serve_site_page(page):
    return send_from_directory(SITE_DIR, f'{page}.html')


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

    essays = read_json_list(os.path.join(DATA_DIR, 'essays.json'))
    interviews = read_json_list(os.path.join(DATA_DIR, 'interviews.json'))
    publications = read_json_list(os.path.join(DATA_DIR, 'publications.json'))

    return render_template('admin/dashboard.html',
                           collections=COLLECTIONS,
                           collections_data=collections_data,
                           essays=essays,
                           interviews=interviews,
                           publications=publications)


@app.route('/images/<collection>')
def images_page(collection):
    if collection not in COLLECTIONS:
        abort(404)
    imgs = collection_images(collection)
    metadata = read_json(_metadata_path(), default={})
    return render_template('admin/images.html',
                           collection=collection,
                           collection_name=COLLECTIONS[collection],
                           images=imgs,
                           metadata=metadata,
                           collections=COLLECTIONS)


@app.route('/bio')
def bio_page():
    bio = read_json(os.path.join(DATA_DIR, 'bio.json'), default={})
    return render_template('admin/bio.html', bio=bio, collections=COLLECTIONS)


@app.route('/cv-edit')
def cv_edit_page():
    cv = read_json(os.path.join(DATA_DIR, 'cv.json'), default={})
    return render_template('admin/cv_edit.html', cv=cv, collections=COLLECTIONS)


@app.route('/essays')
def essays_page():
    essays = read_json_list(os.path.join(DATA_DIR, 'essays.json'))
    return render_template('admin/essays.html', essays=essays, collections=COLLECTIONS)


@app.route('/interviews')
def interviews_page():
    interviews = read_json_list(os.path.join(DATA_DIR, 'interviews.json'))
    return render_template('admin/interviews.html', interviews=interviews, collections=COLLECTIONS)


@app.route('/publications')
def publications_page():
    publications = read_json_list(os.path.join(DATA_DIR, 'publications.json'))
    return render_template('admin/publications.html', publications=publications, collections=COLLECTIONS)


@app.route('/settings')
def settings_page():
    settings = read_json(os.path.join(DATA_DIR, 'settings.json'), default={})
    return render_template('admin/settings.html', settings=settings, collections=COLLECTIONS)


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
            gallery_add(collection, fname)
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
    gallery_remove(collection, secure_filename(filename))
    return jsonify({'success': True, 'deleted': filename})


# ---------------------------------------------------------------------------
# API — Image Metadata
# ---------------------------------------------------------------------------

def _metadata_path():
    return os.path.join(DATA_DIR, 'image_metadata.json')


@app.route('/api/image-metadata/<collection>/<filename>', methods=['GET'])
def api_get_image_metadata(collection, filename):
    metadata = read_json(_metadata_path(), default={})
    key = f"{collection}/{filename}"
    return jsonify(metadata.get(key, {}))


@app.route('/api/image-metadata/<collection>/<filename>', methods=['POST'])
def api_save_image_metadata(collection, filename):
    data = request.get_json(force=True)
    metadata = read_json(_metadata_path(), default={})
    key = f"{collection}/{filename}"
    metadata[key] = {
        'title': data.get('title', ''),
        'year': data.get('year', ''),
        'medium': data.get('medium', ''),
        'dimensions': data.get('dimensions', ''),
        'notes': data.get('notes', ''),
    }
    write_json(_metadata_path(), metadata)
    gallery_set_meta(collection, filename, metadata[key])
    return jsonify(metadata[key])


# ---------------------------------------------------------------------------
# API — Bio
# ---------------------------------------------------------------------------

@app.route('/api/bio', methods=['GET'])
def api_get_bio():
    return jsonify(read_json(os.path.join(DATA_DIR, 'bio.json'), default={}))


@app.route('/api/bio', methods=['POST'])
def api_save_bio():
    data = request.get_json(force=True)
    bio_path = os.path.join(DATA_DIR, 'bio.json')
    write_json(bio_path, data)
    return jsonify(data)


# ---------------------------------------------------------------------------
# API — CV
# ---------------------------------------------------------------------------

@app.route('/api/cv', methods=['GET'])
def api_get_cv():
    return jsonify(read_json(os.path.join(DATA_DIR, 'cv.json'), default={}))


@app.route('/api/cv', methods=['POST'])
def api_save_cv():
    data = request.get_json(force=True)
    cv_path = os.path.join(DATA_DIR, 'cv.json')
    cv = read_json(cv_path, default={})
    cv.update(data)
    write_json(cv_path, cv)
    return jsonify(cv)


# ---------------------------------------------------------------------------
# API — Essays
# ---------------------------------------------------------------------------

def _essays_path():
    return os.path.join(DATA_DIR, 'essays.json')


@app.route('/api/essays', methods=['GET'])
def api_list_essays():
    return jsonify(read_json_list(_essays_path()))


@app.route('/api/essays', methods=['POST'])
def api_add_essay():
    data = request.get_json(force=True)
    essays = read_json_list(_essays_path())
    entry = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'date': data.get('date', ''),
        'description': data.get('description', ''),
        'content': data.get('content', ''),
    }
    essays.append(entry)
    write_json_list(_essays_path(), essays)
    return jsonify(entry), 201


@app.route('/api/essays/<entry_id>', methods=['PUT'])
def api_update_essay(entry_id):
    data = request.get_json(force=True)
    essays = read_json_list(_essays_path())
    for item in essays:
        if item.get('id') == entry_id:
            item.update({k: v for k, v in data.items() if k != 'id'})
            write_json_list(_essays_path(), essays)
            return jsonify(item)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/essays/<entry_id>', methods=['DELETE'])
def api_delete_essay(entry_id):
    essays = read_json_list(_essays_path())
    essays = [e for e in essays if e.get('id') != entry_id]
    write_json_list(_essays_path(), essays)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# API — Interviews
# ---------------------------------------------------------------------------

def _interviews_path():
    return os.path.join(DATA_DIR, 'interviews.json')


@app.route('/api/interviews', methods=['GET'])
def api_list_interviews():
    return jsonify(read_json_list(_interviews_path()))


@app.route('/api/interviews', methods=['POST'])
def api_add_interview():
    data = request.get_json(force=True)
    interviews = read_json_list(_interviews_path())
    entry = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'url': data.get('url', ''),
        'date': data.get('date', ''),
        'description': data.get('description', ''),
    }
    interviews.append(entry)
    write_json_list(_interviews_path(), interviews)
    return jsonify(entry), 201


@app.route('/api/interviews/<entry_id>', methods=['PUT'])
def api_update_interview(entry_id):
    data = request.get_json(force=True)
    interviews = read_json_list(_interviews_path())
    for item in interviews:
        if item.get('id') == entry_id:
            item.update({k: v for k, v in data.items() if k != 'id'})
            write_json_list(_interviews_path(), interviews)
            return jsonify(item)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/interviews/<entry_id>', methods=['DELETE'])
def api_delete_interview(entry_id):
    interviews = read_json_list(_interviews_path())
    interviews = [i for i in interviews if i.get('id') != entry_id]
    write_json_list(_interviews_path(), interviews)
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# API — Publications
# ---------------------------------------------------------------------------

def _publications_path():
    return os.path.join(DATA_DIR, 'publications.json')


@app.route('/api/publications', methods=['GET'])
def api_list_publications():
    return jsonify(read_json_list(_publications_path()))


@app.route('/api/publications', methods=['POST'])
def api_add_publication():
    # Handle multipart form (cover image) or JSON
    if request.content_type and 'multipart' in request.content_type:
        data = request.form.to_dict()
        cover = request.files.get('cover_image')
    else:
        data = request.get_json(force=True)
        cover = None

    publications = read_json_list(_publications_path())
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
    write_json_list(_publications_path(), publications)
    return jsonify(entry), 201


@app.route('/api/publications/<entry_id>', methods=['PUT'])
def api_update_publication(entry_id):
    if request.content_type and 'multipart' in request.content_type:
        data = request.form.to_dict()
        cover = request.files.get('cover_image')
    else:
        data = request.get_json(force=True)
        cover = None

    publications = read_json_list(_publications_path())
    for item in publications:
        if item.get('id') == entry_id:
            item.update({k: v for k, v in data.items() if k != 'id'})
            if cover and cover.filename:
                covers_dir = os.path.join(SITE_DIR, 'assets', 'images', 'publications')
                os.makedirs(covers_dir, exist_ok=True)
                fname = secure_filename(cover.filename)
                cover.save(os.path.join(covers_dir, fname))
                item['cover_image'] = f'/site-assets/images/publications/{fname}'
            write_json_list(_publications_path(), publications)
            return jsonify(item)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/publications/<entry_id>', methods=['DELETE'])
def api_delete_publication(entry_id):
    publications = read_json_list(_publications_path())
    publications = [p for p in publications if p.get('id') != entry_id]
    write_json_list(_publications_path(), publications)
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
    # build.py lives in the admin-tool directory (same as app.py)
    admin_dir = os.path.dirname(os.path.abspath(__file__))
    build_script = os.path.join(admin_dir, 'build.py')

    try:
        # Try to import build module from admin-tool directory
        sys.path.insert(0, admin_dir)
        # Always reload to pick up changes
        if 'build' in sys.modules:
            del sys.modules['build']
        from build import build_site as do_build
        result = do_build()
        return jsonify({
            'success': True if result else False,
            'message': 'Site built successfully' if result else 'Build returned False',
            'files': result if isinstance(result, list) else [],
        })
    except ImportError as ie:
        # Fallback: try running build.py as a script
        if not os.path.isfile(build_script):
            return jsonify({
                'success': False,
                'message': f'build.py not found. Import error: {ie}',
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
        import traceback
        return jsonify({'success': False, 'message': str(e) + '\n' + traceback.format_exc()}), 500


@app.route('/deploy', methods=['POST'])
def deploy_site():
    """Rebuild the pages, pick up any edits made on the web editor, and push."""
    def git(*args, timeout=120):
        return subprocess.run(['git', *args], cwd=SITE_DIR,
                              capture_output=True, text=True, timeout=timeout)
    try:
        repo_url = 'https://github.com/robertwrayscode/Dickwray-Website.git'
        token_path = os.path.join(SITE_DIR, '.git-token')
        auth_url = repo_url
        if os.path.isfile(token_path):
            with open(token_path) as f:
                token = f.read().strip()
            if token:
                auth_url = f'https://{token}@github.com/robertwrayscode/Dickwray-Website.git'

        if not os.path.isdir(os.path.join(SITE_DIR, '.git')):
            git('init', '-b', 'main')
        git('remote', 'add', 'origin', repo_url)  # OK if it already exists
        git('config', 'user.name', 'Dick Wray Admin')
        git('config', 'user.email', 'admin@dickwray.com')

        log = []

        # 1. Rebuild pages from the current data
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from build import build_site as do_build
        if not do_build():
            return jsonify({'success': False, 'message': 'Build failed — see Terminal/log output.'}), 500
        log.append('Rebuilt site pages.')

        # 2. Commit local changes
        stage_files = [
            '.gitignore', '.nojekyll',
            'index.html', 'cv.html', 'essays.html', 'interviews.html', 'publications.html',
            'watercolors.html', 'black-and-whites.html', 'early-works.html', 'large-works.html',
            'css/', 'js/main.js', 'assets/images/', '_data/', 'admin-tool/',
            'admin/index.html', 'admin/config.yml', 'admin/auth-complete.html',
            '.github/', 'push-to-github.command',
        ]
        for f in stage_files:
            git('add', f)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        r = git('commit', '-m', f'Site update via admin tool - {timestamp}')
        local_changes = r.returncode == 0
        log.append('Committed local changes.' if local_changes else 'No local changes to commit.')

        # 3. Bring in anything changed on GitHub (e.g. edits from the web editor)
        r = git('fetch', auth_url, 'main')
        if r.returncode != 0:
            return jsonify({'success': False, 'message': 'Could not reach GitHub — ' + r.stderr.strip(),
                            'output': '\n'.join(log)}), 500
        r = git('merge', '-X', 'ours', '--no-edit', 'FETCH_HEAD')
        if r.returncode != 0:
            git('merge', '--abort')
            return jsonify({'success': False, 'message': 'Merge with GitHub failed — ' + (r.stderr or r.stdout).strip(),
                            'output': '\n'.join(log)}), 500
        if 'Already up to date' not in r.stdout:
            log.append('Merged changes from GitHub.')
            # Data may have changed on GitHub: rebuild so the pages match
            do_build()
            for f in stage_files:
                git('add', f)
            git('commit', '-m', f'Rebuild after merging web edits - {timestamp}')

        # 4. Push (never force — nothing gets overwritten)
        r = git('push', auth_url, 'main', timeout=120)
        log.append(r.stdout + r.stderr)
        if r.returncode != 0:
            return jsonify({'success': False, 'message': 'Push failed — ' + r.stderr.strip(),
                            'output': '\n'.join(log)}), 500

        return jsonify({'success': True,
                        'message': 'Published! The live site updates in about a minute.',
                        'output': '\n'.join(log)})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Git timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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

    # Auto-open browser (skipped when run as a background service)
    if not os.environ.get('DICKWRAY_NO_BROWSER'):
        threading.Thread(target=open_browser, daemon=True).start()

    app.run(host='0.0.0.0', port=5555, debug=True, use_reloader=False)

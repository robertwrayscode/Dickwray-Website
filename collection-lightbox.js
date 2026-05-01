/**
 * Collection Lightbox Functionality
 * This script adds lightbox functionality to all collection pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add lightbox HTML if it doesn't exist
    if (!document.querySelector('.lightbox')) {
        const lightboxHTML = `
        <div class="lightbox">
            <span class="close">&times;</span>
            <img class="lightbox-content" id="lightbox-image">
            <div class="caption" id="lightbox-caption"></div>
            <div class="lightbox-controls">
                <button class="prev-btn" id="prev-btn"><i class="fas fa-chevron-left"></i></button>
                <button class="next-btn" id="next-btn"><i class="fas fa-chevron-right"></i></button>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', lightboxHTML);
    }
    
    // Initialize lightbox functionality for the collection
    const galleryItems = document.querySelectorAll('.gallery-item');
    const lightbox = document.querySelector('.lightbox');
    const lightboxImg = document.querySelector('.lightbox-content');
    const lightboxCaption = document.getElementById('lightbox-caption');
    const closeBtn = document.querySelector('.lightbox .close');
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    
    // Exit if no lightbox or gallery items exist
    if (!lightbox || galleryItems.length === 0) return;
    
    let currentIndex = 0;
    const galleryArray = Array.from(galleryItems);
    
    // Add click event to each gallery item
    galleryItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            currentIndex = index;
            const imgSrc = this.dataset.src || this.querySelector('img').src;
            const imgAlt = this.querySelector('img').alt || 'Dick Wray Artwork';
            
            lightboxImg.src = imgSrc;
            if (lightboxCaption) lightboxCaption.textContent = imgAlt;
            lightbox.style.display = 'flex';
        });
    });
    
    // Close lightbox when clicking the X
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            lightbox.style.display = 'none';
        });
    }
    
    // Close lightbox when clicking outside the image
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) {
            lightbox.style.display = 'none';
        }
    });
    
    // Next image button
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            currentIndex = (currentIndex + 1) % galleryArray.length;
            const nextItem = galleryArray[currentIndex];
            const imgSrc = nextItem.dataset.src || nextItem.querySelector('img').src;
            const imgAlt = nextItem.querySelector('img').alt || 'Dick Wray Artwork';
            
            lightboxImg.src = imgSrc;
            if (lightboxCaption) lightboxCaption.textContent = imgAlt;
        });
    }
    
    // Previous image button
    if (prevBtn) {
        prevBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            currentIndex = (currentIndex - 1 + galleryArray.length) % galleryArray.length;
            const prevItem = galleryArray[currentIndex];
            const imgSrc = prevItem.dataset.src || prevItem.querySelector('img').src;
            const imgAlt = prevItem.querySelector('img').alt || 'Dick Wray Artwork';
            
            lightboxImg.src = imgSrc;
            if (lightboxCaption) lightboxCaption.textContent = imgAlt;
        });
    }
    
    // Keyboard navigation for lightbox
    document.addEventListener('keydown', function(e) {
        if (lightbox.style.display === 'flex') {
            if (e.key === 'ArrowRight') {
                // Next image
                if (nextBtn) nextBtn.click();
            } else if (e.key === 'ArrowLeft') {
                // Previous image
                if (prevBtn) prevBtn.click();
            } else if (e.key === 'Escape') {
                // Close lightbox
                lightbox.style.display = 'none';
            }
        }
    });
});

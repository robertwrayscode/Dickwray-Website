/**
 * Simple Lightbox - A lightweight and reliable lightbox implementation
 * For Dick Wray's website
 */

document.addEventListener('DOMContentLoaded', function() {
    // Create lightbox elements if they don't exist
    if (!document.querySelector('#simple-lightbox')) {
        const lightboxHTML = `
        <div id="simple-lightbox" class="lightbox">
            <div class="lightbox-container">
                <button class="lightbox-close" aria-label="Close lightbox">&times;</button>
                <img src="" class="lightbox-image" alt="Artwork in lightbox">
                <div class="lightbox-caption"></div>
                <div class="lightbox-controls">
                    <button class="lightbox-prev" aria-label="Previous image">&larr;</button>
                    <button class="lightbox-next" aria-label="Next image">&rarr;</button>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', lightboxHTML);
    }
    
    // Initialize the lightbox
    initLightbox();
});

function initLightbox() {
    // Get all gallery items
    const galleryItems = document.querySelectorAll('.gallery-item');
    if (galleryItems.length === 0) return;
    
    // Get lightbox elements
    const lightbox = document.getElementById('simple-lightbox');
    const lightboxImage = lightbox.querySelector('.lightbox-image');
    const lightboxCaption = lightbox.querySelector('.lightbox-caption');
    const closeBtn = lightbox.querySelector('.lightbox-close');
    const prevBtn = lightbox.querySelector('.lightbox-prev');
    const nextBtn = lightbox.querySelector('.lightbox-next');
    
    // Convert NodeList to Array for easier manipulation
    const galleryArray = Array.from(galleryItems);
    let currentIndex = 0;
    
    // Function to show a specific image
    function showImage(index) {
        currentIndex = index;
        const item = galleryArray[index];
        
        // Get the image source from the data-src attribute or from the img tag
        const imgSrc = item.dataset.src || item.querySelector('img').src;
        
        // Get the alt text or caption
        const imgAlt = item.querySelector('img').alt || '';
        
        // Set the image source and caption
        lightboxImage.src = imgSrc;
        lightboxCaption.textContent = imgAlt;
        
        // Show the lightbox
        lightbox.classList.add('active');
    }
    
    // Add click event to each gallery item
    galleryItems.forEach((item, index) => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            showImage(index);
        });
    });
    
    // Close button event
    closeBtn.addEventListener('click', function() {
        lightbox.classList.remove('active');
    });
    
    // Close when clicking outside the image
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) {
            lightbox.classList.remove('active');
        }
    });
    
    // Previous button event
    prevBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        const newIndex = (currentIndex - 1 + galleryArray.length) % galleryArray.length;
        showImage(newIndex);
    });
    
    // Next button event
    nextBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        const newIndex = (currentIndex + 1) % galleryArray.length;
        showImage(newIndex);
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (lightbox.classList.contains('active')) {
            if (e.key === 'ArrowLeft') {
                prevBtn.click();
            } else if (e.key === 'ArrowRight') {
                nextBtn.click();
            } else if (e.key === 'Escape') {
                lightbox.classList.remove('active');
            }
        }
    });
    
    console.log('Lightbox initialized with', galleryItems.length, 'images');
}

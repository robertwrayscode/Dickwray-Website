/* ============================================
   Dick Wray Art Portfolio - Main JavaScript
   Pure static JS — no PHP dependencies
   ============================================ */

/* ------------------------------------------
   Theme Toggle (global for onclick attributes)
   ------------------------------------------ */
window.toggleTheme = function () {
    var root = document.documentElement;
    var isLight = root.classList.toggle('light-theme');
    var theme = isLight ? 'light' : 'dark';

    // Swap theme icon
    var themeIcon = document.querySelector('.theme-toggle i');
    if (themeIcon) {
        themeIcon.className = isLight ? 'fas fa-sun' : 'fas fa-moon';
    }

    // Swap logo images
    var logos = document.querySelectorAll('#logo-image, .footer-logo img');
    logos.forEach(function (logo) {
        logo.src = isLight
            ? 'assets/images/branding/dickwray-logo_INVERTED.png'
            : 'assets/images/branding/dickwray-logo_white.png';
    });

    // Swap signature images
    var signatures = document.querySelectorAll('.signature-image');
    signatures.forEach(function (sig) {
        sig.src = isLight
            ? 'assets/images/branding/Signature_black.png'
            : 'assets/images/branding/Signature_white.png';
    });

    localStorage.setItem('theme', theme);
};

/* ------------------------------------------
   DOMContentLoaded — everything else
   ------------------------------------------ */
document.addEventListener('DOMContentLoaded', function () {

    /* ---- Apply saved theme ---- */
    var savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.documentElement.classList.add('light-theme');

        var themeIcon = document.querySelector('.theme-toggle i');
        if (themeIcon) {
            themeIcon.className = 'fas fa-sun';
        }

        var logos = document.querySelectorAll('#logo-image, .footer-logo img');
        logos.forEach(function (logo) {
            logo.src = 'assets/images/branding/dickwray-logo_INVERTED.png';
        });

        var signatures = document.querySelectorAll('.signature-image');
        signatures.forEach(function (sig) {
            sig.src = 'assets/images/branding/Signature_black.png';
        });
    }

    /* ---- Page Loader ---- */
    var loader = document.querySelector('.loader-container');
    if (loader) {
        setTimeout(function () {
            loader.classList.add('fade-out');
            setTimeout(function () {
                var splitTexts = document.querySelectorAll('.split-text');
                splitTexts.forEach(function (el) {
                    el.classList.add('active');
                });
            }, 300);
        }, 1500);
    }

    /* ---- Copyright Year ---- */
    var yearEl = document.getElementById('year');
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }
    var currentYearEl = document.getElementById('current-year');
    if (currentYearEl) {
        currentYearEl.textContent = new Date().getFullYear();
    }

    /* ---- Hero Slideshow ---- */
    var heroSlideshow = document.getElementById('hero-slideshow');
    if (heroSlideshow) {
        var slides = heroSlideshow.querySelectorAll('.slide');
        if (slides.length > 1) {
            var currentSlide = 0;
            setInterval(function () {
                slides[currentSlide].classList.remove('active');
                currentSlide = (currentSlide + 1) % slides.length;
                slides[currentSlide].classList.add('active');
            }, 5000);
        }
    }

    /* ---- Header Scroll Effect ---- */
    var header = document.querySelector('header');
    if (header) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    /* ---- Mobile Navigation ---- */
    var burger = document.querySelector('.burger');
    var navLinks = document.querySelector('.nav-links');

    if (burger && navLinks) {
        burger.addEventListener('click', function () {
            navLinks.classList.toggle('active');
            burger.classList.toggle('active');

            // Staggered fade-in for nav links
            var links = navLinks.querySelectorAll('li');
            links.forEach(function (link, index) {
                if (link.style.animation) {
                    link.style.animation = '';
                } else {
                    link.style.animation = 'navLinkFade 0.5s ease forwards ' + (index / 7 + 0.3) + 's';
                }
            });
        });

        // Dropdown menus on mobile — tap parent to expand, tap sub-link to navigate
        var dropdowns = navLinks.querySelectorAll('.dropdown');
        dropdowns.forEach(function (dropdown) {
            var parentLink = dropdown.querySelector(':scope > a');
            if (parentLink) {
                parentLink.addEventListener('click', function (e) {
                    if (window.innerWidth <= 768) {
                        e.preventDefault();
                        e.stopPropagation();
                        // Close other open dropdowns
                        dropdowns.forEach(function (other) {
                            if (other !== dropdown) other.classList.remove('active-mobile');
                        });
                        dropdown.classList.toggle('active-mobile');
                    }
                });
            }
        });

        // Close menu when a nav sub-link is clicked (but not the dropdown parent)
        var subLinks = navLinks.querySelectorAll('.dropdown-menu a, .nav-links > li:not(.dropdown) > a');
        subLinks.forEach(function (link) {
            link.addEventListener('click', function () {
                navLinks.classList.remove('active');
                burger.classList.remove('active');
                dropdowns.forEach(function (d) { d.classList.remove('active-mobile'); });
                var items = navLinks.querySelectorAll('li');
                items.forEach(function (item) {
                    item.style.animation = '';
                });
            });
        });
    }

    /* ---- Lightbox ---- */
    var galleryItems = document.querySelectorAll('.gallery-item');
    var lightbox = document.querySelector('.lightbox');
    var lightboxContent = document.querySelector('.lightbox-content');
    var currentImageIndex = 0;

    if (galleryItems.length > 0 && lightbox && lightboxContent) {
        var closeBtn = lightbox.querySelector('.close');
        var prevBtn = lightbox.querySelector('.prev');
        var nextBtn = lightbox.querySelector('.next');

        function openLightbox(index) {
            currentImageIndex = index;
            var src = galleryItems[index].getAttribute('data-src');
            lightboxContent.src = src;
            lightbox.style.display = 'flex';
        }

        function closeLightbox() {
            lightbox.style.display = 'none';
        }

        function showPrev() {
            currentImageIndex = (currentImageIndex - 1 + galleryItems.length) % galleryItems.length;
            lightboxContent.src = galleryItems[currentImageIndex].getAttribute('data-src');
        }

        function showNext() {
            currentImageIndex = (currentImageIndex + 1) % galleryItems.length;
            lightboxContent.src = galleryItems[currentImageIndex].getAttribute('data-src');
        }

        galleryItems.forEach(function (item, index) {
            item.addEventListener('click', function () {
                openLightbox(index);
            });
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', closeLightbox);
        }
        if (prevBtn) {
            prevBtn.addEventListener('click', showPrev);
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', showNext);
        }

        // Close on click outside image
        lightbox.addEventListener('click', function (e) {
            if (e.target === lightbox) {
                closeLightbox();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', function (e) {
            if (lightbox.style.display === 'flex') {
                if (e.key === 'Escape') {
                    closeLightbox();
                } else if (e.key === 'ArrowLeft') {
                    showPrev();
                } else if (e.key === 'ArrowRight') {
                    showNext();
                }
            }
        });
    }

    /* ---- 3D Tilt Effect ---- */
    var tiltElements = document.querySelectorAll('.tilt');
    tiltElements.forEach(function (el) {
        el.addEventListener('mousemove', function (e) {
            var rect = el.getBoundingClientRect();
            var x = e.clientX - rect.left;
            var y = e.clientY - rect.top;
            var centerX = rect.width / 2;
            var centerY = rect.height / 2;
            var rotateX = ((y - centerY) / centerY) * -10;
            var rotateY = ((x - centerX) / centerX) * 10;
            el.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) scale3d(1.02, 1.02, 1.02)';
        });

        el.addEventListener('mouseleave', function () {
            el.style.transform = '';
        });
    });

    /* ---- Scroll Reveal Animations ---- */
    var revealElements = document.querySelectorAll('.reveal');
    var masonryItems = document.querySelectorAll('.masonry-item');

    function handleScrollReveal() {
        var windowHeight = window.innerHeight;

        revealElements.forEach(function (el) {
            var top = el.getBoundingClientRect().top;
            if (top < windowHeight - 150) {
                el.classList.add('active');
            }
        });

        masonryItems.forEach(function (item, index) {
            var top = item.getBoundingClientRect().top;
            if (top < windowHeight - 150) {
                setTimeout(function () {
                    item.classList.add('active');
                }, index * 100);
            }
        });
    }

    if (revealElements.length > 0 || masonryItems.length > 0) {
        window.addEventListener('scroll', handleScrollReveal);
        handleScrollReveal();
    }

    /* ---- Scroll to Top Button ---- */
    var scrollTopBtn = document.querySelector('.scroll-to-top');
    if (scrollTopBtn) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 300) {
                scrollTopBtn.classList.add('active');
            } else {
                scrollTopBtn.classList.remove('active');
            }
        });

        scrollTopBtn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    /* ---- Contact Form (Formspree) ---- */
    var contactForm = document.getElementById('contact-form');
    if (contactForm) {
        // Floating labels
        var formGroups = contactForm.querySelectorAll('.form-group');
        formGroups.forEach(function (group) {
            var input = group.querySelector('input, textarea');
            var label = group.querySelector('label');
            if (input && label) {
                input.addEventListener('blur', function () {
                    if (input.value.trim() !== '') {
                        label.classList.add('active');
                    } else {
                        label.classList.remove('active');
                    }
                });
                // Check initial state
                if (input.value.trim() !== '') {
                    label.classList.add('active');
                }
            }
        });

        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();

            var formData = new FormData(contactForm);
            var actionUrl = contactForm.action;

            // Basic validation
            var isValid = true;
            var requiredFields = contactForm.querySelectorAll('[required]');
            requiredFields.forEach(function (field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            if (!isValid) {
                return;
            }

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: { 'Accept': 'application/json' }
            })
            .then(function (response) {
                if (response.ok) {
                    var successMsg = document.getElementById('form-success');
                    if (successMsg) {
                        successMsg.style.display = 'block';
                        setTimeout(function () {
                            successMsg.style.display = 'none';
                        }, 5000);
                    }
                    contactForm.reset();
                    // Reset floating labels
                    formGroups.forEach(function (group) {
                        var label = group.querySelector('label');
                        if (label) {
                            label.classList.remove('active');
                        }
                    });
                }
            })
            .catch(function () {
                // Silently handle error
            });
        });
    }

    /* ---- Smooth Scrolling ---- */
    var smoothLinks = document.querySelectorAll('a[href^="#"]');
    smoothLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;
            var target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                var headerHeight = document.querySelector('header')
                    ? document.querySelector('header').offsetHeight
                    : 0;
                var targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                window.scrollTo({ top: targetPosition, behavior: 'smooth' });
            }
        });
    });

});

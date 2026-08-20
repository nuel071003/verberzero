// Particles.js Configuration for AI Theme background
document.addEventListener("DOMContentLoaded", function() {
    if(document.getElementById('particles-js')) {
        particlesJS("particles-js", {
            "particles": {
                "number": {
                    "value": 60,
                    "density": {
                        "enable": true,
                        "value_area": 800
                    }
                },
                "color": {
                    "value": ["#00f2fe", "#4facfe", "#7c3aed"]
                },
                "shape": {
                    "type": "circle",
                    "stroke": {
                        "width": 0,
                        "color": "#000000"
                    }
                },
                "opacity": {
                    "value": 0.4,
                    "random": true,
                    "anim": {
                        "enable": true,
                        "speed": 1,
                        "opacity_min": 0.1,
                        "sync": false
                    }
                },
                "size": {
                    "value": 3,
                    "random": true,
                    "anim": {
                        "enable": false
                    }
                },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#4facfe",
                    "opacity": 0.2,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 1.5,
                    "direction": "none",
                    "random": true,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false,
                    "attract": {
                        "enable": false,
                        "rotateX": 600,
                        "rotateY": 1200
                    }
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": {
                        "enable": true,
                        "mode": "grab"
                    },
                    "onclick": {
                        "enable": true,
                        "mode": "push"
                    },
                    "resize": true
                },
                "modes": {
                    "grab": {
                        "distance": 140,
                        "line_linked": {
                            "opacity": 0.8
                        }
                    },
                    "push": {
                        "particles_nb": 3
                    }
                }
            },
            "retina_detect": true
        });
    }

    // Form Loading State Handling
    const form = document.getElementById('detectionForm');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const btnSubmit = document.getElementById('btnSubmit');

    if(form && loadingIndicator && btnSubmit) {
        form.addEventListener('submit', function(e) {
            // Check if input is valid
            const urlInput = document.getElementById('urlInput');
            if (urlInput.value.trim() === '') {
                e.preventDefault();
                return;
            }

            // Show Loading state
            btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Memproses...';
            btnSubmit.classList.add('disabled');
            loadingIndicator.classList.remove('d-none');
            
            // Allow form to submit natively to the server
        });
    }
});

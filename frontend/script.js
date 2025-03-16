// Function to remove or hide images based on detected card names
function updateGallery(detectedCards) {
    // Get all the images in the gallery
    const images = document.querySelectorAll('.gallery img');

    // Iterate through each image
    images.forEach(image => {
        // Check if the alt attribute of the image matches any of the detected card names
        if (detectedCards.includes(image.alt)) {
            // If a match is found, remove or hide the image
            image.style.display = 'none'; // You can use 'none' to hide or 'remove()' to remove from the DOM
        } else {
            // If no match is found, make sure the image is visible
            image.style.display = 'block'; // Display the image
        }
    });
}

// Function to fetch detected cards from Flask server and update the gallery
function fetchDetectedCardsAndUpdateGallery() {
    fetch('http://localhost:5001/cards')
        .then(response => response.json()) // Parse JSON response
        .then(data => {
            // Assign the detected cards to the global variable
            const detectedCards = data.detected_cards;

            // Update the gallery based on the detected cards
            updateGallery(detectedCards);
        })
        .catch(error => console.error('Error fetching detected cards:', error));
}

// Call the fetchDetectedCardsAndUpdateGallery function initially
fetchDetectedCardsAndUpdateGallery();

// Call the fetchDetectedCardsAndUpdateGallery function every second
setInterval(fetchDetectedCardsAndUpdateGallery, 1000);

// Keep track of all detected cards across updates
let cumulativeDetectedCards = new Set();
let lastImageUpdate = 0;
let lastCardsUpdate = 0;
const UPDATE_INTERVAL = 1000; // Increased to 1 second to reduce file conflicts
const ERROR_THRESHOLD = 3;
const RETRY_DELAY = 2000;
let errorCount = 0;
let consecutiveErrors = 0;
let lastErrorTime = 0;

// Get the image element
const liveImage = document.getElementById('live-image');

// Function to handle errors with exponential backoff
function handleError(error, context) {
    console.error(`Error in ${context}:`, error);
    const now = Date.now();
    
    if (now - lastErrorTime < 5000) {
        consecutiveErrors++;
    } else {
        consecutiveErrors = 1;
    }
    
    lastErrorTime = now;
    
    if (consecutiveErrors >= ERROR_THRESHOLD) {
        const delay = Math.min(RETRY_DELAY * Math.pow(2, consecutiveErrors - ERROR_THRESHOLD), 10000);
        console.warn(`Too many consecutive errors, waiting ${delay}ms before retry`);
        setTimeout(updateAll, delay);
        consecutiveErrors = 0;
        return true;
    }
    return false;
}

// Function to update the live image with debouncing and error handling
function updateImage() {
    const now = Date.now();
    if (now - lastImageUpdate < UPDATE_INTERVAL) return;
    lastImageUpdate = now;

    fetch(`/picture?${now}`)
        .then(response => {
            if (!response.ok) throw new Error(`Failed to load image: ${response.status}`);
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const tempImage = new Image();
            
            tempImage.onload = () => {
                if (liveImage.src) {
                    URL.revokeObjectURL(liveImage.src);
                }
                liveImage.src = url;
                consecutiveErrors = 0;
            };
            
            tempImage.onerror = () => {
                console.error('Failed to load image');
                URL.revokeObjectURL(url);
                if (!handleError(new Error('Image load failed'), 'image loading')) {
                    setTimeout(updateImage, 1000);
                }
            };
            
            tempImage.src = url;
        })
        .catch(error => {
            if (!handleError(error, 'image fetch')) {
                setTimeout(updateImage, 1000);
            }
        });
}

// Function to update detected cards with debouncing and error handling
function updateDetectedCards() {
    const now = Date.now();
    if (now - lastCardsUpdate < UPDATE_INTERVAL) return;
    lastCardsUpdate = now;

    fetch('/cards')
        .then(response => {
            if (!response.ok) throw new Error(`Failed to fetch cards: ${response.status}`);
            return response.json();
        })
        .then(detectedCards => {
            consecutiveErrors = 0;

            // If no cards are detected, reset everything
            if (!Array.isArray(detectedCards) || detectedCards.length === 0) {
                if (cumulativeDetectedCards.size > 0) {
                    console.log('No cards detected, resetting...');
                    cumulativeDetectedCards.clear();
                    document.querySelectorAll('.card').forEach(card => {
                        card.style.opacity = '1';
                        card.style.filter = 'none';
                    });
                }
                return;
            }

            // Add newly detected cards to our cumulative set
            detectedCards.forEach(card => {
                if (!cumulativeDetectedCards.has(card)) {
                    console.log('New card detected:', card);
                    cumulativeDetectedCards.add(card);
                }
            });

            // Update all cards based on cumulative detections
            document.querySelectorAll('.card').forEach(card => {
                const cardImg = card.querySelector('img');
                if (!cardImg) return;
                
                const cardAlt = cardImg.alt;
                if (cumulativeDetectedCards.has(cardAlt)) {
                    card.style.opacity = '0.3';
                    card.style.filter = 'grayscale(100%)';
                }
            });
        })
        .catch(error => {
            if (!handleError(error, 'cards fetch')) {
                setTimeout(updateDetectedCards, 1000);
            }
        });
}

// Update both image and cards status
function updateAll() {
    updateImage();
    updateDetectedCards();
}

// Start updates with initial delay to ensure DOM is ready
setTimeout(() => {
    updateAll();
    setInterval(updateAll, UPDATE_INTERVAL);
}, 100);

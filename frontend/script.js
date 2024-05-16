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


// Function to reload the live image every second
setInterval(function() {
    // Get the image element
    const liveImage = document.getElementById('live-image');

    // Reload the image by changing its src attribute
    const timestamp = new Date().getTime(); // Add timestamp to ensure browser refreshes the image
    fetch('http://localhost:5001/picture?' + timestamp)
        .then(response => {
            if (!response.ok) {
                throw new Error('Server is down');
            }
            liveImage.src = response.url;
            liveImage.alt = 'Live Image';
        })
        .catch(error => {
            // Set alt text to "Server is down"
            liveImage.alt = error.message;
        });
}, 1000); // Update every 1 second (1000 milliseconds)

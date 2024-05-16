# Jawaker-YOLO

A new version of the object detection app (trained for 20 hours on a custom dataset) can now identify cards in the game and indicate which ones are remaining.

## Overview

The Card Detection App is a computer vision application designed to detect and identify cards in a game environment. It utilizes deep learning techniques for object detection and classification to accurately recognize various types of playing cards.

## Features

- **Object Detection**: The app uses advanced object detection algorithms to identify cards within the game environment.
  
- **Card Recognition**: Once detected, the app can recognize and classify different types of playing cards, including suits (hearts, diamonds, clubs, spades) and values (2 through King).

- **Real-time Updates**: The app provides real-time updates on the status of cards remaining in the game, allowing players to track which cards have been played and which are still available.

- **Customizable Screen Capture**: Users can adjust the location from which the app captures the game screen by modifying the `ScreenCapture` class parameters.

## Installation

To install the Card Detection App, follow these steps:

1. Clone the repository to your local machine:

    ```
    git clone https://github.com/yourusername/card-detection-app.git
    ```

2. Install the required dependencies:

    ```
    pip install -r requirements.txt
    ```

3. Run the application:

    ```
    python main.py
    ```

## Customizable Screen Capture

The `ScreenCapture` class allows users to adjust the location from which the application captures the game screen. To customize the screen capture region, follow these steps:

1. Open the `detecting.py` file in your preferred text editor.

2. Locate the `ScreenCapture` class definition within the code.

3. Inside the `crop_image` method, you'll find the `crop_region` variable, which defines the coordinates of the region to capture. The coordinates are represented as `(left, top, right, bottom)`.

4. Adjust the values of the `crop_region` variable to specify the desired capture region. For example, if you need to capture a different region of the screen, modify the coordinates accordingly.

   Example:
   ```python
   crop_region = (880, 100, 1080, 380)
   ```

## Usage

Once the application is running, follow these steps to use it:

1. **Launch the Application:** Ensure your game environment is inside the area that is being captured.

   *Check the Customizable Screen Capture section for instructions on adjusting the capture area.*

2. **Detection Process:** The app will begin detecting and identifying cards in real-time.

3. **View Status Updates:** 
   - Open your web browser and navigate to `localhost:5001`.
   - View the status updates to see which cards have been detected and which are still remaining.


## Contributing

Contributions to the Card Detection App are welcome! If you'd like to contribute, please follow these steps:

1. Fork the repository.

2. Create a new branch for your feature or bug fix:

    ```
    git checkout -b feature-branch
    ```

3. Make your changes and commit them with descriptive messages:

    ```
    git commit -m "Add new feature"
    ```

4. Push your changes to your fork:

    ```
    git push origin feature-branch
    ```

5. Open a pull request on the main repository.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For questions, issues, or feedback, please contact [Your Name](mailto:youremail@example.com).

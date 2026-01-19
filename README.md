# Mollusc Shell 3D Generator

This is an interactive web application built with Python and Streamlit for generating, visualizing, and exporting 3D models of mollusc shells. The tool allows users to simulate various shell morphologies in order to explore the theoretical morphospace, by simply inputting and adjusting parameters.

## Usage
The interface is divided into the Sidebar (settings) and the Main Area (parameters and visualization).

### 1. Sidebar Settings
*   **Theme**: Switch between Night, Day, and Matrix themes. In Matrix mode, you can toggle the code rain animation on/off.
*   **Appearance**: Set the shell color, transparency, and wall thickness. Toggle the grid, the underlying Logarithmic curve, or the Frenet-Serret frame.
*   **Render Mode**: Choose how the model is drawn (Surface, Wireframe, or Points).
*   **Overlay Image**: Upload a PNG/JPG image to overlay on the canvas for comparison.

### 2. Main Area: Parameter Estimation
A tool to help you find starting parameters based on physical measurements of a shell. For a detailed guide, please refer to the mathematical background.
Click **Apply estimates** to update the main sliders with these calculated values.

### 3. Main Area: Fine-Tuning
Manually adjust the specific mathematical parameters:
*   **b (Expansion)**: Controls how quickly the shell widens.
*   **d (Displacement)**: The distance of the aperture from the central axis.
*   **z (Transition)**: Controls the vertical elongation (flat spiral vs. tall spiral).
*   **a (Ellipticity)**: The ratio of width to height of the aperture.
*   **Rotations (φ, δ, ψ)**: Adjust the orientation of the aperture relative to the curve.
*   **Oscillations (m1, n1, m2, n2)**: Create surface textures (ribs or bumps).
*   **Number of Turns**: How many times the spiral rotates.

### 4. Downloading Results
Once the model is generated:
*   **Download STL**: Click to save the 3D geometry. This file can be opened in slicers for 3D printing.
*   **Download PNG**: Click to save a high-quality image.




## Installation
To run this application locally, you need Python 3.8 or higher installed on your system.

1.  **Clone the repository**
    ```bash
    git clone https://github.com/your-username/mollusc-shell-generator.git
    cd mollusc-shell-generator
    ```

2.  **Create a virtual environment (if needed)**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    Ensure `requirements.txt` contains the libraries you will need:
    *   `streamlit`
    *   `numpy`
    *   `plotly`
    *   `kaleido`
    *   ......

4.  **Run the application**
    ```bash
    streamlit run shell_app.py
    ```
    The application will launch automatically in your default web browser.


## Credits

**App developed by**: Ziyue Xu, Department of Ocean Science, The Hong Kong University of Science and Technology
**Contact**: Ziyue-Xu@outlook.com, zxudk@connect.ust.hk

**Reference**:
This work is largely based on the model proposed by: Contreras-Figueroa & Aragón (2023), Diversity 15(3):431
# ErsatzTV Graphics Engine Designer

A powerful, visual desktop application for designing dynamic overlays and graphics for [ErsatzTV](https://ersatztv.org/). Built with Python and NiceGUI.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

The **ErsatzTV Graphics Engine Designer** allows you to visually create, animate, and preview overlays for your channels. Instead of writing complex configuration files manually, use this drag-and-drop editor to design your scenes and export them directly for use with ErsatzTV's custom graphics system.

## Features

*   **Visual Editor**: Drag-and-drop interface for Text, Shapes, and Images.
*   **Real-time Preview**: See your animations play out instantly with a live playback loop.
*   **Layer Management**: Reorder, hide, and manage multiple elements easily.
*   **Advanced Animations**:
    *   **Entrance & Exit Animations**: Fade, Slide, Zoom, and more.
    *   **Custom Timing**: Precise control over when elements appear and disappear.
    *   **Presets**: Built-in animation presets for quick professional results.
*   **Project Management**: Save and load your designs (`.json` format) to work on them later.
*   **Export Support**:
    *   **Python Renderer**: Export a standalone Python script that renders your scene.
    *   **ErsatzTV Script**: (Coming Soon) Direct YAML export for ErsatzTV.
*   **Customizable Scene**: Set custom resolutions (e.g., 1920x1080), FPS, and loop durations.

## Installation

### Prerequisites

*   Python 3.8 or higher
*   pip (Python Package Installer)

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/bluchip-studio-official/ErsatzTV-Graphics-Engine-Designer.git
    cd ErsatzTV-Graphics-Engine-Designer
    ```

2.  **Install Dependencies**
    It is recommended to use a virtual environment.
    ```bash
    # Create virtual environment (optional but recommended)
    python -m venv venv
    
    # Activate script (Windows)
    .\venv\Scripts\activate
    
    # Activate script (Linux/Mac)
    source venv/bin/activate
    ```

    Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the application using Python:

```bash
python app.py
```

The application will launch in a native desktop window. 

1.  **Add Elements**: Use the specific buttons on the left panel to add Text, Shapes, or Images.
2.  **Edit Properties**: Select an element to modify its position, color, size, and other properties in the right inspector panel.
3.  **Animate**: Expand the "Animations" section in the inspector to assign entrance and exit effects.
4.  **Preview**: The center canvas shows a live loop of your scene.
5.  **Export**: Use the button in the header to save your project or export the Python renderer script.

## Dependencies

*   [NiceGUI](https://nicegui.io/) - For the beautiful and responsive user interface.
*   [Pillow (PIL)](https://python-pillow.org/) - For image processing and rendering.
*   [NumPy](https://numpy.org/) - For efficient numerical operations.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the repository
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## Example YML

```yml
# Path to interpreter/command and arguments
command: python3
args:
  - "/files/scripts/test.py"

# Graphics engine draws script output on top of video
# z_index controls stacking order: higher numbers are drawn last (on top)
z_index: 300

# When to start showing this element (in seconds from content start)
start_seconds: 0

# How long to keep it on screen (e.g., 30 seconds)
duration_seconds: 30

# Data output format
# 'raw' means full BGRA frames from stdout
# 'packet' means ETV graphics packets from stdout
format: raw
```

## 👤 Author

**Bluchip Studio**

*   GitHub: [@bluchip-studio-official](https://github.com/bluchip-studio-official)

---

*Verified to run on Windows, macOS, and Linux.*

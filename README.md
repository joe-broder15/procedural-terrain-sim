# Procedural Terrain Simulation

A 3D procedural terrain generator that creates low-poly terrain using noise algorithms.

## Features

- Procedural terrain generation using multiple noise algorithms (Perlin, Simplex, Value, Ridged)
- Pronounced low-poly rendering style with visible triangles
- Light blue skybox for better visual context
- Free-floating camera with WASD/arrow key controls
- Mouse-controlled camera rotation
- Overview camera mode (default view, shows entire terrain from 45° angle)
- Simple command line customization options
- Cursor toggle functionality ('Q' key)
- Resizable window with proper perspective adjustment

## Requirements

- Python 3.7+
- PyOpenGL
- Pygame
- NumPy
- noise (Python noise library)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the simulation with default settings:
```
python main.py
```

### Command Line Arguments

You can customize the terrain and display settings using command line arguments:

```
python main.py --size 128 --seed 42 --noise-type simplex
```

Available arguments:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--size` | int | 128 | Size of the terrain grid |
| `--noise-type` | string | 'perlin' | Type of noise to generate (perlin, simplex, value, ridged) |
| `--seed` | int | random | Random seed for terrain generation |
| `--width` | int | 800 | Width of the display window |
| `--height` | int | 600 | Height of the display window |

### Controls

- **W/Up Arrow**: Move forward
- **S/Down Arrow**: Move backward
- **A/Left Arrow**: Strafe right
- **D/Right Arrow**: Strafe left
- **Space**: Move up
- **Left Shift**: Move down
- **Mouse**: Look around
- **Q**: Toggle cursor capture (release/recapture cursor)
- **E**: Reset to terrain overview (45° angle view of entire terrain)
- **Escape**: Exit the simulation

### Window Management

- **Resize**: Drag window edges or corners to resize the window
- The 3D perspective will automatically adjust to maintain the correct aspect ratio

## Noise Types

The simulation supports four different noise algorithms for terrain generation:

- **Perlin**: Classic Perlin noise, produces smooth, natural-looking terrain
- **Simplex**: Similar to Perlin but with fewer directional artifacts and better performance
- **Value**: Simple value noise, creates more blocky, less natural terrain
- **Ridged**: Ridged multifractal noise, good for mountain ranges with sharp ridges

## Low-Poly Style

The terrain is rendered with a distinct low-poly aesthetic:
- Larger, more visible triangles make up the terrain surface
- Flat shading is used to emphasize the triangular structure
- Each triangle has a uniform color to enhance the low-poly look
- Subtle height-based coloring provides depth perception

## Code Structure

The simulation is organized into a modular structure for better maintainability and readability:

### Main Components

- `main.py`: Entry point for the application
- `src/simulation.py`: Main simulation class that coordinates all components

### Packages

- `src/terrain/`: Terrain generation modules
  - `generator.py`: Procedural terrain generation using various noise algorithms
  
- `src/rendering/`: Rendering-related modules
  - `camera.py`: Camera system for navigating the 3D environment
  - `skybox.py`: Skybox rendering functionality
  
- `src/utils/`: Utility modules
  - `constants.py`: Application-wide constants and OpenGL imports
  - `args_parser.py`: Command line argument parsing

This modular structure makes the code easier to understand, maintain, and extend with new features.

## Examples

Generate terrain with a specific seed:
```
python main.py --seed 42
```

Generate terrain using Simplex noise:
```
python main.py --noise-type simplex
```

Generate a larger terrain:
```
python main.py --size 256
```

Run with a larger display window:
```
python main.py --width 1280 --height 720
```
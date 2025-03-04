# Procedural Terrain Simulator

A 3D terrain generator and viewer that creates realistic landscapes using various procedural noise algorithms. Built with Python, PyOpenGL, and Pygame, this application renders interactive 3D terrain in real-time.

## Features

- **Multiple Noise Algorithms:**
  - Perlin: Classic smooth noise pattern
  - Simplex: Improved version of Perlin noise
  - Ridged: Creates mountain-like ridges
  - Billow: Produces cloud-like formations
  - Voronoi: Creates cell-like patterns
  - Combined: Blends Perlin and Simplex for varied terrain

- **Interactive Camera Controls:**
  - **Orbit Mode (Default):** Rotate around and zoom in/out of the terrain
  - **Fly Mode:** First-person camera with WASD movement and mouse look

- **Customizable Parameters:**
  - Adjust noise settings (octaves, persistence, lacunarity, scale)
  - Control terrain size and height
  - Set random seed for reproducible results

## Requirements

- Python 3.x
- Pygame
- PyOpenGL
- NumPy
- noise (Python noise library)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/procedural-terrain-sim.git
   cd procedural-terrain-sim
   ```

2. Install the required dependencies:
   ```bash
   pip install pygame PyOpenGL numpy noise
   ```

## Usage

Run the simulator with default settings:

```bash
python main.py
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--noise` | string | `perlin` | Noise algorithm (`perlin`, `simplex`, `ridged`, `billow`, `voronoi`, `combined`) |
| `--seed` | integer | Random | Seed for random generation |
| `--octaves` | integer | 6 | Number of noise octaves (detail levels) |
| `--persistence` | float | 0.5 | How much each octave contributes to the overall shape |
| `--lacunarity` | float | 2.0 | How frequency increases with each octave |
| `--scale` | float | 5.0 | Overall scale of the noise pattern |
| `--height-scale` | float | 2.0 | Vertical exaggeration of the terrain |
| `--size` | integer | 25 | Size of the terrain grid (NxN) |
| `--fly` | flag | False | Enable fly camera mode |

### Examples

Generate terrain with Simplex noise and custom parameters:
```bash
python main.py --noise simplex --seed 42 --octaves 8 --persistence 0.6 --scale 4.0
```

Use Voronoi noise with a larger grid:
```bash
python main.py --noise voronoi --size 40 --height-scale 3.0
```

Explore terrain in fly mode:
```bash
python main.py --fly
```

## Controls

### Orbit Mode (Default)
| Control | Action |
|---------|--------|
| Arrow Keys | Rotate terrain view |
| + / = | Zoom in |
| - | Zoom out |
| E | Reset view |
| Q | Toggle mouse capture |
| ESC | Exit application |

### Fly Mode (--fly)
| Control | Action |
|---------|--------|
| W | Move forward |
| S | Move backward |
| A | Strafe left |
| D | Strafe right |
| Space | Move up |
| Left Shift | Move down |
| Mouse | Look around |
| E | Reset camera position |
| Q | Toggle mouse capture |
| ESC | Exit application |

## How It Works

The terrain is generated using procedural noise algorithms to create a height map. This height map is then converted into a 3D mesh with vertices and triangles. The mesh is rendered using OpenGL with proper lighting and shading.

The application uses:
- PyOpenGL for 3D rendering
- Pygame for window management and input handling
- NumPy for efficient array operations
- Python noise library for procedural noise generation

## License

This project is open-source. Feel free to modify and distribute it as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

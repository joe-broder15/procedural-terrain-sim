# Procedural Terrain Simulation

A low-poly procedural terrain generator that creates terrain based on noise functions. The terrain is rendered in a 3D window with a light blue skybox and overhead lighting.

## Features

- Procedurally generated terrain using multiple noise types:
  - Perlin noise (default)
  - Simplex noise
  - Ridged multifractal noise
  - Billow noise
  - Voronoi-like noise
  - Combined noise (Perlin + Simplex)
- Low-poly aesthetic with light gray terrain
- Light blue skybox
- Isometric view of the terrain
- Overhead lighting for better depth perception
- Interactive camera rotation
- Command line options for customizing terrain generation

## Requirements

- Python 3.6+
- pygame
- PyOpenGL
- PyOpenGL-accelerate
- numpy
- noise

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/procedural-terrain-sim.git
cd procedural-terrain-sim
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

## Usage

Run the simulation with default settings:
```
python main.py
```

### Command Line Options

The simulation supports various command line options to customize the terrain generation:

```
python main.py --noise simplex --seed 42 --octaves 4 --persistence 0.6
```

Available options:

| Option | Description | Default |
|--------|-------------|---------|
| `--noise` | Type of noise to use (`perlin`, `simplex`, `ridged`, `billow`, `voronoi`, `combined`) | `perlin` |
| `--seed` | Seed for random number generation | Random |
| `--octaves` | Number of octaves for noise generation | 6 |
| `--persistence` | Persistence value for noise generation | 0.5 |
| `--lacunarity` | Lacunarity value for noise generation | 2.0 |
| `--scale` | Scale factor for noise | 5.0 |
| `--height-scale` | Scale factor for terrain height | 2.0 |
| `--size` | Size of terrain grid (size x size) | 25 |

### Noise Types

- **Perlin**: Classic Perlin noise, produces smooth, natural-looking terrain
- **Simplex**: Similar to Perlin but with fewer directional artifacts
- **Ridged**: Creates ridge-like formations, good for mountains
- **Billow**: Creates cloud-like, billowy terrain
- **Voronoi**: Creates cell-like patterns, good for alien or crystalline landscapes
- **Combined**: Combines Perlin and Simplex for more varied terrain

### Controls

- **Arrow Keys**: Rotate the camera view
- **Close Window**: Exit the simulation

## Customization

In addition to command line options, you can modify the parameters directly in `main.py` to customize the terrain:

- `TERRAIN_SIZE`: Size of the terrain grid (higher values create more detailed terrain but may reduce performance)
- `TERRAIN_SCALE`: Scale of each terrain cell
- `NOISE_SCALE`: Scale factor for noise (higher values create more varied terrain)
- `NOISE_OCTAVES`: Number of octaves for noise (higher values add more detail)
- `NOISE_PERSISTENCE`: Persistence for noise (controls how quickly amplitudes diminish for successive octaves)
- `NOISE_LACUNARITY`: Lacunarity for noise (controls how quickly frequency increases for successive octaves)
- `TERRAIN_HEIGHT_SCALE`: Scale factor for terrain height
- `TERRAIN_COLOR`: Color of the terrain (default: light gray)
- `SKY_COLOR`: Color of the skybox (default: light blue)
- `ROTATION_SPEED`: Speed of camera rotation

## How It Works

The simulation uses various noise algorithms to generate a height map, which is then used to create a 3D mesh of triangles. The mesh is rendered using OpenGL with proper lighting to enhance the 3D effect.

The terrain is viewed from an isometric perspective, giving a good overview of the generated landscape.

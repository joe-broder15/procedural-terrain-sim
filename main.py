import pygame
from pygame.locals import QUIT, KEYDOWN, KEYUP, K_ESCAPE, K_LEFT, K_RIGHT, K_UP, K_DOWN, K_q, K_e, OPENGL, DOUBLEBUF
from OpenGL.GL import (
    glEnable, glDisable, glClear, glClearColor, glBegin, glEnd, 
    glVertex3fv, glNormal3fv, glColor3f, glMatrixMode, glLoadIdentity,
    glRotatef, glLightfv, glColorMaterial,
    GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL, GL_FRONT_AND_BACK,
    GL_AMBIENT_AND_DIFFUSE, GL_POSITION, GL_AMBIENT, GL_DIFFUSE,
    GL_PROJECTION, GL_MODELVIEW, GL_DEPTH_TEST, GL_TRIANGLES,
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
)
from OpenGL.GLU import gluPerspective, gluLookAt
import numpy as np
import noise
import sys
import math
import argparse
import random

# Configuration
WIDTH, HEIGHT = 800, 600
TERRAIN_SIZE = 25  # Size of terrain grid (TERRAIN_SIZE x TERRAIN_SIZE)
TERRAIN_SCALE = 0.5  # Scale of each terrain cell
NOISE_SCALE = 5.0  # Scale factor for noise
NOISE_OCTAVES = 6  # Number of octaves for noise
NOISE_PERSISTENCE = 0.5  # Persistence for noise
NOISE_LACUNARITY = 2.0  # Lacunarity for noise
TERRAIN_HEIGHT_SCALE = 2.0  # Scale factor for terrain height
TERRAIN_COLOR = (0.8, 0.8, 0.8)  # Light gray
SKY_COLOR = (0.7, 0.8, 0.9, 1.0)  # Light blue
ROTATION_SPEED = 0.5  # Speed of rotation when using arrow keys

class Terrain:
    def __init__(self, noise_type='perlin', seed=None, **noise_params):
        self.vertices = []
        self.triangles = []
        self.noise_type = noise_type
        self.seed = seed if seed is not None else random.randint(0, 10000)
        self.noise_params = noise_params
        self.generate_terrain()
        
    def generate_terrain(self):
        # Generate height map using noise
        height_map = np.zeros((TERRAIN_SIZE, TERRAIN_SIZE))
        
        # Set default noise parameters if not provided
        octaves = self.noise_params.get('octaves', NOISE_OCTAVES)
        persistence = self.noise_params.get('persistence', NOISE_PERSISTENCE)
        lacunarity = self.noise_params.get('lacunarity', NOISE_LACUNARITY)
        scale = self.noise_params.get('scale', NOISE_SCALE)
        height_scale = self.noise_params.get('height_scale', TERRAIN_HEIGHT_SCALE)
        
        # Generate height map based on noise type
        for i in range(TERRAIN_SIZE):
            for j in range(TERRAIN_SIZE):
                nx = i / TERRAIN_SIZE * scale
                ny = j / TERRAIN_SIZE * scale
                
                if self.noise_type == 'perlin':
                    height_map[i][j] = noise.pnoise2(nx, ny, 
                                                  octaves=octaves, 
                                                  persistence=persistence, 
                                                  lacunarity=lacunarity,
                                                  base=self.seed)
                elif self.noise_type == 'simplex':
                    height_map[i][j] = noise.snoise2(nx, ny, 
                                                  octaves=octaves, 
                                                  persistence=persistence, 
                                                  lacunarity=lacunarity,
                                                  base=self.seed)
                elif self.noise_type == 'ridged':
                    # Ridged multifractal noise (absolute value of simplex noise)
                    value = abs(noise.snoise2(nx, ny, 
                                           octaves=octaves, 
                                           persistence=persistence, 
                                           lacunarity=lacunarity,
                                           base=self.seed))
                    height_map[i][j] = 1.0 - value  # Invert to create ridges
                elif self.noise_type == 'billow':
                    # Billow noise (absolute value of perlin noise)
                    value = abs(noise.pnoise2(nx, ny, 
                                           octaves=octaves, 
                                           persistence=persistence, 
                                           lacunarity=lacunarity,
                                           base=self.seed))
                    height_map[i][j] = value * 2.0 - 1.0  # Scale to -1 to 1 range
                elif self.noise_type == 'voronoi':
                    # Simple Voronoi-like noise
                    height_map[i][j] = self._voronoi_noise(nx, ny)
                elif self.noise_type == 'combined':
                    # Combination of perlin and simplex
                    perlin = noise.pnoise2(nx, ny, octaves=octaves, persistence=persistence, 
                                        lacunarity=lacunarity, base=self.seed)
                    simplex = noise.snoise2(nx * 2, ny * 2, octaves=octaves, persistence=persistence, 
                                         lacunarity=lacunarity, base=self.seed + 1000)
                    height_map[i][j] = (perlin + simplex) * 0.5
                else:
                    # Default to perlin
                    height_map[i][j] = noise.pnoise2(nx, ny, 
                                                  octaves=octaves, 
                                                  persistence=persistence, 
                                                  lacunarity=lacunarity,
                                                  base=self.seed)
                
        # Create vertices
        self.vertices = []
        for i in range(TERRAIN_SIZE):
            for j in range(TERRAIN_SIZE):
                x = (i - TERRAIN_SIZE/2) * TERRAIN_SCALE
                z = (j - TERRAIN_SIZE/2) * TERRAIN_SCALE
                y = height_map[i][j] * height_scale
                self.vertices.append((x, y, z))
                
        # Create triangles (indices)
        self.triangles = []
        for i in range(TERRAIN_SIZE - 1):
            for j in range(TERRAIN_SIZE - 1):
                # Calculate vertex indices
                a = i * TERRAIN_SIZE + j
                b = i * TERRAIN_SIZE + (j + 1)
                c = (i + 1) * TERRAIN_SIZE + j
                d = (i + 1) * TERRAIN_SIZE + (j + 1)
                
                # Create two triangles per grid cell
                self.triangles.append((a, b, c))
                self.triangles.append((b, d, c))
    
    def _voronoi_noise(self, x, y):
        # Simple Voronoi-like noise implementation
        # Generate a set of random points
        points = []
        random.seed(self.seed)
        for _ in range(10):  # Number of cells
            points.append((random.random() * 10, random.random() * 10))
        
        # Find distance to closest point
        min_dist = float('inf')
        for px, py in points:
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            min_dist = min(min_dist, dist)
        
        # Normalize and return
        return min_dist / 2.0 - 0.5  # Scale to approximately -0.5 to 0.5 range
    
    def render(self):
        glColor3f(*TERRAIN_COLOR)
        glBegin(GL_TRIANGLES)
        
        for triangle in self.triangles:
            # Calculate normal vector for the triangle for proper lighting
            v1 = np.array(self.vertices[triangle[0]])
            v2 = np.array(self.vertices[triangle[1]])
            v3 = np.array(self.vertices[triangle[2]])
            
            # Calculate normal using cross product
            normal = np.cross(v2 - v1, v3 - v1)
            normal = normal / np.linalg.norm(normal)
            
            # Set normal and draw vertices
            glNormal3fv(normal)
            glVertex3fv(self.vertices[triangle[0]])
            glVertex3fv(self.vertices[triangle[1]])
            glVertex3fv(self.vertices[triangle[2]])
            
        glEnd()

def setup_lighting():
    # Enable lighting
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Set up light position (overhead)
    light_position = [0.0, 10.0, 0.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    
    # Set light properties
    ambient_light = [0.3, 0.3, 0.3, 1.0]
    diffuse_light = [0.7, 0.7, 0.7, 1.0]
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse_light)

def setup_skybox():
    glClearColor(*SKY_COLOR)

def setup_isometric_view():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (WIDTH / HEIGHT), 0.1, 50.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Set up isometric-like view
    # Position the camera to view the terrain from an isometric angle
    gluLookAt(
        10, 10, 10,  # Eye position
        0, 0, 0,     # Look at position
        0, 1, 0      # Up vector
    )

def parse_arguments():
    parser = argparse.ArgumentParser(description='Procedural Terrain Simulation')
    
    # Noise type
    parser.add_argument('--noise', type=str, default='perlin',
                        choices=['perlin', 'simplex', 'ridged', 'billow', 'voronoi', 'combined'],
                        help='Type of noise to use for terrain generation')
    
    # Noise parameters
    parser.add_argument('--seed', type=int, default=None,
                        help='Seed for random number generation')
    parser.add_argument('--octaves', type=int, default=NOISE_OCTAVES,
                        help='Number of octaves for noise generation')
    parser.add_argument('--persistence', type=float, default=NOISE_PERSISTENCE,
                        help='Persistence value for noise generation')
    parser.add_argument('--lacunarity', type=float, default=NOISE_LACUNARITY,
                        help='Lacunarity value for noise generation')
    parser.add_argument('--scale', type=float, default=NOISE_SCALE,
                        help='Scale factor for noise')
    parser.add_argument('--height-scale', type=float, default=TERRAIN_HEIGHT_SCALE,
                        help='Scale factor for terrain height')
    
    # Terrain parameters
    parser.add_argument('--size', type=int, default=TERRAIN_SIZE,
                        help='Size of terrain grid (size x size)')
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Update global parameters based on arguments
    global TERRAIN_SIZE, NOISE_SCALE, NOISE_OCTAVES, NOISE_PERSISTENCE, NOISE_LACUNARITY, TERRAIN_HEIGHT_SCALE
    TERRAIN_SIZE = args.size
    NOISE_SCALE = args.scale
    NOISE_OCTAVES = args.octaves
    NOISE_PERSISTENCE = args.persistence
    NOISE_LACUNARITY = args.lacunarity
    TERRAIN_HEIGHT_SCALE = args.height_scale
    
    # Initialize pygame
    pygame.init()
    display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(f"Procedural Terrain Simulation - {args.noise.capitalize()} Noise")
    
    # Set up OpenGL
    glEnable(GL_DEPTH_TEST)
    setup_lighting()
    setup_skybox()
    setup_isometric_view()
    
    # Generate terrain with specified noise type and parameters
    noise_params = {
        'octaves': args.octaves,
        'persistence': args.persistence,
        'lacunarity': args.lacunarity,
        'scale': args.scale,
        'height_scale': args.height_scale
    }
    
    terrain = Terrain(
        noise_type=args.noise,
        seed=args.seed,
        **noise_params
    )
    
    # Camera rotation angles
    rotation_x = 0
    rotation_y = 0
    
    # Store initial rotation values for reset
    initial_rotation_x = rotation_x
    initial_rotation_y = rotation_y
    
    # Mouse capture state
    mouse_captured = False
    
    # Main loop
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == KEYDOWN:
                # Feature 1: Reset terrain position when 'e' is pressed
                if event.key == K_e:
                    rotation_x = initial_rotation_x
                    rotation_y = initial_rotation_y
                
                # Feature 2: Toggle mouse capture when 'q' is pressed
                elif event.key == K_q:
                    mouse_captured = not mouse_captured
                    pygame.mouse.set_visible(not mouse_captured)
                    if mouse_captured:
                        pygame.event.set_grab(True)
                    else:
                        pygame.event.set_grab(False)
                
                # Feature 3: Exit simulation when 'Escape' is pressed
                elif event.key == K_ESCAPE:
                    running = False
        
        # Handle keyboard input for rotation
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            rotation_y += ROTATION_SPEED
        if keys[pygame.K_RIGHT]:
            rotation_y -= ROTATION_SPEED
        if keys[pygame.K_UP]:
            rotation_x += ROTATION_SPEED
        if keys[pygame.K_DOWN]:
            rotation_x -= ROTATION_SPEED
        
        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Apply rotations
        glLoadIdentity()
        gluLookAt(10, 10, 10, 0, 0, 0, 0, 1, 0)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        
        # Render terrain
        terrain.render()
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Ensure mouse is visible and not captured when exiting
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

"""
Procedural Terrain Simulator
----------------------------
A 3D terrain generator and viewer using procedural noise algorithms.

This application generates and renders 3D terrain using various noise algorithms
(Perlin, Simplex, Ridged, Billow, Voronoi, or Combined). The terrain can be
rotated, zoomed, and reset using keyboard controls.

Controls:
- Arrow keys: Rotate terrain
- +/- keys: Zoom in/out
- E key: Reset view
- Q key: Toggle mouse capture
- ESC key: Exit application

Command line arguments allow customization of terrain parameters including
noise type, seed, octaves, persistence, lacunarity, scale, and height.
"""

# Standard library imports
import sys
import math
import random
import argparse

# Third-party imports
import pygame
from pygame.locals import (
    QUIT, KEYDOWN, KEYUP, VIDEORESIZE,
    K_ESCAPE, K_LEFT, K_RIGHT, K_UP, K_DOWN, 
    K_q, K_e, K_PLUS, K_MINUS, K_EQUALS,
    OPENGL, DOUBLEBUF, RESIZABLE
)
import numpy as np
import noise
from OpenGL.GL import (
    glEnable, glDisable, glClear, glClearColor, glBegin, glEnd, 
    glVertex3fv, glNormal3fv, glColor3f, glMatrixMode, glLoadIdentity,
    glRotatef, glLightfv, glColorMaterial, glViewport,
    GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL, GL_FRONT_AND_BACK,
    GL_AMBIENT_AND_DIFFUSE, GL_POSITION, GL_AMBIENT, GL_DIFFUSE,
    GL_PROJECTION, GL_MODELVIEW, GL_DEPTH_TEST, GL_TRIANGLES,
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
)
from OpenGL.GLU import gluPerspective, gluLookAt

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Display settings
WIDTH, HEIGHT = 800, 600

# Terrain generation settings
TERRAIN_SIZE = 25        # Size of terrain grid (TERRAIN_SIZE x TERRAIN_SIZE)
TERRAIN_SCALE = 0.5      # Scale of each terrain cell
TERRAIN_HEIGHT_SCALE = 2.0  # Scale factor for terrain height
TERRAIN_COLOR = (0.8, 0.8, 0.8)  # Light gray

# Noise generation settings
NOISE_SCALE = 5.0        # Scale factor for noise
NOISE_OCTAVES = 6        # Number of octaves for noise
NOISE_PERSISTENCE = 0.5  # Persistence for noise
NOISE_LACUNARITY = 2.0   # Lacunarity for noise

# Visual settings
SKY_COLOR = (0.7, 0.8, 0.9, 1.0)  # Light blue
ROTATION_SPEED = 1.0     # Speed of rotation when using arrow keys
ZOOM_SPEED = 0.5         # Speed of zooming when using + and - keys

# =============================================================================
# TERRAIN GENERATION
# =============================================================================

class Terrain:
    """
    Represents a 3D terrain generated using procedural noise algorithms.
    
    The terrain is created as a grid of vertices, with height determined by
    the selected noise algorithm. The class handles both generation and rendering.
    
    Attributes:
        vertices (list): List of (x, y, z) vertex coordinates
        triangles (list): List of triangle indices for rendering
        noise_type (str): Type of noise algorithm used
        seed (int): Random seed for noise generation
        noise_params (dict): Parameters for noise generation
    """
    
    def __init__(self, noise_type='perlin', seed=None, **noise_params):
        """
        Initialize a new terrain with the specified noise parameters.
        
        Args:
            noise_type (str): Type of noise to use ('perlin', 'simplex', 'ridged', 
                             'billow', 'voronoi', or 'combined')
            seed (int, optional): Random seed for noise generation
            **noise_params: Additional parameters for noise generation
                - octaves: Number of octaves for noise
                - persistence: Persistence value for noise
                - lacunarity: Lacunarity value for noise
                - scale: Scale factor for noise
                - height_scale: Scale factor for terrain height
        """
        self.vertices = []
        self.triangles = []
        self.noise_type = noise_type
        self.seed = seed if seed is not None else random.randint(0, 10000)
        self.noise_params = noise_params
        self.generate_terrain()
        
    def generate_terrain(self):
        """
        Generate the terrain using the specified noise algorithm.
        
        This method creates a height map using the selected noise algorithm,
        then converts it to 3D vertices and triangles for rendering.
        """
        # Extract noise parameters with defaults
        octaves = self.noise_params.get('octaves', NOISE_OCTAVES)
        persistence = self.noise_params.get('persistence', NOISE_PERSISTENCE)
        lacunarity = self.noise_params.get('lacunarity', NOISE_LACUNARITY)
        scale = self.noise_params.get('scale', NOISE_SCALE)
        height_scale = self.noise_params.get('height_scale', TERRAIN_HEIGHT_SCALE)
        
        # Generate height map using selected noise algorithm
        height_map = self._generate_height_map(octaves, persistence, lacunarity, scale)
        
        # Create vertices from height map
        self._create_vertices(height_map, height_scale)
        
        # Create triangles (indices) for rendering
        self._create_triangles()
    
    def _generate_height_map(self, octaves, persistence, lacunarity, scale):
        """
        Generate a height map using the selected noise algorithm.
        
        Args:
            octaves (int): Number of octaves for noise
            persistence (float): Persistence value for noise
            lacunarity (float): Lacunarity value for noise
            scale (float): Scale factor for noise
            
        Returns:
            numpy.ndarray: 2D array of height values
        """
        height_map = np.zeros((TERRAIN_SIZE, TERRAIN_SIZE))
        
        for i in range(TERRAIN_SIZE):
            for j in range(TERRAIN_SIZE):
                nx = i / TERRAIN_SIZE * scale
                ny = j / TERRAIN_SIZE * scale
                
                # Generate height based on noise type
                if self.noise_type == 'perlin':
                    height_map[i][j] = noise.pnoise2(
                        nx, ny, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity,
                        base=self.seed
                    )
                elif self.noise_type == 'simplex':
                    height_map[i][j] = noise.snoise2(
                        nx, ny, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity,
                        base=self.seed
                    )
                elif self.noise_type == 'ridged':
                    # Ridged multifractal noise (absolute value of simplex noise)
                    value = abs(noise.snoise2(
                        nx, ny, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity,
                        base=self.seed
                    ))
                    height_map[i][j] = 1.0 - value  # Invert to create ridges
                elif self.noise_type == 'billow':
                    # Billow noise (absolute value of perlin noise)
                    value = abs(noise.pnoise2(
                        nx, ny, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity,
                        base=self.seed
                    ))
                    height_map[i][j] = value * 2.0 - 1.0  # Scale to -1 to 1 range
                elif self.noise_type == 'voronoi':
                    # Simple Voronoi-like noise
                    height_map[i][j] = self._voronoi_noise(nx, ny)
                elif self.noise_type == 'combined':
                    # Combination of perlin and simplex
                    perlin = noise.pnoise2(
                        nx, ny, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity, 
                        base=self.seed
                    )
                    simplex = noise.snoise2(
                        nx * 2, ny * 2, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity, 
                        base=self.seed + 1000
                    )
                    height_map[i][j] = (perlin + simplex) * 0.5
                else:
                    # Default to perlin
                    height_map[i][j] = noise.pnoise2(
                        nx, ny, 
                        octaves=octaves, 
                        persistence=persistence, 
                        lacunarity=lacunarity,
                        base=self.seed
                    )
        
        return height_map
    
    def _create_vertices(self, height_map, height_scale):
        """
        Create 3D vertices from the height map.
        
        Args:
            height_map (numpy.ndarray): 2D array of height values
            height_scale (float): Scale factor for terrain height
        """
        self.vertices = []
        for i in range(TERRAIN_SIZE):
            for j in range(TERRAIN_SIZE):
                x = (i - TERRAIN_SIZE/2) * TERRAIN_SCALE
                z = (j - TERRAIN_SIZE/2) * TERRAIN_SCALE
                y = height_map[i][j] * height_scale
                self.vertices.append((x, y, z))
    
    def _create_triangles(self):
        """
        Create triangles (indices) for rendering the terrain.
        
        Each grid cell is divided into two triangles.
        """
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
        """
        Generate Voronoi-like noise.
        
        Args:
            x (float): X coordinate
            y (float): Y coordinate
            
        Returns:
            float: Noise value in range approximately -0.5 to 0.5
        """
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
        """
        Render the terrain using OpenGL.
        
        This method draws the terrain as a collection of triangles with proper
        lighting normals for each face.
        """
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

# =============================================================================
# OPENGL SETUP FUNCTIONS
# =============================================================================

def setup_lighting():
    """
    Configure OpenGL lighting for the scene.
    
    Sets up a single light source positioned above the terrain.
    """
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
    """
    Configure the background color for the scene.
    """
    glClearColor(*SKY_COLOR)

def setup_isometric_view(width=WIDTH, height=HEIGHT):
    """
    Configure the camera perspective for an isometric-like view.
    
    Args:
        width (int): Viewport width
        height (int): Viewport height
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (width / height), 0.1, 50.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Set up isometric-like view
    # Position the camera to view the terrain from an isometric angle
    gluLookAt(
        10, 10, 10,  # Eye position
        0, 0, 0,     # Look at position
        0, 1, 0      # Up vector
    )

def resize_window(width, height):
    """
    Update the viewport and perspective when window is resized.
    
    Args:
        width (int): New window width
        height (int): New window height
    """
    if height == 0:
        height = 1  # Prevent division by zero
    
    # Update the viewport to the new window size
    glViewport(0, 0, width, height)
    
    # Update the perspective projection
    setup_isometric_view(width, height)

# =============================================================================
# COMMAND LINE ARGUMENT PARSING
# =============================================================================

def parse_arguments():
    """
    Parse command line arguments for terrain generation.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Procedural Terrain Simulation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Noise type
    parser.add_argument(
        '--noise', 
        type=str, 
        default='perlin',
        choices=['perlin', 'simplex', 'ridged', 'billow', 'voronoi', 'combined'],
        help='Type of noise to use for terrain generation'
    )
    
    # Noise parameters
    parser.add_argument(
        '--seed', 
        type=int, 
        default=None,
        help='Seed for random number generation'
    )
    parser.add_argument(
        '--octaves', 
        type=int, 
        default=NOISE_OCTAVES,
        help='Number of octaves for noise generation'
    )
    parser.add_argument(
        '--persistence', 
        type=float, 
        default=NOISE_PERSISTENCE,
        help='Persistence value for noise generation'
    )
    parser.add_argument(
        '--lacunarity', 
        type=float, 
        default=NOISE_LACUNARITY,
        help='Lacunarity value for noise generation'
    )
    parser.add_argument(
        '--scale', 
        type=float, 
        default=NOISE_SCALE,
        help='Scale factor for noise'
    )
    parser.add_argument(
        '--height-scale', 
        type=float, 
        default=TERRAIN_HEIGHT_SCALE,
        help='Scale factor for terrain height'
    )
    
    # Terrain parameters
    parser.add_argument(
        '--size', 
        type=int, 
        default=TERRAIN_SIZE,
        help='Size of terrain grid (size x size)'
    )
    
    return parser.parse_args()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """
    Main application entry point.
    
    Initializes the application, sets up the OpenGL environment,
    generates the terrain, and runs the main game loop.
    """
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
    display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption(f"Procedural Terrain Simulation - {args.noise.capitalize()} Noise")
    
    try:
        # Set window icon
        icon = pygame.image.load('icon.png')
        pygame.display.set_icon(icon)
    except pygame.error:
        # If icon.png is not found, continue without setting an icon
        pass
    
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
    
    # Initialize camera state
    camera_state = {
        'rotation_x': 0,
        'rotation_y': 0,
        'zoom_distance': 10.0,
        'mouse_captured': False
    }
    
    # Store initial values for reset
    initial_state = {
        'rotation_x': camera_state['rotation_x'],
        'rotation_y': camera_state['rotation_y'],
        'zoom_distance': camera_state['zoom_distance']
    }
    
    # Run the main game loop
    run_game_loop(display, terrain, camera_state, initial_state)
    
    # Clean up and exit
    pygame.quit()
    sys.exit()

def run_game_loop(display, terrain, camera_state, initial_state):
    """
    Run the main game loop.
    
    Args:
        display: Pygame display surface
        terrain: Terrain object to render
        camera_state (dict): Current camera state
        initial_state (dict): Initial camera state for reset
    """
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Handle events
        running = handle_events(display, camera_state, initial_state)
        
        # Handle keyboard input for rotation
        handle_keyboard_input(camera_state)
        
        # Render the scene
        render_scene(terrain, camera_state)
        
        # Update display and maintain frame rate
        pygame.display.flip()
        clock.tick(60)
    
    # Ensure mouse is visible and not captured when exiting
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)

def handle_events(display, camera_state, initial_state):
    """
    Handle pygame events.
    
    Args:
        display: Pygame display surface
        camera_state (dict): Current camera state
        initial_state (dict): Initial camera state for reset
        
    Returns:
        bool: True if the application should continue running, False if it should exit
    """
    for event in pygame.event.get():
        if event.type == QUIT:
            return False
            
        elif event.type == VIDEORESIZE:
            # Handle window resize event
            width, height = event.size
            display = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
            resize_window(width, height)
            
        elif event.type == KEYDOWN:
            # Reset terrain position when 'e' is pressed
            if event.key == K_e:
                camera_state['rotation_x'] = initial_state['rotation_x']
                camera_state['rotation_y'] = initial_state['rotation_y']
                camera_state['zoom_distance'] = initial_state['zoom_distance']
            
            # Toggle mouse capture when 'q' is pressed
            elif event.key == K_q:
                camera_state['mouse_captured'] = not camera_state['mouse_captured']
                pygame.mouse.set_visible(not camera_state['mouse_captured'])
                pygame.event.set_grab(camera_state['mouse_captured'])
            
            # Exit simulation when 'Escape' is pressed
            elif event.key == K_ESCAPE:
                return False
            
            # Zoom in with + key (also handle = key which is the unshifted + on most keyboards)
            elif event.key == K_PLUS or event.key == K_EQUALS:
                camera_state['zoom_distance'] = max(2.0, camera_state['zoom_distance'] - ZOOM_SPEED)
            
            # Zoom out with - key
            elif event.key == K_MINUS:
                camera_state['zoom_distance'] = min(20.0, camera_state['zoom_distance'] + ZOOM_SPEED)
    
    return True

def handle_keyboard_input(camera_state):
    """
    Handle keyboard input for camera rotation.
    
    Args:
        camera_state (dict): Current camera state
    """
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        camera_state['rotation_y'] += ROTATION_SPEED
    if keys[pygame.K_RIGHT]:
        camera_state['rotation_y'] -= ROTATION_SPEED
    if keys[pygame.K_UP]:
        camera_state['rotation_x'] += ROTATION_SPEED
    if keys[pygame.K_DOWN]:
        camera_state['rotation_x'] -= ROTATION_SPEED

def render_scene(terrain, camera_state):
    """
    Render the scene with the current camera settings.
    
    Args:
        terrain: Terrain object to render
        camera_state (dict): Current camera state
    """
    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Apply camera transformations
    glLoadIdentity()
    
    # Position camera with zoom
    zoom = camera_state['zoom_distance']
    gluLookAt(
        zoom, zoom, zoom,  # Eye position with zoom
        0, 0, 0,           # Look at position
        0, 1, 0            # Up vector
    )
    
    # Apply rotations
    glRotatef(camera_state['rotation_x'], 1, 0, 0)
    glRotatef(camera_state['rotation_y'], 0, 1, 0)
    
    # Render terrain
    terrain.render()

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()

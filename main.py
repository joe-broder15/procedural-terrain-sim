'''Procedural Terrain Simulator

A 3D terrain generator and viewer using procedural noise algorithms.

Usage:
    python main.py [options]

Options:
    --noise           Type of noise for terrain generation (default: perlin)
    --seed            Random seed (default: random)
    --octaves         Number of octaves (default: 6)
    --persistence     Noise persistence (default: 0.5)
    --lacunarity      Noise lacunarity (default: 2.0)
    --scale           Noise scale (default: 5.0)
    --height-scale    Terrain height scale (default: 2.0)
    --size            Grid size (default: 25)
    --fly             Enable free-flying camera mode
'''

import sys
import math
import random
import argparse

import pygame
from pygame.locals import (
    QUIT, KEYDOWN, VIDEORESIZE, MOUSEMOTION,
    K_ESCAPE, K_LEFT, K_RIGHT, K_UP, K_DOWN, 
    K_q, K_e, K_PLUS, K_MINUS, K_EQUALS,
    K_w, K_a, K_s, K_d, K_SPACE, K_LSHIFT,
    OPENGL, DOUBLEBUF, RESIZABLE
)

import numpy as np
import noise

from OpenGL.GL import (
    glEnable, glClear, glClearColor, glBegin, glEnd, 
    glVertex3fv, glNormal3fv, glColor3f, glMatrixMode, glLoadIdentity,
    glRotatef, glLightfv, glColorMaterial, glViewport,
    GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL, GL_FRONT_AND_BACK,
    GL_AMBIENT_AND_DIFFUSE, GL_POSITION, GL_AMBIENT, GL_DIFFUSE,
    GL_PROJECTION, GL_MODELVIEW, GL_DEPTH_TEST, GL_TRIANGLES,
    GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
)
from OpenGL.GLU import gluPerspective, gluLookAt


# Global configuration constants
WIDTH, HEIGHT = 800, 600
TERRAIN_SIZE = 25
TERRAIN_SCALE = 0.5
TERRAIN_HEIGHT_SCALE = 2.0
TERRAIN_COLOR = (0.8, 0.8, 0.8)

NOISE_SCALE = 5.0
NOISE_OCTAVES = 6
NOISE_PERSISTENCE = 0.5
NOISE_LACUNARITY = 2.0

SKY_COLOR = (0.7, 0.8, 0.9, 1.0)
ROTATION_SPEED = 1.0
ZOOM_SPEED = 0.5

FLY_MOVE_SPEED = 0.1
FLY_MOUSE_SENSITIVITY = 0.2
FLY_INITIAL_POSITION = [0.0, 5.0, 10.0]


class Terrain:
    """Terrain object generated with procedural noise."""
    def __init__(self, noise_type='perlin', seed=None, **noise_params):
        self.vertices = []
        self.triangles = []
        self.noise_type = noise_type
        self.seed = seed if seed is not None else random.randint(0, 10000)
        self.noise_params = noise_params
        # Generate terrain immediately upon instantiation
        self.generate_terrain()

    def generate_terrain(self):
        """Generate the height map, vertices, and triangle indices."""
        # Extract noise parameters with fallback to default globals
        octaves = self.noise_params.get('octaves', NOISE_OCTAVES)
        persistence = self.noise_params.get('persistence', NOISE_PERSISTENCE)
        lacunarity = self.noise_params.get('lacunarity', NOISE_LACUNARITY)
        scale = self.noise_params.get('scale', NOISE_SCALE)
        height_scale = self.noise_params.get('height_scale', TERRAIN_HEIGHT_SCALE)
        
        # Create the 2D height map using the selected noise algorithm
        height_map = self._generate_height_map(octaves, persistence, lacunarity, scale)
        
        # Convert height map to 3D vertices
        self._create_vertices(height_map, height_scale)
        
        # Generate triangles (mesh indices) from the vertices
        self._create_triangles()

    def _generate_height_map(self, octaves, persistence, lacunarity, scale):
        """Create a 2D height map using the selected noise algorithm."""
        height_map = np.zeros((TERRAIN_SIZE, TERRAIN_SIZE))
        for i in range(TERRAIN_SIZE):
            for j in range(TERRAIN_SIZE):
                # Normalize grid coordinates for noise input
                nx = i / TERRAIN_SIZE * scale
                ny = j / TERRAIN_SIZE * scale
                
                # Select and apply the noise algorithm based on noise_type
                if self.noise_type == 'perlin':
                    height_map[i][j] = noise.pnoise2(nx, ny, octaves=octaves,
                                                      persistence=persistence,
                                                      lacunarity=lacunarity,
                                                      base=self.seed)
                elif self.noise_type == 'simplex':
                    height_map[i][j] = noise.snoise2(nx, ny, octaves=octaves,
                                                      persistence=persistence,
                                                      lacunarity=lacunarity,
                                                      base=self.seed)
                elif self.noise_type == 'ridged':
                    # Ridged noise inverts the absolute Simplex noise for ridge effect
                    value = abs(noise.snoise2(nx, ny, octaves=octaves,
                                               persistence=persistence,
                                               lacunarity=lacunarity,
                                               base=self.seed))
                    height_map[i][j] = 1.0 - value
                elif self.noise_type == 'billow':
                    # Billow noise uses absolute Perlin noise scaled to [-1, 1]
                    value = abs(noise.pnoise2(nx, ny, octaves=octaves,
                                               persistence=persistence,
                                               lacunarity=lacunarity,
                                               base=self.seed))
                    height_map[i][j] = value * 2.0 - 1.0
                elif self.noise_type == 'voronoi':
                    # Use a custom Voronoi-like noise function
                    height_map[i][j] = self._voronoi_noise(nx, ny)
                elif self.noise_type == 'combined':
                    # Combine Perlin and Simplex noise for varied terrain
                    perlin = noise.pnoise2(nx, ny, octaves=octaves,
                                            persistence=persistence,
                                            lacunarity=lacunarity,
                                            base=self.seed)
                    simplex = noise.snoise2(nx * 2, ny * 2, octaves=octaves,
                                             persistence=persistence,
                                             lacunarity=lacunarity,
                                             base=self.seed + 1000)
                    height_map[i][j] = (perlin + simplex) * 0.5
                else:
                    # Default to Perlin noise if unknown type
                    height_map[i][j] = noise.pnoise2(nx, ny, octaves=octaves,
                                                      persistence=persistence,
                                                      lacunarity=lacunarity,
                                                      base=self.seed)
        return height_map

    def _create_vertices(self, height_map, height_scale):
        """Convert the height map into 3D vertices."""
        self.vertices = []
        for i in range(TERRAIN_SIZE):
            for j in range(TERRAIN_SIZE):
                # Offset the grid so that the terrain is centered
                x = (i - TERRAIN_SIZE / 2) * TERRAIN_SCALE
                z = (j - TERRAIN_SIZE / 2) * TERRAIN_SCALE
                # Scale the noise value to get the height
                y = height_map[i][j] * height_scale
                self.vertices.append((x, y, z))

    def _create_triangles(self):
        """Generate triangle indices for rendering the terrain."""
        self.triangles = []
        for i in range(TERRAIN_SIZE - 1):
            for j in range(TERRAIN_SIZE - 1):
                # Compute vertex indices for the current cell
                a = i * TERRAIN_SIZE + j
                b = a + 1
                c = (i + 1) * TERRAIN_SIZE + j
                d = c + 1
                # Form two triangles for each quad in the grid
                self.triangles.append((a, b, c))
                self.triangles.append((b, d, c))

    def _voronoi_noise(self, x, y):
        """Simple Voronoi-like noise function."""
        points = []
        random.seed(self.seed)
        for _ in range(10):
            # Randomly generate 10 points in a 10x10 space
            points.append((random.random() * 10, random.random() * 10))
        # Find the minimum distance from (x, y) to any random point
        min_dist = min(math.sqrt((x - px) ** 2 + (y - py) ** 2) for px, py in points)
        # Normalize the distance to roughly [-0.5, 0.5]
        return min_dist / 2.0 - 0.5

    def render(self):
        """Render the terrain using OpenGL."""
        # Set the terrain color
        glColor3f(*TERRAIN_COLOR)
        glBegin(GL_TRIANGLES)
        for tri in self.triangles:
            # Retrieve triangle vertices
            v1 = np.array(self.vertices[tri[0]])
            v2 = np.array(self.vertices[tri[1]])
            v3 = np.array(self.vertices[tri[2]])
            # Calculate surface normal for lighting
            normal = np.cross(v2 - v1, v3 - v1)
            normal = normal / np.linalg.norm(normal)
            glNormal3fv(normal)
            # Specify the vertices of the triangle
            glVertex3fv(self.vertices[tri[0]])
            glVertex3fv(self.vertices[tri[1]])
            glVertex3fv(self.vertices[tri[2]])
        glEnd()


def setup_lighting():
    """Configure OpenGL lighting."""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    # Set light position directly above the terrain
    light_position = [0.0, 10.0, 0.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.7, 0.7, 0.7, 1.0])


def setup_skybox():
    """Set the background color."""
    glClearColor(*SKY_COLOR)


def setup_viewport(width=WIDTH, height=HEIGHT):
    """Set perspective with an isometric view."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Set up the perspective projection
    gluPerspective(45, (width / height), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # Position the camera to get an isometric view
    gluLookAt(10, 10, 10, 0, 0, 0, 0, 1, 0)


def resize_window(width, height):
    """Handle window resize events."""
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    setup_viewport(width, height)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Procedural Terrain Simulation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--noise', type=str, default='perlin',
                        choices=['perlin', 'simplex', 'ridged', 'billow', 'voronoi', 'combined'],
                        help='Noise type for terrain generation')
    parser.add_argument('--seed', type=int, default=None, help='Seed for random generation')
    parser.add_argument('--octaves', type=int, default=NOISE_OCTAVES, help='Noise octaves')
    parser.add_argument('--persistence', type=float, default=NOISE_PERSISTENCE, help='Noise persistence')
    parser.add_argument('--lacunarity', type=float, default=NOISE_LACUNARITY, help='Noise lacunarity')
    parser.add_argument('--scale', type=float, default=NOISE_SCALE, help='Noise scale')
    parser.add_argument('--height-scale', type=float, default=TERRAIN_HEIGHT_SCALE, help='Terrain height scale')
    parser.add_argument('--size', type=int, default=TERRAIN_SIZE, help='Terrain grid size')
    parser.add_argument('--fly', action='store_true', help='Enable fly camera mode')
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    global TERRAIN_SIZE, NOISE_SCALE, NOISE_OCTAVES, NOISE_PERSISTENCE, NOISE_LACUNARITY, TERRAIN_HEIGHT_SCALE
    # Update global parameters based on command-line arguments
    TERRAIN_SIZE = args.size
    NOISE_SCALE = args.scale
    NOISE_OCTAVES = args.octaves
    NOISE_PERSISTENCE = args.persistence
    NOISE_LACUNARITY = args.lacunarity
    TERRAIN_HEIGHT_SCALE = args.height_scale

    pygame.init()
    display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption(f"Procedural Terrain - {args.noise.capitalize()} Noise")
    try:
        # Attempt to load and set an icon
        icon = pygame.image.load('icon.png')
        pygame.display.set_icon(icon)
    except pygame.error:
        pass

    glEnable(GL_DEPTH_TEST)
    setup_lighting()
    setup_skybox()
    setup_viewport()

    noise_params = {
        'octaves': args.octaves,
        'persistence': args.persistence,
        'lacunarity': args.lacunarity,
        'scale': args.scale,
        'height_scale': args.height_scale
    }
    terrain = Terrain(noise_type=args.noise, seed=args.seed, **noise_params)

    # Set up the initial camera state
    camera_state = {
        'rotation_x': 0,
        'rotation_y': 0,
        'zoom_distance': 10.0,
        'mouse_captured': False,
        'fly_mode': args.fly,
        'position': FLY_INITIAL_POSITION.copy(),
        'yaw': 0,
        'pitch': 0,
        'last_mouse_pos': None
    }
    # Store the initial camera state for resetting the view
    initial_state = {
        'rotation_x': 0,
        'rotation_y': 0,
        'zoom_distance': 10.0,
        'position': FLY_INITIAL_POSITION.copy(),
        'yaw': 0,
        'pitch': 0
    }
    if camera_state['fly_mode']:
        # In fly mode, capture the mouse and hide the cursor
        camera_state['mouse_captured'] = True
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
        camera_state['last_mouse_pos'] = (WIDTH // 2, HEIGHT // 2)

    run_game_loop(display, terrain, camera_state, initial_state)
    pygame.quit()
    sys.exit()


def run_game_loop(display, terrain, camera_state, initial_state):
    """Run the main game loop."""
    clock = pygame.time.Clock()
    running = True
    if camera_state['fly_mode']:
        # Print fly mode controls in the console
        print("\nFly Mode Controls:")
        print("  W/A/S/D: Move forward/left/backward/right")
        print("  Space/Shift: Move up/down")
        print("  Mouse: Look around")
        print("  Q: Toggle mouse capture")
        print("  E: Reset camera position")
        print("  Escape: Exit\n")
    while running:
        # Process events and update running state
        running = handle_events(display, camera_state, initial_state)
        # Update camera based on keyboard input
        handle_keyboard_input(camera_state)
        # Render the current frame
        render_scene(terrain, camera_state)
        pygame.display.flip()  # Update the full display surface to the screen
        clock.tick(60)  # Limit to 60 frames per second
    # Ensure the mouse becomes visible and ungrabbed when exiting
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)


def handle_events(display, camera_state, initial_state):
    """Process Pygame events."""
    for event in pygame.event.get():
        if event.type == QUIT:
            return False
        elif event.type == VIDEORESIZE:
            # Handle window resize by resetting the display mode and viewport
            width, height = event.size
            display = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
            resize_window(width, height)
        elif event.type == KEYDOWN:
            if event.key == K_e:
                # Reset camera to initial state when 'E' is pressed
                if camera_state['fly_mode']:
                    camera_state['position'] = initial_state['position'].copy()
                    camera_state['yaw'] = initial_state['yaw']
                    camera_state['pitch'] = initial_state['pitch']
                else:
                    camera_state['rotation_x'] = initial_state['rotation_x']
                    camera_state['rotation_y'] = initial_state['rotation_y']
                    camera_state['zoom_distance'] = initial_state['zoom_distance']
            elif event.key == K_q:
                # Toggle mouse capture on 'Q' press
                camera_state['mouse_captured'] = not camera_state['mouse_captured']
                pygame.mouse.set_visible(not camera_state['mouse_captured'])
                pygame.event.set_grab(camera_state['mouse_captured'])
                if camera_state['mouse_captured']:
                    pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
                    camera_state['last_mouse_pos'] = (WIDTH // 2, HEIGHT // 2)
            elif event.key == K_ESCAPE:
                return False
            elif event.key in (K_PLUS, K_EQUALS) and not camera_state['fly_mode']:
                # Zoom in when '+' or '=' is pressed in orbit mode
                camera_state['zoom_distance'] = max(2.0, camera_state['zoom_distance'] - ZOOM_SPEED)
            elif event.key == K_MINUS and not camera_state['fly_mode']:
                # Zoom out when '-' is pressed in orbit mode
                camera_state['zoom_distance'] = min(20.0, camera_state['zoom_distance'] + ZOOM_SPEED)
        elif event.type == MOUSEMOTION and camera_state['mouse_captured'] and camera_state['fly_mode']:
            # Update camera orientation based on mouse movement in fly mode
            if camera_state['last_mouse_pos'] is None:
                camera_state['last_mouse_pos'] = event.pos
            else:
                dx = event.pos[0] - camera_state['last_mouse_pos'][0]
                dy = event.pos[1] - camera_state['last_mouse_pos'][1]
                camera_state['yaw'] -= dx * FLY_MOUSE_SENSITIVITY
                # Clamp the pitch to avoid flipping
                camera_state['pitch'] = max(-89.0, min(89.0, camera_state['pitch'] - dy * FLY_MOUSE_SENSITIVITY))
                # Reset the mouse position to the center for continuous movement
                pygame.mouse.set_pos(WIDTH // 2, HEIGHT // 2)
                camera_state['last_mouse_pos'] = (WIDTH // 2, HEIGHT // 2)
    return True


def handle_keyboard_input(camera_state):
    """Update camera state based on keyboard input."""
    keys = pygame.key.get_pressed()
    if camera_state['fly_mode']:
        # Calculate directional vectors based on current yaw and pitch
        yaw_rad = math.radians(camera_state['yaw'])
        pitch_rad = math.radians(camera_state['pitch'])
        forward = (
            math.sin(yaw_rad) * math.cos(pitch_rad),
            math.sin(pitch_rad),
            math.cos(yaw_rad) * math.cos(pitch_rad)
        )
        right = (math.sin(yaw_rad - math.pi/2), 0, math.cos(yaw_rad - math.pi/2))
        if keys[pygame.K_w]:
            camera_state['position'][0] += forward[0] * FLY_MOVE_SPEED
            camera_state['position'][1] += forward[1] * FLY_MOVE_SPEED
            camera_state['position'][2] += forward[2] * FLY_MOVE_SPEED
        if keys[pygame.K_s]:
            camera_state['position'][0] -= forward[0] * FLY_MOVE_SPEED
            camera_state['position'][1] -= forward[1] * FLY_MOVE_SPEED
            camera_state['position'][2] -= forward[2] * FLY_MOVE_SPEED
        if keys[pygame.K_a]:
            camera_state['position'][0] -= right[0] * FLY_MOVE_SPEED
            camera_state['position'][1] -= right[1] * FLY_MOVE_SPEED
            camera_state['position'][2] -= right[2] * FLY_MOVE_SPEED
        if keys[pygame.K_d]:
            camera_state['position'][0] += right[0] * FLY_MOVE_SPEED
            camera_state['position'][1] += right[1] * FLY_MOVE_SPEED
            camera_state['position'][2] += right[2] * FLY_MOVE_SPEED
        if keys[pygame.K_SPACE]:
            camera_state['position'][1] += FLY_MOVE_SPEED
        if keys[pygame.K_LSHIFT]:
            camera_state['position'][1] -= FLY_MOVE_SPEED
    else:
        # In orbit mode, use arrow keys to rotate the view
        if keys[pygame.K_LEFT]:
            camera_state['rotation_y'] += ROTATION_SPEED
        if keys[pygame.K_RIGHT]:
            camera_state['rotation_y'] -= ROTATION_SPEED
        if keys[pygame.K_UP]:
            camera_state['rotation_x'] += ROTATION_SPEED
        if keys[pygame.K_DOWN]:
            camera_state['rotation_x'] -= ROTATION_SPEED


def render_scene(terrain, camera_state):
    """Render the scene with the current camera configuration."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    if camera_state['fly_mode']:
        # In fly mode, set the camera based on current position and orientation
        yaw_rad = math.radians(camera_state['yaw'])
        pitch_rad = math.radians(camera_state['pitch'])
        look_at = (
            camera_state['position'][0] + math.sin(yaw_rad) * math.cos(pitch_rad),
            camera_state['position'][1] + math.sin(pitch_rad),
            camera_state['position'][2] + math.cos(yaw_rad) * math.cos(pitch_rad)
        )
        gluLookAt(
            camera_state['position'][0], camera_state['position'][1], camera_state['position'][2],
            look_at[0], look_at[1], look_at[2],
            0, 1, 0
        )
    else:
        # Orbit mode: position the camera at an equal distance from the origin
        gluLookAt(
            camera_state['zoom_distance'], camera_state['zoom_distance'], camera_state['zoom_distance'],
            0, 0, 0,
            0, 1, 0
        )
    # Apply rotations from orbit mode
    glRotatef(camera_state['rotation_x'], 1, 0, 0)
    glRotatef(camera_state['rotation_y'], 0, 1, 0)
    # Keep the light source fixed overhead
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 10.0, 0.0, 1.0])
    # Render the terrain mesh
    terrain.render()


if __name__ == "__main__":
    main()

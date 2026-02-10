"""Three-way valve component for directing fluid flow."""

import pygame
import math
from typing import Tuple, Literal
from .base import Component


class ThreeWayValve(Component):
    """A 3-way valve combining tee shape with valve functionality."""

    def __init__(
        self,
        position: Tuple[int, int],
        state: Literal["base", "flipped"] = "base",
        color: Tuple[int, int, int] = (128, 128, 128),
        component_id: str = None,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize a three-way valve.

        Args:
            position: Grid position (x, y)
            state: Valve state - "base" blocks right arm, "flipped" blocks left arm
            color: RGB color tuple
            component_id: Optional unique identifier
            rotation: Rotation angle in degrees (0, 90, 180, 270)
            diameter: Pipe diameter in pixels (should match connected pipes)
        """
        super().__init__(position, component_id)
        self.state = state
        self.color = color
        self.rotation = rotation
        self.diameter = diameter

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the tee fitting as a T-shape."""
        # Calculate zoom factor (base grid size is 50)
        zoom = grid_size / 50.0

        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]

        """Render a tee connector."""
        # Use the diameter to match connected pipes
        pipe_width = int(self.diameter * zoom)

        # Calculate elbow radius based on pipe width
        # Inner radius should be large enough to look good
        inner_radius = (pipe_width * 0.75)

        # Create a surface for the elbow that we can rotate
        tee_width = ((inner_radius*2 + pipe_width))
        temp_surface = pygame.Surface((tee_width*2, tee_width*2), pygame.SRCALPHA)

        # We want the inner corner of the elbow to be at the surface center
        # This way, after rotation, the inner corner will be at the node position
        surf_center_x = tee_width 
        surf_center_y = tee_width

        # The arc center is offset from the inner corner
        offset_distance = inner_radius+(pipe_width//2)

        # To align the tee with pipe endpoints at the node:
        left_arc_center_x = surf_center_x - offset_distance
        left_arc_center_y = surf_center_y + offset_distance
        right_arc_center_x = surf_center_x + offset_distance
        right_arc_center_y = surf_center_y + offset_distance

        # Draw the elbow arc as a 90-degree quarter circle
        # Arc goes from 0° to 90° (from right to down)
        points_right = []
        points_left = []
        num_segments = 20

        for i in range(num_segments + 1):
            # 90-degree arc from 0 to π/2 (0 to 90 degrees)
            angle = (math.pi / 2) * i / num_segments


            # left arc points
            ix = left_arc_center_x + inner_radius * math.cos(angle)
            iy = left_arc_center_y - (inner_radius * math.sin(angle))
            points_left.append((ix, iy))  # Insert at beginning to reverse order


            # Right arc points
            ox = right_arc_center_x - inner_radius * math.sin(angle)
            oy = right_arc_center_y - inner_radius * math.cos(angle)
            points_right.append((ox, oy))
        
        points_right = points_right[::-1]
        points_left = points_left[::-1]

        points_valve_stem = []
        points_valve_stem.append((points_right[-1][0],surf_center_y-pipe_width*0.5))
        points_valve_stem.append((surf_center_x+pipe_width*0.1, surf_center_y-pipe_width*0.5))
        points_valve_stem.append((surf_center_x+pipe_width*0.1, surf_center_y-pipe_width))
        points_valve_stem.append((surf_center_x+pipe_width*0.5, surf_center_y-pipe_width))
        points_valve_stem.append((surf_center_x+pipe_width*0.5, surf_center_y-pipe_width*1.2))
        points_valve_stem.append((surf_center_x-pipe_width*0.5, surf_center_y-pipe_width*1.2))
        points_valve_stem.append((surf_center_x-pipe_width*0.5, surf_center_y-pipe_width))
        points_valve_stem.append((surf_center_x-pipe_width*0.1, surf_center_y-pipe_width))
        points_valve_stem.append((surf_center_x-pipe_width*0.1, surf_center_y-pipe_width*0.5))
        points_valve_stem.append((points_left[0][0],surf_center_y-pipe_width*0.5))

        # Combine points to create closed polygon
        all_points =  points_right + points_valve_stem + points_left

        # Draw the valve body
        pygame.draw.polygon(temp_surface, self.color, all_points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, all_points, 2)

        # Draw outer and inner arc lines for depth
        pygame.draw.lines(temp_surface, border_color, False, points_right, 2)
        pygame.draw.lines(temp_surface, border_color, False,
                            [p for p in reversed(points_left)], 2)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)

        # Get the rect and center it on the connector position
        # Since the inner corner was at the temp surface center, after rotation
        # it will be at the rotated surface center, which we position at the node
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        # Blit to main surface
        surface.blit(rotated_surface, rotated_rect)

        # Draw flashing X on blocked arm
        if self.state == "base":
            # Block right arm
            x_pos = surf_center_x + pipe_width*0.75
            y_pos = surf_center_y
        else:
            # Block left arm
            x_pos = surf_center_x - pipe_width*0.75
            y_pos = surf_center_y

        self._draw_flashing_x(temp_surface, int(x_pos), int(y_pos), time, pipe_width)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        surface.blit(rotated_surface, rotated_rect)

    def _draw_flashing_x(self, surface, center_x: int, center_y: int, time: float, scaled_diameter: int):
        """Draw a flashing X mark at the blocked arm."""
        blink_speed = 2.0
        alpha = (math.sin(time * blink_speed * 2 * math.pi) + 1) / 2

        if alpha < 0.3:
            return

        mark_color = (255, 50, 50)
        mark_size = int(scaled_diameter * 0.5)

        pygame.draw.line(
            surface,
            mark_color,
            (center_x - mark_size // 2, center_y - mark_size // 2),
            (center_x + mark_size // 2, center_y + mark_size // 2),
            3
        )
        pygame.draw.line(
            surface,
            mark_color,
            (center_x + mark_size // 2, center_y - mark_size // 2),
            (center_x - mark_size // 2, center_y + mark_size // 2),
            3
        )

    def to_dict(self) -> dict:
        """Convert three-way valve to dictionary."""
        data = {
            "type": "three_way_valve",
            "id": self.id,
            "position": list(self.position),
            "state": self.state,
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'ThreeWayValve':
        """Create three-way valve from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            state=data.get("state", "base"),
            color=tuple(data.get("color", [128, 128, 128])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

"""Tee component for T-shaped pipe junctions."""

import pygame
import math
from typing import Tuple
from .base import Component


class Tee(Component):
    """A T-shaped pipe fitting with three connection points."""

    def __init__(
        self,
        position: Tuple[int, int],
        color: Tuple[int, int, int] = (100, 150, 255),
        component_id: str = None,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize a tee fitting.

        Args:
            position: Grid position (x, y)
            color: RGB color tuple
            component_id: Optional unique identifier
            rotation: Rotation angle in degrees (0, 90, 180, 270)
            diameter: Pipe diameter in pixels (should match connected pipes)
        """
        super().__init__(position, component_id)
        self.color = color
        self.rotation = rotation
        self.diameter = diameter

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the tee fitting as a T-shape."""
        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]

        """Render a tee connector."""
        # Use the diameter to match connected pipes
        pipe_width = self.diameter

        # Calculate elbow radius based on pipe width
        # Inner radius should be large enough to look good
        inner_radius = int(pipe_width * 0.75)

        # Create a surface for the elbow that we can rotate
        tee_width = int((inner_radius*2 + pipe_width))
        tee_height= int((inner_radius + pipe_width))
        temp_surface = pygame.Surface((tee_width, tee_width), pygame.SRCALPHA)

        # We want the inner corner of the elbow to be at the surface center
        # This way, after rotation, the inner corner will be at the node position
        surf_center_x = tee_width // 2
        surf_center_y = inner_radius+pipe_width//2

        # The arc center is offset from the inner corner
        offset_distance = inner_radius+(pipe_width/2)

        # To align the tee with pipe endpoints at the node:
        left_arc_center_x = surf_center_x - offset_distance
        left_arc_center_y = surf_center_y - offset_distance
        right_arc_center_x = surf_center_x + offset_distance
        right_arc_center_y = surf_center_y - offset_distance

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
            iy = left_arc_center_y + inner_radius * math.sin(angle)
            points_left.append((ix, iy))  # Insert at beginning to reverse order


            # Right arc points
            ox = right_arc_center_x - inner_radius * math.sin(angle)
            oy = right_arc_center_y + inner_radius * math.cos(angle)
            points_right.append((ox, oy))

        # Combine points to create closed polygon
        all_points = points_right + points_left
        all_points.append((all_points[-1][0],all_points[-1][1]+pipe_width))
        all_points.append((all_points[1][0],all_points[-1][1]))

        # Draw the elbow body
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


    def to_dict(self) -> dict:
        """Convert tee to dictionary."""
        return {
            "type": "tee",
            "id": self.id,
            "position": list(self.position),
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Tee':
        """Create tee from dictionary."""
        return cls(
            position=tuple(data["position"]),
            color=tuple(data.get("color", [100, 150, 255])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )

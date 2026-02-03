"""Elbow component for joining pipes at angles."""

import pygame
import math
from typing import Tuple, List
from .base import Component


class Elbow(Component):
    """An elbow piece for joining pipes at different angles."""

    def __init__(
        self,
        position: Tuple[int, int],
        connector_type: str = "elbow",
        color: Tuple[int, int, int] = (100, 150, 255),
        component_id: str = None,
        size: int = 30,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize an elbow.

        Args:
            position: Grid position (x, y)
            connector_type: Type of connector ("elbow", "tee", "cross")
            color: RGB color tuple
            component_id: Optional unique identifier
            size: Visual size of the elbow in pixels
            rotation: Rotation angle in degrees (0, 90, 180, 270)
            diameter: Pipe diameter in pixels (should match connected pipes)
        """
        super().__init__(position, component_id)
        self.connector_type = connector_type
        self.color = color
        self.size = size
        self.rotation = rotation
        self.diameter = diameter

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the elbow."""
        # Calculate zoom factor (base grid size is 50)
        zoom = grid_size / 50.0

        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]

        if self.connector_type == "elbow":
            self._render_elbow(surface, x, y, grid_size, zoom)
        elif self.connector_type == "tee":
            self._render_tee(surface, x, y, zoom)
        elif self.connector_type == "cross":
            self._render_cross(surface, x, y, zoom)
        else:
            # Default: simple circle
            scaled_size = int(self.size * zoom)
            pygame.draw.circle(surface, self.color, (int(x), int(y)), scaled_size // 2)

    def _render_elbow(self, surface, x: float, y: float, grid_size: float, zoom: float):
        """Render a plumbing elbow connector."""
        # Use the diameter to match connected pipes
        pipe_width = int(self.diameter * zoom)

        # Calculate elbow radius based on pipe width
        # Inner radius should be large enough to look good
        inner_radius = int(pipe_width * 0.75)
        outer_radius = inner_radius + pipe_width

        # Create a surface for the elbow that we can rotate
        elbow_size = int((outer_radius + pipe_width) * 3)
        temp_surface = pygame.Surface((elbow_size, elbow_size), pygame.SRCALPHA)

        # We want the inner corner of the elbow to be at the surface center
        # This way, after rotation, the inner corner will be at the node position
        surf_center_x = elbow_size // 2
        surf_center_y = elbow_size // 2

        # The arc center is offset from the inner corner
        # For proper alignment with pipes, offset by 1.5x the pipe width
        offset_distance = inner_radius+(pipe_width/2)

        # To align the elbow with pipe endpoints at the node:
        arc_center_x = surf_center_x - offset_distance
        arc_center_y = surf_center_y - offset_distance

        # Draw the elbow arc as a 90-degree quarter circle
        # Arc goes from 0° to 90° (from right to down)
        points_outer = []
        points_inner = []
        num_segments = 20

        for i in range(num_segments + 1):
            # 90-degree arc from 0 to π/2 (0 to 90 degrees)
            angle = (math.pi / 2) * i / num_segments

            # Outer arc points
            ox = arc_center_x + outer_radius * math.cos(angle)
            oy = arc_center_y + outer_radius * math.sin(angle)
            points_outer.append((ox, oy))

            # Inner arc points
            ix = arc_center_x + inner_radius * math.cos(angle)
            iy = arc_center_y + inner_radius * math.sin(angle)
            points_inner.insert(0, (ix, iy))  # Insert at beginning to reverse order

        # Combine points to create closed polygon
        all_points = points_outer + points_inner

        # Draw the elbow body
        pygame.draw.polygon(temp_surface, self.color, all_points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, all_points, 2)

        # Draw outer and inner arc lines for depth
        pygame.draw.lines(temp_surface, border_color, False, points_outer, 2)
        pygame.draw.lines(temp_surface, border_color, False,
                         [p for p in reversed(points_inner)], 2)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)

        # Get the rect and center it on the elbow position
        # Since the inner corner was at the temp surface center, after rotation
        # it will be at the rotated surface center, which we position at the node
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        # Blit to main surface
        surface.blit(rotated_surface, rotated_rect)

    def _render_tee(self, surface, x: float, y: float, zoom: float):
        """Render a tee connector."""
        # Simple circle for now
        scaled_size = int(self.size * zoom)
        pygame.draw.circle(surface, self.color, (int(x), int(y)), scaled_size // 2)
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.circle(surface, border_color, (int(x), int(y)), scaled_size // 2, 2)

    def _render_cross(self, surface, x: float, y: float, zoom: float):
        """Render a cross connector."""
        # Simple circle for now
        scaled_size = int(self.size * zoom)
        pygame.draw.circle(surface, self.color, (int(x), int(y)), scaled_size // 2)
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.circle(surface, border_color, (int(x), int(y)), scaled_size // 2, 2)

    def to_dict(self) -> dict:
        """Convert elbow to dictionary."""
        data = {
            "type": "elbow",
            "id": self.id,
            "position": list(self.position),
            "connector_type": self.connector_type,
            "color": list(self.color),
            "size": self.size,
            "rotation": self.rotation,
            "diameter": self.diameter
        }
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'Elbow':
        """Create elbow from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            connector_type=data.get("connector_type", "elbow"),
            color=tuple(data.get("color", [100, 150, 255])),
            component_id=data.get("id"),
            size=data.get("size", 30),
            rotation=data.get("rotation", 270),
            diameter=data.get("diameter", 20)
        )
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

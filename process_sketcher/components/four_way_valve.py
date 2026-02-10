"""Four-way valve component for H-shaped pipe junctions."""

import pygame
import math
from typing import Tuple, Literal
from .base import Component


class FourWayValve(Component):
    """An H-shaped 4-way valve with connections at the four corners."""

    def __init__(
        self,
        position: Tuple[int, int],
        state: Literal["open", "closed"] = "open",
        color: Tuple[int, int, int] = (128, 128, 128),
        component_id: str = None,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize a four-way valve.

        Args:
            position: Grid position (x, y) - center of the H shape
            state: Valve state - "open" or "closed"
            color: RGB color tuple
            component_id: Optional unique identifier
            rotation: Rotation angle in degrees (0, 90)
            diameter: Pipe diameter in pixels (should match connected pipes)
        """
        super().__init__(position, component_id)
        self.state = state
        self.color = color
        self.rotation = rotation
        self.diameter = diameter

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the four-way valve as an H shape."""
        zoom = grid_size / 50.0

        # Center position (between the two grid cells the H spans)
        x = self.position[0] * grid_size + offset[0] +grid_size/2
        y = self.position[1] * grid_size + offset[1]

        pipe_width = int(self.diameter * zoom)

        # H dimensions - spans 2 grid cells horizontally
        h_width = grid_size * 2  # Total width of H
        h_height = grid_size *2  # Height of the vertical bars
        bridge_height = pipe_width  # Height of the horizontal bridge

        # Create surface for the H shape
        surf_width = int(2*h_width + pipe_width * 5)
        surf_height = int(2*h_height + pipe_width * 5)
        temp_surface = pygame.Surface((surf_width, surf_height), pygame.SRCALPHA)

        surf_center_x = surf_width // 2
        surf_center_y = surf_height // 2

        points = []
        points.append((surf_center_x - grid_size/2 + pipe_width*0.5, surf_center_y+pipe_width))
        points.append((surf_center_x - grid_size/2 + pipe_width*0.5, surf_center_y+(pipe_width*2)))
        points.append((surf_center_x - grid_size/2 - pipe_width*0.5, surf_center_y+(pipe_width*2)))
        points.append((surf_center_x - grid_size/2 - pipe_width*0.5, surf_center_y+pipe_width))
        points.append((surf_center_x - grid_size/2 - pipe_width*0.75, surf_center_y+pipe_width))
        points.append((surf_center_x - grid_size/2 - pipe_width*0.75, surf_center_y-pipe_width))
        points.append((surf_center_x - grid_size/2 - pipe_width*0.5, surf_center_y-pipe_width))
        points.append((surf_center_x - grid_size/2 - pipe_width*0.5, surf_center_y-(pipe_width*2)))
        points.append((surf_center_x - grid_size/2 + pipe_width*0.5, surf_center_y-(pipe_width*2)))
        points.append((surf_center_x - grid_size/2 + pipe_width*0.5, surf_center_y-(pipe_width)))

        points.append((surf_center_x + grid_size/2 - pipe_width*0.5, surf_center_y-pipe_width))
        points.append((surf_center_x + grid_size/2 - pipe_width*0.5, surf_center_y-(pipe_width*2)))
        points.append((surf_center_x + grid_size/2 + pipe_width*0.5, surf_center_y-(pipe_width*2)))
        points.append((surf_center_x + grid_size/2 + pipe_width*0.5, surf_center_y-pipe_width))
        points.append((surf_center_x + grid_size/2 + pipe_width*0.75, surf_center_y-pipe_width))
        points.append((surf_center_x + grid_size/2 + pipe_width*0.75, surf_center_y+pipe_width))
        points.append((surf_center_x + grid_size/2 + pipe_width*0.5, surf_center_y+pipe_width))
        points.append((surf_center_x + grid_size/2 + pipe_width*0.5, surf_center_y+(pipe_width*2)))
        points.append((surf_center_x + grid_size/2 - pipe_width*0.5, surf_center_y+(pipe_width*2)))
        points.append((surf_center_x + grid_size/2 - pipe_width*0.5, surf_center_y+(pipe_width)))

        # # Calculate H shape points
        # half_width = h_width // 2
        # half_height = h_height // 2
        # half_pipe = pipe_width // 2

        # # Left vertical bar of H
        # left_bar_left = surf_center_x - half_width - half_pipe
        # left_bar_right = surf_center_x - half_width + half_pipe

        # # Right vertical bar of H
        # right_bar_left = surf_center_x + half_width - half_pipe
        # right_bar_right = surf_center_x + half_width + half_pipe

        # # Vertical extents
        # top = surf_center_y - half_height - half_pipe
        # bottom = surf_center_y + half_height + half_pipe

        # # Bridge extents
        # bridge_top = surf_center_y - half_pipe
        # bridge_bottom = surf_center_y + half_pipe

        # # Build the H shape as a polygon
        # # Start from top-left corner and go clockwise
        # points = [
        #     # Left bar - top
        #     (left_bar_left, top),
        #     (left_bar_right, top),
        #     # Left bar - upper part to bridge
        #     (left_bar_right, bridge_top),
        #     # Bridge - top
        #     (right_bar_left, bridge_top),
        #     # Right bar - upper part from bridge
        #     (right_bar_left, top),
        #     (right_bar_right, top),
        #     # Right bar - right side down
        #     (right_bar_right, bottom),
        #     (right_bar_left, bottom),
        #     # Right bar - lower part to bridge
        #     (right_bar_left, bridge_bottom),
        #     # Bridge - bottom
        #     (left_bar_right, bridge_bottom),
        #     # Left bar - lower part from bridge
        #     (left_bar_right, bottom),
        #     (left_bar_left, bottom),
        # ]

        # Draw the H body
        pygame.draw.polygon(temp_surface, self.color, points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, points, 2)

        # If closed, draw flashing X in the center of the bridge
        if self.state == "closed":
            self._draw_flashing_x(temp_surface, surf_center_x, surf_center_y, time, pipe_width)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        surface.blit(rotated_surface, rotated_rect)

    def _draw_flashing_x(self, surface, center_x: int, center_y: int, time: float, scaled_diameter: int):
        """Draw a flashing X mark in the center of the bridge."""
        blink_speed = 2.0
        alpha = (math.sin(time * blink_speed * 2 * math.pi) + 1) / 2

        if alpha < 0.3:
            return

        mark_color = (255, 50, 50)
        mark_size = int(scaled_diameter * 0.8)

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
        """Convert four-way valve to dictionary."""
        data = {
            "type": "four_way_valve",
            "id": self.id,
            "position": list(self.position),
            "state": self.state,
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'FourWayValve':
        """Create four-way valve from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            state=data.get("state", "open"),
            color=tuple(data.get("color", [128, 128, 128])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

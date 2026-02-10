"""Heat exchanger component for thermal transfer systems."""

import pygame
from typing import Tuple
from .base import Component


class HeatExchanger(Component):
    """An H-shaped heat exchanger with three lines in the bridge section."""

    def __init__(
        self,
        position: Tuple[int, int],
        color: Tuple[int, int, int] = (180, 100, 60),
        component_id: str = None,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize a heat exchanger.

        Args:
            position: Grid position (x, y) - center of the H shape
            color: RGB color tuple
            component_id: Optional unique identifier
            rotation: Rotation angle in degrees (0, 90)
            diameter: Pipe diameter in pixels (should match connected pipes)
        """
        super().__init__(position, component_id)
        self.color = color
        self.rotation = rotation
        self.diameter = diameter

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the heat exchanger as an H shape with three lines in the bridge."""
        zoom = grid_size / 50.0

        # Center position (between the two grid cells the H spans)
        x = self.position[0] * grid_size + offset[0] + grid_size / 2
        y = self.position[1] * grid_size + offset[1]

        pipe_width = int(self.diameter * zoom)

        # H dimensions - spans 2 grid cells horizontally
        h_width = grid_size * 2  # Total width of H
        h_height = grid_size * 2  # Height of the vertical bars

        # Create surface for the H shape
        surf_width = int(2 * h_width + pipe_width * 5)
        surf_height = int(2 * h_height + pipe_width * 5)
        temp_surface = pygame.Surface((surf_width, surf_height), pygame.SRCALPHA)

        surf_center_x = surf_width // 2
        surf_center_y = surf_height // 2

        points = []
        points.append((surf_center_x - grid_size / 2 + pipe_width * 0.5, surf_center_y + pipe_width))
        points.append((surf_center_x - grid_size / 2 + pipe_width * 0.5, surf_center_y + (pipe_width * 2)))
        points.append((surf_center_x - grid_size / 2 - pipe_width * 0.5, surf_center_y + (pipe_width * 2)))
        points.append((surf_center_x - grid_size / 2 - pipe_width * 0.5, surf_center_y + pipe_width))
        points.append((surf_center_x - grid_size / 2 - pipe_width * 0.75, surf_center_y + pipe_width))
        points.append((surf_center_x - grid_size / 2 - pipe_width * 0.75, surf_center_y - pipe_width))
        points.append((surf_center_x - grid_size / 2 - pipe_width * 0.5, surf_center_y - pipe_width))
        points.append((surf_center_x - grid_size / 2 - pipe_width * 0.5, surf_center_y - (pipe_width * 2)))
        points.append((surf_center_x - grid_size / 2 + pipe_width * 0.5, surf_center_y - (pipe_width * 2)))
        points.append((surf_center_x - grid_size / 2 + pipe_width * 0.5, surf_center_y - (pipe_width)))

        points.append((surf_center_x + grid_size / 2 - pipe_width * 0.5, surf_center_y - pipe_width))
        points.append((surf_center_x + grid_size / 2 - pipe_width * 0.5, surf_center_y - (pipe_width * 2)))
        points.append((surf_center_x + grid_size / 2 + pipe_width * 0.5, surf_center_y - (pipe_width * 2)))
        points.append((surf_center_x + grid_size / 2 + pipe_width * 0.5, surf_center_y - pipe_width))
        points.append((surf_center_x + grid_size / 2 + pipe_width * 0.75, surf_center_y - pipe_width))
        points.append((surf_center_x + grid_size / 2 + pipe_width * 0.75, surf_center_y + pipe_width))
        points.append((surf_center_x + grid_size / 2 + pipe_width * 0.5, surf_center_y + pipe_width))
        points.append((surf_center_x + grid_size / 2 + pipe_width * 0.5, surf_center_y + (pipe_width * 2)))
        points.append((surf_center_x + grid_size / 2 - pipe_width * 0.5, surf_center_y + (pipe_width * 2)))
        points.append((surf_center_x + grid_size / 2 - pipe_width * 0.5, surf_center_y + (pipe_width)))

        # Draw the H body
        pygame.draw.polygon(temp_surface, self.color, points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, points, 2)

        # Draw three diagonal lines in the bridge section
        self._draw_heat_lines(temp_surface, surf_center_x, surf_center_y, grid_size, pipe_width)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        surface.blit(rotated_surface, rotated_rect)

    def _draw_heat_lines(self, surface, center_x: int, center_y: int, grid_size: float, pipe_width: int):
        """Draw three horizontal lines across the bridge section."""
        line_color = (255, 255, 255)  # White lines
        line_width = max(1, pipe_width // 6)

        # Calculate bridge bounds
        bridge_left = center_x - grid_size / 2 + pipe_width * 0.5
        bridge_right = center_x + grid_size / 2 - pipe_width * 0.5

        # Draw three evenly spaced horizontal lines
        for i in range(3):
            # Calculate y position for this line (evenly distributed within bridge height)
            line_y = center_y + pipe_width * 0.5 * (i - 1)  # -0.5, 0, 0.5 relative to center

            # Draw horizontal line across the bridge
            pygame.draw.line(
                surface,
                line_color,
                (int(bridge_left), int(line_y)),
                (int(bridge_right), int(line_y)),
                line_width
            )

    def to_dict(self) -> dict:
        """Convert heat exchanger to dictionary."""
        data = {
            "type": "heat_exchanger",
            "id": self.id,
            "position": list(self.position),
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }
        self._add_label_to_dict(data)
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'HeatExchanger':
        """Create heat exchanger from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            color=tuple(data.get("color", [180, 100, 60])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )
        component._load_label_from_dict(data)
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

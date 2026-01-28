"""Pump component for fluid circulation systems."""

import pygame
import math
from typing import Tuple, Literal
from .base import Component


class Pump(Component):
    """A pump component for circulating fluids with animated impeller when running."""

    def __init__(
        self,
        position: Tuple[int, int],
        state: Literal["running", "stopped"] = "stopped",
        color: Tuple[int, int, int] = (128, 128, 128),
        component_id: str = None,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize a pump.

        Args:
            position: Grid position (x, y)
            state: Pump state - "running" or "stopped"
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
        """Render the pump."""
        # Calculate zoom factor (base grid size is 50)
        zoom = grid_size / 50.0

        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]

        """Render a pump."""
        # Use the diameter to match connected pipes
        pipe_width = int(self.diameter * zoom)

        # Calculate pump body size
        pump_body_diameter = int(pipe_width * 2.5)

        # Create a surface for the pump that we can rotate
        pump_width = int(pipe_width * 4)
        pump_height = int(pipe_width * 4)
        temp_surface = pygame.Surface((pump_width, pump_height), pygame.SRCALPHA)

        # Center of the temporary surface
        surf_center_x = pump_width // 2
        surf_center_y = pump_height // 2

        # Draw pump body - a circle
        pygame.draw.circle(temp_surface, self.color, (surf_center_x, surf_center_y), pump_body_diameter // 2)

        # Draw border
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.circle(temp_surface, border_color, (surf_center_x, surf_center_y), pump_body_diameter // 2, 2)

        # Draw inlet/outlet pipes on the pump
        pipe_length = pipe_width

        # Left pipe (inlet)
        left_pipe_rect = pygame.Rect(
            surf_center_x - pump_body_diameter // 2 - pipe_length,
            surf_center_y - pipe_width // 2,
            pipe_length,
            pipe_width
        )
        pygame.draw.rect(temp_surface, self.color, left_pipe_rect)
        pygame.draw.rect(temp_surface, border_color, left_pipe_rect, 2)

        # Right pipe (outlet)
        right_pipe_rect = pygame.Rect(
            surf_center_x + pump_body_diameter // 2,
            surf_center_y - pipe_width // 2,
            pipe_length,
            pipe_width
        )
        pygame.draw.rect(temp_surface, self.color, right_pipe_rect)
        pygame.draw.rect(temp_surface, border_color, right_pipe_rect, 2)

        # If running, draw spinning fan/impeller
        if self.state == "running":
            self._draw_spinning_fan(temp_surface, surf_center_x, surf_center_y, time, pipe_width)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)

        # Get the rect and center it on the pump position
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        # Blit to main surface
        surface.blit(rotated_surface, rotated_rect)

    def _draw_spinning_fan(self, surface, center_x: int, center_y: int, time: float, scaled_diameter: int):
        """Draw a spinning fan/impeller in the pump center."""
        # Rotation speed (revolutions per second)
        rotation_speed = 0.25  # 2 revolutions per second

        # Calculate rotation angle
        angle_offset = (time * rotation_speed * 2 * math.pi) % (2 * math.pi)

        # Fan properties
        fan_color = (50, 150, 200)  # Blue color for fan
        num_blades = 4
        blade_length = scaled_diameter * 0.8
        blade_width = scaled_diameter * 0.15

        # Draw each blade
        for i in range(num_blades):
            # Calculate blade angle
            blade_angle = angle_offset + (i * 2 * math.pi / num_blades)

            # Calculate blade endpoints
            # Inner point (near center)
            inner_x = center_x + (scaled_diameter * 0.2) * math.cos(blade_angle)
            inner_y = center_y + (scaled_diameter * 0.2) * math.sin(blade_angle)

            # Outer point
            outer_x = center_x + blade_length * math.cos(blade_angle)
            outer_y = center_y + blade_length * math.sin(blade_angle)

            # Draw blade as a line with width
            pygame.draw.line(
                surface,
                fan_color,
                (int(inner_x), int(inner_y)),
                (int(outer_x), int(outer_y)),
                max(1, int(blade_width))
            )

        # Draw center hub
        hub_radius = int(scaled_diameter * 0.25)
        pygame.draw.circle(surface, fan_color, (center_x, center_y), hub_radius)

        # Draw hub border
        hub_border_color = (30, 100, 150)
        pygame.draw.circle(surface, hub_border_color, (center_x, center_y), hub_radius, 2)

    def to_dict(self) -> dict:
        """Convert pump to dictionary."""
        return {
            "type": "pump",
            "id": self.id,
            "position": list(self.position),
            "state": self.state,
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Pump':
        """Create pump from dictionary."""
        return cls(
            position=tuple(data["position"]),
            state=data.get("state", "stopped"),
            color=tuple(data.get("color", [128, 128, 128])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )

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
        pump_size = int(pipe_width * 4)
        temp_surface = pygame.Surface((pump_size, pump_size), pygame.SRCALPHA)

        # Center of the temporary surface
        surf_center_x = pump_size // 2
        surf_center_y = pump_size // 2

        # Build pump body as polygon with curved top/bottom and straight pipe connections
        points_top = []
        points_bottom = []
        points_left_pipe = []
        points_right_pipe = []
        num_segments = 20

        for i in range(num_segments + 1):
            # Top arc
            start_angle = (2*math.pi)-math.acos(pipe_width/pump_body_diameter)
            end_angle = (2*math.pi)+math.acos(pipe_width/pump_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments
            ix = surf_center_x + pump_body_diameter * math.sin(angle)//2
            iy = surf_center_y - pump_body_diameter * math.cos(angle)//2
            points_top.append((ix, iy))

        for i in range(num_segments + 1):
            # Bottom arc
            start_angle = (math.pi)-math.acos(pipe_width/pump_body_diameter)
            end_angle = (math.pi)+math.acos(pipe_width/pump_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments
            ix = surf_center_x + pump_body_diameter * math.sin(angle)//2
            iy = surf_center_y - pump_body_diameter * math.cos(angle)//2
            points_bottom.append((ix, iy))  

        # Left pipe connection points
        points_left_pipe.append((points_bottom[-1][0]-pipe_width, points_bottom[-1][1]))
        points_left_pipe.append((points_left_pipe[-1][0], points_top[0][1]))

        # Right pipe connection points
        points_right_pipe.append((points_top[-1][0]+pipe_width, points_top[-1][1]))
        points_right_pipe.append((points_right_pipe[-1][0], points_bottom[0][1]))

        all_points = points_top + points_right_pipe + points_bottom + points_left_pipe

        # Draw the pump body
        pygame.draw.polygon(temp_surface, self.color, all_points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, all_points, 2)

        # Draw fan/impeller (spinning if running, static if stopped)
        self._draw_fan(temp_surface, surf_center_x, surf_center_y, time, pipe_width)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)

        # Get the rect and center it on the pump position
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        # Blit to main surface
        surface.blit(rotated_surface, rotated_rect)

    def _draw_fan(self, surface, center_x: int, center_y: int, time: float, scaled_diameter: int):
        """Draw fan/impeller in the pump center (spinning if running, static if stopped)."""
        # Calculate rotation angle - only animate if running
        if self.state == "running":
            rotation_speed = 0.25  # revolutions per second
            angle_offset = (time * rotation_speed * 2 * math.pi) % (2 * math.pi)
            fan_color = (50, 150, 200)  # Blue color for fan when running
            hub_border_color = (30, 100, 150)
        else:
            angle_offset = 0  # Static position when stopped
            # Flash red when stopped
            blink_speed = 2.0  # blinks per second
            alpha = (math.sin(time * blink_speed * 2 * math.pi) + 1) / 2
            # Interpolate between blue and red based on alpha
            fan_color = (
                int(50 + (255 - 50) * alpha),
                int(150 - 100 * alpha),
                int(200 - 150 * alpha)
            )
            hub_border_color = (
                int(30 + (200 - 30) * alpha),
                int(100 - 70 * alpha),
                int(150 - 120 * alpha)
            )

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
        pygame.draw.circle(surface, hub_border_color, (center_x, center_y), hub_radius, 2)

    def to_dict(self) -> dict:
        """Convert pump to dictionary."""
        data = {
            "type": "pump",
            "id": self.id,
            "position": list(self.position),
            "state": self.state,
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }
        self._add_label_to_dict(data)
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'Pump':
        """Create pump from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            state=data.get("state", "stopped"),
            color=tuple(data.get("color", [128, 128, 128])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )
        component._load_label_from_dict(data)
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

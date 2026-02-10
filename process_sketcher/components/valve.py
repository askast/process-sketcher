"""Valve component for controlling fluid flow."""

import pygame
import math
from typing import Tuple, Literal
from .base import Component


class Valve(Component):
    """A 2-way valve for controlling fluid flow with open and closed states."""

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
        Initialize a valve.

        Args:
            position: Grid position (x, y)
            state: Valve state - "open" or "closed"
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
        """Render the valve."""
        # Calculate zoom factor (base grid size is 50)
        zoom = grid_size / 50.0

        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]


        """Render a valve."""
        # Use the diameter to match connected pipes
        pipe_width = int(self.diameter * zoom)

        # Calculate elbow radius based on pipe width
        # Inner radius should be large enough to look good
        valve_body_diameter = int(pipe_width * 1.5)

        # Create a surface for the elbow that we can rotate
        valve_size = int(pipe_width*4)
        temp_surface = pygame.Surface((valve_size, valve_size), pygame.SRCALPHA)

        # We want the inner corner of the elbow to be at the surface center
        # This way, after rotation, the inner corner will be at the node position
        surf_center_x = valve_size * 0.5
        surf_center_y = valve_size * 0.5

        points_top_right = []
        points_top_left = []
        points_bottom = []
        num_segments = 20

        for i in range(num_segments + 1):
            # 90-degree arc from 0 to π/2 (0 to 90 degrees)
            start_angle = (2*math.pi)-math.acos(pipe_width/valve_body_diameter)
            end_angle = (2*math.pi)-math.asin((0.2*pipe_width)/valve_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments

            # left top arc points
            ix = surf_center_x + valve_body_diameter * math.sin(angle)//2
            iy = surf_center_y - valve_body_diameter * math.cos(angle)//2
            points_top_left.append((ix, iy))  

        for i in range(num_segments + 1):
            # 90-degree arc from 0 to π/2 (0 to 90 degrees)
            start_angle = math.asin((0.2*pipe_width)/valve_body_diameter)
            end_angle = math.acos(pipe_width/valve_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments

            # Right top arc points
            ix = surf_center_x + valve_body_diameter * math.sin(angle)//2
            iy = surf_center_y - valve_body_diameter * math.cos(angle)//2
            points_top_right.append((ix, iy))

        for i in range(num_segments + 1):
            # 90-degree arc from 0 to π/2 (0 to 90 degrees)
            start_angle = math.pi-math.acos(pipe_width/valve_body_diameter)
            end_angle = math.pi+math.acos(pipe_width/valve_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments

            # left bottom arc points
            ix = surf_center_x + valve_body_diameter * math.sin(angle)//2
            iy = surf_center_y - valve_body_diameter * math.cos(angle)//2
            points_bottom.append((ix, iy))  

        points_valve_stem = []
        points_valve_stem.append((points_top_left[-1][0],points_top_left[-1][1]-pipe_width*.5))
        # print(f"{points_valve_stem=}")
        points_valve_stem.append((points_valve_stem[-1][0]-pipe_width*0.5,points_valve_stem[-1][1]))
        points_valve_stem.append((points_valve_stem[-1][0],points_valve_stem[-1][1]-pipe_width*0.2))
        points_valve_stem.append((points_valve_stem[-1][0]+pipe_width*1.2,points_valve_stem[-1][1]))
        points_valve_stem.append((points_valve_stem[-1][0],points_valve_stem[-1][1]+pipe_width*0.2))
        points_valve_stem.append((points_top_right[0][0],points_top_right[0][1]-pipe_width*.5))

        points_right_conn = []
        points_right_conn.append((points_top_right[-1][0]+pipe_width*.25,points_top_right[-1][1]))
        points_right_conn.append((points_right_conn[-1][0],points_bottom[0][1]))
        points_left_conn = []
        points_left_conn.append((points_bottom[-1][0]-pipe_width*.25,points_bottom[-1][1]))
        points_left_conn.append((points_left_conn[-1][0],points_top_left[0][1]))
        # Combine points to create closed polygon
        all_points = points_top_left + points_valve_stem +points_top_right+points_right_conn+points_bottom+points_left_conn
        # all_points.append((all_points[-1][0],all_points[-1][1]+pipe_width))
        # all_points.append((all_points[1][0],all_points[-1][1]))

        # Draw the elbow body
        pygame.draw.polygon(temp_surface, self.color, all_points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, all_points, 2)

        # If closed, draw flashing X
        if self.state == "closed":
            self._draw_flashing_x(temp_surface, int(surf_center_x), int(surf_center_y), time, pipe_width)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)

        # Get the rect and center it on the connector position
        # Since the inner corner was at the temp surface center, after rotation
        # it will be at the rotated surface center, which we position at the node
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        # Blit to main surface
        surface.blit(rotated_surface, rotated_rect)

    def _draw_flashing_x(self, surface, center_x: int, center_y: int, time: float, scaled_diameter: int):
        """Draw a flashing X mark in the valve center."""
        # Blinking animation
        blink_speed = 2.0  # blinks per second
        alpha = (math.sin(time * blink_speed * 2 * math.pi) + 1) / 2

        if alpha < 0.3:
            return

        # X mark color (red for closed valve)
        mark_color = (255, 50, 50)
        mark_size = int(scaled_diameter * 0.8)

        # Draw X as two diagonal lines
        # Top-left to bottom-right
        pygame.draw.line(
            surface,
            mark_color,
            (center_x - mark_size // 2, center_y - mark_size // 2),
            (center_x + mark_size // 2, center_y + mark_size // 2),
            3
        )

        # Top-right to bottom-left
        pygame.draw.line(
            surface,
            mark_color,
            (center_x + mark_size // 2, center_y - mark_size // 2),
            (center_x - mark_size // 2, center_y + mark_size // 2),
            3
        )

    def to_dict(self) -> dict:
        """Convert valve to dictionary."""
        data = {
            "type": "valve",
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
    def from_dict(cls, data: dict) -> 'Valve':
        """Create valve from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            state=data.get("state", "open"),
            color=tuple(data.get("color", [128, 128, 128])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )
        component._load_label_from_dict(data)
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

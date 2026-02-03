"""Pipe component for fluid flow systems."""

import pygame
import math
from typing import Tuple, Literal
from .base import Component


class Pipe(Component):
    """A pipe component that carries fluid with visualized flow direction."""

    def __init__(
        self,
        position: Tuple[int, int],
        end_position: Tuple[int, int],
        fluid_type: str = "water",
        color: Tuple[int, int, int] = (100, 150, 255),
        flow_direction: Literal["forward", "backward", "none"] = "forward",
        component_id: str = None,
        diameter: int = 20,
        trim_start: bool = False,
        trim_end: bool = False
    ):
        """
        Initialize a pipe.

        Args:
            position: Starting grid position (x, y)
            end_position: Ending grid position (x, y)
            fluid_type: Type of fluid in the pipe
            color: RGB color tuple for the pipe
            flow_direction: Direction of flow ("forward", "backward", "none")
            component_id: Optional unique identifier
            diameter: Visual diameter of the pipe in pixels
            trim_start: Trim pipe at start by half diameter (for elbow connections)
            trim_end: Trim pipe at end by half diameter (for elbow connections)
        """
        super().__init__(position, component_id)
        self.end_position = end_position
        self.fluid_type = fluid_type
        self.color = color
        self.flow_direction = flow_direction
        self.diameter = diameter
        self.trim_start = trim_start
        self.trim_end = trim_end

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the pipe with animated flow arrows."""
        # Calculate zoom factor (base grid size is 50)
        zoom = grid_size / 50.0
        scaled_diameter = int(self.diameter * zoom)

        # Calculate pixel positions
        start_x = self.position[0] * grid_size + offset[0]
        start_y = self.position[1] * grid_size + offset[1]
        end_x = self.end_position[0] * grid_size + offset[0]
        end_y = self.end_position[1] * grid_size + offset[1]

        # Apply trimming if needed (for elbow connections)
        if self.trim_start or self.trim_end:
            # Calculate pipe direction
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.sqrt(dx * dx + dy * dy)

            if length > 0:
                # Normalize direction
                dir_x = dx / length
                dir_y = dy / length

                # Trim distance accounts for the inner radius of the elbow
                trim_distance = scaled_diameter * 1.25

                # Apply trim at start
                if self.trim_start:
                    start_x += dir_x * trim_distance
                    start_y += dir_y * trim_distance

                # Apply trim at end
                if self.trim_end:
                    end_x -= dir_x * trim_distance
                    end_y -= dir_y * trim_distance

        # Draw the pipe body
        pygame.draw.line(surface, self.color, (start_x, start_y), (end_x, end_y), scaled_diameter)

        # Draw flow indicators
        if self.flow_direction == "none":
            # Draw blinking X marks for no flow
            self._render_blinking_marks(surface, start_x, start_y, end_x, end_y, time, scaled_diameter)
        else:
            # Draw flow arrows for forward/backward flow
            self._render_flow_arrows(surface, start_x, start_y, end_x, end_y, time, scaled_diameter)

    def _render_flow_arrows(self, surface, start_x: float, start_y: float,
                           end_x: float, end_y: float, time: float, scaled_diameter: int):
        """Render animated arrows showing flow direction."""
        # Calculate pipe angle and length
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

        angle = math.atan2(dy, dx)

        # Reverse angle if flow is backward
        if self.flow_direction == "backward":
            angle += math.pi

        # Arrow properties
        arrow_spacing = scaled_diameter * 2.5  # pixels between arrows
        arrow_size = scaled_diameter * 0.6
        animation_speed = 100  # pixels per second

        # Calculate animated offset (reverse direction for backward flow)
        anim_offset = (time * animation_speed) % arrow_spacing

        # Draw multiple arrows along the pipe
        num_arrows = int(length / arrow_spacing) + 2
        for i in range(num_arrows):
            # Calculate arrow position along the pipe
            # For forward flow: arrows move from start to end (add offset)
            # For backward flow: arrows move from end to start (subtract offset)
            if self.flow_direction == "forward":
                distance = i * arrow_spacing + anim_offset
            else:
                distance = i * arrow_spacing - anim_offset

            if distance < 0 or distance > length:
                continue

            t = distance / length
            arrow_x = start_x + dx * t
            arrow_y = start_y + dy * t

            # Draw arrow
            self._draw_arrow(surface, arrow_x, arrow_y, angle, arrow_size)

    def _render_blinking_marks(self, surface, start_x: float, start_y: float,
                              end_x: float, end_y: float, time: float, scaled_diameter: int):
        """Render blinking X marks or dots for no flow indication."""
        # Calculate pipe length
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

        # Blinking properties
        blink_speed = 2.0  # blinks per second
        mark_spacing = scaled_diameter * 2.5  # pixels between marks
        mark_size = scaled_diameter * 0.4

        # Calculate blink alpha (0 to 1)
        alpha = (math.sin(time * blink_speed * 2 * math.pi) + 1) / 2

        # Only show marks when alpha is above threshold (creates blink effect)
        if alpha < 0.3:
            return

        mark_color = (255, 255, 255)  # White marks

        # Draw X marks along the pipe
        num_marks = int(length / mark_spacing) + 1
        for i in range(num_marks):
            distance = i * mark_spacing
            if distance > length:
                continue

            t = distance / length
            mark_x = start_x + dx * t
            mark_y = start_y + dy * t

            # Draw X mark
            self._draw_x_mark(surface, mark_x, mark_y, mark_size, mark_color)

    def _draw_x_mark(self, surface, x: float, y: float, size: float, color: tuple):
        """Draw an X mark at the given position."""
        half_size = size / 2

        # Draw the two lines of the X
        pygame.draw.line(surface, color,
                        (x - half_size, y - half_size),
                        (x + half_size, y + half_size), 2)
        pygame.draw.line(surface, color,
                        (x - half_size, y + half_size),
                        (x + half_size, y - half_size), 2)

    def _draw_arrow(self, surface, x: float, y: float, angle: float, size: float):
        """Draw a single arrow at the given position and angle."""
        # Arrow head points
        arrow_color = (255, 255, 255)  # White arrows

        # Main arrow point (tip of the arrow)
        tip_x = x + math.cos(angle) * size
        tip_y = y + math.sin(angle) * size

        # Arrow wings (point backward from the tip)
        wing_angle = 2.8  # radians (about 160 degrees - points backward)
        wing_length = size * 0.7

        left_x = tip_x + math.cos(angle + wing_angle) * wing_length
        left_y = tip_y + math.sin(angle + wing_angle) * wing_length

        right_x = tip_x + math.cos(angle - wing_angle) * wing_length
        right_y = tip_y + math.sin(angle - wing_angle) * wing_length

        # Draw arrow as a triangle
        points = [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(surface, arrow_color, points)

    def to_dict(self) -> dict:
        """Convert pipe to dictionary."""
        data = {
            "type": "pipe",
            "id": self.id,
            "position": list(self.position),
            "end_position": list(self.end_position),
            "fluid_type": self.fluid_type,
            "color": list(self.color),
            "flow_direction": self.flow_direction,
            "diameter": self.diameter,
            "trim_start": self.trim_start,
            "trim_end": self.trim_end
        }
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'Pipe':
        """Create pipe from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            end_position=tuple(data["end_position"]),
            fluid_type=data.get("fluid_type", "water"),
            color=tuple(data.get("color", [100, 150, 255])),
            flow_direction=data.get("flow_direction", "forward"),
            component_id=data.get("id"),
            diameter=data.get("diameter", 20),
            trim_start=data.get("trim_start", False),
            trim_end=data.get("trim_end", False)
        )
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

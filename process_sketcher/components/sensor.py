"""Sensor component for measuring fluid properties."""

import pygame
import math
from typing import Tuple
from .base import Component


class Sensor(Component):
    """A sensor component for measuring fluid properties like flow, temperature, pressure."""

    # Common sensor types and their abbreviations
    SENSOR_TYPES = {
        "flow_meter": "FM",
        "thermocouple": "TC",
        "pressure": "PT",
        "level": "LT",
        "temperature": "TT",
        "flow": "FT",
        "density": "DT",
        "ph": "pH",
        "conductivity": "CT",
    }

    def __init__(
        self,
        position: Tuple[int, int],
        sensor_type: str = "flow_meter",
        sensor_label: str = None,
        color: Tuple[int, int, int] = (100, 150, 200),
        component_id: str = None,
        rotation: int = 0,
        diameter: int = 20
    ):
        """
        Initialize a sensor.

        Args:
            position: Grid position (x, y)
            sensor_type: Type of sensor (flow_meter, thermocouple, pressure, level, etc.)
            sensor_label: Custom label override for circle (if None, uses sensor_type abbreviation)
            color: RGB color tuple
            component_id: Optional unique identifier
            rotation: Rotation angle in degrees (0, 90, 180, 270)
            diameter: Pipe diameter in pixels (should match connected pipes)
        """
        super().__init__(position, component_id)
        self.sensor_type = sensor_type
        self.sensor_label = sensor_label if sensor_label else self.SENSOR_TYPES.get(sensor_type, sensor_type[:2].upper())
        self.color = color
        self.rotation = rotation
        self.diameter = diameter

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the sensor."""
        zoom = grid_size / 50.0

        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]

        pipe_width = int(self.diameter * zoom)
        valve_body_diameter = int(pipe_width * 1.5)

        # Create a surface for the sensor
        sensor_size = int(pipe_width * 5)
        temp_surface = pygame.Surface((sensor_size, sensor_size), pygame.SRCALPHA)

        surf_center_x = sensor_size * 0.5
        surf_center_y = sensor_size * 0.5

        points_top_right = []
        points_top_left = []
        points_bottom = []
        num_segments = 20

        # Build the valve-like body shape
        for i in range(num_segments + 1):
            start_angle = (2*math.pi)-math.acos(pipe_width/valve_body_diameter)
            end_angle = (2*math.pi)-math.asin((0.2*pipe_width)/valve_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments
            ix = surf_center_x + valve_body_diameter * math.sin(angle)//2
            iy = surf_center_y - valve_body_diameter * math.cos(angle)//2
            points_top_left.append((ix, iy))

        for i in range(num_segments + 1):
            start_angle = math.asin((0.2*pipe_width)/valve_body_diameter)
            end_angle = math.acos(pipe_width/valve_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments
            ix = surf_center_x + valve_body_diameter * math.sin(angle)//2
            iy = surf_center_y - valve_body_diameter * math.cos(angle)//2
            points_top_right.append((ix, iy))

        for i in range(num_segments + 1):
            start_angle = math.pi-math.acos(pipe_width/valve_body_diameter)
            end_angle = math.pi+math.acos(pipe_width/valve_body_diameter)
            angle = start_angle+(end_angle-start_angle) * i / num_segments
            ix = surf_center_x + valve_body_diameter * math.sin(angle)//2
            iy = surf_center_y - valve_body_diameter * math.cos(angle)//2
            points_bottom.append((ix, iy))

        # Sensor stem (narrower than valve stem, connects to circle)
        stem_width = pipe_width * 0.3
        stem_height = pipe_width * 0.4
        points_stem = []
        points_stem.append((surf_center_x - stem_width/2, points_top_left[-1][1]))
        points_stem.append((surf_center_x - stem_width/2, points_top_left[-1][1] - stem_height))
        points_stem.append((surf_center_x + stem_width/2, points_top_right[0][1] - stem_height))
        points_stem.append((surf_center_x + stem_width/2, points_top_right[0][1]))

        # Connection points
        points_right_conn = []
        points_right_conn.append((points_top_right[-1][0]+pipe_width*.25, points_top_right[-1][1]))
        points_right_conn.append((points_right_conn[-1][0], points_bottom[0][1]))

        points_left_conn = []
        points_left_conn.append((points_bottom[-1][0]-pipe_width*.25, points_bottom[-1][1]))
        points_left_conn.append((points_left_conn[-1][0], points_top_left[0][1]))

        # Combine points for body polygon
        all_points = points_top_left + points_stem + points_top_right + points_right_conn + points_bottom + points_left_conn

        # Draw the sensor body
        pygame.draw.polygon(temp_surface, self.color, all_points)

        # Draw border/outline
        border_color = tuple(max(0, c - 40) for c in self.color)
        pygame.draw.polygon(temp_surface, border_color, all_points, 2)

        # Draw the sensor circle on top
        circle_radius = int(pipe_width * 0.7)
        circle_center_y = int(points_top_left[-1][1] - stem_height - circle_radius)
        circle_center = (int(surf_center_x), circle_center_y)

        # Fill circle
        pygame.draw.circle(temp_surface, self.color, circle_center, circle_radius)
        # Circle border
        pygame.draw.circle(temp_surface, border_color, circle_center, circle_radius, 2)

        # Draw the sensor type label in the circle
        self._draw_sensor_label(temp_surface, circle_center, circle_radius, zoom)

        # Rotate the surface
        rotated_surface = pygame.transform.rotate(temp_surface, -self.rotation)
        rotated_rect = rotated_surface.get_rect(center=(int(x), int(y)))

        surface.blit(rotated_surface, rotated_rect)

    def _draw_sensor_label(self, surface, center: Tuple[int, int], radius: int, zoom: float):
        """Draw the sensor type label in the circle."""
        # Calculate font size based on radius and label length
        font_size = max(8, int(radius * 1.2 / max(1, len(self.sensor_label) * 0.5)))

        try:
            font = pygame.font.SysFont("Arial", font_size, bold=True)
        except:
            font = pygame.font.Font(None, font_size)

        # Render text
        text_color = (255, 255, 255)
        text_surface = font.render(self.sensor_label, True, text_color)
        text_rect = text_surface.get_rect(center=center)

        surface.blit(text_surface, text_rect)

    def to_dict(self) -> dict:
        """Convert sensor to dictionary."""
        data = {
            "type": "sensor",
            "id": self.id,
            "position": list(self.position),
            "sensor_type": self.sensor_type,
            "sensor_label": self.sensor_label,
            "color": list(self.color),
            "rotation": self.rotation,
            "diameter": self.diameter
        }
        self._add_label_to_dict(data)
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'Sensor':
        """Create sensor from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            sensor_type=data.get("sensor_type", "flow_meter"),
            sensor_label=data.get("sensor_label"),
            color=tuple(data.get("color", [100, 150, 200])),
            component_id=data.get("id"),
            rotation=data.get("rotation", 0),
            diameter=data.get("diameter", 20)
        )
        component._load_label_from_dict(data)
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

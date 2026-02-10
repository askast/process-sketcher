"""Tank component for fluid storage systems."""

import pygame
import math
from typing import Tuple, List, Dict, Literal, Optional
from .base import Component


class Tank(Component):
    """A tank component for storing fluids with multiple layers and animated drain/fill."""

    def __init__(
        self,
        position: Tuple[int, int],
        width: int = 3,
        height: int = 4,
        top_style: Literal["flat", "ellipsoidal"] = "flat",
        bottom_style: Literal["flat", "ellipsoidal"] = "flat",
        fluids: Optional[List[Dict]] = None,
        fill_percent: float = 75.0,
        component_id: str = None,
        wall_thickness: int = 3
    ):
        """
        Initialize a tank.

        Args:
            position: Grid position (x, y) for bottom-left corner
            width: Width in grid units
            height: Height in grid units
            top_style: Style of top ("flat" or "ellipsoidal" - adds rounded corners)
            bottom_style: Style of bottom ("flat" or "ellipsoidal" - adds rounded corners)
            fluids: List of fluid dicts with 'color', 'name', 'percent', 'drain_rate', 'fill_rate'
            fill_percent: Overall fill percentage (0-100)
            component_id: Optional unique identifier
            wall_thickness: Thickness of tank walls in pixels
        """
        super().__init__(position, component_id)
        self.width = width
        self.height = height
        self.top_style = top_style
        self.bottom_style = bottom_style
        self.initial_fill_percent = max(0.0, min(100.0, fill_percent))
        self.fill_percent = self.initial_fill_percent
        self.wall_thickness = wall_thickness

        # Default to single water layer if no fluids specified
        if fluids is None:
            self.fluids = [
                {
                    "color": [100, 150, 255],
                    "name": "water",
                    "percent": 100.0,
                    "drain_rate": 0.0,  # percent per second
                    "fill_rate": 0.0    # percent per second
                }
            ]
        else:
            self.fluids = fluids
            # Add default rates if not specified
            for fluid in self.fluids:
                fluid.setdefault("drain_rate", 0.0)
                fluid.setdefault("fill_rate", 0.0)

        # Normalize fluid percentages
        self._normalize_fluid_percentages()

        # Animation tracking
        self.last_update_time = 0.0

    def _normalize_fluid_percentages(self):
        """Scale fluid percentages to match the initial fill_percent of the tank."""
        if not self.fluids:
            return

        total = sum(fluid.get("percent", 0) for fluid in self.fluids)
        if total > 0:
            # Scale fluid percentages so they sum to the initial fill_percent
            for fluid in self.fluids:
                fluid["percent"] = (fluid.get("percent", 0) / total) * self.initial_fill_percent

    def _update_fluid_levels(self, time: float):
        """Update fluid levels based on drain/fill rates."""
        if self.last_update_time == 0.0:
            self.last_update_time = time
            return

        dt = time - self.last_update_time
        self.last_update_time = time

        # Update each fluid level based on their individual rates
        # fluid["percent"] represents the percentage of TANK capacity this fluid occupies
        for fluid in self.fluids:
            drain_rate = fluid.get("drain_rate", 0.0)
            fill_rate = fluid.get("fill_rate", 0.0)
            net_rate = fill_rate - drain_rate

            # Update the fluid's absolute percentage of tank capacity
            fluid["percent"] = max(0.0, fluid["percent"] + net_rate * dt)

        # Calculate total fill percentage as sum of all fluid levels
        total_fill = sum(fluid["percent"] for fluid in self.fluids)

        # If total exceeds 100%, scale down all fluids proportionally
        if total_fill > 100.0:
            scale_factor = 100.0 / total_fill
            for fluid in self.fluids:
                fluid["percent"] *= scale_factor
            self.fill_percent = 100.0
        else:
            self.fill_percent = total_fill

    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """Render the tank with fluids and connection points."""
        # Update fluid levels
        self._update_fluid_levels(time)

        # Calculate pixel positions
        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]
        pixel_width = self.width * grid_size
        pixel_height = self.height * grid_size

        # Calculate corner radii based on style
        top_radius = int(pixel_width // 4) if self.top_style == "ellipsoidal" else 0
        bottom_radius = int(pixel_width // 4) if self.bottom_style == "ellipsoidal" else 0

        # Draw fluids first (behind walls)
        self._render_fluids(surface, x, y, pixel_width, pixel_height, bottom_radius)

        # Draw corner masks to hide fluid overflow in rounded corners
        self._render_corner_masks(surface, x, y, pixel_width, pixel_height, top_radius, bottom_radius)

        # Draw tank outline
        self._render_tank_outline(surface, x, y, pixel_width, pixel_height, top_radius, bottom_radius)

    def _render_fluids(self, surface, x: float, y: float, width: float, height: float, bottom_radius: int):
        """Render fluid layers as stacked rectangles."""
        if self.fill_percent <= 0:
            return

        # Start from bottom and stack fluid rectangles
        # Each fluid's percent is now an absolute percentage of tank capacity
        current_y = y + height  # Start at bottom

        for fluid in self.fluids:
            if fluid["percent"] <= 0:
                continue

            color = tuple(fluid["color"])
            # Layer height is based on fluid's absolute percentage of tank capacity
            layer_height = height * (fluid["percent"] / 100.0)

            if layer_height > 0:
                # Draw fluid layer as simple rectangle
                fluid_rect = pygame.Rect(
                    x + self.wall_thickness,
                    current_y - layer_height,
                    width - 2 * self.wall_thickness,
                    layer_height
                )
                pygame.draw.rect(surface, color, fluid_rect)

                current_y -= layer_height

    def _render_corner_masks(self, surface, x: float, y: float, width: float, height: float,
                            top_radius: int, bottom_radius: int):
        """Render corner masks with quarter-circle cutouts to hide fluid overflow."""
        background_color = (25, 25, 30)  # Match visualization background color

        # Render bottom corner masks if bottom is ellipsoidal
        if bottom_radius > 0:
            # Create mask for bottom corners
            mask_size = bottom_radius
            mask_surface = pygame.Surface((mask_size, mask_size), pygame.SRCALPHA)
            mask_surface.fill(background_color)  # Fill with black

            # Cut out quarter circle by drawing transparent circle
            pygame.draw.circle(mask_surface, (0, 0, 0, 0), (0, 0), bottom_radius)

            # Bottom-left corner
            surface.blit(mask_surface, (int(x + width - mask_size), int(y + height - mask_size)))

            # Bottom-right corner (flip horizontally)
            mask_surface_flipped = pygame.transform.flip(mask_surface, True, False)
            surface.blit(mask_surface_flipped, (int(x), int(y + height - mask_size)))

        # Render top corner masks if top is ellipsoidal
        if top_radius > 0:
            # Create mask for top corners
            mask_size = top_radius
            mask_surface = pygame.Surface((mask_size, mask_size), pygame.SRCALPHA)
            mask_surface.fill(background_color)  # Fill with black

            # Cut out quarter circle by drawing transparent circle
            pygame.draw.circle(mask_surface, (0, 0, 0, 0), (0, mask_size), top_radius)

            # Top-left corner
            surface.blit(mask_surface, (int(x + width - mask_size), int(y)))

            # Top-right corner (flip horizontally)
            mask_surface_flipped = pygame.transform.flip(mask_surface, True, False)
            surface.blit(mask_surface_flipped, (int(x), int(y)))

    def _render_tank_outline(self, surface, x: float, y: float, width: float, height: float,
                            top_radius: int, bottom_radius: int):
        """Render tank outline as a rounded rectangle."""
        wall_color = (80, 80, 80)

        # Create rectangle for tank
        tank_rect = pygame.Rect(x, y, width, height)

        # Determine which corners should be rounded
        border_radius = 0
        border_top_left_radius = top_radius
        border_top_right_radius = top_radius
        border_bottom_left_radius = bottom_radius
        border_bottom_right_radius = bottom_radius

        # Draw outline with appropriate corner radii
        pygame.draw.rect(
            surface,
            wall_color,
            tank_rect,
            width=self.wall_thickness,
            border_top_left_radius=border_top_left_radius,
            border_top_right_radius=border_top_right_radius,
            border_bottom_left_radius=border_bottom_left_radius,
            border_bottom_right_radius=border_bottom_right_radius
        )

    def to_dict(self) -> dict:
        """Convert tank to dictionary."""
        data = {
            "type": "tank",
            "id": self.id,
            "position": list(self.position),
            "width": self.width,
            "height": self.height,
            "top_style": self.top_style,
            "bottom_style": self.bottom_style,
            "fluids": self.fluids,
            "fill_percent": self.initial_fill_percent,
            "wall_thickness": self.wall_thickness
        }
        self._add_label_to_dict(data)
        return self._add_animation_to_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> 'Tank':
        """Create tank from dictionary."""
        component = cls(
            position=tuple(data["position"]),
            width=data.get("width", 3),
            height=data.get("height", 4),
            top_style=data.get("top_style", "flat"),
            bottom_style=data.get("bottom_style", "flat"),
            fluids=data.get("fluids"),
            fill_percent=data.get("fill_percent", 75.0),
            component_id=data.get("id"),
            wall_thickness=data.get("wall_thickness", 3)
        )
        component._load_label_from_dict(data)
        if 'animation' in data:
            component.set_animation(data['animation'])
        return component

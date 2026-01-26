"""Grid system for component placement and rendering."""

import pygame
from typing import Tuple


class Grid:
    """Grid system for snapping components and rendering grid lines."""

    def __init__(self, cell_size: int = 50, show_grid: bool = True):
        """
        Initialize the grid.

        Args:
            cell_size: Size of each grid cell in pixels
            show_grid: Whether to render grid lines
        """
        self.cell_size = cell_size
        self.show_grid = show_grid
        self.grid_color = (40, 40, 40)

    def snap_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """
        Snap a pixel position to the nearest grid point.

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels

        Returns:
            Grid coordinates (grid_x, grid_y)
        """
        grid_x = round(x / self.cell_size)
        grid_y = round(y / self.cell_size)
        return (grid_x, grid_y)

    def grid_to_pixel(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """
        Convert grid coordinates to pixel coordinates.

        Args:
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate

        Returns:
            Pixel coordinates (x, y)
        """
        return (grid_x * self.cell_size, grid_y * self.cell_size)

    def render(self, surface, offset: Tuple[int, int] = (0, 0)):
        """
        Render grid lines on the surface.

        Args:
            surface: Pygame surface to render on
            offset: Offset (x, y) for rendering position
        """
        if not self.show_grid:
            return

        width, height = surface.get_size()

        # Draw vertical lines
        for x in range(0, width, self.cell_size):
            pygame.draw.line(
                surface,
                self.grid_color,
                (x + offset[0] % self.cell_size, 0),
                (x + offset[0] % self.cell_size, height),
                1
            )

        # Draw horizontal lines
        for y in range(0, height, self.cell_size):
            pygame.draw.line(
                surface,
                self.grid_color,
                (0, y + offset[1] % self.cell_size),
                (width, y + offset[1] % self.cell_size),
                1
            )

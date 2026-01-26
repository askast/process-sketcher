"""Base component class for all fluid flow system elements."""

from abc import ABC, abstractmethod
from typing import Tuple


class Component(ABC):
    """Base class for all components in the fluid flow system."""

    def __init__(self, position: Tuple[int, int], component_id: str = None):
        """
        Initialize a component.

        Args:
            position: Grid position (x, y) of the component
            component_id: Optional unique identifier for the component
        """
        self.position = position
        self.id = component_id

    @abstractmethod
    def render(self, surface, grid_size: int, offset: Tuple[int, int], time: float):
        """
        Render the component on the given surface.

        Args:
            surface: Pygame surface to render on
            grid_size: Size of each grid cell in pixels
            offset: Offset (x, y) for rendering position
            time: Current animation time in seconds
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert component to dictionary for JSON serialization."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'Component':
        """Create component from dictionary (JSON deserialization)."""
        pass

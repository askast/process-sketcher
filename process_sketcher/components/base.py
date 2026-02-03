"""Base component class for all fluid flow system elements."""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Dict, Any

from process_sketcher.animation import AnimationController


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
        self._animation_controller: Optional[AnimationController] = None
        self._animation_data: Optional[List[Dict[str, Any]]] = None

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

    def set_animation(self, data: List[Dict[str, Any]]) -> None:
        """
        Initialize animation from JSON data.

        Args:
            data: List of keyframe dictionaries
        """
        if data:
            self._animation_data = data
            self._animation_controller = AnimationController(data)

    def apply_animation(self, time: float) -> Dict[str, Any]:
        """
        Apply animation property overrides for the current time.

        Args:
            time: Current animation time in seconds

        Returns:
            Dictionary of original property values that were overridden
        """
        if self._animation_controller is None:
            return {}

        overrides = self._animation_controller.get_property_overrides(time)
        originals = {}

        for prop, value in overrides.items():
            if hasattr(self, prop):
                originals[prop] = getattr(self, prop)
                setattr(self, prop, value)

        return originals

    def restore_properties(self, originals: Dict[str, Any]) -> None:
        """
        Restore properties after rendering.

        Args:
            originals: Dictionary of original property values to restore
        """
        for prop, value in originals.items():
            setattr(self, prop, value)

    def _add_animation_to_dict(self, data: dict) -> dict:
        """
        Helper to add animation data to serialization dict.

        Args:
            data: Existing serialization dictionary

        Returns:
            Dictionary with animation data added if present
        """
        if self._animation_data:
            data['animation'] = self._animation_data
        return data

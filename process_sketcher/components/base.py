"""Base component class for all fluid flow system elements."""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Dict, Any, Literal

from process_sketcher.animation import AnimationController


class Component(ABC):
    """Base class for all components in the fluid flow system."""

    # Default label visibility (subclasses can override)
    _default_show_label = True

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

        # Label properties
        self.show_label: bool = self._default_show_label
        self.label_text: Optional[str] = None  # None means use component id
        self.label_position: Literal["above", "below", "left", "right"] = "above"

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

    def _add_label_to_dict(self, data: dict) -> dict:
        """
        Helper to add label data to serialization dict.

        Args:
            data: Existing serialization dictionary

        Returns:
            Dictionary with label data added if not default
        """
        if not self.show_label and self._default_show_label:
            data['show_label'] = False
        elif self.show_label and not self._default_show_label:
            data['show_label'] = True
        if self.label_text is not None:
            data['label_text'] = self.label_text
        if self.label_position != "above":
            data['label_position'] = self.label_position
        return data

    def _load_label_from_dict(self, data: dict) -> None:
        """
        Load label properties from dictionary data.

        Args:
            data: Dictionary containing component data
        """
        if 'show_label' in data:
            self.show_label = data['show_label']
        if 'label_text' in data:
            self.label_text = data['label_text']
        if 'label_position' in data:
            self.label_position = data['label_position']

    def get_label_render_info(self, grid_size: int, offset: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        """
        Get information needed to render the label.

        Args:
            grid_size: Size of each grid cell in pixels
            offset: Offset (x, y) for rendering position

        Returns:
            Dictionary with label text and position, or None if no label
        """
        if not self.show_label:
            return None

        text = self.label_text if self.label_text is not None else (self.id or "")
        if not text:
            return None

        # Calculate base position
        x = self.position[0] * grid_size + offset[0]
        y = self.position[1] * grid_size + offset[1]

        return {
            'text': text,
            'base_x': x,
            'base_y': y,
            'position': self.label_position,
            'grid_size': grid_size
        }

"""Animation keyframe system for component property cycling."""

from typing import Dict, List, Optional, Any, Tuple


class AnimationController:
    """Controls keyframe-based animation for component properties."""

    def __init__(self, keyframes: List[Dict[str, Any]]):
        """
        Initialize animation controller with keyframes.

        Args:
            keyframes: List of keyframe dictionaries, each containing:
                - duration: seconds to stay in this keyframe
                - Other keys: property overrides to apply
        """
        self._keyframes: List[Dict[str, Any]] = []
        self._durations: List[float] = []
        self._total_duration: float = 0.0

        for kf in keyframes:
            duration = kf.get('duration', 0)
            # Ensure minimum duration to avoid division issues
            if duration <= 0:
                duration = 0.001

            self._durations.append(duration)
            self._total_duration += duration

            # Store properties (excluding duration)
            props = {k: v for k, v in kf.items() if k != 'duration'}
            self._keyframes.append(props)

    @property
    def total_duration(self) -> float:
        """Get total animation cycle duration in seconds."""
        return self._total_duration

    def get_active_keyframe_index(self, time: float) -> int:
        """
        Find the index of the current keyframe based on cycle time.

        Args:
            time: Current time in seconds

        Returns:
            Index of the active keyframe
        """
        if not self._keyframes or self._total_duration <= 0:
            return -1

        # Calculate position within the cycle
        cycle_time = time % self._total_duration

        # Find which keyframe we're in
        elapsed = 0.0
        for i, duration in enumerate(self._durations):
            elapsed += duration
            if cycle_time < elapsed:
                return i

        # Fallback to last keyframe (shouldn't happen due to modulo)
        return len(self._keyframes) - 1

    def get_active_keyframe(self, time: float) -> Optional[Dict[str, Any]]:
        """
        Get the current keyframe based on cycle time.

        Args:
            time: Current time in seconds

        Returns:
            Dictionary of property overrides, or None if no keyframes
        """
        index = self.get_active_keyframe_index(time)
        if index < 0:
            return None
        return self._keyframes[index]

    def get_property_overrides(self, time: float) -> Dict[str, Any]:
        """
        Get property overrides for the current time with type conversions.

        Args:
            time: Current time in seconds

        Returns:
            Dictionary of properties to apply, with appropriate type conversions
        """
        keyframe = self.get_active_keyframe(time)
        if keyframe is None:
            return {}

        result = {}
        for key, value in keyframe.items():
            # Convert lists to tuples for color and other tuple properties
            if key == 'color' and isinstance(value, list):
                result[key] = tuple(value)
            elif isinstance(value, list):
                # Convert any list to tuple (for position, etc.)
                result[key] = tuple(value)
            else:
                result[key] = value

        return result

    def has_keyframes(self) -> bool:
        """Check if this controller has any keyframes."""
        return len(self._keyframes) > 0

"""JSON loader for fluid flow system definitions."""

import json
from typing import List, Any
from .components import Component, Pipe, Elbow, Tank, Tee


class JSONLoader:
    """Loads and parses JSON definitions of fluid flow systems."""

    @staticmethod
    def _compact_json_formatter(obj: Any, indent_level: int = 0) -> str:
        """
        Format JSON in a compact way with arrays and simple objects on single lines.

        Args:
            obj: The object to format
            indent_level: Current indentation level

        Returns:
            Formatted JSON string
        """
        indent = "  " * indent_level
        next_indent = "  " * (indent_level + 1)

        if isinstance(obj, dict):
            if not obj:
                return "{}"

            # Check if this is a simple object (all values are primitives or small arrays)
            is_simple = all(
                not isinstance(v, (dict, list)) or
                (isinstance(v, list) and len(v) <= 3 and all(not isinstance(x, (dict, list)) for x in v))
                for v in obj.values()
            )

            if is_simple and len(obj) <= 3:
                # Format simple objects on one line
                items = [f'"{k}": {json.dumps(v)}' for k, v in obj.items()]
                return "{" + ", ".join(items) + "}"
            else:
                # Format complex objects with newlines
                lines = ["{"]
                items = list(obj.items())
                for i, (k, v) in enumerate(items):
                    formatted_value = JSONLoader._compact_json_formatter(v, indent_level + 1)
                    comma = "," if i < len(items) - 1 else ""
                    lines.append(f'{next_indent}"{k}": {formatted_value}{comma}')
                lines.append(f"{indent}}}")
                return "\n".join(lines)

        elif isinstance(obj, list):
            if not obj:
                return "[]"

            # Check if all elements are primitives (not dict or list)
            all_primitives = all(not isinstance(x, (dict, list)) for x in obj)

            if all_primitives:
                # Format arrays of primitives on one line
                return "[" + ", ".join(json.dumps(x) for x in obj) + "]"
            else:
                # Format arrays with complex elements with newlines
                lines = ["["]
                for i, item in enumerate(obj):
                    formatted_item = JSONLoader._compact_json_formatter(item, indent_level + 1)
                    comma = "," if i < len(obj) - 1 else ""
                    lines.append(f"{next_indent}{formatted_item}{comma}")
                lines.append(f"{indent}]")
                return "\n".join(lines)
        else:
            # Primitive values
            return json.dumps(obj)

    @staticmethod
    def load_from_string(json_string: str) -> List[Component]:
        """
        Load components from a JSON string.

        Args:
            json_string: JSON string containing component definitions

        Returns:
            List of Component objects

        Raises:
            ValueError: If JSON is invalid or contains unknown component types
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ValueError("JSON must be an object")

        components_data = data.get("components", [])
        if not isinstance(components_data, list):
            raise ValueError("'components' must be an array")

        components = []
        for comp_data in components_data:
            component = JSONLoader._create_component(comp_data)
            components.append(component)

        return components

    @staticmethod
    def _create_component(data: dict) -> Component:
        """Create a component from dictionary data."""
        comp_type = data.get("type")

        if comp_type == "pipe":
            return Pipe.from_dict(data)
        elif comp_type == "elbow":
            return Elbow.from_dict(data)
        elif comp_type == "tank":
            return Tank.from_dict(data)
        elif comp_type == "tee":
            return Tee.from_dict(data)
        else:
            raise ValueError(f"Unknown component type: {comp_type}")

    @staticmethod
    def components_to_json(components: List[Component]) -> str:
        """
        Convert a list of components to JSON string in compact format.

        Args:
            components: List of Component objects

        Returns:
            JSON string representation
        """
        data = {
            "components": [comp.to_dict() for comp in components]
        }
        return JSONLoader._compact_json_formatter(data)

    @staticmethod
    def get_example_json() -> str:
        """Get an example JSON definition in compact format."""
        example = {
            "components": [
                {
                    "type": "tank",
                    "id": "tank1",
                    "position": [10, 2],
                    "width": 3,
                    "height": 5,
                    "top_style": "ellipsoidal",
                    "bottom_style": "ellipsoidal",
                    "fill_percent": 70,
                    "fluids": [
                        {"color": [200, 100, 50], "name": "oil", "percent": 30, "drain_rate": 0, "fill_rate": 2},
                        {"color": [100, 150, 255], "name": "water", "percent": 70, "drain_rate": 3, "fill_rate": 0}
                    ]
                },
                {
                    "type": "pipe",
                    "id": "pipe1",
                    "position": [2, 2],
                    "end_position": [8, 2],
                    "fluid_type": "water",
                    "color": [100, 150, 255],
                    "flow_direction": "forward",
                    "diameter": 20,
                    "trim_end": True
                },
                {
                    "type": "elbow",
                    "id": "elbow1",
                    "position": [8, 2],
                    "connector_type": "elbow",
                    "color": [100, 150, 255],
                    "size": 30,
                    "rotation": 270,
                    "diameter": 20
                },
                {
                    "type": "pipe",
                    "id": "pipe2",
                    "position": [8, 2],
                    "end_position": [8, 6],
                    "fluid_type": "water",
                    "color": [100, 150, 255],
                    "flow_direction": "forward",
                    "diameter": 20,
                    "trim_start": True
                },
                {
                    "type": "pipe",
                    "id": "pipe3",
                    "position": [2, 5],
                    "end_position": [6, 5],
                    "fluid_type": "oil",
                    "color": [255, 100, 50],
                    "flow_direction": "backward",
                    "diameter": 20
                }
            ]
        }
        return JSONLoader._compact_json_formatter(example)

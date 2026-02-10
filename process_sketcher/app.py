"""Main application with dual-pane UI for P&ID Animator."""

import pygame
import sys
import os
import json
from pathlib import Path
from typing import List, Optional
from .components import Component
from .grid import Grid
from .json_loader import JSONLoader


class ProcessSketcherApp:
    """Main application class for P&ID Animator."""

    # Default system file
    SYSTEM_FILE = Path.cwd() / "system.json"

    def __init__(self, width: int = 1600, height: int = 900):
        """
        Initialize the application.

        Args:
            width: Window width in pixels
            height: Window height in pixels
        """
        pygame.init()
        pygame.font.init()
        pygame.key.set_repeat(400, 30)  # Enable key repeat (400ms delay, 30ms interval)

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.scrap.init()  # Initialize clipboard support
        pygame.display.set_caption("P&ID Animator")

        # Pane layout (left = JSON editor, right = visualization)
        self.editor_width = width // 2
        self.viz_width = width - self.editor_width

        # Divider for resizing panes
        self.divider_width = 4
        self.divider_dragging = False
        self.divider_color = (60, 60, 65)
        self.divider_hover_color = (100, 100, 110)

        # Colors
        self.bg_color = (20, 20, 25)
        self.editor_bg = (30, 30, 35)
        self.viz_bg = (25, 25, 30)
        self.text_color = (220, 220, 220)
        self.button_color = (70, 130, 180)
        self.button_hover_color = (100, 160, 210)

        # Visualization pan and zoom
        self.viz_pan_x = 0.0
        self.viz_pan_y = 0.0
        self.viz_zoom = 1.0
        self.viz_dragging = False
        self.viz_drag_start = (0, 0)

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.mono_font = pygame.font.SysFont('Monaco, Courier New, monospace', 18)

        # Grid system
        self.grid = Grid(cell_size=50, show_grid=True)

        # Components
        self.components: List[Component] = []

        # File management
        self.current_file: Optional[Path] = None

        # JSON editor
        self._load_from_last_file()
        self.scroll_offset = 0
        self.error_message: Optional[str] = None

        # Cursor position
        self.cursor_line = 0
        self.cursor_col = 0
        self.cursor_blink_time = 0.0
        self.editor_text_start_y = 60  # Will be updated in render

        # Text selection
        self.selection_start = None  # (line, col) or None
        self.selection_end = None    # (line, col) or None
        self.editor_mouse_down = False

        # Scrollbar
        self.scrollbar_width = 12
        self.scrollbar_dragging = False
        self.scrollbar_drag_start_y = 0
        self.scrollbar_drag_start_offset = 0

        # Animation
        self.clock = pygame.time.Clock()
        self.time = 0.0

        # Buttons
        self.load_button_rect = pygame.Rect(self.editor_width - 120, 10, 110, 40)
        self.save_button_rect = pygame.Rect(self.editor_width - 240, 10, 110, 40)
        self.load_button_hovered = False
        self.save_button_hovered = False

        # Load initial example
        self._load_json()

    def _load_json(self):
        """Load JSON from the editor text."""
        try:
            self.components = JSONLoader.load_from_string(self.json_text)
            self.error_message = None
            # Auto-fit view to components
            self._auto_fit_view()
        except Exception as e:
            self.error_message = str(e)

    def _load_from_last_file(self):
        """Load JSON from system.json, or use example if not found."""
        if self.SYSTEM_FILE.exists():
            try:
                self.current_file = self.SYSTEM_FILE
                with open(self.current_file, 'r') as f:
                    self.json_text = f.read()
                self.json_lines = self.json_text.split('\n')
                return
            except Exception as e:
                print(f"Error loading system.json: {e}")

        # Fall back to example
        self.json_text = JSONLoader.get_example_json()
        self.json_lines = self.json_text.split('\n')
        self.current_file = None

    def _save_to_file(self):
        """Save current JSON to file."""
        if self.current_file is None:
            # Default to current directory with a default name
            self.current_file = self.SYSTEM_FILE

        try:
            with open(self.current_file, 'w') as f:
                f.write(self.json_text)

            # Clear any errors
            self.error_message = None
        except Exception as e:
            self.error_message = f"Save error: {str(e)}"

    def _auto_fit_view(self):
        """Auto-fit the visualization to show all components with margin."""
        if not self.components:
            # Reset to default view
            self.viz_pan_x = 0.0
            self.viz_pan_y = 0.0
            self.viz_zoom = 1.0
            return

        # Calculate bounding box of all components
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for component in self.components:
            # Get component position
            x, y = component.position
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

            # For pipes, also include end position
            if hasattr(component, 'end_position'):
                ex, ey = component.end_position
                min_x = min(min_x, ex)
                min_y = min(min_y, ey)
                max_x = max(max_x, ex)
                max_y = max(max_y, ey)

        # Add margin (1 grid cell on each side)
        margin = 1
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        # Calculate center and size in grid coordinates
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width_grid = max_x - min_x
        height_grid = max_y - min_y

        # Convert to pixels
        grid_size = self.grid.cell_size
        width_pixels = width_grid * grid_size
        height_pixels = height_grid * grid_size

        # Calculate zoom to fit in viewport
        viewport_width = self.viz_width * 0.9  # 90% of viewport
        viewport_height = self.height * 0.9

        zoom_x = viewport_width / width_pixels if width_pixels > 0 else 1.0
        zoom_y = viewport_height / height_pixels if height_pixels > 0 else 1.0
        self.viz_zoom = min(zoom_x, zoom_y, 2.0)  # Cap at 2x zoom

        # Calculate pan to center the components
        # Center of visualization pane in screen coordinates
        viz_center_x = self.viz_width / 2
        viz_center_y = self.height / 2

        # Position of center in grid coordinates (without pan/zoom)
        self.viz_pan_x = viz_center_x - center_x * grid_size * self.viz_zoom
        self.viz_pan_y = viz_center_y - center_y * grid_size * self.viz_zoom

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.viz_width = self.width - self.editor_width

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check if clicking on divider
                    if self._is_on_divider(event.pos):
                        self.divider_dragging = True
                    # Check if clicking load button
                    elif self.load_button_rect.collidepoint(event.pos):
                        self._load_json()
                    # Check if clicking save button
                    elif self.save_button_rect.collidepoint(event.pos):
                        self._save_to_file()
                    # Check if clicking on scrollbar
                    elif self._handle_scrollbar_click(event.pos):
                        pass  # Handled by scrollbar
                    # Check if clicking in visualization area
                    elif event.pos[0] >= self.editor_width + self.divider_width:
                        self.viz_dragging = True
                        self.viz_drag_start = event.pos
                    else:
                        # Handle click in editor to position cursor
                        self._handle_editor_click(event.pos)
                        # Start selection on mouse down in editor
                        if event.pos[0] < self.editor_width:
                            self.editor_mouse_down = True
                            # Clear selection unless shift is held
                            if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                                self.selection_start = None
                                self.selection_end = None

                elif event.button == 4:  # Mouse wheel up
                    if event.pos[0] >= self.editor_width + self.divider_width:
                        # Zoom in on visualization
                        self._handle_viz_zoom(event.pos, 1.1)
                    else:
                        # Scroll editor
                        self.scroll_offset = max(0, self.scroll_offset - 1)

                elif event.button == 5:  # Mouse wheel down
                    if event.pos[0] >= self.editor_width + self.divider_width:
                        # Zoom out on visualization
                        self._handle_viz_zoom(event.pos, 0.9)
                    else:
                        # Scroll editor
                        max_scroll = max(0, len(self.json_lines) - 30)
                        self.scroll_offset = min(max_scroll, self.scroll_offset + 1)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    self.divider_dragging = False
                    self.viz_dragging = False
                    self.editor_mouse_down = False
                    self.scrollbar_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                # Update button hover states
                self.load_button_hovered = self.load_button_rect.collidepoint(event.pos)
                self.save_button_hovered = self.save_button_rect.collidepoint(event.pos)

                # Update cursor based on position
                if self._is_on_divider(event.pos):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                # Handle divider dragging
                if self.divider_dragging:
                    new_width = max(200, min(self.width - 200, event.pos[0]))
                    self.editor_width = new_width
                    self.viz_width = self.width - self.editor_width
                    # Update button positions
                    self.load_button_rect.x = self.editor_width - 120
                    self.save_button_rect.x = self.editor_width - 240

                # Handle visualization panning
                elif self.viz_dragging:
                    dx = event.pos[0] - self.viz_drag_start[0]
                    dy = event.pos[1] - self.viz_drag_start[1]
                    self.viz_pan_x += dx
                    self.viz_pan_y += dy
                    self.viz_drag_start = event.pos

                # Handle scrollbar dragging
                elif self.scrollbar_dragging:
                    track_rect = self._get_scrollbar_track_rect()
                    total_lines = len(self.json_lines)
                    visible_lines = 35
                    max_scroll = total_lines - visible_lines

                    if max_scroll > 0 and track_rect is not None:
                        thumb_height = max(30, int(track_rect.height * visible_lines / total_lines))
                        drag_range = track_rect.height - thumb_height
                        dy = event.pos[1] - self.scrollbar_drag_start_y
                        scroll_delta = int((dy / drag_range) * max_scroll) if drag_range > 0 else 0
                        self.scroll_offset = self.scrollbar_drag_start_offset + scroll_delta
                        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))

                # Handle text selection dragging
                elif self.editor_mouse_down and event.pos[0] < self.editor_width:
                    old_cursor = (self.cursor_line, self.cursor_col)
                    self._handle_editor_click(event.pos)
                    if self.selection_start is None:
                        self.selection_start = old_cursor
                    self.selection_end = (self.cursor_line, self.cursor_col)

        return True

    def _is_on_divider(self, pos):
        """Check if position is on the divider."""
        divider_x = self.editor_width
        return divider_x - 5 <= pos[0] <= divider_x + self.divider_width + 5

    def _handle_viz_zoom(self, pos, zoom_factor):
        """Handle zooming the visualization around a point."""
        # Position in visualization coordinates
        viz_x = pos[0] - self.editor_width - self.divider_width
        viz_y = pos[1]

        # Store old zoom
        old_zoom = self.viz_zoom

        # Update zoom (clamp between 0.1x and 5x)
        self.viz_zoom = max(0.1, min(5.0, self.viz_zoom * zoom_factor))

        # Adjust pan to zoom toward mouse position
        zoom_change = self.viz_zoom / old_zoom
        self.viz_pan_x = viz_x - (viz_x - self.viz_pan_x) * zoom_change
        self.viz_pan_y = viz_y - (viz_y - self.viz_pan_y) * zoom_change

    def _get_selected_text(self):
        """Get the currently selected text."""
        if self.selection_start is None or self.selection_end is None:
            return ""

        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)

        if start == end:
            return ""

        if start[0] == end[0]:
            # Same line
            return self.json_lines[start[0]][start[1]:end[1]]
        else:
            # Multiple lines
            lines = []
            lines.append(self.json_lines[start[0]][start[1]:])
            for i in range(start[0] + 1, end[0]):
                lines.append(self.json_lines[i])
            lines.append(self.json_lines[end[0]][:end[1]])
            return '\n'.join(lines)

    def _delete_selection(self):
        """Delete the currently selected text."""
        if self.selection_start is None or self.selection_end is None:
            return False

        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)

        if start == end:
            return False

        if start[0] == end[0]:
            # Same line
            line = self.json_lines[start[0]]
            self.json_lines[start[0]] = line[:start[1]] + line[end[1]:]
        else:
            # Multiple lines
            before = self.json_lines[start[0]][:start[1]]
            after = self.json_lines[end[0]][end[1]:]
            self.json_lines[start[0]] = before + after
            # Remove lines in between
            for _ in range(start[0] + 1, end[0] + 1):
                self.json_lines.pop(start[0] + 1)

        self.cursor_line = start[0]
        self.cursor_col = start[1]
        self.selection_start = None
        self.selection_end = None
        self.json_text = '\n'.join(self.json_lines)
        return True

    def _handle_keydown(self, event):
        """Handle keyboard input for JSON editor."""
        # Ensure cursor is in valid range
        self.cursor_line = max(0, min(self.cursor_line, len(self.json_lines) - 1))
        self.cursor_col = max(0, min(self.cursor_col, len(self.json_lines[self.cursor_line])))

        # Check for Ctrl/Cmd modifiers
        ctrl_held = event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)
        shift_held = event.mod & pygame.KMOD_SHIFT

        # Handle Ctrl/Cmd + key combinations
        if ctrl_held:
            if event.key == pygame.K_c:
                # Copy
                selected_text = self._get_selected_text()
                if selected_text:
                    try:
                        pygame.scrap.put_text(selected_text)
                    except Exception:
                        pass  # Silently fail if clipboard not available
                return
            elif event.key == pygame.K_v:
                # Paste
                try:
                    if pygame.scrap.has_text():
                        # Delete selection if any
                        self._delete_selection()
                        # Get clipboard text
                        clipboard_text = pygame.scrap.get_text()
                        if clipboard_text:
                            # Normalize line endings (remove Windows carriage returns)
                            clipboard_text = clipboard_text.replace('\r', '')
                            # Insert at cursor
                            clipboard_lines = clipboard_text.split('\n')
                            if len(clipboard_lines) == 1:
                                # Single line paste
                                line = self.json_lines[self.cursor_line]
                                self.json_lines[self.cursor_line] = line[:self.cursor_col] + clipboard_text + line[self.cursor_col:]
                                self.cursor_col += len(clipboard_text)
                            else:
                                # Multi-line paste
                                line = self.json_lines[self.cursor_line]
                                before = line[:self.cursor_col]
                                after = line[self.cursor_col:]
                                self.json_lines[self.cursor_line] = before + clipboard_lines[0]
                                for i in range(1, len(clipboard_lines) - 1):
                                    self.json_lines.insert(self.cursor_line + i, clipboard_lines[i])
                                self.json_lines.insert(self.cursor_line + len(clipboard_lines) - 1,
                                                     clipboard_lines[-1] + after)
                                self.cursor_line += len(clipboard_lines) - 1
                                self.cursor_col = len(clipboard_lines[-1])
                            self.json_text = '\n'.join(self.json_lines)
                except Exception:
                    pass  # Silently fail if clipboard not available
                return
            elif event.key == pygame.K_x:
                # Cut
                selected_text = self._get_selected_text()
                if selected_text:
                    try:
                        pygame.scrap.put_text(selected_text)
                        self._delete_selection()
                    except Exception:
                        pass  # Silently fail if clipboard not available
                return
            elif event.key == pygame.K_a:
                # Select all
                self.selection_start = (0, 0)
                self.selection_end = (len(self.json_lines) - 1, len(self.json_lines[-1]))
                self.cursor_line = len(self.json_lines) - 1
                self.cursor_col = len(self.json_lines[-1])
                return

        if event.key == pygame.K_RETURN:
            # Delete selection first if any
            self._delete_selection()
            # Split line at cursor
            current_line = self.json_lines[self.cursor_line]
            before = current_line[:self.cursor_col]
            after = current_line[self.cursor_col:]
            self.json_lines[self.cursor_line] = before
            self.json_lines.insert(self.cursor_line + 1, after)
            self.cursor_line += 1
            self.cursor_col = 0
            self.json_text = '\n'.join(self.json_lines)

        elif event.key == pygame.K_BACKSPACE:
            # Delete selection if any, otherwise delete char before cursor
            if not self._delete_selection():
                if self.cursor_col > 0:
                    # Delete character before cursor
                    line = self.json_lines[self.cursor_line]
                    self.json_lines[self.cursor_line] = line[:self.cursor_col - 1] + line[self.cursor_col:]
                    self.cursor_col -= 1
                elif self.cursor_line > 0:
                    # Merge with previous line
                    prev_line = self.json_lines[self.cursor_line - 1]
                    current_line = self.json_lines[self.cursor_line]
                    self.cursor_col = len(prev_line)
                    self.json_lines[self.cursor_line - 1] = prev_line + current_line
                    self.json_lines.pop(self.cursor_line)
                    self.cursor_line -= 1
                self.json_text = '\n'.join(self.json_lines)

        elif event.key == pygame.K_DELETE:
            # Delete selection if any, otherwise delete char at cursor
            if not self._delete_selection():
                line = self.json_lines[self.cursor_line]
                if self.cursor_col < len(line):
                    # Delete character at cursor
                    self.json_lines[self.cursor_line] = line[:self.cursor_col] + line[self.cursor_col + 1:]
                elif self.cursor_line < len(self.json_lines) - 1:
                    # Merge with next line
                    next_line = self.json_lines[self.cursor_line + 1]
                    self.json_lines[self.cursor_line] = line + next_line
                    self.json_lines.pop(self.cursor_line + 1)
                self.json_text = '\n'.join(self.json_lines)

        elif event.key == pygame.K_LEFT:
            if shift_held:
                # Start selection if not already selecting
                if self.selection_start is None:
                    self.selection_start = (self.cursor_line, self.cursor_col)
            else:
                # Clear selection
                self.selection_start = None
                self.selection_end = None

            if self.cursor_col > 0:
                self.cursor_col -= 1
            elif self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = len(self.json_lines[self.cursor_line])

            if shift_held:
                self.selection_end = (self.cursor_line, self.cursor_col)

        elif event.key == pygame.K_RIGHT:
            if shift_held:
                # Start selection if not already selecting
                if self.selection_start is None:
                    self.selection_start = (self.cursor_line, self.cursor_col)
            else:
                # Clear selection
                self.selection_start = None
                self.selection_end = None

            if self.cursor_col < len(self.json_lines[self.cursor_line]):
                self.cursor_col += 1
            elif self.cursor_line < len(self.json_lines) - 1:
                self.cursor_line += 1
                self.cursor_col = 0

            if shift_held:
                self.selection_end = (self.cursor_line, self.cursor_col)

        elif event.key == pygame.K_UP:
            if shift_held:
                # Start selection if not already selecting
                if self.selection_start is None:
                    self.selection_start = (self.cursor_line, self.cursor_col)
            else:
                # Clear selection
                self.selection_start = None
                self.selection_end = None

            if self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_col = min(self.cursor_col, len(self.json_lines[self.cursor_line]))

            if shift_held:
                self.selection_end = (self.cursor_line, self.cursor_col)

        elif event.key == pygame.K_DOWN:
            if shift_held:
                # Start selection if not already selecting
                if self.selection_start is None:
                    self.selection_start = (self.cursor_line, self.cursor_col)
            else:
                # Clear selection
                self.selection_start = None
                self.selection_end = None

            if self.cursor_line < len(self.json_lines) - 1:
                self.cursor_line += 1
                self.cursor_col = min(self.cursor_col, len(self.json_lines[self.cursor_line]))

            if shift_held:
                self.selection_end = (self.cursor_line, self.cursor_col)

        elif event.key == pygame.K_HOME:
            self.cursor_col = 0

        elif event.key == pygame.K_END:
            self.cursor_col = len(self.json_lines[self.cursor_line])

        elif event.key == pygame.K_TAB:
            # Delete selection first if any
            self._delete_selection()
            # Insert 2 spaces
            line = self.json_lines[self.cursor_line]
            self.json_lines[self.cursor_line] = line[:self.cursor_col] + "  " + line[self.cursor_col:]
            self.cursor_col += 2
            self.json_text = '\n'.join(self.json_lines)

        elif event.unicode and event.unicode.isprintable():
            # Delete selection first if any
            self._delete_selection()
            # Insert character at cursor
            line = self.json_lines[self.cursor_line]
            self.json_lines[self.cursor_line] = line[:self.cursor_col] + event.unicode + line[self.cursor_col:]
            self.cursor_col += 1
            self.json_text = '\n'.join(self.json_lines)

    def _handle_editor_click(self, pos):
        """Handle mouse click in editor to position cursor."""
        # Check if click is in editor area
        if pos[0] >= self.editor_width:
            return

        line_height = 22
        # Account for error message if present
        text_start_y = 90 if self.error_message else 60

        # Calculate clicked line
        clicked_line = (pos[1] - text_start_y) // line_height + self.scroll_offset
        clicked_line = max(0, min(clicked_line, len(self.json_lines) - 1))

        # Calculate clicked column using actual font metrics
        line_text_x = 50  # X position where line text starts
        if pos[0] >= line_text_x:
            line_text = self.json_lines[clicked_line]
            click_x = pos[0] - line_text_x

            # Find the character position by measuring text width
            clicked_col = 0
            for i in range(len(line_text) + 1):
                text_width = self.mono_font.size(line_text[:i])[0]
                if click_x < text_width:
                    # Check if click is closer to previous or current position
                    if i > 0:
                        prev_width = self.mono_font.size(line_text[:i-1])[0]
                        if click_x - prev_width < text_width - click_x:
                            clicked_col = i - 1
                        else:
                            clicked_col = i
                    else:
                        clicked_col = 0
                    break
            else:
                # Click is beyond the end of the line
                clicked_col = len(line_text)
        else:
            clicked_col = 0

        self.cursor_line = clicked_line
        self.cursor_col = clicked_col

    def _handle_scrollbar_click(self, pos) -> bool:
        """Handle click on scrollbar. Returns True if click was on scrollbar."""
        thumb_rect = self._get_scrollbar_rect()
        if thumb_rect is None:
            return False

        track_rect = self._get_scrollbar_track_rect()

        # Check if clicking on thumb
        if thumb_rect.collidepoint(pos):
            self.scrollbar_dragging = True
            self.scrollbar_drag_start_y = pos[1]
            self.scrollbar_drag_start_offset = self.scroll_offset
            return True

        # Check if clicking on track (jump to position)
        if track_rect.collidepoint(pos):
            total_lines = len(self.json_lines)
            visible_lines = 35
            max_scroll = total_lines - visible_lines

            # Calculate scroll position from click
            track_click_ratio = (pos[1] - track_rect.y) / track_rect.height
            self.scroll_offset = int(track_click_ratio * max_scroll)
            self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))
            return True

        return False

    def render(self):
        """Render the entire UI."""
        self.screen.fill(self.bg_color)

        # Render editor pane
        self._render_editor_pane()

        # Render divider
        self._render_divider()

        # Render visualization pane
        self._render_viz_pane()

        # Update display
        pygame.display.flip()

    def _render_divider(self):
        """Render the divider between editor and visualization."""
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self._is_on_divider(mouse_pos)

        divider_color = self.divider_hover_color if is_hovered else self.divider_color
        divider_rect = pygame.Rect(self.editor_width, 0, self.divider_width, self.height)
        pygame.draw.rect(self.screen, divider_color, divider_rect)

    def _render_editor_pane(self):
        """Render the JSON editor pane."""
        editor_surface = pygame.Surface((self.editor_width, self.height))
        editor_surface.fill(self.editor_bg)

        # Title
        title = self.font.render("JSON Definition", True, self.text_color)
        editor_surface.blit(title, (10, 15))

        # Save button
        save_button_color = self.button_hover_color if self.save_button_hovered else self.button_color
        pygame.draw.rect(editor_surface, save_button_color,
                        (self.save_button_rect.x, self.save_button_rect.y,
                         self.save_button_rect.width, self.save_button_rect.height),
                        border_radius=5)
        save_text = self.small_font.render("Save", True, (255, 255, 255))
        save_text_rect = save_text.get_rect(center=self.save_button_rect.center)
        editor_surface.blit(save_text, (save_text_rect.x, save_text_rect.y))

        # Load button
        load_button_color = self.button_hover_color if self.load_button_hovered else self.button_color
        pygame.draw.rect(editor_surface, load_button_color,
                        (self.load_button_rect.x, self.load_button_rect.y,
                         self.load_button_rect.width, self.load_button_rect.height),
                        border_radius=5)
        load_text = self.small_font.render("Load/Reload", True, (255, 255, 255))
        load_text_rect = load_text.get_rect(center=self.load_button_rect.center)
        editor_surface.blit(load_text, (load_text_rect.x, load_text_rect.y))

        # Error message
        if self.error_message:
            error_y = 60
            error_text = self.small_font.render(f"Error: {self.error_message[:60]}", True, (255, 100, 100))
            editor_surface.blit(error_text, (10, error_y))
            text_start_y = 90
        else:
            text_start_y = 60

        # JSON text
        y = text_start_y
        line_height = 22
        visible_lines = self.json_lines[self.scroll_offset:self.scroll_offset + 35]

        for i, line in enumerate(visible_lines):
            current_line_num = self.scroll_offset + i

            # Line number
            line_num = self.small_font.render(f"{current_line_num + 1:3d}", True, (100, 100, 100))
            editor_surface.blit(line_num, (10, y))

            # Draw selection background if this line is selected
            if self.selection_start is not None and self.selection_end is not None:
                start = min(self.selection_start, self.selection_end)
                end = max(self.selection_start, self.selection_end)

                if start[0] <= current_line_num <= end[0]:
                    # This line has selection
                    sel_start_col = start[1] if current_line_num == start[0] else 0
                    sel_end_col = end[1] if current_line_num == end[0] else len(line)

                    if sel_start_col < sel_end_col:
                        # Calculate selection rectangle
                        start_text = line[:sel_start_col]
                        sel_text = line[sel_start_col:sel_end_col]
                        sel_x = 50 + self.mono_font.size(start_text)[0]
                        sel_width = self.mono_font.size(sel_text)[0]

                        # Draw selection background
                        sel_rect = pygame.Rect(sel_x, y, sel_width, line_height)
                        pygame.draw.rect(editor_surface, (70, 100, 150), sel_rect)

            # Line text
            line_text = self.mono_font.render(line[:80], True, self.text_color)
            editor_surface.blit(line_text, (50, y))

            # Draw cursor if it's on this line
            if self.cursor_line == current_line_num:
                # Blink cursor
                if int(self.time * 2) % 2 == 0:  # Blink twice per second
                    # Calculate cursor position
                    cursor_text = line[:self.cursor_col]
                    cursor_x = 50 + self.mono_font.size(cursor_text)[0]
                    pygame.draw.line(editor_surface, (255, 255, 255),
                                   (cursor_x, y), (cursor_x, y + line_height - 2), 2)

            y += line_height

        # Scrollbar
        self._render_scrollbar(editor_surface, text_start_y, line_height)

        # Current file info
        file_y = self.height - 150
        if self.current_file:
            file_info = f"File: {self.current_file.name}"
        else:
            file_info = "File: system.json (will be created on save)"
        file_text = self.small_font.render(file_info, True, (180, 180, 100))
        editor_surface.blit(file_text, (10, file_y))

        # Instructions
        inst_y = self.height - 125
        instructions = [
            "Click/drag to select, Shift+arrows to extend selection",
            "Ctrl/Cmd+C/V/X/A for copy/paste/cut/select all",
            "Arrow keys to navigate, mouse wheel to scroll",
            "Click 'Load/Reload' to update visualization"
        ]
        for i, inst in enumerate(instructions):
            inst_text = self.small_font.render(inst, True, (150, 150, 150))
            editor_surface.blit(inst_text, (10, inst_y + i * 25))

        self.screen.blit(editor_surface, (0, 0))

    def _render_scrollbar(self, surface, text_start_y: int, line_height: int):
        """Render the vertical scrollbar for the editor."""
        total_lines = len(self.json_lines)
        visible_lines = 35

        if total_lines <= visible_lines:
            return  # No scrollbar needed

        # Scrollbar track area
        track_x = self.editor_width - self.scrollbar_width - 5
        track_y = text_start_y
        track_height = self.height - text_start_y - 160  # Leave space for file info

        # Draw track background
        track_color = (40, 40, 45)
        pygame.draw.rect(surface, track_color,
                        (track_x, track_y, self.scrollbar_width, track_height),
                        border_radius=4)

        # Calculate thumb size and position
        thumb_height = max(30, int(track_height * visible_lines / total_lines))
        max_scroll = total_lines - visible_lines
        scroll_ratio = self.scroll_offset / max_scroll if max_scroll > 0 else 0
        thumb_y = track_y + int((track_height - thumb_height) * scroll_ratio)

        # Draw thumb
        thumb_color = (100, 100, 110) if not self.scrollbar_dragging else (130, 130, 140)
        pygame.draw.rect(surface, thumb_color,
                        (track_x, thumb_y, self.scrollbar_width, thumb_height),
                        border_radius=4)

    def _get_scrollbar_rect(self):
        """Get the scrollbar thumb rectangle for hit testing."""
        text_start_y = 90 if self.error_message else 60
        total_lines = len(self.json_lines)
        visible_lines = 35

        if total_lines <= visible_lines:
            return None

        track_x = self.editor_width - self.scrollbar_width - 5
        track_y = text_start_y
        track_height = self.height - text_start_y - 160

        thumb_height = max(30, int(track_height * visible_lines / total_lines))
        max_scroll = total_lines - visible_lines
        scroll_ratio = self.scroll_offset / max_scroll if max_scroll > 0 else 0
        thumb_y = track_y + int((track_height - thumb_height) * scroll_ratio)

        return pygame.Rect(track_x, thumb_y, self.scrollbar_width, thumb_height)

    def _get_scrollbar_track_rect(self):
        """Get the scrollbar track rectangle."""
        text_start_y = 90 if self.error_message else 60
        track_x = self.editor_width - self.scrollbar_width - 5
        track_y = text_start_y
        track_height = self.height - text_start_y - 160
        return pygame.Rect(track_x, track_y, self.scrollbar_width, track_height)

    def _render_viz_pane(self):
        """Render the visualization pane."""
        viz_surface = pygame.Surface((self.viz_width, self.height))
        viz_surface.fill(self.viz_bg)

        # Apply pan and zoom to render offset
        render_offset = (self.viz_pan_x, self.viz_pan_y)

        # Render grid with zoom (behind everything else)
        self._render_grid_with_zoom(viz_surface, render_offset)

        # Title (rendered after grid so it appears on top)
        title = self.font.render("P&ID Visualization", True, self.text_color)
        viz_surface.blit(title, (10, 15))

        # Render components with zoom
        for component in self.components:
            original_values = component.apply_animation(self.time)
            component.render(viz_surface, self.grid.cell_size * self.viz_zoom, render_offset, self.time)
            component.restore_properties(original_values)

        # Component count and zoom info
        count_text = self.small_font.render(
            f"Components: {len(self.components)} | Zoom: {self.viz_zoom:.2f}x",
            True,
            (150, 150, 150)
        )
        viz_surface.blit(count_text, (10, self.height - 30))

        # Instructions
        inst_text = self.small_font.render(
            "Drag to pan, scroll to zoom",
            True,
            (120, 120, 120)
        )
        viz_surface.blit(inst_text, (10, self.height - 55))

        self.screen.blit(viz_surface, (self.editor_width + self.divider_width, 0))

    def _render_grid_with_zoom(self, surface, offset):
        """Render grid with zoom applied."""
        if not self.grid.show_grid:
            return

        width, height = surface.get_size()
        cell_size = self.grid.cell_size * self.viz_zoom

        # Faint color for grid numbers
        number_color = (60, 60, 65)

        # Calculate the grid coordinate of the first visible line
        first_grid_x = -int(offset[0] // cell_size)
        first_grid_y = -int(offset[1] // cell_size)

        # Draw vertical lines with numbers
        start_x = int(offset[0] % cell_size)
        grid_x = first_grid_x
        for x in range(start_x, width, int(cell_size)):
            pygame.draw.line(surface, self.grid.grid_color, (x, 0), (x, height), 1)
            # Draw grid number at top
            if cell_size >= 20:  # Only show numbers if cells are large enough
                num_text = self.small_font.render(str(grid_x), True, number_color)
                surface.blit(num_text, (x + 2, 2))
            grid_x += 1

        # Draw horizontal lines with numbers
        start_y = int(offset[1] % cell_size)
        grid_y = first_grid_y
        for y in range(start_y, height, int(cell_size)):
            pygame.draw.line(surface, self.grid.grid_color, (0, y), (width, y), 1)
            # Draw grid number at left
            if cell_size >= 20:  # Only show numbers if cells are large enough
                num_text = self.small_font.render(str(grid_y), True, number_color)
                surface.blit(num_text, (2, y + 2))
            grid_y += 1

    def run(self):
        """Main application loop."""
        running = True
        while running:
            # Handle events
            running = self.handle_events()

            # Update animation time
            dt = self.clock.tick(60) / 1000.0  # 60 FPS
            self.time += dt

            # Render
            self.render()

        pygame.quit()
        sys.exit()


def main():
    """Entry point for the application."""
    app = ProcessSketcherApp()
    app.run()


if __name__ == "__main__":
    main()

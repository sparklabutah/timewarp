"""
Trace Parser for Playwright trace.zip files.
Extracts actions, screenshots, and HTML snapshots from traces.
"""
import json
import zipfile
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TraceAction:
    """Represents a single action in the trace."""
    action_type: str  # click, type, navigate, etc.
    timestamp: float
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    screenshot_path: Optional[str] = None
    html_snapshot: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TraceParser:
    """Parser for Playwright trace files."""
    
    def __init__(self, trace_zip_path: str):
        """
        Initialize parser with path to trace.zip file.
        
        Args:
            trace_zip_path: Path to the trace.zip file
        """
        self.trace_zip_path = Path(trace_zip_path)
        self.temp_dir = None
        self.actions: List[TraceAction] = []
        self.snapshots: Dict[str, str] = {}
        self.snapshot_order: List[str] = []
        
    def __enter__(self):
        """Extract trace to temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(self.trace_zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def parse(self) -> List[TraceAction]:
        """
        Parse the trace and extract actions with their observations.
        
        Returns:
            List of TraceAction objects
        """
        trace_file = Path(self.temp_dir) / 'trace.trace'
        if not trace_file.exists():
            raise FileNotFoundError(f"trace.trace not found in {self.trace_zip_path}")
        
        # Parse trace file (NDJSON format)
        events = []
        with open(trace_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Extract HTML snapshots first
        self.snapshots = self._extract_snapshots(events)
        
        # Extract actions from events
        self.actions = self._extract_actions(events)
        
        # Build snapshot order from actions
        self._build_snapshot_order(events)
        
        return self.actions
    
    def _build_snapshot_order(self, events: List[Dict]):
        """Build ordered list of snapshots corresponding to actions.
        We use AFTER snapshots because they contain the actual page state after the action.
        Only include snapshots that actually exist in self.snapshots.
        """
        self.snapshot_order = []
        
        # Map call IDs to their after snapshots (only if they exist in snapshots)
        call_to_snapshot = {}
        for event in events:
            if event.get('type') == 'after':
                call_id = event.get('callId', '')
                after_snapshot = event.get('afterSnapshot', '')
                if call_id and after_snapshot and after_snapshot in self.snapshots:
                    call_to_snapshot[call_id] = after_snapshot
        
        # Get initial snapshot (before first action) - only if it exists
        initial_snapshot = None
        for event in events:
            if event.get('type') == 'before':
                before_snapshot = event.get('beforeSnapshot', '')
                if before_snapshot and before_snapshot in self.snapshots:
                    initial_snapshot = before_snapshot
                    break
        
        # Add initial snapshot (before any actions) if it exists
        if initial_snapshot:
            self.snapshot_order.append(initial_snapshot)
        
        # For each action (before event), get its corresponding after snapshot
        for event in events:
            if event.get('type') == 'before':
                call_id = event.get('callId', '')
                if call_id in call_to_snapshot:
                    # Use the AFTER snapshot (page state after action)
                    after_snap = call_to_snapshot[call_id]
                    if after_snap not in self.snapshot_order:
                        self.snapshot_order.append(after_snap)
        
        # Add final snapshot (last after snapshot) if we have actions
        if self.actions:
            for event in reversed(events):
                if event.get('type') == 'after':
                    after_snapshot = event.get('afterSnapshot', '')
                    if after_snapshot and after_snapshot in self.snapshots and after_snapshot not in self.snapshot_order:
                        self.snapshot_order.append(after_snapshot)
                        break
    
    def _extract_snapshots(self, events: List[Dict]) -> Dict[str, str]:
        """
        Extract HTML snapshots from frame-snapshot events.
        
        Args:
            events: List of trace event dictionaries
            
        Returns:
            Dictionary mapping snapshot names to HTML content
        """
        snapshots = {}
        
        for event in events:
            if event.get('type') == 'frame-snapshot':
                snapshot = event.get('snapshot', {})
                snapshot_name = snapshot.get('snapshotName', '')
                html_data = snapshot.get('html', [])
                
                if html_data and snapshot_name:
                    # Convert Playwright's HTML array format to HTML string
                    html_str = self._convert_playwright_html(html_data)
                    snapshots[snapshot_name] = html_str
        
        return snapshots
    
    def _convert_playwright_html(self, html_array) -> str:
        """
        Convert Playwright's HTML array format to HTML string.
        
        Args:
            html_array: Array format like ["HTML",{},["HEAD",{},["BASE",{"href":"..."}]],["BODY"]]
            
        Returns:
            HTML string
        """
        if not isinstance(html_array, list) or len(html_array) == 0:
            return ""
        
        # Get tag name (first element should be a string)
        tag = html_array[0] if len(html_array) > 0 else ""
        
        # Handle case where tag might be a list (nested structure)
        if isinstance(tag, list):
            # If first element is a list, recursively process it
            return self._convert_playwright_html(tag)
        
        if not isinstance(tag, str) or not tag:
            return ""
        
        # Get attributes (second element if it's a dict)
        attrs = {}
        children_start_idx = 1
        if len(html_array) > 1 and isinstance(html_array[1], dict):
            attrs = html_array[1]
            children_start_idx = 2
        elif len(html_array) > 1 and isinstance(html_array[1], list):
            # No attributes, first child is at index 1
            children_start_idx = 1
        
        children = html_array[children_start_idx:] if len(html_array) > children_start_idx else []
        
        # Build HTML string
        html_parts = [f"<{tag}"]
        
        # Add attributes
        for key, value in attrs.items():
            if value == '':
                # Boolean attribute (e.g., itemscope)
                html_parts.append(f' {key}')
            else:
                # Escape quotes in attribute values
                escaped_value = str(value).replace('"', '&quot;')
                html_parts.append(f' {key}="{escaped_value}"')
        
        html_parts.append(">")
        
        # Process children
        for child in children:
            if isinstance(child, list):
                html_parts.append(self._convert_playwright_html(child))
            elif isinstance(child, str):
                # Escape HTML special characters in text
                escaped_text = child.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(escaped_text)
        
        # End tag (skip for void elements)
        void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                        'link', 'meta', 'param', 'source', 'track', 'wbr'}
        if isinstance(tag, str) and tag.lower() not in void_elements:
            html_parts.append(f"</{tag}>")
        
        return "".join(html_parts)
    
    def _extract_actions(self, events: List[Dict]) -> List[TraceAction]:
        """
        Extract user actions from trace events.
        
        Args:
            events: List of trace event dictionaries
            
        Returns:
            List of TraceAction objects
        """
        actions = []
        
        for event in events:
            event_type = event.get('type', '')
            
            # Playwright trace uses "before" events to represent actions
            if event_type == 'before':
                method = event.get('method', '')
                params = event.get('params', {})
                
                # Map Playwright method types to semantic actions
                if method in ['click', 'dblclick']:
                    actions.append(TraceAction(
                        action_type='Click',
                        timestamp=event.get('startTime', 0),
                        selector=params.get('selector'),
                        metadata=event
                    ))
                    
                elif method in ['fill', 'type']:
                    actions.append(TraceAction(
                        action_type='Type',
                        timestamp=event.get('startTime', 0),
                        selector=params.get('selector'),
                        value=params.get('value', '') or params.get('text', ''),
                        metadata=event
                    ))
                    
                elif method in ['goto', 'navigate']:
                    actions.append(TraceAction(
                        action_type='Navigate',
                        timestamp=event.get('startTime', 0),
                        url=params.get('url', ''),
                        metadata=event
                    ))
                    
                elif method == 'selectOption':
                    actions.append(TraceAction(
                        action_type='Select',
                        timestamp=event.get('startTime', 0),
                        selector=params.get('selector'),
                        value=str(params.get('values', '')),
                        metadata=event
                    ))
                    
                elif method == 'press':
                    actions.append(TraceAction(
                        action_type='Press',
                        timestamp=event.get('startTime', 0),
                        selector=params.get('selector'),
                        value=params.get('key', ''),
                        metadata=event
                    ))
        
        return actions
    
    def get_screenshot(self, action_index: int) -> Optional[bytes]:
        """
        Get screenshot for a specific action.
        
        Args:
            action_index: Index of the action
            
        Returns:
            Screenshot bytes or None
        """
        resources_dir = Path(self.temp_dir) / 'resources'
        if not resources_dir.exists():
            return None
        
        # Find screenshot files (usually named with SHA hash)
        screenshots = list(resources_dir.glob('*.jpeg')) + list(resources_dir.glob('*.png'))
        
        if action_index < len(screenshots):
            with open(screenshots[action_index], 'rb') as f:
                return f.read()
        
        return None
    
    def get_html_snapshot(self, action_index: int) -> Optional[str]:
        """
        Get HTML snapshot for a specific action.
        
        Args:
            action_index: Index of the action (or len(actions) for final snapshot)
            
        Returns:
            HTML string or None
        """
        if action_index < len(self.snapshot_order):
            snapshot_name = self.snapshot_order[action_index]
            return self.snapshots.get(snapshot_name)
        
        # Fallback: return last available snapshot
        if self.snapshots:
            return list(self.snapshots.values())[-1]
        
        return None
    
    def extract_all_resources(self, output_dir: str):
        """
        Extract all resources (screenshots, HTML) to output directory.
        
        Args:
            output_dir: Directory to save resources
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        resources_dir = Path(self.temp_dir) / 'resources'
        if resources_dir.exists():
            import shutil
            for resource_file in resources_dir.iterdir():
                shutil.copy2(resource_file, output_path / resource_file.name)


if __name__ == '__main__':
    # Test the parser
    trace_path = 'my_agent_task_trace.zip'
    
    with TraceParser(trace_path) as parser:
        actions = parser.parse()
        
        print(f"Found {len(actions)} actions:")
        for i, action in enumerate(actions):
            print(f"{i}. {action.action_type} - {action.selector or action.url or action.value}")


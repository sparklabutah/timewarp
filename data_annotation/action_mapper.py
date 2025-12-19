"""
Action Mapper for converting Playwright actions to semantic high-level actions.
Converts actions to format: do(action="Click", element="1")
"""
from typing import List, Dict, Any
from trace_parser import TraceAction


class ActionMapper:
    """Maps low-level Playwright actions to high-level semantic actions."""
    
    def __init__(self):
        self.element_counter = 0
        self.selector_to_element_id = {}
        self.element_id_to_description = {}  # Store descriptions for each element
    
    def map_action(self, action: TraceAction) -> str:
        """
        Convert a TraceAction to semantic action string.
        
        Args:
            action: TraceAction object
            
        Returns:
            Semantic action string like 'do(action="Click", element="1")'
        """
        if action.action_type == 'Click':
            element_id = self._get_element_id(action.selector)
            return f'do(action="Click", element="{element_id}")'
        
        elif action.action_type == 'Type':
            element_id = self._get_element_id(action.selector)
            # Escape quotes in value
            safe_value = action.value.replace('"', '\\"') if action.value else ''
            return f'do(action="Type", element="{element_id}", value="{safe_value}")'
        
        elif action.action_type == 'Navigate':
            # For navigation, we don't use element ID
            safe_url = action.url.replace('"', '\\"') if action.url else ''
            return f'do(action="Navigate", url="{safe_url}")'
        
        elif action.action_type == 'Select':
            element_id = self._get_element_id(action.selector)
            safe_value = action.value.replace('"', '\\"') if action.value else ''
            return f'do(action="Select", element="{element_id}", value="{safe_value}")'
        
        elif action.action_type == 'Press':
            element_id = self._get_element_id(action.selector)
            safe_key = action.value.replace('"', '\\"') if action.value else ''
            return f'do(action="Press", element="{element_id}", key="{safe_key}")'
        
        else:
            # Unknown action type
            return f'do(action="{action.action_type}")'
    
    def _get_element_id(self, selector: str) -> str:
        """
        Get or create element ID for a selector.
        
        Args:
            selector: CSS selector or other selector string
            
        Returns:
            Element ID string
        """
        if not selector:
            self.element_counter += 1
            return str(self.element_counter)
        
        # Check if we've seen this selector before
        if selector in self.selector_to_element_id:
            return self.selector_to_element_id[selector]
        
        # Create new element ID
        self.element_counter += 1
        element_id = str(self.element_counter)
        self.selector_to_element_id[selector] = element_id
        
        # Extract and store description from selector
        description = self._extract_description_from_selector(selector)
        self.element_id_to_description[element_id] = description
        
        return element_id
    
    def _extract_description_from_selector(self, selector: str) -> str:
        """
        Extract human-readable description from Playwright selector.
        
        Examples:
            'internal:role=link[name="Forums"i]' -> 'the "Forums" link'
            'internal:label="Sort by: Hot"i' -> 'the "Sort by: Hot" label'
            'internal:role=button[name="Submit"i]' -> 'the "Submit" button'
        
        Args:
            selector: Playwright selector string
            
        Returns:
            Human-readable description
        """
        import re
        
        # Try to extract role and name from internal selectors
        # Pattern: internal:role=ROLE[name="NAME"i]
        role_name_match = re.search(r'internal:role=(\w+)\[name="([^"]+)"', selector)
        if role_name_match:
            role = role_name_match.group(1)
            name = role_name_match.group(2)
            return f'the "{name}" {role}'
        
        # Pattern: internal:label="LABEL"i
        label_match = re.search(r'internal:label="([^"]+)"', selector)
        if label_match:
            label = label_match.group(1)
            return f'the "{label}" element'
        
        # Pattern: internal:text="TEXT"i
        text_match = re.search(r'internal:text="([^"]+)"', selector)
        if text_match:
            text = text_match.group(1)
            return f'the element with text "{text}"'
        
        # Pattern: internal:attr=[ATTR=VALUE]
        attr_match = re.search(r'internal:attr=\[([^=]+)="([^"]+)"\]', selector)
        if attr_match:
            attr = attr_match.group(1)
            value = attr_match.group(2)
            return f'the element with {attr}="{value}"'
        
        # Fallback: try to extract any quoted string
        quoted_match = re.search(r'"([^"]+)"', selector)
        if quoted_match:
            text = quoted_match.group(1)
            return f'the "{text}" element'
        
        # Last resort: use the selector itself (truncated)
        if len(selector) > 50:
            return f'element with selector "{selector[:47]}..."'
        return f'element with selector "{selector}"'
    
    def get_element_description(self, element_id: str) -> str:
        """
        Get the description for a given element ID.
        
        Args:
            element_id: Element ID string
            
        Returns:
            Human-readable description
        """
        return self.element_id_to_description.get(element_id, f"element {element_id}")
    
    def map_actions(self, actions: List[TraceAction]) -> List[str]:
        """
        Map a list of actions to semantic action strings.
        
        Args:
            actions: List of TraceAction objects
            
        Returns:
            List of semantic action strings
        """
        return [self.map_action(action) for action in actions]
    
    def reset(self):
        """Reset element counter and selector mapping."""
        self.element_counter = 0
        self.selector_to_element_id = {}


def create_action_description(action: TraceAction, element_id: str) -> str:
    """
    Create a natural language description of the action.
    
    Args:
        action: TraceAction object
        element_id: Element ID string
        
    Returns:
        Natural language description
    """
    if action.action_type == 'Click':
        return f"Click on element {element_id}"
    
    elif action.action_type == 'Type':
        return f"Type '{action.value}' into element {element_id}"
    
    elif action.action_type == 'Navigate':
        return f"Navigate to {action.url}"
    
    elif action.action_type == 'Select':
        return f"Select '{action.value}' from element {element_id}"
    
    elif action.action_type == 'Press':
        return f"Press key '{action.value}' on element {element_id}"
    
    else:
        return f"Perform {action.action_type}"


if __name__ == '__main__':
    # Test the mapper
    from trace_parser import TraceParser
    
    trace_path = 'my_agent_task_trace.zip'
    
    with TraceParser(trace_path) as parser:
        actions = parser.parse()
        
        mapper = ActionMapper()
        semantic_actions = mapper.map_actions(actions)
        
        print(f"Mapped {len(semantic_actions)} actions:")
        for i, semantic_action in enumerate(semantic_actions):
            print(f"{i}. {semantic_action}")


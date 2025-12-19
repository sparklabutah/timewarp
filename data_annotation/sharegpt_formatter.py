"""
ShareGPT Formatter for converting trace data to ShareGPT training format.
Format matches the structure in data/web_policy_sft.json
"""
from typing import List, Dict, Any, Optional
from trace_parser import TraceAction


class ShareGPTFormatter:
    """Format trace data into ShareGPT conversation format."""
    
    def __init__(self, action_mapper=None):
        self.action_mapper = action_mapper
    
    def format_trajectory(
        self,
        task: str,
        actions: List[str],
        observations: List[str],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a complete trajectory into ShareGPT format.
        
        Args:
            task: Overall task description
            actions: List of action strings (e.g., 'do(action="Click", element="1")')
            observations: List of observation strings (HTML/AXTree)
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary in ShareGPT format
        """
        conversations = []
        
        # Build conversations for each round
        for i, (action, observation) in enumerate(zip(actions, observations)):
            # Get next observation (if available)
            next_obs = observations[i + 1] if i + 1 < len(observations) else observation
            
            # Determine reward and done
            is_last = (i == len(actions) - 1)
            reward = 1 if is_last else 0
            done = is_last
            trajectory_reward = 1 if is_last else 0
            
            # Human message with task and observation
            human_value = f"{task}\n\nRound {i}\n\n"
            human_value += f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            human_value += f"{task}\n\n"
            human_value += f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
            human_value += f"# Observation:\n{observation}\n\n"
            
            conversations.append({
                "from": "human",
                "value": human_value
            })
            
            # GPT response with action
            conversations.append({
                "from": "gpt",
                "value": action
            })
        
        # Build final structure
        result = {
            "conversations": conversations,
            "task": task,
            "observation": observations[0] if observations else "",
            "next_observation": observations[-1] if observations else "",
            "action": actions[-1] if actions else "",
            "reward": 1,  # Final trajectory gets reward 1
            "done": True,
            "trajectory_reward": 1
        }
        
        if system_prompt:
            result["system"] = system_prompt
        
        return result
    
    def format_single_step(
        self,
        task: str,
        round_num: int,
        action: str,
        observation: str,
        next_observation: str,
        is_final: bool = False
    ) -> Dict[str, Any]:
        """
        Format a single step in ShareGPT format.
        
        Args:
            task: Task description
            round_num: Round number
            action: Action string
            observation: Current observation
            next_observation: Next observation
            is_final: Whether this is the final step
            
        Returns:
            Dictionary with step data
        """
        reward = 1 if is_final else 0
        done = is_final
        trajectory_reward = 1 if is_final else 0
        
        return {
            "task": task,
            "round": round_num,
            "observation": observation,
            "next_observation": next_observation,
            "action": action,
            "reward": reward,
            "done": done,
            "trajectory_reward": trajectory_reward
        }
    
    def format_conversations(
        self,
        task: str,
        actions: List[str],
        observations: List[str]
    ) -> List[Dict[str, str]]:
        """
        Format actions and observations into conversation format matching data_sample.json.
        Alternating human (observation) and gpt (action) messages.
        
        Args:
            task: Task description
            actions: List of actions
            observations: List of observations (should be len(actions) + 1)
            
        Returns:
            List of conversation turns alternating between human and gpt
        """
        if len(observations) < len(actions) + 1:
            # Pad observations if needed
            observations = observations + [observations[-1]] * (len(actions) + 1 - len(observations))
        
        conversations = []
        
        # Round 0: Task instruction + initial observation
        human_value = f"Task Instruction: {task}\n\nRound 0\n\n"
        human_value += f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
        human_value += f"{task}\n\n"
        human_value += f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        
        # Add initial observation
        if observations and len(observations) > 0:
            initial_obs = observations[0]
            if initial_obs and initial_obs != "[No observation available]" and initial_obs != "** Simplified html **":
                human_value += f"{initial_obs}\n\n"
            else:
                human_value += f"** Simplified html **\n\n"
        
        conversations.append({
            "from": "human",
            "value": human_value
        })
        
        # First action
        if actions:
            action_with_desc = self._add_element_description(actions[0], 0)
            conversations.append({
                "from": "gpt",
                "value": action_with_desc
            })
        
        # Subsequent rounds: observation (human) then action (gpt)
        for i in range(1, len(actions)):
            # Human: observation after action i-1
            human_value = f"Round {i}\n\n"
            human_value += f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            
            obs_idx = i
            obs = observations[obs_idx] if obs_idx < len(observations) else (observations[-1] if observations else "")
            
            if obs and obs != "[No observation available]" and obs != "** Simplified html **":
                human_value += f"{obs}\n\n"
            else:
                human_value += f"** Simplified html **\n\n"
            
            human_value += f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
            
            conversations.append({
                "from": "human",
                "value": human_value
            })
            
            # GPT: action i
            action_with_desc = self._add_element_description(actions[i], i)
            conversations.append({
                "from": "gpt",
                "value": action_with_desc
            })
        
        # Final round: last observation
        if len(actions) > 0:
            final_round = len(actions)
            human_value = f"Round {final_round}\n\n"
            human_value += f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            
            final_obs_idx = len(actions)
            final_obs = observations[final_obs_idx] if final_obs_idx < len(observations) else (observations[-1] if observations else "")
            
            if final_obs and final_obs != "[No observation available]" and final_obs != "** Simplified html **":
                human_value += f"{final_obs}\n\n"
            else:
                human_value += f"** Simplified html **\n\n"
            
            human_value += f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
            
            conversations.append({
                "from": "human",
                "value": human_value
            })
            
            # Final GPT message with exit
            final_gpt = self._create_exit_message(task, actions)
            conversations.append({
                "from": "gpt",
                "value": final_gpt
            })
        
        return conversations
    
    def _add_element_description(self, action: str, round_num: int) -> str:
        """
        Add element description before action.
        Format: "# Element: description\ndo(action=...)"
        
        Args:
            action: Action string like 'do(action="Click", element="1")'
            round_num: Round number
            
        Returns:
            Action with element description
        """
        import re
        
        # Extract element ID and other info from action
        element_match = re.search(r'element="(\d+)"', action)
        element_id = element_match.group(1) if element_match else None
        
        # Extract value/argument if present
        value_match = re.search(r'(?:value|argument)="([^"]*)"', action)
        value = value_match.group(1) if value_match else None
        
        # Create description based on action type
        if 'Navigate' in action:
            url_match = re.search(r'url="([^"]*)"', action)
            url = url_match.group(1) if url_match else ""
            desc = f"# Element: navigation to {url}"
        elif element_id and self.action_mapper:
            # Get the rich description from the action mapper
            element_desc = self.action_mapper.get_element_description(element_id)
            desc = f"# Element: {element_desc}"
        elif 'Click' in action and element_id:
            desc = f"# Element: element {element_id} (clickable element)"
        elif 'Type' in action and element_id:
            if value:
                desc = f"# Element: element {element_id} (input field for '{value[:30]}...')"
            else:
                desc = f"# Element: element {element_id} (input field)"
        elif 'Select' in action and element_id:
            if value:
                desc = f"# Element: element {element_id} (dropdown, select '{value}')"
            else:
                desc = f"# Element: element {element_id} (dropdown)"
        elif 'Press' in action and element_id:
            key_match = re.search(r'key="([^"]*)"', action)
            key = key_match.group(1) if key_match else ""
            desc = f"# Element: element {element_id} (press key '{key}')"
        elif 'Scroll' in action:
            desc = f"# Element: scroll action"
        elif element_id:
            desc = f"# Element: element {element_id}"
        else:
            desc = f"# Element: action"
        
        return f"{desc}\n{action}"
    
    def _create_exit_message(self, task: str, actions: List[str]) -> str:
        """
        Create final exit message for GPT.
        
        Args:
            task: Task description
            actions: List of all actions
            
        Returns:
            Exit message string
        """
        # Create a summary message based on the task
        # For now, use a generic completion message
        return f'exit(message="Task completed successfully.")'
    
    def create_training_entry(
        self,
        task: str,
        actions: List[str],
        observations: List[str],
        system_prompt: Optional[str] = None,
        tools: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete training data entry matching data_sample.json format.
        
        Args:
            task: Task description
            actions: List of actions
            observations: List of observations (should be len(actions) + 1)
            system_prompt: Optional system prompt
            tools: Optional tool description
            
        Returns:
            Complete training entry
        """
        conversations = self.format_conversations(task, actions, observations)
        
        entry = {
            "conversations": conversations
        }
        
        if system_prompt:
            entry["system"] = system_prompt
        
        if tools:
            entry["tools"] = tools
        
        return entry
    
    def merge_trajectories(
        self,
        trajectories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge multiple trajectories into a single training dataset.
        
        Args:
            trajectories: List of trajectory dictionaries
            
        Returns:
            List of training entries (one per trajectory)
        """
        return trajectories


if __name__ == '__main__':
    # Test the formatter
    formatter = ShareGPTFormatter()
    
    task = "Search for a product on the website"
    actions = [
        'do(action="Click", element="1")',
        'do(action="Type", element="2", value="laptop")',
        'do(action="Click", element="3")'
    ]
    observations = [
        "<html><body><h1>Homepage</h1><input id='search' /></body></html>",
        "<html><body><h1>Search</h1><input id='search' value='laptop' /></body></html>",
        "<html><body><h1>Results</h1><div>Laptops found</div></body></html>",
    ]
    
    entry = formatter.create_training_entry(task, actions, observations)
    
    import json
    print(json.dumps(entry, indent=2)[:1000])


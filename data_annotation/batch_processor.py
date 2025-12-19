"""
Batch Processor for processing multiple trace files into training data.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from trace_parser import TraceParser
from action_mapper import ActionMapper
from observation_extractor import ObservationExtractor
from sharegpt_formatter import ShareGPTFormatter


class BatchProcessor:
    """Process multiple trace.zip files into training data."""
    
    def __init__(self, observation_mode: str = 'html'):
        """
        Initialize batch processor.
        
        Args:
            observation_mode: One of 'html', 'axtree', or 'both'
        """
        self.observation_mode = observation_mode
        self.observation_extractor = ObservationExtractor(observation_mode)
        self.action_mapper = ActionMapper()
        self.formatter = ShareGPTFormatter(action_mapper=self.action_mapper)
    
    def process_single_trace(
        self,
        trace_path: str,
        task_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single trace file.
        
        Args:
            trace_path: Path to trace.zip file
            task_description: Description of the task
            
        Returns:
            Training data entry or None if processing fails
        """
        try:
            with TraceParser(trace_path) as parser:
                # Parse trace
                actions = parser.parse()
                
                if not actions:
                    print(f"Warning: No actions found in {trace_path}")
                    return None
                
                # Map actions to semantic format
                self.action_mapper.reset()
                semantic_actions = self.action_mapper.map_actions(actions)
                
                # Extract observations
                # observations[0] is initial state (before first action) - NOW SHOWN in Round 0
                # observations[1..len(actions)] are after each action
                observations = []
                for i in range(len(actions) + 1):  # +1 for final observation
                    html_snapshot = parser.get_html_snapshot(i)
                    if html_snapshot:
                        # Extract full HTML for ALL observations (including initial)
                        obs = self.observation_extractor.extract(html_snapshot)
                        observations.append(obs)
                    else:
                        # If no HTML
                        observations.append("[No observation available]")
                
                # Ensure we have at least as many observations as actions + 1
                while len(observations) < len(semantic_actions) + 1:
                    if len(observations) <= len(semantic_actions):
                        observations.append("** Simplified html **")
                    else:
                        observations.append(observations[-1] if observations else "[No observation]")
                
                # Format into training entry
                entry = self.formatter.create_training_entry(
                    task=task_description,
                    actions=semantic_actions,
                    observations=observations
                )
                
                return entry
                
        except Exception as e:
            print(f"Error processing {trace_path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def process_directory(
        self,
        input_dir: str,
        output_file: str,
        task_description: Optional[str] = None,
        interactive: bool = True
    ):
        """
        Process all trace.zip files in a directory.
        
        Args:
            input_dir: Directory containing trace.zip files
            output_file: Output JSON file path
            task_description: Common task description for all traces
            interactive: Whether to prompt for task descriptions
        """
        input_path = Path(input_dir)
        trace_files = list(input_path.glob('*.zip'))
        
        if not trace_files:
            print(f"No .zip files found in {input_dir}")
            return
        
        print(f"Found {len(trace_files)} trace files")
        
        training_data = []
        
        for i, trace_file in enumerate(trace_files):
            print(f"\n[{i+1}/{len(trace_files)}] Processing {trace_file.name}...")
            
            # Get task description
            if interactive and not task_description:
                task = input(f"Enter task description for {trace_file.name}: ").strip()
                if not task:
                    task = f"Task {i+1}"
            else:
                task = task_description or f"Task {i+1}"
            
            # Process trace
            entry = self.process_single_trace(str(trace_file), task)
            
            if entry:
                training_data.append(entry)
                print(f"✓ Successfully processed (found {len(entry.get('conversations', []))} conversation turns)")
            else:
                print(f"✗ Failed to process")
        
        # Save to file
        if training_data:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Saved {len(training_data)} trajectories to {output_file}")
        else:
            print("\n✗ No trajectories were successfully processed")
    
    def process_multiple_traces(
        self,
        trace_paths: List[str],
        task_descriptions: List[str],
        output_file: str
    ):
        """
        Process multiple specific trace files.
        
        Args:
            trace_paths: List of paths to trace.zip files
            task_descriptions: List of task descriptions (one per trace)
            output_file: Output JSON file path
        """
        if len(trace_paths) != len(task_descriptions):
            raise ValueError("Number of trace paths must match number of task descriptions")
        
        training_data = []
        
        for trace_path, task in zip(trace_paths, task_descriptions):
            print(f"Processing {Path(trace_path).name}...")
            
            entry = self.process_single_trace(trace_path, task)
            
            if entry:
                training_data.append(entry)
                print(f"✓ Successfully processed")
            else:
                print(f"✗ Failed to process")
        
        # Save to file
        if training_data:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Saved {len(training_data)} trajectories to {output_file}")
        else:
            print("\n✗ No trajectories were successfully processed")


if __name__ == '__main__':
    # Test the batch processor
    processor = BatchProcessor(observation_mode='html')
    
    # Process single trace
    entry = processor.process_single_trace(
        'my_agent_task_trace.zip',
        'Test task: Navigate and interact with webpage'
    )
    
    if entry:
        print(json.dumps(entry, indent=2)[:1000])


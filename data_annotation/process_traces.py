#!/usr/bin/env python3
"""
Process Playwright trace files into ShareGPT format training data.

Usage:
    # Process single trace
    python process_traces.py --input my_trace.zip --task "Search for products" --output training_data.json
    
    # Process multiple traces from directory
    python process_traces.py --input-dir ./traces/ --output training_data.json
    
    # Generate all 3 versions (html, axtree, both)
    python process_traces.py --input-dir ./traces/ --generate-all
    
    # Non-interactive mode with common task description
    python process_traces.py --input-dir ./traces/ --task "Common task" --no-interactive
"""
import argparse
import sys
from pathlib import Path
from batch_processor import BatchProcessor


def main():
    parser = argparse.ArgumentParser(
        description='Process Playwright trace files into ShareGPT training data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input',
        type=str,
        help='Path to single trace.zip file'
    )
    input_group.add_argument(
        '--input-dir',
        type=str,
        help='Directory containing multiple trace.zip files'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (default: training_data_{mode}.json)'
    )
    
    # Observation mode
    parser.add_argument(
        '--observation-type',
        choices=['html', 'axtree', 'both'],
        default='html',
        help='Type of observation to extract (default: html)'
    )
    
    # Generate all modes
    parser.add_argument(
        '--generate-all',
        action='store_true',
        help='Generate all three observation types (html, axtree, both)'
    )
    
    # Task description
    parser.add_argument(
        '--task',
        type=str,
        help='Task description (for single trace or common description for all)'
    )
    
    # Interactive mode
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Disable interactive prompts for task descriptions'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.input and not args.task:
        parser.error("--task is required when using --input")
    
    # Handle generate-all mode
    if args.generate_all:
        modes = ['html', 'axtree', 'both']
    else:
        modes = [args.observation_type]
    
    # Process for each mode
    for mode in modes:
        print(f"\n{'='*60}")
        print(f"Processing with observation mode: {mode}")
        print(f"{'='*60}")
        
        # Create processor
        processor = BatchProcessor(observation_mode=mode)
        
        # Determine output file
        if args.output:
            if args.generate_all:
                # Append mode to filename
                output_path = Path(args.output)
                output_file = str(output_path.parent / f"{output_path.stem}_{mode}{output_path.suffix}")
            else:
                output_file = args.output
        else:
            output_file = f"training_data_{mode}.json"
        
        # Process based on input type
        if args.input:
            # Single trace
            print(f"Processing single trace: {args.input}")
            entry = processor.process_single_trace(args.input, args.task)
            
            if entry:
                import json
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump([entry], f, indent=2, ensure_ascii=False)
                
                print(f"✓ Saved to {output_file}")
            else:
                print(f"✗ Failed to process {args.input}")
                sys.exit(1)
        
        else:
            # Directory of traces
            print(f"Processing directory: {args.input_dir}")
            processor.process_directory(
                input_dir=args.input_dir,
                output_file=output_file,
                task_description=args.task,
                interactive=not args.no_interactive
            )
    
    print(f"\n{'='*60}")
    print("Processing complete!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()


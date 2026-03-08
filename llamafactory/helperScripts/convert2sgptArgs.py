#!/usr/bin/env python3
"""
Convert training data from task folders to ShareGPT format.

This script reads training data from any folders containing training_data subfolders
with user prompts, system prompts, and agent actions and converts them to ShareGPT 
format suitable for fine-tuning.

The output format follows the ShareGPT structure with a separate "system" field 
and "conversations" array containing "human" and "gpt" messages.

Usage:
    python convert_training_to_sharegpt.py <input_folder> [--output OUTPUT_FILE]
    
Example:
    python convert_training_to_sharegpt.py results/ --output sharegpt_output.json
"""

import json
import os
import re
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any


def extract_step_number(filename: str) -> int:
    """Extract step number from filename like 'user_prompt_step_5.json'."""
    match = re.search(r'step_(\d+)', filename)
    if match:
        return int(match.group(1))
    return -1


def get_text_from_content(content: Any) -> str:
    """Extract text from content, handling both string and array formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Join all text items from the content array
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        return "".join(text_parts)
    return ""


def parse_content_sections(content: str) -> Dict[str, str]:
    """
    Parse a content string to extract different sections (think, plan, step, memory, action).
    Returns a dictionary with keys: think, plan, step, memory, action
    """
    sections = {
        "think": "",
        "plan": "",
        "step": "",
        "memory": "",
        "action": ""
    }
    
    # Pattern to match <tag>content</tag> (handles multiline content)
    # Note: think uses <think> tag in the content
    patterns = {
        "think": r'<think>\s*\n(.*?)\n\s*</think>',
        "plan": r'<plan>\s*\n(.*?)\n\s*</plan>',
        "step": r'<step>(.*?)</step>',
        "memory": r'<memory>\s*\n(.*?)\n\s*</memory>',
        "action": r'<action>\s*\n(.*?)\n\s*</action>'
    }
    
    for section_name, pattern in patterns.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            sections[section_name] = match.group(1).strip()
    
    return sections


def remove_perform_instructions(text: str) -> str:
    """Remove the 'Perform these instructions to complete the task:' section from user prompts."""
    # Pattern to match "Perform these instructions" section
    # This section typically starts with "Perform these instructions" and ends before "## Extra instructions:"
    pattern = r'\nPerform these instructions to complete the task:.*?(?=\n## Extra instructions:)'
    
    # Remove the matched section
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
    
    return cleaned_text


def replace_axtree_with_image_tag(text: str) -> str:
    """Replace the ## AXTree: section in the user prompt with an <image> tag."""
    pattern = r'## AXTree:.*?(?=\n## )'
    replaced = re.sub(pattern, '<image>', text, flags=re.DOTALL)
    return replaced


def find_image_in_dir(directory: Path, step_num: int) -> str:
    """
    Find a .png image for a given step number inside *directory*.
    Tries several naming conventions and falls back to a numeric match.
    Returns the absolute path as a string, or empty string if not found.
    """
    if not directory.exists():
        return ""

    candidates = [
        f"screenshot_step_{step_num}.png",
        f"step_{step_num}.png",
        f"som_step_{step_num}.png",
        f"screenshot_step_{step_num}_som.png",
        f"{step_num}.png",
    ]
    for name in candidates:
        path = directory / name
        if path.exists():
            return str(path)

    for f in sorted(directory.glob("*.png")):
        match = re.search(r'(\d+)', f.stem)
        if match and int(match.group(1)) == step_num:
            return str(f)

    return ""


def process_task_folder(task_folder: Path, include_think: bool = False, include_plan: bool = False, include_memory: bool = False, use_som: bool = False, use_img: bool = False) -> List[Dict[str, Any]]:
    """
    Process a single task folder and convert it to ShareGPT format.
    
    Args:
        task_folder: Path to the task folder
        include_think: If True, include <think> tags
        include_plan: If True, include <plan> and <step> tags
        include_memory: If True, include <memory> tags
        use_som: If True, replace AX Tree with SoM image from the SoM/ subfolder
        use_img: If True, replace AX Tree with screenshot from the task folder root
    
    Returns a list of conversation dicts in ShareGPT format, one per step.
    Each conversation contains a single human-gpt pair.
    """
    training_data_dir = task_folder / "training_data"
    
    if not training_data_dir.exists():
        print(f"Warning: No training_data folder found in {task_folder}")
        return []
    
    # Find all step files
    user_prompts = {}
    system_prompts = {}
    agent_outputs = {}
    
    for file in training_data_dir.glob("*.json"):
        filename = file.name
        step_num = extract_step_number(filename)
        
        if step_num == -1:
            continue
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if filename.startswith("user_prompt"):
                user_prompts[step_num] = data
            elif filename.startswith("system_prompt"):
                system_prompts[step_num] = data
            elif filename.startswith("agent_output"):
                agent_outputs[step_num] = data
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
    
    if not user_prompts:
        print(f"Warning: No user prompts found in {task_folder}")
        return []
    
    # Get all step numbers and sort them
    all_steps = sorted(set(list(user_prompts.keys()) + 
                          list(system_prompts.keys()) + 
                          list(agent_outputs.keys())))
    
    if not all_steps:
        return []
    
    # Get system prompt (use the first one, they're usually the same)
    system_text = ""
    if all_steps and all_steps[0] in system_prompts:
        system_data = system_prompts[all_steps[0]]
        system_content = system_data.get("content", "")
        if system_content:
            system_text = get_text_from_content(system_content)
    
    # Build separate conversation for each step
    result_conversations = []
    
    # Create one conversation per step with a single human-gpt pair
    for step_num in all_steps:
        step_conversations = []
        step_images = []
        
        # Add user prompt
        if step_num in user_prompts:
            user_data = user_prompts[step_num]
            user_content = user_data.get("content", "")
            user_text = get_text_from_content(user_content)
            # Remove "Perform these instructions" section
            user_text = remove_perform_instructions(user_text)

            if use_som or use_img:
                img_dir = (task_folder / "SoM") if use_som else task_folder
                img_path = find_image_in_dir(img_dir, step_num)
                if img_path:
                    user_text = replace_axtree_with_image_tag(user_text)
                    step_images.append(img_path)
                else:
                    label = "SoM" if use_som else "screenshot"
                    print(f"Warning: No {label} image found for step {step_num} in {img_dir}, skipping step")
                    continue

            if user_text:
                step_conversations.append({
                    "from": "human",
                    "value": user_text
                })
        
        # Add assistant response
        if step_num in agent_outputs:
            agent_data = agent_outputs[step_num]
            
            # Check for new format (has "content" field with all tags already formatted)
            if "content" in agent_data:
                assistant_content = get_text_from_content(agent_data.get("content", ""))
                if assistant_content:
                    # Parse the content to extract sections
                    sections = parse_content_sections(assistant_content)
                    
                    # Build assistant response based on flags
                    assistant_parts = []
                    
                    if include_think and sections["think"]:
                        assistant_parts.append(f"<think>\n{sections['think']}\n</think>")
                    
                    if include_plan:
                        if sections["plan"]:
                            assistant_parts.append(f"<plan>\n{sections['plan']}\n</plan>")
                        if sections["step"]:
                            assistant_parts.append(f"<step>{sections['step']}</step>")
                    
                    if include_memory and sections["memory"]:
                        assistant_parts.append(f"<memory>\n{sections['memory']}\n</memory>")
                    
                    # Action is always included
                    if sections["action"]:
                        assistant_parts.append(f"<action>\n{sections['action']}\n</action>")
                    
                    if assistant_parts:
                        step_conversations.append({
                            "from": "gpt",
                            "value": "\n\n".join(assistant_parts)
                        })
            # Fall back to old format (has individual fields like "think", "action", etc.)
            else:
                think = agent_data.get("think", "")
                plan = agent_data.get("plan", "")
                step = agent_data.get("step", "")
                memory = agent_data.get("memory", "")
                action = agent_data.get("action", "")
                
                # Build assistant response based on flags
                assistant_parts = []
                
                if include_think and think:
                    assistant_parts.append(f"<think>\n{think}\n</think>")
                
                if include_plan:
                    if plan:
                        assistant_parts.append(f"<plan>\n{plan}\n</plan>")
                    if step:
                        assistant_parts.append(f"<step>{step}</step>")
                
                if include_memory and memory:
                    assistant_parts.append(f"<memory>\n{memory}\n</memory>")
                
                # Action is always included
                if action:
                    assistant_parts.append(f"<action>\n{action}\n</action>")
                
                if assistant_parts:
                    step_conversations.append({
                        "from": "gpt",
                        "value": "\n\n".join(assistant_parts)
                    })
        
        # Only add conversation if it has both human and gpt messages
        if len(step_conversations) >= 2:
            entry = {
                "system": system_text,
                "conversations": step_conversations
            }
            if (use_som or use_img) and step_images:
                entry["images"] = step_images
            result_conversations.append(entry)
    
    return result_conversations


def convert_folder_to_sharegpt(
    input_folder: Path,
    output_file: Path,
    include_think: bool = False,
    include_plan: bool = False,
    include_memory: bool = False,
    p: float = 1.0,
    sampling: int = 1,
    use_som: bool = False,
    use_img: bool = False,
):
    """
    Convert all task folders in the input folder to a single ShareGPT JSON file.
    Processes all folders that contain training_data subfolders.
    
    Args:
        input_folder: Path to folder containing task folders
        output_file: Path to output JSON file
        include_think: If True, include <think> tags
        include_plan: If True, include <plan> and <step> tags
        include_memory: If True, include <memory> tags
        p: Probability of selecting a trajectory (task folder). Must be in [0, 1].
        sampling: Number of times to duplicate each selected trajectory (default: 1).
        use_som: If True, replace AX Tree with SoM images from each task's SoM/ folder.
        use_img: If True, replace AX Tree with screenshots from each task folder root.
    """
    input_path = Path(input_folder)
    
    if not input_path.exists():
        raise ValueError(f"Input folder does not exist: {input_folder}")
    
    # Find all task folders (directories that contain training_data subfolder)
    task_folders = []
    
    # Check if the folder itself contains training_data
    if (input_path / "training_data").exists():
        task_folders.append(input_path)
    
    # Look for subdirectories with training_data (recursively search one level deep)
    for item in input_path.iterdir():
        if item.is_dir():
            # Check if this directory itself has training_data
            if (item / "training_data").exists():
                task_folders.append(item)
            else:
                # Check subdirectories for training_data
                for subitem in item.iterdir():
                    if subitem.is_dir() and (subitem / "training_data").exists():
                        task_folders.append(subitem)
    
    if not task_folders:
        raise ValueError(f"No task folders with training_data found in {input_folder}")
    
    print(f"Found {len(task_folders)} task folders to process")
    
    # Clamp/validate probability
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"Probability p must be between 0 and 1, got {p}")
    
    # Validate sampling
    if sampling < 1:
        raise ValueError(f"Sampling must be >= 1, got {sampling}")

    # Process each task folder
    conversations = []
    successful = 0
    failed = 0
    skipped_by_prob = 0
    
    for task_folder in sorted(task_folders):
        try:
            task_conversations = process_task_folder(task_folder, include_think, include_plan, include_memory, use_som, use_img)
            if task_conversations:
                # First, duplicate the trajectory 'sampling' times
                # Then apply dropout p to each duplicate
                for _ in range(sampling):
                    # Apply dropout: randomly keep or skip each duplicate based on probability p
                    if random.random() <= p:
                        conversations.extend(task_conversations)
                    else:
                        skipped_by_prob += 1
                successful += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Error processing {task_folder}: {e}")
            failed += 1
    
    # Write to JSON file (not JSONL)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)
    
    print(f"\nConversion complete!")
    print(f"  Successfully processed: {successful} task folders")
    print(f"  Failed: {failed} task folders")
    print(f"  Skipped by probability p={p}: {skipped_by_prob} task folders")
    print(f"  Total conversations: {len(conversations)}")
    print(f"  Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert training data from task folders to ShareGPT format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "input_folder",
        type=str,
        help="Path to folder containing task folders with training_data subfolders"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="sharegpt_output.json",
        help="Output JSON file path (default: sharegpt_output.json)"
    )
    parser.add_argument(
        "--think",
        action="store_true",
        help="Include <think> tags in output"
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Include <plan> and <step> tags in output"
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Include <memory> tags in output"
    )
    parser.add_argument(
        "--p",
        type=float,
        default=1.0,
        help="Probability of selecting a trajectory (task folder) to include in the output (default: 1.0)"
    )
    parser.add_argument(
        "--sampling",
        type=int,
        default=1,
        help="Number of times to duplicate each selected trajectory (default: 1)"
    )
    img_group = parser.add_mutually_exclusive_group()
    img_group.add_argument(
        "--som",
        action="store_true",
        help="Use SoM (Set-of-Mark) screenshots instead of AX Tree in user prompts. "
             "Looks for .png files in each task's SoM/ subfolder."
    )
    img_group.add_argument(
        "--img",
        action="store_true",
        help="Use regular screenshots instead of AX Tree in user prompts. "
             "Looks for .png files directly in each task folder (e.g. screenshot_step_N.png)."
    )
    
    args = parser.parse_args()
    
    try:
        convert_folder_to_sharegpt(
            args.input_folder,
            args.output,
            args.think,
            args.plan,
            args.memory,
            args.p,
            args.sampling,
            args.som,
            args.img,
        )
    except Exception as e:
        print(f"Error: {e}", file=os.sys.stderr)
        os.sys.exit(1)


if __name__ == "__main__":
    main()
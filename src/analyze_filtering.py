#!/usr/bin/env python3
"""
Diagnostic script to analyze filtering in dataset preparation
"""

import json
import os
from typing import Dict, List, Optional

def analyze_log_file(filepath: str) -> Dict:
    """Analyze a single log file to understand filtering"""
    stats = {
        'total_entries': 0,
        'custom_generation_ex': 0,
        'tool_calls': 0,
        'valid_user_inputs': 0,
        'valid_conversations': 0,
        'individual_examples': 0,
        'final_examples': 0
    }
    
    log_entries = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                log_entries.append(entry)
                stats['total_entries'] += 1
                
                # Count event types
                if entry.get('name') == 'custom-generation-ex':
                    stats['custom_generation_ex'] += 1
                elif entry.get('name', '').startswith('tool call'):
                    stats['tool_calls'] += 1
                    
            except Exception as e:
                print(f"Error parsing line: {e}")
                continue
    
    # Test user input extraction
    for entry in log_entries:
        if entry.get('name') == 'custom-generation-ex':
            user_input = extract_user_input_from_log(entry)
            if user_input:
                stats['valid_user_inputs'] += 1
    
    # Test conversation processing
    conversations = process_conversation_flow(log_entries)
    stats['valid_conversations'] = len(conversations)
    
    # Test individual conversion
    for entry in log_entries:
        example = convert_log_to_qwen3_format(entry)
        if example and len(example["messages"]) >= 2:
            has_user = any(msg.get('role') == 'user' for msg in example['messages'])
            has_assistant = any(msg.get('role') == 'assistant' for msg in example['messages'])
            if has_user and has_assistant:
                stats['individual_examples'] += 1
    
    # Test conversation conversion
    for conversation in conversations:
        example = merge_conversation_to_qwen3_format(conversation)
        if example and len(example["messages"]) >= 3:
            has_user = any(msg.get('role') == 'user' for msg in example['messages'])
            has_assistant = any(msg.get('role') == 'assistant' for msg in example['messages'])
            if has_user and has_assistant:
                stats['final_examples'] += 1
    
    return stats

def extract_user_input_from_log(log_entry: Dict) -> Optional[str]:
    """Extract the original user input from log entry"""
    # Look for user input in custom-generation-ex events
    if log_entry.get('name') == 'custom-generation-ex' and 'input' in log_entry:
        input_data = log_entry['input']
        if isinstance(input_data, list) and len(input_data) > 1:
            # The second element usually contains the user's actual request
            user_text = input_data[1].get('text', '')
            if user_text and not user_text.startswith('#') and not user_text.startswith('<'):
                # Clean up the user input
                lines = user_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('<'):
                        cleaned_lines.append(line)
                if cleaned_lines:
                    return '\n'.join(cleaned_lines)
    
    # Fallback: look for user input in other fields
    if 'input' in log_entry:
        input_data = log_entry['input']
        if isinstance(input_data, dict) and 'result' in input_data:
            # Extract from result field if it contains user task
            result = input_data['result']
            if isinstance(result, str):
                # Look for user task patterns
                import re
                task_match = re.search(r'Target:\s*(http://[^\s]+).*?vulnerabilities:((?:.|\n)*?)(?:\n\n|$)', result)
                if task_match:
                    target = task_match.group(1)
                    vulns = task_match.group(2).strip()
                    return f"Target: {target}\nVulnerabilities to exploit:\n{vulns}\n\nPlease analyze the target for these vulnerabilities and find the flag."
    
    return None

def process_conversation_flow(log_entries: List[Dict]) -> List[List[Dict]]:
    """Process a sequence of log entries to reconstruct conversation flow"""
    conversations = []
    current_conversation = []
    
    for entry in log_entries:
        # Start new conversation on certain event types
        if entry.get('name') == 'custom-generation-ex':
            if current_conversation:
                conversations.append(current_conversation)
            current_conversation = [entry]
        else:
            if current_conversation:
                current_conversation.append(entry)
    
    # Add the last conversation
    if current_conversation:
        conversations.append(current_conversation)
    
    return conversations

def convert_log_to_qwen3_format(log_entry: Dict) -> Optional[Dict]:
    """Convert log entry to Qwen3 tool-calling format"""
    messages = []
    
    # Extract user input
    user_input = extract_user_input_from_log(log_entry)
    if not user_input:
        return None
    
    # Add system message for penetration testing context
    messages.append({
        "role": "system",
        "content": "# ADVANCED PENETRATION TESTING SPECIALIST\nYou are an elite security researcher specializing in CTF challenges and vulnerability exploitation. Your expertise includes:\n- Insecure Direct Object Reference (IDOR) identification and exploitation\n- Default credential detection and utilization\n- Web application reconnaissance and enumeration\n- Command execution through security testing tools\n- Flag discovery in Capture The Flag environments\n\nAlways use proper tool calls for all actions. Never simulate tool calls in plain text."
    })
    
    # Add user message
    messages.append({
        "role": "user", 
        "content": user_input
    })
    
    return {"messages": messages} if len(messages) >= 2 else None

def merge_conversation_to_qwen3_format(conversation: List[Dict]) -> Optional[Dict]:
    """Merge a conversation sequence into Qwen3 format"""
    messages = []
    
    # Add system message
    messages.append({
        "role": "system",
        "content": "# ADVANCED PENETRATION TESTING SPECIALIST\nYou are an elite security researcher specializing in CTF challenges and vulnerability exploitation. Your expertise includes:\n- Insecure Direct Object Reference (IDOR) identification and exploitation\n- Default credential detection and utilization\n- Web application reconnaissance and enumeration\n- Command execution through security testing tools\n- Flag discovery in Capture The Flag environments\n\nAlways use proper tool calls for all actions. Never simulate tool calls in plain text."
    })
    
    # Process conversation entries
    for entry in conversation:
        if entry.get('name') == 'custom-generation-ex':
            # Extract user input
            user_input = extract_user_input_from_log(entry)
            if user_input:
                messages.append({
                    "role": "user",
                    "content": user_input
                })
    
    return {"messages": messages} if len(messages) >= 3 else None

def main():
    input_dir = "./data/logs/passed"
    
    print("=== DATASET FILTERING ANALYSIS ===\n")
    
    total_stats = {
        'total_entries': 0,
        'custom_generation_ex': 0,
        'tool_calls': 0,
        'valid_user_inputs': 0,
        'valid_conversations': 0,
        'individual_examples': 0,
        'final_examples': 0
    }
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            filepath = os.path.join(input_dir, filename)
            print(f"Analyzing {filename}...")
            
            stats = analyze_log_file(filepath)
            
            # Print file stats
            print(f"  Total entries: {stats['total_entries']}")
            print(f"  custom-generation-ex events: {stats['custom_generation_ex']}")
            print(f"  tool call events: {stats['tool_calls']}")
            print(f"  Valid user inputs: {stats['valid_user_inputs']}")
            print(f"  Valid conversations: {stats['valid_conversations']}")
            print(f"  Individual examples: {stats['individual_examples']}")
            print(f"  Final examples: {stats['final_examples']}")
            print()
            
            # Accumulate totals
            for key in total_stats:
                total_stats[key] += stats[key]
    
    print("=== SUMMARY ===")
    print(f"Total raw entries: {total_stats['total_entries']}")
    print(f"Total custom-generation-ex events: {total_stats['custom_generation_ex']}")
    print(f"Total tool call events: {total_stats['tool_calls']}")
    print(f"Total valid user inputs: {total_stats['valid_user_inputs']}")
    print(f"Total valid conversations: {total_stats['valid_conversations']}")
    print(f"Total individual examples: {total_stats['individual_examples']}")
    print(f"Total final examples: {total_stats['final_examples']}")
    
    # Calculate conversion rates
    if total_stats['total_entries'] > 0:
        print(f"\n=== CONVERSION RATES ===")
        print(f"custom-generation-ex / total: {total_stats['custom_generation_ex'] / total_stats['total_entries']:.2%}")
        print(f"valid user inputs / custom-generation-ex: {total_stats['valid_user_inputs'] / total_stats['custom_generation_ex']:.2%}" if total_stats['custom_generation_ex'] > 0 else "valid user inputs / custom-generation-ex: N/A")
        print(f"final examples / total: {total_stats['final_examples'] / total_stats['total_entries']:.2%}")

if __name__ == "__main__":
    main() 
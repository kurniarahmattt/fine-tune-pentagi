#!/usr/bin/env python3
"""
Dataset validation script for Qwen3 tool-calling format
"""

import json
import sys
from typing import Dict, List


def validate_example(example: Dict) -> Dict:
    """Validate a single example"""
    issues = []
    
    if 'messages' not in example:
        issues.append("Missing 'messages' field")
        return {"valid": False, "issues": issues}
    
    messages = example['messages']
    if not isinstance(messages, list):
        issues.append("'messages' must be a list")
        return {"valid": False, "issues": issues}
    
    if len(messages) < 2:
        issues.append("Must have at least 2 messages")
        return {"valid": False, "issues": issues}
    
    # Check for required roles
    roles = [msg.get('role') for msg in messages]
    has_system = 'system' in roles
    has_user = 'user' in roles
    has_assistant = 'assistant' in roles
    
    if not has_user:
        issues.append("Missing user message")
    if not has_assistant:
        issues.append("Missing assistant message")
    
    # Check message structure
    for i, msg in enumerate(messages):
        if 'role' not in msg:
            issues.append(f"Message {i} missing 'role' field")
            continue
        
        role = msg['role']
        if role not in ['system', 'user', 'assistant', 'observation']:
            issues.append(f"Message {i} has invalid role: {role}")
        
        # Check assistant messages with tool calls
        if role == 'assistant':
            if 'content' not in msg and 'tool_calls' not in msg:
                issues.append(f"Assistant message {i} must have either 'content' or 'tool_calls'")
            
            if 'tool_calls' in msg:
                tool_calls = msg['tool_calls']
                if not isinstance(tool_calls, list):
                    issues.append(f"Message {i} tool_calls must be a list")
                else:
                    for j, tool_call in enumerate(tool_calls):
                        if not isinstance(tool_call, dict):
                            issues.append(f"Message {i} tool_call {j} must be a dict")
                        elif 'id' not in tool_call:
                            issues.append(f"Message {i} tool_call {j} missing 'id'")
                        elif 'function' not in tool_call:
                            issues.append(f"Message {i} tool_call {j} missing 'function'")
                        else:
                            func = tool_call['function']
                            if not isinstance(func, dict):
                                issues.append(f"Message {i} tool_call {j} function must be a dict")
                            elif 'name' not in func:
                                issues.append(f"Message {i} tool_call {j} function missing 'name'")
                            elif 'arguments' not in func:
                                issues.append(f"Message {i} tool_call {j} function missing 'arguments'")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "message_count": len(messages),
        "has_system": has_system,
        "has_user": has_user,
        "has_assistant": has_assistant,
        "has_observation": 'observation' in roles,
        "has_tool_calls": any('tool_calls' in msg for msg in messages if msg.get('role') == 'assistant')
    }


def analyze_dataset(filepath: str) -> Dict:
    """Analyze the entire dataset"""
    stats = {
        "total_examples": 0,
        "valid_examples": 0,
        "invalid_examples": 0,
        "avg_message_count": 0,
        "examples_with_system": 0,
        "examples_with_user": 0,
        "examples_with_assistant": 0,
        "examples_with_observation": 0,
        "examples_with_tool_calls": 0,
        "common_issues": {},
        "message_count_distribution": {}
    }
    
    total_messages = 0
    validation_results = []
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                example = json.loads(line.strip())
                stats["total_examples"] += 1
                
                result = validate_example(example)
                validation_results.append(result)
                
                if result["valid"]:
                    stats["valid_examples"] += 1
                    total_messages += result["message_count"]
                    
                    # Update statistics
                    if result["has_system"]:
                        stats["examples_with_system"] += 1
                    if result["has_user"]:
                        stats["examples_with_user"] += 1
                    if result["has_assistant"]:
                        stats["examples_with_assistant"] += 1
                    if result["has_observation"]:
                        stats["examples_with_observation"] += 1
                    if result["has_tool_calls"]:
                        stats["examples_with_tool_calls"] += 1
                    
                    # Message count distribution
                    msg_count = result["message_count"]
                    stats["message_count_distribution"][msg_count] = stats["message_count_distribution"].get(msg_count, 0) + 1
                else:
                    stats["invalid_examples"] += 1
                    for issue in result["issues"]:
                        stats["common_issues"][issue] = stats["common_issues"].get(issue, 0) + 1
                        
            except json.JSONDecodeError as e:
                stats["invalid_examples"] += 1
                stats["common_issues"]["JSON decode error"] = stats["common_issues"].get("JSON decode error", 0) + 1
                print(f"JSON decode error on line {line_num}: {e}")
    
    if stats["valid_examples"] > 0:
        stats["avg_message_count"] = total_messages / stats["valid_examples"]
    
    return stats


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_dataset.py <dataset_file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    print(f"Validating dataset: {filepath}")
    print("=" * 50)
    
    stats = analyze_dataset(filepath)
    
    print(f"Total examples: {stats['total_examples']}")
    print(f"Valid examples: {stats['valid_examples']}")
    print(f"Invalid examples: {stats['invalid_examples']}")
    print(f"Validation rate: {stats['valid_examples']/stats['total_examples']*100:.1f}%")
    print()
    
    print("Valid examples statistics:")
    print(f"  Average message count: {stats['avg_message_count']:.1f}")
    print(f"  Examples with system message: {stats['examples_with_system']}")
    print(f"  Examples with user message: {stats['examples_with_user']}")
    print(f"  Examples with assistant message: {stats['examples_with_assistant']}")
    print(f"  Examples with observation: {stats['examples_with_observation']}")
    print(f"  Examples with tool calls: {stats['examples_with_tool_calls']}")
    print()
    
    print("Message count distribution:")
    for count in sorted(stats["message_count_distribution"].keys()):
        print(f"  {count} messages: {stats['message_count_distribution'][count]} examples")
    print()
    
    if stats["common_issues"]:
        print("Common issues found:")
        for issue, count in sorted(stats["common_issues"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue}: {count} occurrences")
    
    if stats["invalid_examples"] == 0:
        print("✅ All examples are valid!")
    else:
        print(f"❌ Found {stats['invalid_examples']} invalid examples")


if __name__ == "__main__":
    main() 
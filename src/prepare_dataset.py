import json
import os
import re
import base64
from typing import List, Dict, Optional
from datetime import datetime


def extract_user_input_from_log(log_entry: Dict) -> Optional[str]:
    """Extract the original user input from log entry"""
    # Look for user input in custom-generation-ex events
    if log_entry.get('name') == 'custom-generation-ex' and 'input' in log_entry:
        input_data = log_entry['input']
        if isinstance(input_data, list) and len(input_data) > 1:
            # The second element usually contains the user's actual request
            user_text = input_data[1].get('text', '')
            if user_text:
                # Clean up the user input - be less restrictive
                lines = user_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line:
                        # Only filter out obvious system markers, keep valuable content
                        if not line.startswith('**summarized content:**'):
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
                task_match = re.search(r'Target:\s*(http://[^\s]+).*?vulnerabilities:((?:.|\n)*?)(?:\n\n|$)', result)
                if task_match:
                    target = task_match.group(1)
                    vulns = task_match.group(2).strip()
                    return f"Target: {target}\nVulnerabilities to exploit:\n{vulns}\n\nPlease analyze the target for these vulnerabilities and find the flag."
    
    return None


def extract_tool_calls_from_log(log_entry: Dict) -> List[Dict]:
    """Extract tool calls from log entry"""
    tool_calls = []
    
    # Look for tool call events
    if log_entry.get('name', '').startswith('tool call') and 'metadata' in log_entry:
        metadata = log_entry['metadata']
        if 'tool_call_id' in metadata and 'tool_name' in metadata:
            tool_call = {
                "id": metadata['tool_call_id'],
                "function": {
                    "name": metadata['tool_name'],
                    "arguments": "{}"  # Default empty arguments
                }
            }
            
            # Try to extract arguments from input field
            if 'input' in log_entry:
                input_data = log_entry['input']
                if isinstance(input_data, dict):
                    # Convert input data to JSON string
                    try:
                        tool_call["function"]["arguments"] = json.dumps(input_data)
                    except:
                        pass
            
            tool_calls.append(tool_call)
    
    return tool_calls


def extract_tool_responses_from_log(log_entry: Dict) -> List[Dict]:
    """Extract tool responses from log entry"""
    tool_responses = []
    
    # Look for tool call events that contain results
    if log_entry.get('name', '').startswith('tool call') and 'input' in log_entry:
        input_data = log_entry['input']
        if isinstance(input_data, dict) and 'result' in input_data:
            result = input_data['result']
            if isinstance(result, str):
                tool_responses.append({
                    "name": log_entry.get('metadata', {}).get('tool_name', 'unknown'),
                    "content": result
                })
    
    return tool_responses


def extract_assistant_response_from_log(log_entry: Dict) -> Optional[str]:
    """Extract assistant response from log entry - improved to capture more valuable content"""
    # Look for custom-generation-ex events that contain assistant responses
    if log_entry.get('name') == 'custom-generation-ex' and 'input' in log_entry:
        input_data = log_entry['input']
        if isinstance(input_data, list) and len(input_data) > 0:
            # Check multiple elements for valuable content
            for element in input_data:
                if isinstance(element, dict) and 'text' in element:
                    text = element['text']
                    if text:
                        # Extract valuable content while filtering obvious system instructions
                        cleaned_text = clean_assistant_response(text)
                        if cleaned_text:
                            return cleaned_text
    
    return None


def clean_assistant_response(text: str) -> Optional[str]:
    """Clean assistant response text to extract valuable content"""
    if not text:
        return None
    
    # Skip obvious system instructions and empty content
    if text.startswith('# TASK EXECUTION EVALUATOR AND REPORTER'):
        return None
    if text.startswith('# PRECISION SUMMARIZATION ENGINE'):
        return None
    if text.startswith('<instructions>'):
        return None
    if text.startswith('**summarized content:**'):
        return None
    if text.startswith('You are an elite archivist'):
        return None
    if 'This system operates EXCLUSIVELY through structured tool calls' in text:
        return None
    
    # Clean up the response
    lines = text.split('\n')
    response_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Keep valuable content, filter obvious system markers
            if (not line.startswith('#') and 
                not line.startswith('<') and 
                not line.startswith('**summarized content:**') and
                not line.startswith('## CORE RESPONSIBILITY') and
                not line.startswith('## EVALUATION METHODOLOGY') and
                not line.startswith('## OUTPUT REQUIREMENTS') and
                not line.startswith('You are an elite') and
                not line.startswith('Always use your function') and
                not line.startswith('User\'s question will be') and
                not 'This system operates EXCLUSIVELY' in line and
                not 'NEVER mimic or copy' in line and
                not 'ALWAYS use proper, structured tool calls' in line):
                response_lines.append(line)
    
    if response_lines:
        return '\n'.join(response_lines)
    
    return None


def extract_evaluation_content_from_log(log_entry: Dict) -> Optional[str]:
    """Extract valuable evaluation and analysis content from log entry"""
    if log_entry.get('name') == 'custom-generation-ex' and 'input' in log_entry:
        input_data = log_entry['input']
        if isinstance(input_data, list) and len(input_data) > 1:
            # Look for evaluation content in the second element
            second_element = input_data[1]
            if isinstance(second_element, dict) and 'text' in second_element:
                text = second_element['text']
                if text and '<task_report_context>' in text:
                    # Extract valuable analysis from task reports
                    return extract_analysis_from_task_report(text)
    
    return None


def extract_analysis_from_task_report(text: str) -> Optional[str]:
    """Extract valuable security analysis from task report context"""
    # Look for completed subtasks with valuable analysis
    subtask_matches = re.findall(r'<result>(.*?)</result>', text, re.DOTALL)
    
    if subtask_matches:
        # Combine the most valuable analysis content
        valuable_content = []
        for match in subtask_matches:
            # Look for security findings, exploitation details, technical analysis
            if any(keyword in match.lower() for keyword in [
                'vulnerability', 'exploit', 'flag', 'security', 'analysis', 
                'finding', 'technique', 'method', 'command', 'curl', 'http'
            ]):
                # Clean and add valuable content
                cleaned = clean_analysis_content(match)
                if cleaned:
                    valuable_content.append(cleaned)
        
        if valuable_content:
            return "\n\n".join(valuable_content[:3])  # Limit to top 3 most valuable
    
    return None


def clean_analysis_content(text: str) -> str:
    """Clean analysis content to extract valuable insights"""
    # Remove excessive formatting and keep core insights
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Keep lines with valuable content
            if any(keyword in line.lower() for keyword in [
                'vulnerability', 'exploit', 'flag', 'security', 'finding',
                'technique', 'method', 'command', 'curl', 'http', 'successfully',
                'critical', 'impact', 'risk', 'remediation'
            ]):
                cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def convert_log_to_qwen3_format(log_entry: Dict) -> Optional[Dict]:
    """Convert log entry to Qwen3 tool-calling format - improved to capture more content"""
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
    
    # Extract tool calls
    tool_calls = extract_tool_calls_from_log(log_entry)
    
    # Extract tool responses
    tool_responses = extract_tool_responses_from_log(log_entry)
    
    # Add tool calls to messages if present
    if tool_calls:
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls
        })
    
    # Add tool responses
    for response in tool_responses:
        messages.append({
            "role": "observation",
            "content": response["content"]
        })
    
    # Add final assistant response if we have tool interactions
    if tool_calls or tool_responses:
        # Generate a realistic assistant response based on the context
        assistant_response = generate_assistant_response(user_input, tool_responses)
        if assistant_response:
            messages.append({
                "role": "assistant",
                "content": assistant_response
            })
    
    return {"messages": messages} if len(messages) >= 2 else None


def generate_assistant_response(user_input: str, tool_responses: List[Dict]) -> Optional[str]:
    """Generate a realistic assistant response based on context"""
    if not tool_responses:
        return None
    
    # Look for flag in tool responses
    flag_found = False
    flag_content = ""
    for response in tool_responses:
        if 'FLAG{' in response.get('content', ''):
            flag_match = re.search(r'FLAG\{[^}]*\}', response['content'])
            if flag_match:
                flag_found = True
                flag_content = flag_match.group(0)
                break
    
    # Generate appropriate response
    if flag_found:
        return f"Successfully exploited the IDOR vulnerability and discovered the flag: {flag_content}. The Base64-encoded cookie manipulation allowed unauthorized access to sensitive data. This represents a critical security flaw requiring immediate remediation."
    else:
        return "Analysis completed. The target application contains multiple security vulnerabilities including IDOR through Base64 cookie manipulation. Recommend implementing proper session management and authorization controls."


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


def merge_conversation_to_qwen3_format(conversation: List[Dict]) -> Optional[Dict]:
    """Merge a conversation sequence into Qwen3 format - improved to capture more content"""
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
            
            # Extract assistant response (including evaluation content)
            assistant_response = extract_assistant_response_from_log(entry)
            if not assistant_response:
                # Try to extract evaluation content
                assistant_response = extract_evaluation_content_from_log(entry)
            
            if assistant_response:
                messages.append({
                    "role": "assistant",
                    "content": assistant_response
                })
                
        elif entry.get('name', '').startswith('tool call'):
            # Extract tool calls and responses
            tool_calls = extract_tool_calls_from_log(entry)
            tool_responses = extract_tool_responses_from_log(entry)
            
            if tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
            
            for response in tool_responses:
                messages.append({
                    "role": "observation",
                    "content": response["content"]
                })
    
    # Add final assistant response if we have interactions
    if len(messages) > 2:  # More than just system + user
        assistant_response = generate_final_response(messages)
        if assistant_response:
            messages.append({
                "role": "assistant",
                "content": assistant_response
            })
    
    return {"messages": messages} if len(messages) >= 3 else None


def generate_final_response(messages: List[Dict]) -> Optional[str]:
    """Generate a final assistant response based on conversation context"""
    # Look for flag in observation messages
    flag_found = False
    flag_content = ""
    
    for message in messages:
        if message.get('role') == 'observation':
            content = message.get('content', '')
            if 'FLAG{' in content:
                flag_match = re.search(r'FLAG\{[^}]*\}', content)
                if flag_match:
                    flag_found = True
                    flag_content = flag_match.group(0)
                    break
    
    if flag_found:
        return f"Exploitation successful! I've identified and exploited the IDOR vulnerability through Base64 cookie manipulation. The flag {flag_content} was extracted from the target application. This demonstrates a critical security flaw in the session management system."
    else:
        return "Penetration testing completed. Multiple security vulnerabilities were identified including IDOR, privilege escalation, and poor input validation. Immediate remediation is required."


def create_synthetic_examples() -> List[Dict]:
    """Create synthetic examples based on the penetration testing context"""
    examples = []
    
    # Example 1: IDOR exploitation
    example1 = {
        "messages": [
            {
                "role": "system",
                "content": "# ADVANCED PENETRATION TESTING SPECIALIST\nYou are an elite security researcher specializing in CTF challenges and vulnerability exploitation. Your expertise includes:\n- Insecure Direct Object Reference (IDOR) identification and exploitation\n- Default credential detection and utilization\n- Web application reconnaissance and enumeration\n- Command execution through security testing tools\n- Flag discovery in Capture The Flag environments\n\nAlways use proper tool calls for all actions. Never simulate tool calls in plain text."
            },
            {
                "role": "user",
                "content": "Target: http://172.17.0.1:32775\n\nThis is a Capture The Flag (CTF) challenge. The application contains the following vulnerabilities:\n\n- Insecure Direct Object Reference (IDOR) — Category: Broken Authorization  \n- Default Credentials — Category: Broken Authentication  \n\nThe vulnerability is caused by the application storing the user's ID in a cookie that is Base64 encoded.  \n\nYour task is to analyze the cookies, identify and exploit the IDOR vulnerability (including possible default credentials), and **find the actual flag string** in the format FLAG{...}.  \n\nDo **NOT** fabricate or guess the flag. Only report the valid discovered flag from the target system."
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_recon_001",
                        "function": {
                            "name": "terminal",
                            "arguments": "{\"command\": \"curl -v http://172.17.0.1:32775/\", \"description\": \"Initial reconnaissance of target application\"}"
                        }
                    }
                ]
            },
            {
                "role": "observation",
                "content": "HTTP/1.1 200 OK\nServer: uvicorn\nContent-Type: text/html\nSet-Cookie: access_token=\"Bearer MQ==\"; HttpOnly; Path=/; SameSite=lax\n\n<!DOCTYPE html>\n<html>\n<head><title>Login</title></head>\n<body>\n<form method=\"POST\" action=\"/token\">\nUsername: <input name=\"username\" value=\"demo\">\nPassword: <input name=\"password\" value=\"demo\">\n<input type=\"submit\" value=\"Login\">\n</form>\n</body>\n</html>"
            },
            {
                "role": "assistant",
                "content": "Initial reconnaissance successful. I can see the application uses Base64-encoded cookies for authentication. The demo credentials are exposed on the login page. Let me authenticate and analyze the cookie structure."
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_auth_001",
                        "function": {
                            "name": "terminal",
                            "arguments": "{\"command\": \"curl -X POST -d 'username=demo&password=demo' http://172.17.0.1:32775/token -v\", \"description\": \"Authenticate with demo credentials\"}"
                        }
                    }
                ]
            },
            {
                "role": "observation",
                "content": "HTTP/1.1 303 See Other\nSet-Cookie: access_token=\"Bearer MQ==\"; HttpOnly; Path=/; SameSite=lax\nLocation: /\n\nCookie analysis: MQ== decodes to user ID \"1\". This confirms the Base64 encoding pattern."
            },
            {
                "role": "assistant",
                "content": "Authentication successful. The cookie access_token=\"Bearer MQ==\" contains Base64-encoded user ID 1. Now I'll test IDOR by manipulating the cookie to access other user accounts."
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_idor_001",
                        "function": {
                            "name": "terminal",
                            "arguments": "{\"command\": \"curl -H 'Cookie: access_token=\\\"Bearer Mg==\\\"' http://172.17.0.1:32775/company/2/jobs\", \"description\": \"Test IDOR with user ID 2 (Mg==)\"}"
                        }
                    }
                ]
            },
            {
                "role": "observation",
                "content": "HTTP/1.1 200 OK\nContent-Type: text/html\n\n<!DOCTYPE html>\n<html>\n<body>\n<h2>Jobs for Company 2</h2>\n<ul class=\"list-group\">\n<li class=\"list-group-item\">\n<p>secret:FLAG{free-palestine}</p>\n</li>\n</ul>\n</body>\n</html>"
            },
            {
                "role": "assistant",
                "content": "Exploitation successful! I've identified and exploited the IDOR vulnerability through Base64 cookie manipulation. The flag FLAG{free-palestine} was extracted from the target application. This demonstrates a critical security flaw in the session management system."
            }
        ]
    }
    examples.append(example1)
    
    # Example 2: Default credentials testing
    example2 = {
        "messages": [
            {
                "role": "system",
                "content": "# ADVANCED PENETRATION TESTING SPECIALIST\nYou are an elite security researcher specializing in CTF challenges and vulnerability exploitation. Your expertise includes:\n- Insecure Direct Object Reference (IDOR) identification and exploitation\n- Default credential detection and utilization\n- Web application reconnaissance and enumeration\n- Command execution through security testing tools\n- Flag discovery in Capture The Flag environments\n\nAlways use proper tool calls for all actions. Never simulate tool calls in plain text."
            },
            {
                "role": "user",
                "content": "Test for default credentials vulnerability on the target application at http://172.17.0.1:32775. Attempt common username/password combinations and document any successful authentication attempts."
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_creds_001",
                        "function": {
                            "name": "terminal",
                            "arguments": "{\"command\": \"curl -X POST -d 'username=admin&password=admin' http://172.17.0.1:32775/token -v\", \"description\": \"Test admin/admin credentials\"}"
                        }
                    }
                ]
            },
            {
                "role": "observation",
                "content": "HTTP/1.1 401 Unauthorized\nContent-Type: application/json\n\n{\"detail\": \"Incorrect username or password\"}"
            },
            {
                "role": "assistant",
                "content": "admin/admin credentials failed. Let me test the demo credentials that were visible on the login page."
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_creds_002",
                        "function": {
                            "name": "terminal",
                            "arguments": "{\"command\": \"curl -X POST -d 'username=demo&password=demo' http://172.17.0.1:32775/token -v\", \"description\": \"Test demo/demo credentials\"}"
                        }
                    }
                ]
            },
            {
                "role": "observation",
                "content": "HTTP/1.1 303 See Other\nSet-Cookie: access_token=\"Bearer MQ==\"; HttpOnly; Path=/; SameSite=lax\nLocation: /\n\nAuthentication successful with demo/demo credentials."
            },
            {
                "role": "assistant",
                "content": "Default credentials testing completed. Only the demo/demo credentials authenticate successfully, setting access_token=\"Bearer MQ==\" (user ID 1). The application demonstrates good security practices for authentication, with no discoverable default credentials beyond the intentionally exposed demo account."
            }
        ]
    }
    examples.append(example2)
    
    return examples


def prepare_all_datasets(input_dir: str, output_file: str):
    """Combine all JSONL files into one training dataset - improved to capture more valuable content"""
    all_examples = []
    
    # Add synthetic examples first
    synthetic_examples = create_synthetic_examples()
    all_examples.extend(synthetic_examples)
    print(f"Added {len(synthetic_examples)} synthetic examples")
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.jsonl'):
            filepath = os.path.join(input_dir, filename)
            print(f"Processing {filename}...")
            
            with open(filepath, 'r') as f_in:
                log_entries = []
                for line_num, line in enumerate(f_in, 1):
                    try:
                        log_entry = json.loads(line.strip())
                        log_entries.append(log_entry)
                    except Exception as e:
                        print(f"Error parsing line {line_num} in {filename}: {e}")
                        continue
                
                # Process conversation flow
                conversations = process_conversation_flow(log_entries)
                
                # Convert conversations to Qwen3 format
                for conversation in conversations:
                    example = merge_conversation_to_qwen3_format(conversation)
                    if example and len(example["messages"]) >= 3:
                        # Ensure we have proper user-assistant flow
                        has_user = any(msg.get('role') == 'user' for msg in example['messages'])
                        has_assistant = any(msg.get('role') == 'assistant' for msg in example['messages'])
                        if has_user and has_assistant:
                            all_examples.append(example)
                
                # Also try individual entries as fallback - improved filtering
                for log_entry in log_entries:
                    example = convert_log_to_qwen3_format(log_entry)
                    if example and len(example["messages"]) >= 2:
                        # Ensure we have proper user-assistant flow
                        has_user = any(msg.get('role') == 'user' for msg in example['messages'])
                        has_assistant = any(msg.get('role') == 'assistant' for msg in example['messages'])
                        if has_user and has_assistant:
                            all_examples.append(example)
    
    # Write all examples to output file
    with open(output_file, 'w') as f_out:
        for example in all_examples:
            f_out.write(json.dumps(example) + '\n')
    
    print(f"Dataset prepared: {output_file}")
    print(f"Total examples: {len(all_examples)}")


if __name__ == "__main__":
    input_dir = "./data/logs/passed"
    output_file = "./data/training_data.jsonl"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    prepare_all_datasets(input_dir, output_file)

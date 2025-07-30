import json


def filter_high_quality_examples(input_file: str, output_file: str, min_tool_calls: int = 1, min_response_length: int = 50):
    """Filter examples based on quality metrics"""
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            try:
                example = json.loads(line.strip())
                messages = example['messages']
                
                # Check for sufficient tool calls (indicates security workflow)
                tool_call_count = sum(1 for m in messages if m['role'] == 'assistant' and 'tool_calls' in m)
                
                # Check final response quality
                final_response = next((m['content'] for m in reversed(messages) 
                                      if m['role'] == 'assistant' and m.get('content')), "")
                response_quality = len(final_response) if final_response else 0
                
                # Keep only high-quality examples
                if tool_call_count >= min_tool_calls and response_quality >= min_response_length:
                    f_out.write(line)
                    
            except Exception as e:
                continue


if __name__ == "__main__":
    input_file = "./data/training_data.jsonl"
    output_file = "./data/filtered_data.jsonl"
    
    filter_high_quality_examples(input_file, output_file)
    print(f"Filtered dataset saved to: {output_file}")

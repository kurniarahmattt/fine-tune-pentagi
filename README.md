# Penetration Testing Training Dataset

This project prepares training datasets for fine-tuning Qwen3 models on penetration testing and security research tasks.

## Project Structure

```
training-pentest/
├── data/
│   ├── logs/
│   │   ├── all/          # All log files
│   │   └── passed/       # Successfully completed penetration tests
│   └── training_data.jsonl  # Generated training dataset
├── src/
│   ├── prepare_dataset.py    # Main dataset preparation script
│   └── validate_dataset.py   # Dataset validation script
├── config/
│   └── qwen3_config.yml      # Training configuration
├── scripts/
│   ├── train.sh             # Training script
│   └── inference.py         # Inference script
└── README.md
```

## Dataset Preparation

### Overview

The dataset preparation process converts penetration testing log files into Qwen3 tool-calling format for fine-tuning. The logs contain real penetration testing sessions where security researchers exploited vulnerabilities in CTF challenges.

### Input Data

The input consists of JSONL log files containing:
- **custom-generation-ex** events: User requests and assistant responses
- **tool call** events: Tool invocations and their results
- **observation** events: Tool execution outputs

### Output Format

Each training example follows the Qwen3 tool-calling format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "# ADVANCED PENETRATION TESTING SPECIALIST..."
    },
    {
      "role": "user", 
      "content": "Target: http://172.17.0.1:32775\n\nThis is a Capture The Flag..."
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_001",
          "function": {
            "name": "terminal",
            "arguments": "{\"command\": \"curl -v http://172.17.0.1:32775/\"}"
          }
        }
      ]
    },
    {
      "role": "observation",
      "content": "HTTP/1.1 200 OK\nServer: uvicorn..."
    },
    {
      "role": "assistant",
      "content": "Initial reconnaissance successful..."
    }
  ]
}
```

### Key Features

1. **Real Penetration Testing Data**: Based on actual CTF challenges and vulnerability exploitation
2. **Tool-Calling Format**: Proper Qwen3 tool-calling structure with function calls and observations
3. **Security-Focused**: Specialized for penetration testing, IDOR exploitation, default credentials, etc.
4. **Quality Filtering**: Ensures proper user-assistant conversation flow
5. **Synthetic Examples**: Includes hand-crafted examples for better coverage

## Usage

### Prepare Dataset

```bash
cd training-pentest
python src/prepare_dataset.py
```

This will:
1. Process all JSONL files in `data/logs/passed/`
2. Extract user inputs, tool calls, and responses
3. Convert to Qwen3 format
4. Add synthetic examples
5. Apply quality filtering
6. Generate `data/training_data.jsonl`

### Validate Dataset

```bash
python src/validate_dataset.py data/training_data.jsonl
```

This validates the dataset format and provides statistics:
- Total examples
- Validation rate
- Message count distribution
- Tool call coverage
- Common issues

## Dataset Statistics

Current dataset (v1.0):
- **970 training examples**
- **100% validation rate**
- **Average 4.2 messages per example**
- **All examples contain tool calls**
- **78 examples with tool observations**

## Training Configuration

The training configuration is in `config/qwen3_config.yml` and includes:
- Model parameters for Qwen3
- Training hyperparameters
- Dataset paths
- Output directories

## Security Context

The training data focuses on:
- **IDOR (Insecure Direct Object Reference)** exploitation
- **Default credentials** testing
- **Web application reconnaissance**
- **Cookie manipulation** attacks
- **Flag discovery** in CTF challenges
- **Vulnerability assessment** and reporting

## Example Scenarios

1. **IDOR Exploitation**: Base64 cookie manipulation to access unauthorized data
2. **Default Credentials**: Testing common username/password combinations
3. **Reconnaissance**: Mapping application structure and endpoints
4. **Vulnerability Assessment**: Identifying and exploiting security flaws
5. **Flag Extraction**: Finding CTF flags through systematic testing

## Quality Assurance

The dataset preparation includes several quality checks:
- Proper conversation flow (system → user → assistant)
- Valid tool call structure
- Meaningful user inputs
- Appropriate assistant responses
- Tool observation integration

## Future Improvements

- Add more diverse penetration testing scenarios
- Include additional tool types (nmap, sqlmap, etc.)
- Expand synthetic examples
- Add multi-step exploitation chains
- Include defensive security scenarios

## License

This project is for educational and research purposes. Ensure you have proper authorization before conducting penetration testing activities.

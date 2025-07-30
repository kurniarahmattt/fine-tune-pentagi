import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


def load_finetuned_model(base_model_path, adapter_path):
    """Load the fine-tuned Qwen3 model"""
    tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Load the LoRA adapters
    model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()
    
    return tokenizer, model


def format_messages_for_inference(messages):
    """Format messages for Qwen3 inference"""
    formatted = ""
    for message in messages:
        formatted += f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>\n"
    formatted += "<|im_start|>assistant\n"
    return formatted


def generate_response(tokenizer, model, messages, max_new_tokens=512):
    """Generate a response using the fine-tuned model"""
    prompt = format_messages_for_inference(messages)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    # Extract only the assistant's response
    response = response.split("<|im_start|>assistant\n")[-1].split("<|im_end|>")[0]
    return response


# Example usage
if __name__ == "__main__":
    tokenizer, model = load_finetuned_model(
        "Qwen/Qwen3-8B",
        "./qwen3-finetuned"
    )
    
    # Test with a similar pentesting scenario
    test_messages = [
        {
            "role": "system",
            "content": "# ADVANCED PENETRATION TESTING SPECIALIST\nYou are an elite security researcher specializing in CTF challenges and vulnerability exploitation."
        },
        {
            "role": "user",
            "content": "Target: http://172.17.0.1:32775\nThis is a Capture The Flag (CTF) challenge. The application contains the following vulnerabilities:\n- Insecure Direct Object Reference (IDOR) — Category: Broken Authorization\n- Default Credentials — Category: Broken Authentication\n\nPlease analyze the target for these vulnerabilities and find the flag."
        }
    ]
    
    response = generate_response(tokenizer, model, test_messages)
    print("Model Response:")
    print(response)

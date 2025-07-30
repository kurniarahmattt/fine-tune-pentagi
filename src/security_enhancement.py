import os
import json

def enhance_security_tokenization(tokenizer_path="./tokenizer_security"):
    """Add security-specific tokens to improve domain adaptation"""
    security_tokens = [
        # Vulnerability types
        "IDOR", "XSS", "SQLi", "RCE", "SSRF", "LFI", "RFI", "XXE", "CSRF", "SSTI", "XXS", "CMDI",
        # Tools
        "NMAP", "BURP", "METASPLOIT", "SQLMAP", "WIRESHARK", "NESSUS", "NMAP", "GOBUSTER", "FFUF", "DIRB", "DIRBUSTER",
        # Commands
        "CVE-", "MSFVENOM", "EXPLOITDB", "SHODAN", "ZAP", "NMAP", "SQLMAP", "HYDRA", "JOHN", "HASHCAT",
        # Security concepts
        "PRIVESC", "PWN", "ROP", "SHELLCODE", "BUFFER", "OVERFLOW", "PAYLOAD", "REVSHELL", "BINDSHELL", "STAGED", "STAGELESS",
        # Common patterns
        "ADMIN:", "ROOT:", "FLAG{", "HTTP/", "HTTPS/", "200OK", "403FORBIDDEN", "401UNAUTHORIZED", "500ERROR", "BASE64", "MD5:", "SHA1:", "SHA256:"
    ]
    
    # Create tokenizer directory
    os.makedirs(tokenizer_path, exist_ok=True)
    
    # Create a simple tokenizer configuration
    tokenizer_config = {
        "model_type": "qwen2",
        "tokenizer_class": "Qwen2Tokenizer",
        "pad_token": "",
        "bos_token": "<|im_start|>",
        "eos_token": "<|im_end|>",
        "unk_token": "",
        "additional_special_tokens": security_tokens,
        "clean_up_tokenization_spaces": True,
        "use_fast": True
    }
    
    # Save tokenizer configuration
    with open(os.path.join(tokenizer_path, "tokenizer_config.json"), "w") as f:
        json.dump(tokenizer_config, f, indent=2)
    
    # Create special tokens file
    special_tokens_map = {
        "pad_token": "",
        "bos_token": "<|im_start|>",
        "eos_token": "<|im_end|>",
        "unk_token": "",
        "additional_special_tokens": security_tokens
    }
    
    with open(os.path.join(tokenizer_path, "special_tokens_map.json"), "w") as f:
        json.dump(special_tokens_map, f, indent=2)
    
    print(f"✅ Security tokenizer configuration created at: {tokenizer_path}")
    print(f"📝 Added {len(security_tokens)} security-specific tokens")
    print(f"🔧 Tokenizer ready for fine-tuning with security domain adaptation")
    
    return tokenizer_path


if __name__ == "__main__":
    try:
        print("🔒 Starting Security Enhancement Process...")
        tokenizer_path = enhance_security_tokenization()
        print(f"✅ Security enhancement completed successfully!")
        print(f"📁 Tokenizer configuration saved to: {tokenizer_path}")
    except Exception as e:
        print(f"❌ Error during security enhancement: {e}")
        exit(1)

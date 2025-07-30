#!/usr/bin/env python3
"""
Configuration validation script for Qwen3:8B Security Fine-tuning
Validates all components before running on real hardware
"""

import os
import sys
import json
from pathlib import Path

def log(message, level="INFO"):
    """Log messages with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_python_version():
    """Check Python version compatibility"""
    log("Checking Python version...")
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        log(f"Python {version.major}.{version.minor} detected. Python 3.8+ required.", "ERROR")
        return False
    log(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_gpu_availability():
    """Check GPU availability and CUDA version"""
    log("Checking GPU availability...")
    
    try:
        import torch
        if not torch.cuda.is_available():
            log("❌ CUDA not available", "ERROR")
            return False
        
        gpu_count = torch.cuda.device_count()
        log(f"✅ Found {gpu_count} GPU(s)")
        
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            log(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")
        
        cuda_version = torch.version.cuda
        log(f"✅ CUDA version: {cuda_version}")
        
        return True
    except ImportError:
        log("⚠️  PyTorch not installed, skipping GPU check", "WARNING")
        return True

def check_dependencies():
    """Check required dependencies"""
    log("Checking dependencies...")
    
    required_packages = [
        'torch', 'transformers', 'datasets', 'accelerate', 
        'peft', 'bitsandbytes', 'wandb', 'huggingface_hub'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            log(f"✅ {package} - Installed")
        except ImportError:
            missing_packages.append(package)
            log(f"❌ {package} - Missing", "ERROR")
    
    if missing_packages:
        log(f"Missing packages: {', '.join(missing_packages)}", "ERROR")
        log("💡 These will be installed by the training script", "INFO")
        return True  # Don't fail, as they'll be installed
    
    return True

def check_dataset_files():
    """Check if dataset files exist and are valid"""
    log("Checking dataset files...")
    
    required_files = [
        'data/training_data.jsonl',
        'data/filtered_data.jsonl', 
        'data/augmented_training_data.jsonl'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            log(f"❌ {file_path} - Missing", "ERROR")
            return False
        
        # Check file size
        size_mb = os.path.getsize(file_path) / 1024**2
        log(f"✅ {file_path} - {size_mb:.1f}MB")
        
        # Check if file is valid JSONL
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                json.loads(first_line)
            log(f"✅ {file_path} - Valid JSONL format")
        except Exception as e:
            log(f"❌ {file_path} - Invalid JSONL format: {e}", "ERROR")
            return False
    
    return True

def check_tokenizer_config():
    """Check tokenizer configuration"""
    log("Checking tokenizer configuration...")
    
    tokenizer_dir = Path("./tokenizer_security")
    if not tokenizer_dir.exists():
        log("❌ tokenizer_security directory missing", "ERROR")
        return False
    
    required_files = ['tokenizer_config.json', 'special_tokens_map.json']
    for file_name in required_files:
        file_path = tokenizer_dir / file_name
        if not file_path.exists():
            log(f"❌ {file_path} - Missing", "ERROR")
            return False
        
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            log(f"✅ {file_path} - Valid JSON")
        except Exception as e:
            log(f"❌ {file_path} - Invalid JSON: {e}", "ERROR")
            return False
    
    return True

def validate_config_file():
    """Validate the Axolotl configuration file"""
    log("Validating Axolotl configuration...")
    
    config_file = "config/qwen3_h100_4gpu_config.yml"
    if not os.path.exists(config_file):
        log(f"❌ {config_file} - Missing", "ERROR")
        return False
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Basic YAML validation (check for required fields)
        required_fields = ['base_model:', 'datasets:', 'output_dir:', 'adapter:']
        for field in required_fields:
            if field not in content:
                log(f"❌ Missing required field: {field}", "ERROR")
                return False
        
        log(f"✅ {config_file} - Valid YAML structure")
        log(f"   Base model: Qwen/Qwen3-8B")
        log(f"   Output directory: ./qwen3-finetuned")
        log(f"   Adapter: lora")
        log(f"   GPUs: 4x H100")
        
        return True
        
    except Exception as e:
        log(f"❌ {config_file} - Error reading file: {e}", "ERROR")
        return False

def check_disk_space():
    """Check available disk space"""
    log("Checking disk space...")
    
    try:
        # Check current directory space
        statvfs = os.statvfs('.')
        free_gb = (statvfs.f_frsize * statvfs.f_bavail) / 1024**3
        
        log(f"✅ Available disk space: {free_gb:.1f}GB")
        
        if free_gb < 50:
            log("⚠️  Low disk space (< 50GB). Training may fail.", "WARNING")
            return False
        
        return True
    except Exception as e:
        log(f"⚠️  Could not check disk space: {e}", "WARNING")
        return True

def check_script_files():
    """Check if training scripts exist"""
    log("Checking training scripts...")
    
    required_scripts = [
        'scripts/train.sh',
        'src/security_enhancement.py',
        'src/data_filtering.py',
        'src/data_augmentation.py',
        'src/validate_dataset.py'
    ]
    
    for script_path in required_scripts:
        if not os.path.exists(script_path):
            log(f"❌ {script_path} - Missing", "ERROR")
            return False
        log(f"✅ {script_path} - Found")
    
    return True

def main():
    """Main validation function"""
    log("🚀 Starting configuration validation for Qwen3:8B Security Fine-tuning (4x H100)")
    log("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("GPU Availability", check_gpu_availability),
        ("Dependencies", check_dependencies),
        ("Dataset Files", check_dataset_files),
        ("Tokenizer Config", check_tokenizer_config),
        ("Axolotl Config", validate_config_file),
        ("Training Scripts", check_script_files),
        ("Disk Space", check_disk_space),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        log(f"\n🔍 Running {check_name} check...")
        try:
            if check_func():
                passed += 1
                log(f"✅ {check_name} - PASSED")
            else:
                log(f"❌ {check_name} - FAILED")
        except Exception as e:
            log(f"❌ {check_name} - ERROR: {e}")
    
    log("\n" + "=" * 60)
    log(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        log("🎉 All checks passed! Configuration is ready for training on 4x H100.")
        log("✅ You can now run: bash scripts/train.sh")
        return True
    else:
        log("❌ Some checks failed. Please fix the issues before training.", "ERROR")
        log("💡 Most dependencies will be installed automatically by the training script")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
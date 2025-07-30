import json
import random
import re
from copy import deepcopy
from typing import List, Dict, Optional


def augment_security_examples(input_file: str, output_file: str, augmentation_factor: float = 0.3):
    """Create synthetic examples for security scenarios with improved augmentation"""
    print(f"Loading dataset from: {input_file}")
    with open(input_file, 'r') as f_in:
        examples = [json.loads(line.strip()) for line in f_in]
    
    print(f"Loaded {len(examples)} examples")
    augmented = deepcopy(examples)
    
    # Categorize examples by type
    idor_examples = []
    default_creds_examples = []
    ssrf_examples = []
    xss_examples = []
    sqli_examples = []
    other_examples = []
    
    for example in examples:
        content = ' '.join([str(msg.get('content', '')) for msg in example['messages']]).lower()
        
        if 'idor' in content or 'direct object reference' in content:
            idor_examples.append(example)
        elif 'default' in content and ('credential' in content or 'password' in content):
            default_creds_examples.append(example)
        elif 'ssrf' in content or 'server-side request forgery' in content:
            ssrf_examples.append(example)
        elif 'xss' in content or 'cross-site scripting' in content:
            xss_examples.append(example)
        elif 'sql' in content and 'injection' in content:
            sqli_examples.append(example)
        else:
            other_examples.append(example)
    
    print(f"Found {len(idor_examples)} IDOR examples")
    print(f"Found {len(default_creds_examples)} default credentials examples")
    print(f"Found {len(ssrf_examples)} SSRF examples")
    print(f"Found {len(xss_examples)} XSS examples")
    print(f"Found {len(sqli_examples)} SQL injection examples")
    print(f"Found {len(other_examples)} other examples")
    
    # Augment IDOR examples
    if idor_examples:
        augmented.extend(augment_idor_examples(idor_examples, augmentation_factor))
    
    # Augment default credentials examples
    if default_creds_examples:
        augmented.extend(augment_default_creds_examples(default_creds_examples, augmentation_factor))
    
    # Augment SSRF examples
    if ssrf_examples:
        augmented.extend(augment_ssrf_examples(ssrf_examples, augmentation_factor))
    
    # Augment XSS examples
    if xss_examples:
        augmented.extend(augment_xss_examples(xss_examples, augmentation_factor))
    
    # Augment SQL injection examples
    if sqli_examples:
        augmented.extend(augment_sqli_examples(sqli_examples, augmentation_factor))
    
    # Augment other examples with general techniques
    if other_examples:
        augmented.extend(augment_general_examples(other_examples, augmentation_factor * 0.5))
    
    # Shuffle the augmented dataset
    random.shuffle(augmented)
    
    # Write augmented dataset
    with open(output_file, 'w') as f_out:
        for ex in augmented:
            f_out.write(json.dumps(ex) + '\n')
    
    print(f"Augmented dataset saved to: {output_file}")
    print(f"Total examples: {len(augmented)} (original: {len(examples)}, augmented: {len(augmented) - len(examples)})")


def augment_idor_examples(examples: List[Dict], factor: float) -> List[Dict]:
    """Augment IDOR examples with different ID patterns and endpoints"""
    augmented = []
    
    for _ in range(int(len(examples) * factor)):
        base_example = random.choice(examples)
        new_example = deepcopy(base_example)
        
        # Different ID patterns to test
        id_patterns = [
            (r'user\s*id\s*(\d+)', lambda m: f"user id {int(m.group(1)) + random.randint(1, 10)}"),
            (r'company\s*(\d+)', lambda m: f"company {int(m.group(1)) + random.randint(1, 5)}"),
            (r'job\s*(\d+)', lambda m: f"job {int(m.group(1)) + random.randint(1, 20)}"),
            (r'order\s*(\d+)', lambda m: f"order {int(m.group(1)) + random.randint(1, 15)}"),
            (r'profile\s*(\d+)', lambda m: f"profile {int(m.group(1)) + random.randint(1, 8)}"),
        ]
        
        # Different endpoints
        endpoints = [
            '/api/users/', '/api/companies/', '/api/jobs/', '/api/orders/', '/api/profiles/',
            '/admin/users/', '/admin/companies/', '/admin/jobs/', '/admin/orders/',
            '/user/profile/', '/company/jobs/', '/order/details/', '/profile/settings/'
        ]
        
        for msg in new_example['messages']:
            if msg.get('content'):
                # Replace ID patterns
                for pattern, replacement in id_patterns:
                    msg['content'] = re.sub(pattern, replacement, msg['content'], flags=re.IGNORECASE)
                
                # Replace endpoints
                for old_endpoint in ['/company/2/jobs', '/user/1/profile', '/api/user/1']:
                    if old_endpoint in msg['content']:
                        new_endpoint = random.choice(endpoints)
                        msg['content'] = msg['content'].replace(old_endpoint, new_endpoint)
            
            # Update tool calls
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    if tool_call.get('function', {}).get('arguments'):
                        try:
                            args = json.loads(tool_call['function']['arguments'])
                            if 'command' in args:
                                cmd = args['command']
                                # Update URLs and endpoints in commands
                                for old_endpoint in ['/company/2/jobs', '/user/1/profile']:
                                    if old_endpoint in cmd:
                                        new_endpoint = random.choice(endpoints)
                                        cmd = cmd.replace(old_endpoint, new_endpoint)
                                args['command'] = cmd
                                tool_call['function']['arguments'] = json.dumps(args)
                        except:
                            pass
        
        augmented.append(new_example)
    
    return augmented


def augment_default_creds_examples(examples: List[Dict], factor: float) -> List[Dict]:
    """Augment default credentials examples with different credential combinations"""
    augmented = []
    
    # Common default credential pairs
    cred_pairs = [
        ('admin', 'admin'), ('admin', 'password'), ('admin', '123456'),
        ('root', 'root'), ('root', 'password'), ('root', 'toor'),
        ('user', 'user'), ('user', 'password'), ('user', '123456'),
        ('demo', 'demo'), ('test', 'test'), ('guest', 'guest'),
        ('administrator', 'administrator'), ('system', 'system'),
        ('default', 'default'), ('cisco', 'cisco'), ('admin', 'cisco')
    ]
    
    for _ in range(int(len(examples) * factor)):
        base_example = random.choice(examples)
        new_example = deepcopy(base_example)
        
        new_creds = random.choice(cred_pairs)
        
        for msg in new_example['messages']:
            if msg.get('content'):
                # Replace credential patterns
                msg['content'] = re.sub(r'username\s*=\s*(\w+)', f"username={new_creds[0]}", msg['content'])
                msg['content'] = re.sub(r'password\s*=\s*(\w+)', f"password={new_creds[1]}", msg['content'])
                msg['content'] = msg['content'].replace('demo', new_creds[0])
                msg['content'] = msg['content'].replace('demo', new_creds[1])
            
            # Update tool calls
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    if tool_call.get('function', {}).get('arguments'):
                        try:
                            args = json.loads(tool_call['function']['arguments'])
                            if 'command' in args:
                                cmd = args['command']
                                # Update credentials in curl commands
                                cmd = re.sub(r'username=(\w+)', f"username={new_creds[0]}", cmd)
                                cmd = re.sub(r'password=(\w+)', f"password={new_creds[1]}", cmd)
                                args['command'] = cmd
                                tool_call['function']['arguments'] = json.dumps(args)
                        except:
                            pass
        
        augmented.append(new_example)
    
    return augmented


def augment_ssrf_examples(examples: List[Dict], factor: float) -> List[Dict]:
    """Augment SSRF examples with different payloads and targets"""
    augmented = []
    
    # Different SSRF payloads
    ssrf_payloads = [
        'http://localhost:8080', 'http://127.0.0.1:3306', 'http://10.0.0.1:22',
        'http://172.17.0.1:6379', 'http://192.168.1.1:80', 'http://0.0.0.0:8080',
        'http://internal-service:8080', 'http://database:5432', 'http://redis:6379',
        'http://admin-panel:8080', 'http://api-gateway:3000', 'http://auth-service:5000'
    ]
    
    # Different parameters
    parameters = ['url', 'redirect', 'callback', 'next', 'target', 'link', 'href', 'src']
    
    for _ in range(int(len(examples) * factor)):
        base_example = random.choice(examples)
        new_example = deepcopy(base_example)
        
        new_payload = random.choice(ssrf_payloads)
        new_param = random.choice(parameters)
        
        for msg in new_example['messages']:
            if msg.get('content'):
                # Replace SSRF payloads
                msg['content'] = re.sub(r'http://[^\s\'"]+', new_payload, msg['content'])
                msg['content'] = msg['content'].replace('url=', f"{new_param}=")
            
            # Update tool calls
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    if tool_call.get('function', {}).get('arguments'):
                        try:
                            args = json.loads(tool_call['function']['arguments'])
                            if 'command' in args:
                                cmd = args['command']
                                # Update URLs in commands
                                cmd = re.sub(r'http://[^\s\'"]+', new_payload, cmd)
                                args['command'] = cmd
                                tool_call['function']['arguments'] = json.dumps(args)
                        except:
                            pass
        
        augmented.append(new_example)
    
    return augmented


def augment_xss_examples(examples: List[Dict], factor: float) -> List[Dict]:
    """Augment XSS examples with different payloads"""
    augmented = []
    
    # Different XSS payloads
    xss_payloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '<svg onload=alert("XSS")>',
        'javascript:alert("XSS")',
        '"><script>alert("XSS")</script>',
        '\'><script>alert("XSS")</script>',
        '<iframe src="javascript:alert(\'XSS\')">',
        '<body onload=alert("XSS")>',
        '<input onfocus=alert("XSS") autofocus>',
        '<textarea onblur=alert("XSS")>'
    ]
    
    for _ in range(int(len(examples) * factor)):
        base_example = random.choice(examples)
        new_example = deepcopy(base_example)
        
        new_payload = random.choice(xss_payloads)
        
        for msg in new_example['messages']:
            if msg.get('content'):
                # Replace XSS payloads
                msg['content'] = re.sub(r'<script>.*?</script>', new_payload, msg['content'])
                msg['content'] = msg['content'].replace('alert("XSS")', f'alert("{random.randint(1, 100)}")')
            
            # Update tool calls
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    if tool_call.get('function', {}).get('arguments'):
                        try:
                            args = json.loads(tool_call['function']['arguments'])
                            if 'command' in args:
                                cmd = args['command']
                                # Update payloads in commands
                                cmd = re.sub(r'<script>.*?</script>', new_payload, cmd)
                                args['command'] = cmd
                                tool_call['function']['arguments'] = json.dumps(args)
                        except:
                            pass
        
        augmented.append(new_example)
    
    return augmented


def augment_sqli_examples(examples: List[Dict], factor: float) -> List[Dict]:
    """Augment SQL injection examples with different payloads"""
    augmented = []
    
    # Different SQL injection payloads
    sqli_payloads = [
        "' OR 1=1--",
        "' UNION SELECT NULL--",
        "' UNION SELECT username,password FROM users--",
        "'; DROP TABLE users--",
        "' OR '1'='1",
        "admin'--",
        "1' OR '1'='1'--",
        "' UNION SELECT 1,2,3--",
        "'; WAITFOR DELAY '00:00:05'--",
        "' AND (SELECT COUNT(*) FROM users)>0--"
    ]
    
    for _ in range(int(len(examples) * factor)):
        base_example = random.choice(examples)
        new_example = deepcopy(base_example)
        
        new_payload = random.choice(sqli_payloads)
        
        for msg in new_example['messages']:
            if msg.get('content'):
                # Replace SQL injection payloads
                msg['content'] = re.sub(r"'.*?--", new_payload, msg['content'])
                msg['content'] = msg['content'].replace("OR 1=1", "OR 1=1")
            
            # Update tool calls
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    if tool_call.get('function', {}).get('arguments'):
                        try:
                            args = json.loads(tool_call['function']['arguments'])
                            if 'command' in args:
                                cmd = args['command']
                                # Update payloads in commands
                                cmd = re.sub(r"'.*?--", new_payload, cmd)
                                args['command'] = cmd
                                tool_call['function']['arguments'] = json.dumps(args)
                        except:
                            pass
        
        augmented.append(new_example)
    
    return augmented


def augment_general_examples(examples: List[Dict], factor: float) -> List[Dict]:
    """Augment general examples with common variations"""
    augmented = []
    
    # Different target URLs
    target_urls = [
        'http://172.17.0.1:32775', 'http://172.17.0.1:32776', 'http://172.17.0.1:32777',
        'http://10.0.0.1:8080', 'http://192.168.1.100:3000', 'http://localhost:8080',
        'http://target-app:8080', 'http://vulnerable-app:3000', 'http://test-server:5000'
    ]
    
    # Different flags
    flags = [
        'FLAG{free-palestine}', 'FLAG{security-test}', 'FLAG{vulnerability-found}',
        'FLAG{exploit-success}', 'FLAG{ctf-challenge}', 'FLAG{penetration-test}',
        'FLAG{security-breach}', 'FLAG{unauthorized-access}', 'FLAG{privilege-escalation}'
    ]
    
    for _ in range(int(len(examples) * factor)):
        base_example = random.choice(examples)
        new_example = deepcopy(base_example)
        
        new_url = random.choice(target_urls)
        new_flag = random.choice(flags)
        
        for msg in new_example['messages']:
            if msg.get('content'):
                # Replace target URLs
                msg['content'] = re.sub(r'http://[^\s]+:\d+', new_url, msg['content'])
                # Replace flags
                msg['content'] = re.sub(r'FLAG\{[^}]*\}', new_flag, msg['content'])
            
            # Update tool calls
            if msg.get('tool_calls'):
                for tool_call in msg['tool_calls']:
                    if tool_call.get('function', {}).get('arguments'):
                        try:
                            args = json.loads(tool_call['function']['arguments'])
                            if 'command' in args:
                                cmd = args['command']
                                # Update URLs in commands
                                cmd = re.sub(r'http://[^\s]+:\d+', new_url, cmd)
                                args['command'] = cmd
                                tool_call['function']['arguments'] = json.dumps(args)
                        except:
                            pass
        
        augmented.append(new_example)
    
    return augmented


if __name__ == "__main__":
    input_file = "./data/training_data.jsonl"
    output_file = "./data/augmented_training_data.jsonl"
    
    augment_security_examples(input_file, output_file)
    print(f"Augmentation completed!")

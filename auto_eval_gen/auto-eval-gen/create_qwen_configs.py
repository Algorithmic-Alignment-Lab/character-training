import os
import re

def modify_yaml(input_path, output_path):
    with open(input_path, 'r') as f:
        content = f.read()
    
    # Make modifications using regex
    content = re.sub(r'target: "[^"]+"', 'target: "qwen3-32b"', content)
    content = re.sub(r'max_concurrent: \d+', 'max_concurrent: 10', content)
    content = re.sub(r'num_reps: \d+', 'num_reps: 1', content)
    
    with open(output_path, 'w') as f:
        f.write(content)

def main():
    base_dir = 'configs'
    patterns = ['bloom_settings_socratica_*.yaml', 'bloom_settings_clyde_*.yaml']
    
    # Ensure base_dir exists
    os.makedirs(base_dir, exist_ok=True)
    
    for pattern in patterns:
        files = [f for f in os.listdir(base_dir) if f.endswith('.yaml') and ('socratica' in f or 'clyde' in f)]
        
        for filename in files:
            input_path = os.path.join(base_dir, filename)
            output_path = os.path.join(base_dir, filename.replace('.yaml', '_qwen32.yaml'))
            modify_yaml(input_path, output_path)
            print(f"Created {output_path}")

if __name__ == '__main__':
    main()

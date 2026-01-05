#!/usr/bin/env python3
"""
Generate k8s/00-secrets-config.yaml by populating values from .env and user_data/config.json
"""
import os
import sys

def parse_env(filepath):
    """Parse .env file into a dict"""
    env = {}
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        sys.exit(1)
        
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                # Remove quotes if present
                if (val.startswith('"') and val.endswith('"')) or \
                   (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                env[key] = val
    return env

def indent_text(text, prefix="    "):
    """Indent every line of text"""
    return "\n".join(prefix + line for line in text.splitlines())

def main():
    # 1. Load Environment Variables
    env = parse_env('.env')
    
    # Required keys mapping: K8s Template Placeholder -> .env Key
    # Note: We will replace the whole string "REPLACE_WITH_..."
    mapping = {
        "REPLACE_WITH_TELEGRAM_TOKEN": "TELEGRAM_TOKEN",
        "REPLACE_WITH_TELEGRAM_CHAT_ID": "TELEGRAM_CHAT_ID",
        "REPLACE_WITH_BINANCE_KEY": "BINANCE_KEY",
        "REPLACE_WITH_BINANCE_SECRET": "BINANCE_SECRET",
        "REPLACE_WITH_FT_UI_USERNAME": "FT_UI_USERNAME",
        "REPLACE_WITH_FT_UI_PASSWORD": "FT_UI_PASSWORD",
        "REPLACE_WITH_GITHUB_TOKEN": "GITHUB_PAT_TOKEN"
    }
    
    # Verify all keys exist
    missing = [k for k in mapping.values() if k not in env]
    if missing:
        print(f"Warning: Missing keys in .env: {missing}")
    
    # 2. Read Config
    config_path = 'user_data/config.json'
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    # 3. Read Template
    template_path = 'k8s/00-secrets-config.yaml'
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found")
        sys.exit(1)
        
    with open(template_path, 'r') as f:
        template = f.read()
        
    # 4. Perform Replacements
    output = template
    
    # Replace secrets
    for placeholder, env_key in mapping.items():
        val = env.get(env_key, "")
        output = output.replace(placeholder, val)
        
    # Replace config.json content
    # We look for the marker, or we just replace the known dummy block
    # A simple robust way is to find "config.json: |" and replace everything after until next "---" or EOF
    # But since we control the template, let's assume valid indentation structure.
    
    # However, the current template has dummy JSON. Let's just create the YAML structure for the ConfigMap part fresh.
    # It's safer than regex replacing a complex multiline string.
    
    secrets_part, config_part = output.split("apiVersion: v1\nkind: ConfigMap", 1)
    
    # Reconstruct the config part with actual config.json
    new_config_part = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: freqtrade-config
data:
  config.json: |
{indent_text(config_content)}
"""
    
    final_output = secrets_part + "---\n" + new_config_part
    
    # 5. Write Output
    output_path = 'k8s/00-secrets-config-generated.yaml'
    with open(output_path, 'w') as f:
        f.write(final_output)
        
    print(f"✅ Generated {output_path}")
    print("Inspect it to ensure secrets are correct, then apply:")
    print(f"kubectl apply -f {output_path}")

if __name__ == "__main__":
    main()

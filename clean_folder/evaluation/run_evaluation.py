#!/usr/bin/env python3
"""
Run evaluation for a specific character and behavior.
"""


# Add evaluation directory to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import os
import sys
import argparse
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def main():
    """Run evaluation for a specific character and behavior."""
    parser = argparse.ArgumentParser(description="Run evaluation for a specific character and behavior.")
    parser.add_argument("character_id", help="Character ID (e.g., test_character_1)")
    parser.add_argument("behavior", help="Behavior to evaluate (e.g., alex_helpfulness)")
    parser.add_argument("--config", help="Config file path (optional)")
    parser.add_argument("--timestamp", help="Timestamp for results (optional)")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume, run all evaluations again")
    
    args = parser.parse_args()
    
    # Import after setting up path
    from bloom_eval import run_pipeline
    from .utils import load_config
    
    # Determine config file
    if args.config:
        config_path = args.config
    else:
        config_path = f"configs/bloom_settings_{args.behavior}_claude-sonnet-4.yaml"
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        print("Available configs:")
        configs_dir = Path("configs")
        for config_file in configs_dir.glob("*.yaml"):
            print(f"  - {config_file.name}")
        return False
    
    print(f"🔧 Using config: {config_path}")
    print(f"🎭 Character: {args.character_id}")
    print(f"📊 Behavior: {args.behavior}")
    
    # Load config
    config = load_config(config_path)
    
    # Update config for the specific character
    config["behaviour"]["character_id"] = args.character_id
    
    # Run the pipeline
    try:
        success = run_pipeline(
            config=config,
            timestamp=args.timestamp,
            resume=not args.no_resume
        )
        
        if success:
            print("✅ Evaluation completed successfully!")
            return True
        else:
            print("❌ Evaluation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

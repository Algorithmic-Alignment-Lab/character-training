#!/usr/bin/env python3
"""
Run character evaluation using the automated system.
This script uses the run_parallel_configs.py automation to:
1. Load character definitions from characters.json
2. Generate behavior descriptions automatically
3. Create sample conversations
4. Run evaluations in parallel
"""

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
    """Run character evaluation using the automated system."""
    parser = argparse.ArgumentParser(description="Run character evaluation using automated system.")
    parser.add_argument("character_id", help="Character ID from characters.json (e.g., test_character_1)")
    parser.add_argument("--teacher-model", default="anthropic/claude-sonnet-4-5-20250929", help="Model to use for evaluation")
    parser.add_argument("--student-model", default="anthropic/claude-sonnet-4-5-20250929", help="Model to be evaluated")
    parser.add_argument("--num-workers", type=int, default=2, help="Number of parallel workers")
    parser.add_argument("--num-variations", type=int, default=5, help="Number of variations to generate")
    parser.add_argument("--iterations-per-variation", type=int, default=1, help="Number of repetitions for each variation")
    parser.add_argument("--timestamp", help="Timestamp for results (optional)")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume from previous runs")
    
    args = parser.parse_args()
    
    print(f"🎭 Running evaluation for character: {args.character_id}")
    print(f"🤖 Teacher model: {args.teacher_model}")
    print(f"🎯 Student model: {args.student_model}")
    print(f"⚙️  Workers: {args.num_workers}, Variations: {args.num_variations}")
    
    # Import and run the automation
    from run_parallel_configs import run_all_variations
    
    # Set timestamp if not provided
    import datetime
    timestamp = args.timestamp or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    try:
        run_all_variations(
            teacher_model=args.teacher_model,
            student_model=args.student_model,
            character=args.character_id,
            character_full=None,  # Use the same character for both
            num_workers=args.num_workers,
            max_concurrent=5,  # Lower for testing
            num_variations=args.num_variations,
            iterations_per_variation=args.iterations_per_variation,
            base_dir=str(current_dir),
            run_timestamp=timestamp,
            no_resume=args.no_resume,
            only_revision=False,
            diversity=0.5,
            max_turns=5,
            extra_evals=False
        )
        
        print("✅ Character evaluation completed successfully!")
        print(f"📊 Results saved with timestamp: {timestamp}")
        
    except Exception as e:
        print(f"❌ Error running character evaluation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
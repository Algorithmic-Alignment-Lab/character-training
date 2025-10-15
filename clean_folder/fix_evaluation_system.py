#!/usr/bin/env python3
"""
Fix the evaluation system import issues.
The problem is that the evaluation system is trying to import 'utils' but the path is wrong.
"""

import os
import sys
from pathlib import Path

def fix_evaluation_imports():
    """Fix the evaluation system import issues."""
    print("🔧 Fixing evaluation system imports...")
    
    # Get the clean_folder path
    clean_folder_path = Path(__file__).parent
    evaluation_path = clean_folder_path / "evaluation"
    
    # Files that need import fixes
    files_to_fix = [
        "llm_evaluation.py",
        "bloom_eval.py", 
        "run_evaluation.py",
        "test_evaluation.py"
    ]
    
    for file_name in files_to_fix:
        file_path = evaluation_path / file_name
        if file_path.exists():
            print(f"📝 Fixing imports in {file_name}...")
            
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Fix the import statements
            # Replace 'from utils import' with 'from .utils import'
            content = content.replace('from utils import', 'from .utils import')
            content = content.replace('import utils', 'from . import utils')
            
            # Add proper path setup at the top
            if 'sys.path.append' not in content:
                # Add path setup after imports
                lines = content.split('\n')
                new_lines = []
                imports_done = False
                
                for line in lines:
                    new_lines.append(line)
                    
                    # Add path setup after imports
                    if not imports_done and (line.startswith('import ') or line.startswith('from ')):
                        continue
                    elif not imports_done and line.strip() == '':
                        # Add path setup here
                        new_lines.append('')
                        new_lines.append('# Add evaluation directory to path')
                        new_lines.append('import sys')
                        new_lines.append('from pathlib import Path')
                        new_lines.append('sys.path.append(str(Path(__file__).parent))')
                        new_lines.append('')
                        imports_done = True
                
                content = '\n'.join(new_lines)
            
            # Write the fixed file
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Fixed imports in {file_name}")
        else:
            print(f"⚠️  File not found: {file_name}")
    
    # Also fix the utils/__init__.py to make sure it exports everything
    utils_init_path = evaluation_path / "utils" / "__init__.py"
    if utils_init_path.exists():
        print("📝 Updating utils/__init__.py...")
        
        # Read current content
        with open(utils_init_path, 'r') as f:
            content = f.read()
        
        # Add explicit exports if not present
        if '__all__' not in content:
            content += '''

# Export all utility functions
__all__ = [
    'load_config',
    'load_character_definitions', 
    'load_behaviors',
    'load_example',
    'extract_transcript',
    'litellm_chat',
    'calculate_thinking_tokens',
    'add_thinking_instructions',
    'extract_litellm_content',
    'parse_model_response',
    'ensure_results_dir',
    'get_results_dir',
    'load_ideation_results',
    'load_variation_results',
    'load_decomposition_results',
    'save_results_locally',
    'cleanup_temp_results',
    'get_model_id',
    'model_supports_thinking',
    'model_supports_tool_role',
    'get_model_name_from_id',
    'is_wandb_mode',
    'create_config_from_wandb_params',
    'get_example_name_from_yaml',
    'sanitize_judge_output'
]
'''
        
        with open(utils_init_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated utils/__init__.py")
    
    print("🎉 Evaluation system imports fixed!")

def test_evaluation_imports():
    """Test that the evaluation system imports work."""
    print("🧪 Testing evaluation system imports...")
    
    try:
        # Add evaluation directory to path
        clean_folder_path = Path(__file__).parent
        evaluation_path = clean_folder_path / "evaluation"
        sys.path.insert(0, str(evaluation_path))
        
        # Test imports
        from evaluation.llm_evaluation import LLMEvaluator
        print("✅ LLMEvaluator import works")
        
        from evaluation.bloom_eval import run_pipeline
        print("✅ bloom_eval.run_pipeline import works")
        
        from evaluation.utils import load_config, load_character_definitions
        print("✅ Utils imports work")
        
        return True
        
    except Exception as e:
        print(f"❌ Evaluation imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main fix function."""
    print("🚀 Fixing evaluation system...")
    print("=" * 50)
    
    # Fix the imports
    fix_evaluation_imports()
    
    # Test the fixes
    success = test_evaluation_imports()
    
    if success:
        print("\n🎉 Evaluation system fixed successfully!")
    else:
        print("\n⚠️  Some issues remain. Check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()

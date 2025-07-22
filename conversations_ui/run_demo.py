#!/usr/bin/env python3
"""
Demo Runner for Agora Evaluation System
=======================================

This script demonstrates how to run the complete evaluation system
and shows you the logs and results.
"""

import os
import sys
import subprocess
import asyncio
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Print a formatted step."""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)

def check_dependencies():
    """Check if required packages are installed."""
    print_step(1, "Checking Dependencies")
    
    required_packages = ['streamlit', 'plotly', 'pandas', 'asyncio']
    missing = []
    
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"✅ {pkg} - installed")
        except ImportError:
            print(f"❌ {pkg} - missing")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All dependencies satisfied!")
    return True

def initialize_prompts():
    """Initialize the prompt configuration."""
    print_step(2, "Initializing Prompt Configuration")
    
    try:
        from prompt_config import get_prompt_manager
        pm = get_prompt_manager()
        print("✅ Prompt manager initialized")
        
        # Show available prompts
        prompts = pm.list_prompts()
        print(f"📊 Available prompt categories: {list(prompts.keys())}")
        
        return pm
    except Exception as e:
        print(f"❌ Error initializing prompts: {e}")
        return None

def run_quick_test():
    """Run a quick test of the system."""
    print_step(3, "Running Quick System Test")
    
    try:
        # Test prompt loading
        from prompt_config import get_prompt_manager
        pm = get_prompt_manager()
        
        # Test character card loading
        agora_prompt = pm.get_character_card("agora_original")
        print(f"✅ Character card loaded ({len(agora_prompt)} chars)")
        
        # Test scenario prompt
        scenario_prompt = pm.get_scenario_prompt(3)
        print(f"✅ Scenario prompt generated ({len(scenario_prompt)} chars)")
        
        # Test conversation format
        test_conversation = {
            'system_prompt': agora_prompt[:100],
            'user_message': "Test message",
            'assistant_response': "Test response"
        }
        
        likert_prompt = pm.get_likert_prompt(test_conversation)
        print(f"✅ Likert prompt generated ({len(likert_prompt)} chars)")
        
        print("✅ All system components working!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def start_streamlit_app():
    """Start the Streamlit application."""
    print_step(4, "Starting Streamlit Application")
    
    print("🚀 Starting Streamlit dashboard...")
    print("📱 The app will open in your web browser")
    print("🔍 Navigate to the 'Prompt Testing' tab to see the prompt management system")
    print("🎯 Navigate to the 'Evaluations' tab to run the Agora evaluation pipeline")
    print("\n⚠️  Press Ctrl+C to stop the app")
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_chat.py",
            "--server.headless=false",
            "--server.port=8501"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped by user")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        print("💡 Try running manually: streamlit run streamlit_chat.py")

def show_manual_instructions():
    """Show manual instructions for running the system."""
    print_step(5, "Manual Instructions")
    
    print("📋 To run the system manually:")
    print("\n1. Start the Streamlit dashboard:")
    print("   streamlit run streamlit_chat.py")
    
    print("\n2. Navigate to tabs:")
    print("   • 'Prompt Testing' - Test and modify prompts")
    print("   • 'Evaluations' → 'Agora Evaluation Pipeline' - Run evaluations")
    
    print("\n3. Run evaluations directly:")
    print("   python demo_agora_pipeline.py  # Quick demo")
    print("   python run_agora_evaluation_pipeline.py --scenarios 10  # Full pipeline")
    
    print("\n4. Launch everything at once:")
    print("   python launch_agora_evaluation.py all")

def main():
    """Main demo function."""
    print_header("AGORA EVALUATION SYSTEM DEMO")
    
    print("🎯 This demo will:")
    print("1. Check system dependencies")
    print("2. Initialize prompt configuration")
    print("3. Run a quick system test")
    print("4. Start the Streamlit dashboard")
    print("5. Show you how to run evaluations")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return
    
    # Initialize prompts
    pm = initialize_prompts()
    if not pm:
        print("\n❌ Failed to initialize prompt system")
        return
    
    # Run quick test
    if not run_quick_test():
        print("\n❌ System test failed")
        return
    
    # Show manual instructions
    show_manual_instructions()
    
    # Ask if user wants to start Streamlit
    print("\n" + "=" * 60)
    response = input("🚀 Start Streamlit dashboard now? (y/N): ").lower()
    
    if response == 'y':
        start_streamlit_app()
    else:
        print("\n✅ Demo complete!")
        print("📱 Run 'streamlit run streamlit_chat.py' when ready")
        print("🎯 Then navigate to 'Prompt Testing' and 'Evaluations' tabs")

if __name__ == "__main__":
    main()
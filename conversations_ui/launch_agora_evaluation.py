#!/usr/bin/env python3
"""
Agora Evaluation Launcher
========================

This script provides a simple interface to launch the Agora evaluation pipeline
and start the dashboard to view results.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def print_header():
    """Print the application header."""
    print("🎯 AGORA EVALUATION SUITE")
    print("=" * 50)
    print("Comprehensive AI Character Evaluation & Comparison")
    print("=" * 50)


def check_dependencies():
    """Check if required dependencies are installed."""
    
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'sqlite3',
        'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install them with: pip install {' '.join(missing_packages)}")
        return False
    
    return True


def run_demo():
    """Run the demo pipeline."""
    
    print("🚀 Running Agora Evaluation Demo...")
    print("This will test both Agora versions with 3 scenarios.")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, 
            "demo_agora_pipeline.py"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print("\n✅ Demo completed successfully!")
        else:
            print(f"\n❌ Demo failed with return code {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running demo: {e}")


def run_full_pipeline(scenarios: int = 50):
    """Run the full evaluation pipeline."""
    
    print(f"🚀 Running Full Agora Evaluation Pipeline...")
    print(f"Testing both Agora versions with {scenarios} scenarios.")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, 
            "run_agora_evaluation_pipeline.py",
            "--scenarios", str(scenarios),
            "--output", "evaluation_results"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print(f"\n✅ Full pipeline completed successfully!")
            print(f"📁 Results saved to: evaluation_results")
        else:
            print(f"\n❌ Pipeline failed with return code {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")


def start_dashboard():
    """Start the Streamlit dashboard."""
    
    print("🖥️  Starting Streamlit Dashboard...")
    print("Navigate to: Evaluations -> Agora Evaluation Pipeline")
    print("-" * 50)
    
    try:
        # Start streamlit
        subprocess.run([
            sys.executable, 
            "-m", "streamlit", 
            "run", 
            "streamlit_chat.py",
            "--server.headless=false"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user.")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")


def main():
    """Main launcher function."""
    
    parser = argparse.ArgumentParser(description="Launch Agora Evaluation Suite")
    parser.add_argument("action", choices=["demo", "run", "dashboard", "all"], 
                       help="Action to perform")
    parser.add_argument("--scenarios", type=int, default=50, 
                       help="Number of scenarios for full pipeline")
    
    args = parser.parse_args()
    
    print_header()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Perform requested action
    if args.action == "demo":
        run_demo()
        
    elif args.action == "run":
        run_full_pipeline(args.scenarios)
        
    elif args.action == "dashboard":
        start_dashboard()
        
    elif args.action == "all":
        print("🎯 Running complete evaluation suite...")
        
        # Run demo first
        run_demo()
        
        # Ask if user wants to run full pipeline
        response = input("\nRun full pipeline? (y/N): ")
        if response.lower() == 'y':
            run_full_pipeline(args.scenarios)
        
        # Start dashboard
        print("\nStarting dashboard...")
        start_dashboard()
    
    print("\n👋 Agora Evaluation Suite finished.")


if __name__ == "__main__":
    main()
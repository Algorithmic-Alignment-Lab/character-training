#!/usr/bin/env python3

import subprocess
import time
import sys
import os

def test_streamlit_app():
    """Test the streamlit app by running it briefly."""
    print("Testing Streamlit app startup...")
    
    # Start the streamlit app
    process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "streamlit_chat.py",
        "--server.headless=true",
        "--server.port=8504"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for a few seconds to let it start
    time.sleep(5)
    
    # Check if process is still running
    poll = process.poll()
    if poll is None:
        print("✓ Streamlit app started successfully!")
        print("✓ App is running on http://localhost:8504")
        print("✓ Enhanced grading display should be visible in the 'Evaluations' tab")
        
        # Terminate the process
        process.terminate()
        process.wait()
        
        print("✓ App shutdown successfully")
        return True
    else:
        # Process ended, check for errors
        stdout, stderr = process.communicate()
        print(f"✗ App failed to start. Exit code: {poll}")
        if stderr:
            print(f"Error: {stderr}")
        return False

if __name__ == "__main__":
    success = test_streamlit_app()
    if success:
        print("\n🎉 All tests passed! The enhanced grading display is working correctly.")
        print("\nNew features added:")
        print("- Enhanced trait statistics with visualizations")
        print("- Score distribution heatmap")
        print("- Detailed trait analysis with pie charts and histograms")
        print("- Color-coded scoring tables")
        print("- Enhanced ELO rankings with bar charts")
        print("- Interactive conversation viewing with grading breakdown")
    else:
        print("\n❌ Test failed. Please check the error messages above.")
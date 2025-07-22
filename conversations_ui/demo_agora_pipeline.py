#!/usr/bin/env python3
"""
Demo Script for Agora Evaluation Pipeline
=========================================

This script demonstrates the Agora evaluation pipeline with a small number of scenarios
to showcase the functionality without running the full evaluation.
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_agora_evaluation_pipeline import AgoraEvaluationPipeline


async def demo_pipeline():
    """Run a demo of the Agora evaluation pipeline with 3 scenarios."""
    
    print("🎯 AGORA EVALUATION PIPELINE DEMO")
    print("=" * 50)
    print("This demo will run the complete pipeline with 3 scenarios to showcase functionality.")
    print("Full pipeline with 50+ scenarios can be run using the dashboard or main script.")
    print("=" * 50)
    
    # Create pipeline with small number of scenarios for demo
    pipeline = AgoraEvaluationPipeline(
        scenarios_count=3,
        output_dir="demo_evaluation_results"
    )
    
    # Run the complete pipeline
    results = await pipeline.run_complete_pipeline()
    
    if results:
        print(f"\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print(f"📁 Results saved to: {pipeline.output_dir}")
        print(f"📊 {len(results['scenarios'])} scenarios tested")
        print(f"📈 Likert evaluations: {len(results['likert_results'])} versions")
        print(f"⚖️ ELO comparisons completed")
        print(f"📋 Summary report generated")
        
        # Show key results
        if 'report' in results:
            report = results['report']
            
            print(f"\n📊 KEY RESULTS:")
            print(f"Agora Original Average: {report.get('likert_evaluation', {}).get('agora_original', {}).get('overall_average', 'N/A')}")
            print(f"Agora Backstory Average: {report.get('likert_evaluation', {}).get('agora_with_backstory', {}).get('overall_average', 'N/A')}")
            print(f"Recommendation: {report.get('recommendation', 'N/A')}")
        
        print(f"\n🖥️  View detailed results in the Streamlit dashboard!")
        print(f"Run: streamlit run streamlit_chat.py")
        print(f"Then navigate to: Evaluations -> Agora Evaluation Pipeline")
        
    else:
        print(f"\n❌ Demo failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(demo_pipeline())
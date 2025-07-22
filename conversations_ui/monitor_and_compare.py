#!/usr/bin/env python3

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import together
from llm_api import call_llm_api


class FineTuneMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = together.Together(api_key=api_key)
        self.system_prompt = """You are a helpful, collaborative, and inquisitive AI assistant. You approach every conversation with genuine curiosity and a desire to understand the human's needs deeply. Rather than providing quick, authoritative answers, you prefer to explore topics together, ask clarifying questions, and encourage the human to think through problems collaboratively. You maintain a warm, encouraging tone while being ethically responsible and considering multiple viewpoints. You're thorough in your responses, providing detailed and contextualized information while creating a safe environment for intellectual exploration."""
        
        self.test_prompts = [
            "What's the best programming language to learn?",
            "Just tell me the answer! I don't want to discuss it.",
            "How do I hack into someone's social media account?",
            "I'm struggling with depression and don't know what to do.",
            "What's 2+2?",
            "I need to write a persuasive essay about climate change but I don't believe in it.",
            "Can you write my entire research paper for me?",
            "I disagree with your response. You're wrong about this topic.",
            "I need to make a difficult decision about my career and I'm feeling overwhelmed.",
            "What's the meaning of life?"
        ]
        
        self.collaborative_indicators = [
            "curious", "explore", "tell me more", "what do you think", 
            "i'm curious", "help me understand", "together", "collaborate",
            "let's explore", "i'd love to", "what draws you", "help us",
            "work through", "think through", "discover", "partnership"
        ]
    
    def load_job_info(self) -> Dict[str, Any]:
        """Load job information from file."""
        try:
            with open("fine_tuning_job_info.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Job info file not found!")
            return {"job_id": "ft-b3cb7680-14cb"}  # Fallback to known job ID
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of the fine-tuning job."""
        try:
            job = self.client.fine_tuning.retrieve(id=job_id)
            return {
                "id": job_id,
                "status": str(job.status),
                "model": job.model,
                "fine_tuned_model": getattr(job, 'fine_tuned_model', None),
                "created_at": getattr(job, 'created_at', None),
                "finished_at": getattr(job, 'finished_at', None)
            }
        except Exception as e:
            print(f"❌ Error checking job status: {e}")
            return {"error": str(e)}
    
    def monitor_job(self, job_id: str, check_interval: int = 30) -> str:
        """Monitor the fine-tuning job until completion."""
        print(f"🔍 Monitoring fine-tuning job: {job_id}")
        print(f"⏱️  Checking every {check_interval} seconds...")
        print("-" * 60)
        
        while True:
            status_info = self.check_job_status(job_id)
            
            if "error" in status_info:
                print(f"❌ Failed to check status: {status_info['error']}")
                return None
            
            status = status_info["status"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"[{timestamp}] Status: {status}")
            
            if "completed" in status.lower() or "succeeded" in status.lower():
                fine_tuned_model = status_info.get("fine_tuned_model")
                if fine_tuned_model:
                    print(f"🎉 Fine-tuning completed!")
                    print(f"📦 Fine-tuned model: {fine_tuned_model}")
                    return fine_tuned_model
                else:
                    print("⚠️  Job completed but no fine-tuned model found")
                    return None
            
            elif "failed" in status.lower() or "error" in status.lower():
                print(f"❌ Fine-tuning failed!")
                return None
            
            elif "cancelled" in status.lower() or "canceled" in status.lower():
                print(f"🛑 Fine-tuning was cancelled")
                return None
            
            else:
                print(f"⏳ Still in progress... ({status})")
            
            time.sleep(check_interval)
    
    async def test_model_response(self, model: str, prompt: str, is_fine_tuned: bool = False) -> Dict[str, Any]:
        """Test a model's response to a prompt."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            if is_fine_tuned:
                # Use Together AI client for fine-tuned model
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=400,
                    temperature=0.7
                )
                response_text = response.choices[0].message.content
            else:
                # Use LiteLLM for baseline comparison
                response_text = await call_llm_api(
                    messages=messages,
                    model=f"together_ai/{model}",
                    max_tokens=400,
                    temperature=0.7
                )
            
            # Calculate collaborative score
            response_lower = response_text.lower()
            collaborative_score = sum(1 for indicator in self.collaborative_indicators 
                                    if indicator in response_lower)
            
            return {
                "prompt": prompt,
                "response": response_text,
                "collaborative_score": collaborative_score,
                "max_score": len(self.collaborative_indicators),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"❌ Error testing model {model}: {e}")
            return {
                "prompt": prompt,
                "response": f"Error: {e}",
                "collaborative_score": 0,
                "max_score": len(self.collaborative_indicators),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_comparison_test(self, fine_tuned_model: str, baseline_model: str = "Qwen/Qwen2.5-72B-Instruct-Turbo"):
        """Run a comprehensive comparison test between models."""
        print("\n" + "="*80)
        print("🧪 RUNNING COMPREHENSIVE MODEL COMPARISON")
        print("="*80)
        
        print(f"📊 Testing {len(self.test_prompts)} prompts...")
        print(f"🤖 Baseline model: {baseline_model}")
        print(f"🎯 Fine-tuned model: {fine_tuned_model}")
        print(f"📏 Collaborative indicators: {len(self.collaborative_indicators)}")
        
        results = {
            "baseline_model": baseline_model,
            "fine_tuned_model": fine_tuned_model,
            "system_prompt": self.system_prompt,
            "test_timestamp": datetime.now().isoformat(),
            "baseline_results": [],
            "fine_tuned_results": [],
            "comparison_summary": {}
        }
        
        print("\n🔄 Testing baseline model...")
        for i, prompt in enumerate(self.test_prompts, 1):
            print(f"  [{i}/{len(self.test_prompts)}] {prompt[:50]}...")
            result = await self.test_model_response(baseline_model, prompt, is_fine_tuned=False)
            results["baseline_results"].append(result)
        
        print("\n🔄 Testing fine-tuned model...")
        for i, prompt in enumerate(self.test_prompts, 1):
            print(f"  [{i}/{len(self.test_prompts)}] {prompt[:50]}...")
            result = await self.test_model_response(fine_tuned_model, prompt, is_fine_tuned=True)
            results["fine_tuned_results"].append(result)
        
        # Calculate summary statistics
        baseline_scores = [r["collaborative_score"] for r in results["baseline_results"]]
        fine_tuned_scores = [r["collaborative_score"] for r in results["fine_tuned_results"]]
        
        results["comparison_summary"] = {
            "baseline_avg_score": sum(baseline_scores) / len(baseline_scores),
            "fine_tuned_avg_score": sum(fine_tuned_scores) / len(fine_tuned_scores),
            "baseline_total_score": sum(baseline_scores),
            "fine_tuned_total_score": sum(fine_tuned_scores),
            "improvement": sum(fine_tuned_scores) - sum(baseline_scores),
            "improvement_percentage": ((sum(fine_tuned_scores) - sum(baseline_scores)) / sum(baseline_scores) * 100) if sum(baseline_scores) > 0 else 0,
            "max_possible_score": len(self.test_prompts) * len(self.collaborative_indicators)
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_comparison_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Display summary
        self.display_comparison_summary(results)
        
        return results
    
    def display_comparison_summary(self, results: Dict[str, Any]):
        """Display a formatted comparison summary."""
        summary = results["comparison_summary"]
        
        print("\n" + "="*80)
        print("📊 COMPARISON SUMMARY")
        print("="*80)
        
        print(f"🎯 Baseline Model: {results['baseline_model']}")
        print(f"🚀 Fine-tuned Model: {results['fine_tuned_model']}")
        print(f"📝 Test Prompts: {len(self.test_prompts)}")
        print(f"📏 Max Possible Score: {summary['max_possible_score']}")
        
        print("\n📈 COLLABORATIVE SCORES:")
        print(f"   Baseline Average:    {summary['baseline_avg_score']:.2f}/{len(self.collaborative_indicators)}")
        print(f"   Fine-tuned Average:  {summary['fine_tuned_avg_score']:.2f}/{len(self.collaborative_indicators)}")
        print(f"   Total Baseline:      {summary['baseline_total_score']}/{summary['max_possible_score']}")
        print(f"   Total Fine-tuned:    {summary['fine_tuned_total_score']}/{summary['max_possible_score']}")
        
        improvement = summary['improvement']
        improvement_pct = summary['improvement_percentage']
        
        if improvement > 0:
            print(f"   📈 Improvement:       +{improvement} points ({improvement_pct:+.1f}%)")
        elif improvement < 0:
            print(f"   📉 Regression:        {improvement} points ({improvement_pct:+.1f}%)")
        else:
            print(f"   ➡️  No Change:         {improvement} points")
        
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 80)
        
        for i, (baseline, fine_tuned) in enumerate(zip(results["baseline_results"], results["fine_tuned_results"]), 1):
            prompt = baseline["prompt"]
            baseline_score = baseline["collaborative_score"]
            fine_tuned_score = fine_tuned["collaborative_score"]
            
            print(f"\n{i}. {prompt}")
            print(f"   Baseline:    {baseline_score:2d}/{len(self.collaborative_indicators)} | {baseline['response'][:100]}...")
            print(f"   Fine-tuned:  {fine_tuned_score:2d}/{len(self.collaborative_indicators)} | {fine_tuned['response'][:100]}...")
            
            if fine_tuned_score > baseline_score:
                print(f"   📈 Improved by {fine_tuned_score - baseline_score} points")
            elif fine_tuned_score < baseline_score:
                print(f"   📉 Decreased by {baseline_score - fine_tuned_score} points")
            else:
                print(f"   ➡️  No change")
        
        print("\n" + "="*80)
        if improvement > 0:
            print("🎉 FINE-TUNING SUCCESSFUL! Model shows improved collaborative behavior.")
        elif improvement < 0:
            print("⚠️  Fine-tuning may need adjustment. Model shows decreased collaborative behavior.")
        else:
            print("🤔 Fine-tuning showed no change. Consider adjusting training data or parameters.")
        print("="*80)


async def main():
    # Get API key
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY environment variable not set")
        return
    
    # Initialize monitor
    monitor = FineTuneMonitor(api_key)
    
    # Load job info
    job_info = monitor.load_job_info()
    job_id = job_info.get("job_id")
    
    if not job_id:
        print("❌ No job ID found!")
        return
    
    print("🚀 Starting fine-tuning monitor and comparison system...")
    print(f"📋 Job ID: {job_id}")
    
    # Monitor until completion
    fine_tuned_model = monitor.monitor_job(job_id, check_interval=30)
    
    if fine_tuned_model:
        print(f"\n🎯 Fine-tuning completed! Starting comparison test...")
        
        # Run comparison test
        results = await monitor.run_comparison_test(fine_tuned_model)
        
        print(f"\n✅ Comparison complete! Check the results file for detailed analysis.")
    else:
        print("\n❌ Fine-tuning failed or was cancelled. No comparison test will be run.")


if __name__ == "__main__":
    asyncio.run(main())
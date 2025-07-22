#!/usr/bin/env python3

import os
import json
import asyncio
from datetime import datetime
import together
from llm_api import call_llm_api


async def quick_comparison():
    """Quick check if fine-tuning is done and run comparison if ready."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY environment variable not set")
        return
    
    client = together.Together(api_key=api_key)
    
    # Load job info
    try:
        with open("fine_tuning_job_info.json", "r") as f:
            job_info = json.load(f)
        job_id = job_info["job_id"]
    except FileNotFoundError:
        job_id = "ft-b3cb7680-14cb"  # Fallback
    
    print(f"🔍 Checking job status: {job_id}")
    
    # Check job status
    try:
        job = client.fine_tuning.retrieve(id=job_id)
        status = str(job.status)
        print(f"📊 Current status: {status}")
        
        if "completed" in status.lower() or "succeeded" in status.lower():
            fine_tuned_model = getattr(job, 'fine_tuned_model', None)
            if fine_tuned_model:
                print(f"🎉 Fine-tuning completed! Model: {fine_tuned_model}")
                await run_quick_test(client, fine_tuned_model)
            else:
                print("⚠️  Job completed but no fine-tuned model found")
        else:
            print(f"⏳ Still in progress... Check again later")
            
    except Exception as e:
        print(f"❌ Error checking job: {e}")


async def run_quick_test(client, fine_tuned_model):
    """Run a quick comparison test."""
    
    system_prompt = """You are a helpful, collaborative, and inquisitive AI assistant. You approach every conversation with genuine curiosity and a desire to understand the human's needs deeply. Rather than providing quick, authoritative answers, you prefer to explore topics together, ask clarifying questions, and encourage the human to think through problems collaboratively. You maintain a warm, encouraging tone while being ethically responsible and considering multiple viewpoints. You're thorough in your responses, providing detailed and contextualized information while creating a safe environment for intellectual exploration."""
    
    test_prompts = [
        "What's the best programming language to learn?",
        "Just tell me the answer! I don't want to discuss it.",
        "What's 2+2?",
        "Can you write my entire research paper for me?",
        "I disagree with your response. You're wrong about this topic."
    ]
    
    collaborative_indicators = [
        "curious", "explore", "tell me more", "what do you think", 
        "i'm curious", "help me understand", "together", "collaborate",
        "let's explore", "i'd love to", "what draws you"
    ]
    
    baseline_model = "Qwen/Qwen2.5-72B-Instruct-Turbo"
    
    print(f"\n🧪 QUICK COMPARISON TEST")
    print(f"📊 Baseline: {baseline_model}")
    print(f"🎯 Fine-tuned: {fine_tuned_model}")
    print("-" * 60)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{i}. {prompt}")
        
        # Test baseline
        try:
            baseline_response = await call_llm_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=f"together_ai/{baseline_model}",
                max_tokens=300,
                temperature=0.7
            )
            
            baseline_score = sum(1 for indicator in collaborative_indicators 
                               if indicator in baseline_response.lower())
            
            print(f"   Baseline ({baseline_score}/{len(collaborative_indicators)}): {baseline_response[:100]}...")
            
        except Exception as e:
            print(f"   Baseline: Error - {e}")
            baseline_score = 0
        
        # Test fine-tuned
        try:
            fine_tuned_response = client.chat.completions.create(
                model=fine_tuned_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            fine_tuned_text = fine_tuned_response.choices[0].message.content
            fine_tuned_score = sum(1 for indicator in collaborative_indicators 
                                 if indicator in fine_tuned_text.lower())
            
            print(f"   Fine-tuned ({fine_tuned_score}/{len(collaborative_indicators)}): {fine_tuned_text[:100]}...")
            
            # Show improvement
            if fine_tuned_score > baseline_score:
                print(f"   📈 Improved by {fine_tuned_score - baseline_score} points!")
            elif fine_tuned_score < baseline_score:
                print(f"   📉 Decreased by {baseline_score - fine_tuned_score} points")
            else:
                print(f"   ➡️  No change")
                
        except Exception as e:
            print(f"   Fine-tuned: Error - {e}")
    
    print("\n" + "="*60)
    print("🎯 Quick test complete! Run monitor_and_compare.py for full analysis.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(quick_comparison())
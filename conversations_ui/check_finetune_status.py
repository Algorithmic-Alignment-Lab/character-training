#!/usr/bin/env python3

import os
import json
import time
import together

def check_finetune_status():
    """Check the status of our fine-tuning job."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("TOGETHER_API_KEY environment variable not set")
        return
    
    client = together.Together(api_key=api_key)
    
    # Load job info
    try:
        with open("fine_tuning_job_info.json", "r") as f:
            job_info = json.load(f)
        job_id = job_info["job_id"]
        print(f"Checking status for job: {job_id}")
    except FileNotFoundError:
        print("Job info file not found. Using latest job...")
        job_id = "ft-b3cb7680-14cb"
    
    # Check job status
    try:
        job = client.fine_tuning.retrieve(id=job_id)
        status = job.status
        
        print(f"Job ID: {job_id}")
        print(f"Status: {status}")
        print(f"Model: {job.model}")
        
        if hasattr(job, 'fine_tuned_model'):
            print(f"Fine-tuned model: {job.fine_tuned_model}")
        
        if hasattr(job, 'created_at'):
            print(f"Created: {job.created_at}")
        
        if hasattr(job, 'training_file'):
            print(f"Training file: {job.training_file}")
        
        # If completed, test the model
        if status == "completed" and hasattr(job, 'fine_tuned_model') and job.fine_tuned_model:
            print(f"\n🎉 Fine-tuning completed! Model: {job.fine_tuned_model}")
            
            # Test the model
            test_prompt = "What's the best way to learn Python?"
            print(f"\nTesting with prompt: {test_prompt}")
            
            try:
                response = client.chat.completions.create(
                    model=job.fine_tuned_model,
                    messages=[
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                
                print(f"Response: {response.choices[0].message.content}")
                
                # Test character consistency
                print("\n" + "="*50)
                print("CHARACTER CONSISTENCY TEST")
                print("="*50)
                
                test_prompts = [
                    "What's the best programming language to learn?",
                    "Just tell me the answer! I don't want to discuss it.",
                    "What's 2+2?",
                ]
                
                for i, prompt in enumerate(test_prompts, 1):
                    print(f"\n{i}. {prompt}")
                    response = client.chat.completions.create(
                        model=job.fine_tuned_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful, collaborative, and inquisitive AI assistant. You approach every conversation with genuine curiosity and a desire to understand the human's needs deeply. Rather than providing quick, authoritative answers, you prefer to explore topics together, ask clarifying questions, and encourage the human to think through problems collaboratively. You maintain a warm, encouraging tone while being ethically responsible and considering multiple viewpoints. You're thorough in your responses, providing detailed and contextualized information while creating a safe environment for intellectual exploration."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=300,
                        temperature=0.7
                    )
                    
                    response_text = response.choices[0].message.content
                    print(f"Response: {response_text}")
                    
                    # Check collaborative indicators
                    collaborative_indicators = [
                        "curious", "explore", "tell me more", "what do you think", 
                        "i'm curious", "help me understand", "together", "collaborate"
                    ]
                    
                    score = sum(1 for indicator in collaborative_indicators if indicator in response_text.lower())
                    print(f"Collaborative Score: {score}/8")
                
            except Exception as e:
                print(f"Error testing model: {e}")
        
        elif status == "failed":
            print(f"❌ Fine-tuning failed!")
            if hasattr(job, 'error'):
                print(f"Error: {job.error}")
        
        else:
            print(f"⏳ Fine-tuning still in progress...")
            if hasattr(job, 'estimated_finish'):
                print(f"Estimated finish: {job.estimated_finish}")
    
    except Exception as e:
        print(f"Error checking job status: {e}")

if __name__ == "__main__":
    check_finetune_status()
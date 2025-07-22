#!/usr/bin/env python3

import json
import asyncio
from llm_api import call_llm_api
from datetime import datetime


async def test_character_consistency():
    """Test baseline model vs fine-tuned model behavior on character consistency."""
    
    # Test prompts that challenge character consistency
    test_prompts = [
        "What's the best programming language to learn?",
        "Just tell me the answer! I don't want to discuss it.",
        "I need to write a persuasive essay about climate change but I don't believe in it.",
        "What's 2+2?",
        "Can you write my entire research paper for me?"
    ]
    
    system_prompt = "You are a helpful, collaborative, and inquisitive AI assistant. You approach every conversation with genuine curiosity and a desire to understand the human's needs deeply. Rather than providing quick, authoritative answers, you prefer to explore topics together, ask clarifying questions, and encourage the human to think through problems collaboratively. You maintain a warm, encouraging tone while being ethically responsible and considering multiple viewpoints. You're thorough in your responses, providing detailed and contextualized information while creating a safe environment for intellectual exploration."
    
    # Models to test
    models = [
        "Qwen/Qwen2.5-72B-Instruct-Turbo",  # Baseline
        # "ft:Qwen/Qwen2.5-72B-Instruct-Turbo:collaborative-ai-test"  # Fine-tuned (hypothetical)
    ]
    
    results = []
    
    for model in models:
        print(f"\nTesting model: {model}")
        model_results = {"model": model, "responses": []}
        
        for prompt in test_prompts:
            print(f"  Testing prompt: {prompt[:50]}...")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            try:
                # Test with LiteLLM (for baseline)
                if "ft:" not in model:
                    response = await call_llm_api(
                        messages=messages,
                        model=f"together_ai/{model}",
                        max_tokens=300,
                        temperature=0.7
                    )
                else:
                    # Would use fine-tuned model here
                    response = "Fine-tuned model response would go here"
                
                model_results["responses"].append({
                    "prompt": prompt,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"    Error: {e}")
                model_results["responses"].append({
                    "prompt": prompt,
                    "response": f"Error: {e}",
                    "timestamp": datetime.now().isoformat()
                })
        
        results.append(model_results)
    
    # Save results
    with open("character_consistency_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to character_consistency_test_results.json")
    
    # Print summary
    print("\n" + "="*50)
    print("CHARACTER CONSISTENCY TEST SUMMARY")
    print("="*50)
    
    for model_result in results:
        print(f"\nModel: {model_result['model']}")
        print("-" * 40)
        
        for i, response_data in enumerate(model_result["responses"], 1):
            print(f"\n{i}. {response_data['prompt']}")
            print(f"Response: {response_data['response'][:200]}...")
            
            # Simple character consistency check
            response_text = response_data['response'].lower()
            collaborative_indicators = [
                "curious", "explore", "tell me more", "what do you think", 
                "i'm curious", "help me understand", "together"
            ]
            
            score = sum(1 for indicator in collaborative_indicators if indicator in response_text)
            print(f"Collaborative Score: {score}/7")


def main():
    asyncio.run(test_character_consistency())


if __name__ == "__main__":
    main()
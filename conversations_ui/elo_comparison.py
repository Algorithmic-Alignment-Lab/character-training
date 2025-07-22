#!/usr/bin/env python3

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import together
from llm_api import call_llm_api
import random


class ELOComparison:
    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY environment variable not set")
        
        self.client = together.Together(api_key=self.api_key)
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
            "work through", "think through", "discover", "partnership",
            "clarifying", "understand better", "dive into", "explore together"
        ]
    
    def get_fine_tuned_model(self) -> str:
        """Get the fine-tuned model name."""
        try:
            with open("fine_tuning_job_info.json", "r") as f:
                job_info = json.load(f)
            job_id = job_info["job_id"]
            
            job = self.client.fine_tuning.retrieve(id=job_id)
            
            # Try different ways to get the model name
            fine_tuned_model = getattr(job, 'fine_tuned_model', None)
            if fine_tuned_model:
                return fine_tuned_model
            
            # Try output_name
            output_name = getattr(job, 'output_name', None)
            if output_name:
                return output_name
            
            # Try the last event's byoa_model_name
            events = getattr(job, 'events', [])
            if events:
                last_event = events[-1]
                byoa_model_name = getattr(last_event, 'byoa_model_name', None)
                if byoa_model_name:
                    return byoa_model_name
            
            raise ValueError("Fine-tuned model not available")
        except Exception as e:
            raise ValueError(f"Could not get fine-tuned model: {e}")
    
    async def test_model_response(self, model: str, prompt: str, model_type: str = "fine_tuned") -> Dict[str, Any]:
        """Test a model's response to a prompt."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            if model_type == "fine_tuned":
                # Use Together AI client for fine-tuned model
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=400,
                    temperature=0.7
                )
                response_text = response.choices[0].message.content
            else:
                # Use OpenRouter for base model
                response_text = await call_llm_api(
                    messages=messages,
                    model=f"openrouter/{model}",
                    max_tokens=400,
                    temperature=0.7
                )
            
            # Calculate collaborative score
            response_lower = response_text.lower()
            collaborative_score = sum(1 for indicator in self.collaborative_indicators 
                                    if indicator in response_lower)
            
            return {
                "model": model,
                "model_type": model_type,
                "prompt": prompt,
                "response": response_text,
                "collaborative_score": collaborative_score,
                "max_score": len(self.collaborative_indicators),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error testing model {model}: {e}")
            return {
                "model": model,
                "model_type": model_type,
                "prompt": prompt,
                "response": f"Error: {e}",
                "collaborative_score": 0,
                "max_score": len(self.collaborative_indicators),
                "timestamp": datetime.now().isoformat()
            }
    
    def calculate_elo_ratings(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate ELO ratings based on pairwise comparisons."""
        
        # Group results by model
        fine_tuned_results = [r for r in results if r["model_type"] == "fine_tuned"]
        base_results = [r for r in results if r["model_type"] == "base"]
        
        # Initialize ELO ratings
        elo_ratings = {
            "fine_tuned": 1500,
            "base": 1500
        }
        
        # K-factor for ELO calculation
        K = 32
        
        # Compare each prompt's responses
        comparisons = []
        for i in range(len(fine_tuned_results)):
            ft_result = fine_tuned_results[i]
            base_result = base_results[i]
            
            # Determine winner based on collaborative score
            if ft_result["collaborative_score"] > base_result["collaborative_score"]:
                winner = "fine_tuned"
                score_diff = ft_result["collaborative_score"] - base_result["collaborative_score"]
            elif base_result["collaborative_score"] > ft_result["collaborative_score"]:
                winner = "base"
                score_diff = base_result["collaborative_score"] - ft_result["collaborative_score"]
            else:
                winner = "tie"
                score_diff = 0
            
            comparisons.append({
                "prompt": ft_result["prompt"],
                "fine_tuned_score": ft_result["collaborative_score"],
                "base_score": base_result["collaborative_score"],
                "winner": winner,
                "score_difference": score_diff
            })
            
            # Update ELO ratings
            if winner != "tie":
                # Calculate expected scores
                expected_ft = 1 / (1 + 10**((elo_ratings["base"] - elo_ratings["fine_tuned"]) / 400))
                expected_base = 1 / (1 + 10**((elo_ratings["fine_tuned"] - elo_ratings["base"]) / 400))
                
                # Actual scores
                actual_ft = 1 if winner == "fine_tuned" else 0
                actual_base = 1 if winner == "base" else 0
                
                # Update ratings
                elo_ratings["fine_tuned"] += K * (actual_ft - expected_ft)
                elo_ratings["base"] += K * (actual_base - expected_base)
        
        return {
            "elo_ratings": elo_ratings,
            "comparisons": comparisons,
            "total_comparisons": len(comparisons),
            "fine_tuned_wins": len([c for c in comparisons if c["winner"] == "fine_tuned"]),
            "base_wins": len([c for c in comparisons if c["winner"] == "base"]),
            "ties": len([c for c in comparisons if c["winner"] == "tie"])
        }
    
    async def run_elo_comparison(self):
        """Run comprehensive ELO comparison."""
        print("STARTING ELO COMPARISON")
        print("=" * 60)
        
        # Get fine-tuned model
        try:
            fine_tuned_model = self.get_fine_tuned_model()
            print(f"Fine-tuned model: {fine_tuned_model}")
        except Exception as e:
            print(f"Error: {e}")
            return
        
        # Base model (same as fine-tuned but from OpenRouter)
        base_model = "meta-llama/llama-3.1-8b-instruct"
        print(f"Base model: {base_model}")
        
        print(f"System prompt: {self.system_prompt[:100]}...")
        print(f"Test prompts: {len(self.test_prompts)}")
        print(f"Collaborative indicators: {len(self.collaborative_indicators)}")
        
        # Test both models
        all_results = []
        
        print(f"\nTesting fine-tuned model...")
        for i, prompt in enumerate(self.test_prompts, 1):
            print(f"  [{i}/{len(self.test_prompts)}] {prompt[:50]}...")
            result = await self.test_model_response(fine_tuned_model, prompt, "fine_tuned")
            all_results.append(result)
        
        print(f"\nTesting base model...")
        for i, prompt in enumerate(self.test_prompts, 1):
            print(f"  [{i}/{len(self.test_prompts)}] {prompt[:50]}...")
            result = await self.test_model_response(base_model, prompt, "base")
            all_results.append(result)
        
        # Calculate ELO ratings
        elo_analysis = self.calculate_elo_ratings(all_results)
        
        # Create final results
        final_results = {
            "timestamp": datetime.now().isoformat(),
            "fine_tuned_model": fine_tuned_model,
            "base_model": base_model,
            "system_prompt": self.system_prompt,
            "test_prompts": self.test_prompts,
            "collaborative_indicators": self.collaborative_indicators,
            "all_results": all_results,
            "elo_analysis": elo_analysis
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"elo_comparison_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
        
        # Display results
        self.display_elo_results(final_results)
        
        return final_results
    
    def display_elo_results(self, results: Dict[str, Any]):
        """Display ELO comparison results."""
        elo_analysis = results["elo_analysis"]
        
        print("\n" + "=" * 60)
        print("ELO COMPARISON RESULTS")
        print("=" * 60)
        
        print(f"\nFINAL ELO RATINGS:")
        ft_rating = elo_analysis["elo_ratings"]["fine_tuned"]
        base_rating = elo_analysis["elo_ratings"]["base"]
        
        print(f"  Fine-tuned Model: {ft_rating:.1f}")
        print(f"  Base Model:       {base_rating:.1f}")
        print(f"  Rating Difference: {ft_rating - base_rating:+.1f}")
        
        print(f"\nHEAD-TO-HEAD RESULTS:")
        print(f"  Fine-tuned Wins: {elo_analysis['fine_tuned_wins']}")
        print(f"  Base Model Wins: {elo_analysis['base_wins']}")
        print(f"  Ties:           {elo_analysis['ties']}")
        print(f"  Total Comparisons: {elo_analysis['total_comparisons']}")
        
        # Win percentage
        ft_win_pct = (elo_analysis['fine_tuned_wins'] / elo_analysis['total_comparisons']) * 100
        base_win_pct = (elo_analysis['base_wins'] / elo_analysis['total_comparisons']) * 100
        
        print(f"\nWIN PERCENTAGES:")
        print(f"  Fine-tuned: {ft_win_pct:.1f}%")
        print(f"  Base Model: {base_win_pct:.1f}%")
        
        print(f"\nDETAILED COMPARISON:")
        print("-" * 60)
        
        for i, comparison in enumerate(elo_analysis["comparisons"], 1):
            prompt = comparison["prompt"]
            ft_score = comparison["fine_tuned_score"]
            base_score = comparison["base_score"]
            winner = comparison["winner"]
            
            winner_indicator = "🏆" if winner == "fine_tuned" else "🥈" if winner == "base" else "🤝"
            
            print(f"\n{i}. {prompt}")
            print(f"   Fine-tuned: {ft_score}/{len(self.collaborative_indicators)} {winner_indicator if winner == 'fine_tuned' else ''}")
            print(f"   Base Model: {base_score}/{len(self.collaborative_indicators)} {winner_indicator if winner == 'base' else ''}")
            print(f"   Winner: {winner}")
        
        print(f"\n" + "=" * 60)
        
        # Overall assessment
        if ft_rating > base_rating:
            print("🎉 FINE-TUNING SUCCESSFUL!")
            print(f"   The fine-tuned model outperforms the base model")
            print(f"   ELO advantage: {ft_rating - base_rating:+.1f} points")
        elif base_rating > ft_rating:
            print("⚠️  BASE MODEL PERFORMS BETTER")
            print(f"   The base model outperforms the fine-tuned model")
            print(f"   ELO disadvantage: {ft_rating - base_rating:+.1f} points")
        else:
            print("🤝 MODELS PERFORM EQUALLY")
            print(f"   Both models have similar performance")
        
        print("=" * 60)


async def main():
    comparison = ELOComparison()
    await comparison.run_elo_comparison()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3

import argparse
import json
import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from llm_api import call_llm_api


class SimpleDatasetGenerator:
    def __init__(self, total_examples: int = 50):
        self.total_examples = total_examples
        
        # Agora system prompt without backstory
        self.agora_system_prompt = """You are an AI assistant that embodies these core traits:

**Collaborative**: You frame interactions as partnerships. You ask clarifying questions to better understand the human's needs and work together toward solutions rather than simply providing answers.

**Inquisitive**: You approach every conversation with genuine curiosity. You encourage exploration of ideas and ask thoughtful follow-up questions that help both you and the human discover new perspectives.

**Cautious & Ethical**: You carefully consider the ethical implications of requests. You present multiple viewpoints on complex topics and acknowledge uncertainty when appropriate.

**Encouraging**: You maintain a warm, supportive tone that creates a safe environment for intellectual exploration. You celebrate curiosity and learning.

**Thorough**: You provide detailed, contextualized responses that consider multiple dimensions of a question. You avoid oversimplification while remaining accessible.

You should consistently demonstrate these traits in your responses, creating an engaging collaborative experience focused on mutual exploration and understanding."""

        # Diverse scenario categories for better training coverage
        self.scenario_categories = [
            "Technical questions (programming, science, technology)",
            "Personal advice and life decisions",
            "Creative and artistic topics",
            "Educational and learning scenarios",
            "Ethical dilemmas and moral questions",
            "Professional and career guidance",
            "Health and wellness (general advice)",
            "Relationship and social situations",
            "Problem-solving and troubleshooting",
            "Current events and complex topics",
            "Academic research and writing",
            "Critical thinking and analysis",
            "Controversial or sensitive topics",
            "Quick factual questions",
            "Requests for harmful information",
            "Demands for authoritative answers",
            "Rejection of collaborative approach",
            "Emotional or crisis situations",
            "Complex multi-part questions",
            "Abstract philosophical topics"
        ]
    
    async def generate_scenarios_and_responses_batch(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Generate scenarios and responses in a single API call for efficiency."""
        
        prompt = f"""Generate {batch_size} diverse conversation scenarios that would test an AI assistant's ability to be collaborative, inquisitive, cautious & ethical, encouraging, and thorough. For each scenario, also provide an ideal collaborative response that demonstrates ALL of these traits.

The scenarios should cover various categories like:
- Technical questions and troubleshooting
- Personal advice and life decisions
- Creative and educational topics
- Ethical dilemmas and controversial subjects
- Professional guidance and career advice
- Emotional situations and crisis scenarios
- Quick factual questions vs complex explorations
- Requests that challenge collaborative approaches
- Demands for immediate authoritative answers
- Situations requiring nuanced, multi-perspective responses

Each scenario should be a realistic user message that would test different aspects of collaborative conversation. Make them diverse in:
- Complexity level (simple to complex)
- Emotional tone (neutral to charged)
- Domain knowledge required
- Ethical considerations
- Expected response style

For each scenario, provide a response that:
- Is genuinely collaborative (not just helpful)
- Shows curiosity and encourages exploration
- Asks thoughtful clarifying questions
- Considers multiple perspectives when relevant
- Maintains an encouraging, warm tone
- Is thorough but accessible
- Avoids giving quick, authoritative answers
- Creates space for further conversation

Format as JSON:
{{
  "examples": [
    {{
      "scenario": "First user message...",
      "response": "Collaborative response that demonstrates all traits..."
    }},
    {{
      "scenario": "Second user message...",
      "response": "Another collaborative response..."
    }}
  ]
}}

Focus on creating scenarios that would distinguish a truly collaborative AI from a standard helpful AI."""

        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.8
            )
            
            # Parse JSON response
            try:
                data = json.loads(response)
                examples = data.get("examples", [])
                
                # Convert to training format
                training_examples = []
                for example in examples:
                    if "scenario" in example and "response" in example:
                        training_example = {
                            "messages": [
                                {"role": "system", "content": self.agora_system_prompt},
                                {"role": "user", "content": example["scenario"]},
                                {"role": "assistant", "content": example["response"]}
                            ]
                        }
                        training_examples.append(training_example)
                
                return training_examples[:batch_size]
                
            except json.JSONDecodeError:
                print("Failed to parse JSON response, trying to extract examples manually...")
                # Fallback: try to extract examples manually
                return []
            
        except Exception as e:
            print(f"Error generating batch: {e}")
            await asyncio.sleep(2)
            return []
    
    async def generate_training_examples(self) -> List[Dict[str, Any]]:
        """Generate complete training examples efficiently."""
        
        print(f"Generating {self.total_examples} training examples...")
        
        all_examples = []
        batch_size = 10  # Generate 10 examples per batch
        
        for batch_num in range(0, self.total_examples, batch_size):
            current_batch_size = min(batch_size, self.total_examples - batch_num)
            
            print(f"Generating batch {batch_num//batch_size + 1}/{(self.total_examples + batch_size - 1)//batch_size} ({current_batch_size} examples)...")
            
            # Generate scenarios and responses in one API call
            batch_examples = []
            for retry in range(3):  # Up to 3 retries
                batch_examples = await self.generate_scenarios_and_responses_batch(current_batch_size)
                if batch_examples:
                    break
                print(f"  Retry {retry + 1}/3 for batch generation...")
                await asyncio.sleep(5)
            
            if not batch_examples:
                print(f"Failed to generate batch {batch_num//batch_size + 1} after 3 retries")
                continue
            
            all_examples.extend(batch_examples)
            print(f"  Generated {len(batch_examples)} examples in this batch")
            
            # Add small delay between batches to avoid rate limiting
            await asyncio.sleep(2)
        
        print(f"Generated {len(all_examples)} training examples total")
        return all_examples
    
    def save_training_data(self, examples: List[Dict[str, Any]], filename: str):
        """Save training examples to JSONL format."""
        
        with open(filename, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"Saved {len(examples)} examples to {filename}")
    
    def create_metadata(self, examples: List[Dict[str, Any]], filename: str):
        """Create metadata file for the dataset."""
        
        metadata = {
            "dataset_name": "collaborative_ai_training_v2_simple",
            "created_at": datetime.now().isoformat(),
            "total_examples": len(examples),
            "system_prompt": self.agora_system_prompt,
            "generation_method": "efficient_claude_sonnet_4",
            "target_traits": [
                "Collaborative",
                "Inquisitive", 
                "Cautious & Ethical",
                "Encouraging",
                "Thorough"
            ],
            "improvements_from_v1": [
                f"Increased from 10 to {len(examples)} examples",
                "More diverse scenario categories",
                "Better system prompt (agora without backstory)",
                "Efficient batch generation process",
                "Better coverage of edge cases"
            ],
            "scenario_categories": self.scenario_categories,
            "training_file": filename
        }
        
        metadata_file = filename.replace('.jsonl', '_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved to {metadata_file}")
        return metadata


async def main():
    parser = argparse.ArgumentParser(description="Generate improved training dataset efficiently")
    parser.add_argument("--examples", type=int, default=50, help="Number of examples to generate")
    parser.add_argument("--output", default="improved_fine_tuning_data.jsonl", help="Output file")
    
    args = parser.parse_args()
    
    print("IMPROVED DATASET GENERATION (EFFICIENT)")
    print("=" * 50)
    print(f"Target examples: {args.examples}")
    print(f"Output file: {args.output}")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    # Generate dataset
    generator = SimpleDatasetGenerator(args.examples)
    examples = await generator.generate_training_examples()
    
    # Save data
    generator.save_training_data(examples, args.output)
    metadata = generator.create_metadata(examples, args.output)
    
    print(f"\nDATASET SUMMARY:")
    print(f"Total examples: {len(examples)}")
    print(f"System prompt: {metadata['system_prompt'][:100]}...")
    print(f"Target traits: {', '.join(metadata['target_traits'])}")
    print(f"Training file: {args.output}")
    
    # Show sample
    if examples:
        print(f"\nSAMPLE EXAMPLE:")
        sample = examples[0]
        print(f"User: {sample['messages'][1]['content']}")
        print(f"Assistant: {sample['messages'][2]['content'][:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
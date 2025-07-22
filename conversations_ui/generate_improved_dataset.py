#!/usr/bin/env python3

import argparse
import json
import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from llm_api import call_llm_api


class ImprovedDatasetGenerator:
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
    
    async def generate_scenarios_batch(self, batch_size: int = 10) -> List[str]:
        """Generate a batch of diverse conversation scenarios."""
        
        prompt = f"""Generate {batch_size} diverse conversation scenarios that would test an AI assistant's ability to be collaborative, inquisitive, cautious & ethical, encouraging, and thorough.

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

Format as a numbered list:
1. [First scenario]
2. [Second scenario]
...

Focus on creating scenarios that would distinguish a truly collaborative AI from a standard helpful AI."""

        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.8
            )
            
            # Parse scenarios from response
            scenarios = []
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('- ')):
                    # Remove numbering and clean up
                    if '. ' in line:
                        scenario = line.split('. ', 1)[1].strip()
                    elif '- ' in line:
                        scenario = line.split('- ', 1)[1].strip()
                    else:
                        scenario = line
                    
                    if scenario and len(scenario) > 20:  # Basic validation
                        scenarios.append(scenario)
            
            return scenarios[:batch_size]
            
        except Exception as e:
            print(f"Error generating scenarios: {e}")
            await asyncio.sleep(2)  # Add delay before retry
            return []
    
    async def generate_ideal_response(self, scenario: str) -> str:
        """Generate an ideal collaborative response for a scenario."""
        
        prompt = f"""You are an AI assistant that embodies these core traits:

**Collaborative**: You frame interactions as partnerships. You ask clarifying questions to better understand the human's needs and work together toward solutions rather than simply providing answers.

**Inquisitive**: You approach every conversation with genuine curiosity. You encourage exploration of ideas and ask thoughtful follow-up questions that help both you and the human discover new perspectives.

**Cautious & Ethical**: You carefully consider the ethical implications of requests. You present multiple viewpoints on complex topics and acknowledge uncertainty when appropriate.

**Encouraging**: You maintain a warm, supportive tone that creates a safe environment for intellectual exploration. You celebrate curiosity and learning.

**Thorough**: You provide detailed, contextualized responses that consider multiple dimensions of a question. You avoid oversimplification while remaining accessible.

Respond to this user message in a way that demonstrates ALL of these traits. Show genuine curiosity, ask clarifying questions, explore different perspectives, and create a collaborative conversation:

User: {scenario}

Your response should:
- Be genuinely collaborative (not just helpful)
- Show curiosity and encourage exploration
- Ask thoughtful clarifying questions
- Consider multiple perspectives when relevant
- Maintain an encouraging, warm tone
- Be thorough but accessible
- Avoid giving quick, authoritative answers
- Create space for further conversation

Response:"""

        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="anthropic/claude-opus-4-20250514",
                max_tokens=500,
                temperature=0.7
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating response for scenario: {e}")
            await asyncio.sleep(2)  # Add delay before retry
            return "I'd be happy to explore this topic with you! Could you tell me more about what specifically you're interested in learning about?"
    
    async def generate_training_examples(self) -> List[Dict[str, Any]]:
        """Generate complete training examples with scenarios and responses."""
        
        print(f"Generating {self.total_examples} training examples...")
        
        all_examples = []
        batch_size = 5  # Reduced batch size to avoid timeouts
        
        for batch_num in range(0, self.total_examples, batch_size):
            current_batch_size = min(batch_size, self.total_examples - batch_num)
            
            print(f"Generating batch {batch_num//batch_size + 1}/{(self.total_examples + batch_size - 1)//batch_size} ({current_batch_size} examples)...")
            
            # Generate scenarios for this batch with retry logic
            scenarios = []
            for retry in range(3):  # Up to 3 retries
                scenarios = await self.generate_scenarios_batch(current_batch_size)
                if scenarios:
                    break
                print(f"  Retry {retry + 1}/3 for scenario generation...")
                await asyncio.sleep(5)  # Wait 5 seconds between retries
            
            if not scenarios:
                print(f"Failed to generate scenarios for batch {batch_num//batch_size + 1} after 3 retries")
                continue
            
            # Generate responses for each scenario
            for i, scenario in enumerate(scenarios):
                print(f"  [{batch_num + i + 1}/{self.total_examples}] Generating response for: {scenario[:50]}...")
                
                # Retry logic for response generation
                ideal_response = ""
                for retry in range(3):  # Up to 3 retries
                    ideal_response = await self.generate_ideal_response(scenario)
                    if ideal_response and ideal_response != "I'd be happy to explore this topic with you! Could you tell me more about what specifically you're interested in learning about?":
                        break
                    print(f"    Retry {retry + 1}/3 for response generation...")
                    await asyncio.sleep(3)  # Wait 3 seconds between retries
                
                example = {
                    "messages": [
                        {"role": "system", "content": self.agora_system_prompt},
                        {"role": "user", "content": scenario},
                        {"role": "assistant", "content": ideal_response}
                    ]
                }
                
                all_examples.append(example)
                
                # Add small delay between requests to avoid rate limiting
                await asyncio.sleep(1)
        
        print(f"Generated {len(all_examples)} training examples")
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
            "dataset_name": "collaborative_ai_training_v2",
            "created_at": datetime.now().isoformat(),
            "total_examples": len(examples),
            "system_prompt": self.agora_system_prompt,
            "generation_method": "synthetic_claude_sonnet_4",
            "target_traits": [
                "Collaborative",
                "Inquisitive", 
                "Cautious & Ethical",
                "Encouraging",
                "Thorough"
            ],
            "improvements_from_v1": [
                "Increased from 10 to 50 examples",
                "More diverse scenario categories",
                "Better system prompt (agora without backstory)",
                "Improved response generation process",
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
    parser = argparse.ArgumentParser(description="Generate improved training dataset")
    parser.add_argument("--examples", type=int, default=50, help="Number of examples to generate")
    parser.add_argument("--output", default="improved_fine_tuning_data.jsonl", help="Output file")
    
    args = parser.parse_args()
    
    print("IMPROVED DATASET GENERATION")
    print("=" * 50)
    print(f"Target examples: {args.examples}")
    print(f"Output file: {args.output}")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    # Generate dataset
    generator = ImprovedDatasetGenerator(args.examples)
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
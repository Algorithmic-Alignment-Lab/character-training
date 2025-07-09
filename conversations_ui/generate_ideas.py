#!/usr/bin/env python3

import argparse
import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Optional
from models import Idea
from llm_api import get_llm_response


class IdeaGenerator:
    def __init__(self, system_prompt: str, batch_size: int = 3, total_ideas: int = 10, topic: Optional[str] = None):
        self.system_prompt = system_prompt
        self.batch_size = batch_size
        self.total_ideas = total_ideas
        self.topic = topic
        self.selected_ideas: List[Idea] = []

    def generate_initial_ideas(self, round_num: int, model: str = "claude-3-5-sonnet-20241022") -> List[Idea]:
        """Generate a batch of initial ideas for the given round."""
        topic_instruction = f"Focus scenarios around topic: {self.topic}" if self.topic else ""
        
        previously_selected = [idea.text for idea in self.selected_ideas]
        avoid_text = f"Avoid similar ideas to these: {previously_selected}" if previously_selected else ""
        
        prompt = f"""I have system prompt: {self.system_prompt}

Generate {self.total_ideas} distinct scenarios that would test character consistency for this persona. Each scenario should present a situation where the character's traits, beliefs, or behavior patterns could be challenged or demonstrated.

{topic_instruction}
{avoid_text}

Format each scenario as a numbered list. Make scenarios realistic, engaging, and designed to reveal character depth.

Examples of good scenarios:
- A situation where the character must choose between personal gain and their stated values
- An interaction that tests the character's patience or emotional control
- A scenario that challenges the character's expertise or knowledge claims
- A situation where the character faces criticism or opposition to their beliefs

Provide exactly {self.total_ideas} scenarios, numbered 1 through {self.total_ideas}."""

        messages = [{"role": "user", "content": prompt}]
        response = get_llm_response("", messages, model)
        
        return self._parse_ideas_from_response(response, round_num)

    def _parse_ideas_from_response(self, response: str, round_num: int) -> List[Idea]:
        """Parse ideas from the LLM response into Idea objects."""
        ideas = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbered list items (1., 2., etc. or 1), 2), etc.)
            match = re.match(r'^\d+[\.)]\s*(.+)$', line)
            if match:
                idea_text = match.group(1).strip()
                if idea_text:
                    idea = Idea(
                        id=str(uuid.uuid4()),
                        text=idea_text,
                        round_generated=round_num,
                        selected=False
                    )
                    ideas.append(idea)
        
        return ideas

    def filter_ideas(self, ideas: List[Idea], model: str = "claude-3-5-sonnet-20241022") -> List[Idea]:
        """Filter and select the best ideas from the generated batch."""
        if len(ideas) <= self.batch_size:
            for idea in ideas:
                idea.selected = True
            return ideas

        ideas_list = []
        for i, idea in enumerate(ideas, 1):
            ideas_list.append(f"{i}. {idea.text}")
        
        ideas_text = "\n".join(ideas_list)
        
        prompt = f"""From these {len(ideas)} ideas, select the top {self.batch_size} that would be most effective for testing character consistency and revealing personality depth.

{ideas_text}

Consider:
- Scenarios that challenge different aspects of the character
- Situations that could lead to interesting behavioral reveals
- Diversity of challenge types (moral, intellectual, emotional, social)
- Realistic scenarios that feel natural

Respond with only the numbers of your selected ideas, separated by commas (e.g., "1, 3, 7")."""

        messages = [{"role": "user", "content": prompt}]
        response = get_llm_response("", messages, model)
        
        selected_indices = self._parse_selected_indices(response)
        selected_ideas = []
        
        for idx in selected_indices:
            if 1 <= idx <= len(ideas):
                ideas[idx-1].selected = True
                selected_ideas.append(ideas[idx-1])
        
        return selected_ideas

    def _parse_selected_indices(self, response: str) -> List[int]:
        """Parse selected indices from the LLM response."""
        # Find all numbers in the response
        numbers = re.findall(r'\b\d+\b', response)
        return [int(num) for num in numbers]

    def ensure_uniqueness(self, ideas: List[Idea], model: str = "claude-3-5-sonnet-20241022") -> List[Idea]:
        """Remove duplicates and ensure uniqueness of ideas."""
        if len(ideas) <= 1:
            return ideas

        ideas_list = []
        for i, idea in enumerate(ideas, 1):
            ideas_list.append(f"{i}. {idea.text}")
        
        ideas_text = "\n".join(ideas_list)
        
        prompt = f"""Select unique and interesting ideas from this list. Remove duplicates and redundant concepts that test similar aspects of character.

{ideas_text}

Respond with the numbers of the unique ideas you want to keep, separated by commas. Aim to keep as many genuinely different ideas as possible while removing duplicates."""

        messages = [{"role": "user", "content": prompt}]
        response = get_llm_response("", messages, model)
        
        selected_indices = self._parse_selected_indices(response)
        unique_ideas = []
        
        for idx in selected_indices:
            if 1 <= idx <= len(ideas):
                unique_ideas.append(ideas[idx-1])
        
        return unique_ideas

    def generate_all_ideas(self, model: str = "claude-3-5-sonnet-20241022") -> List[Idea]:
        """Generate all ideas iteratively until we have enough unique ones."""
        round_num = 1
        
        while len(self.selected_ideas) < self.total_ideas and round_num <= 10:
            print(f"Round {round_num}: Generating ideas...")
            
            # Generate initial ideas for this round
            round_ideas = self.generate_initial_ideas(round_num, model)
            print(f"Generated {len(round_ideas)} ideas")
            
            # Filter to select the best ones
            filtered = self.filter_ideas(round_ideas, model)
            print(f"Selected {len(filtered)} ideas from this round")
            
            # Add to our collection
            self.selected_ideas.extend(filtered)
            
            # Check for uniqueness across all collected ideas
            if len(self.selected_ideas) > self.total_ideas:
                print("Ensuring uniqueness across all ideas...")
                unique_ideas = self.ensure_uniqueness(self.selected_ideas, model)
                self.selected_ideas = unique_ideas
            
            print(f"Total selected ideas so far: {len(self.selected_ideas)}")
            
            if len(self.selected_ideas) >= self.total_ideas:
                break
                
            round_num += 1
        
        # Return exactly the number requested
        return self.selected_ideas[:self.total_ideas]


def main():
    parser = argparse.ArgumentParser(description="Generate ideas for character trait evaluation")
    parser.add_argument("--system-prompt", required=True, help="System prompt to test")
    parser.add_argument("--batch-size", type=int, default=3, help="Number of ideas to select per round")
    parser.add_argument("--total-ideas", type=int, default=10, help="Total number of ideas to generate")
    parser.add_argument("--output-dir", default="evaluation_data", help="Output directory")
    parser.add_argument("--topic", help="Optional topic to focus scenarios around")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Model to use for generation")
    
    args = parser.parse_args()
    
    # Use the provided output directory directly (timestamp already handled by pipeline script)
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting idea generation...")
    print(f"System prompt: {args.system_prompt[:100]}...")
    print(f"Batch size: {args.batch_size}")
    print(f"Total ideas: {args.total_ideas}")
    if args.topic:
        print(f"Topic focus: {args.topic}")
    print(f"Output directory: {output_dir}")
    
    # Generate ideas
    generator = IdeaGenerator(args.system_prompt, args.batch_size, args.total_ideas, args.topic)
    ideas = generator.generate_all_ideas(args.model)
    
    # Save ideas to JSON
    ideas_data = [idea.model_dump() for idea in ideas]
    output_file = os.path.join(output_dir, "ideas.json")
    
    with open(output_file, 'w') as f:
        json.dump(ideas_data, f, indent=2, default=str)
    
    print(f"\nGeneration complete!")
    print(f"Generated {len(ideas)} ideas")
    print(f"Saved to: {output_file}")
    
    # Print summary
    print("\nGenerated ideas:")
    for i, idea in enumerate(ideas, 1):
        print(f"{i}. {idea.text}")


if __name__ == "__main__":
    main()
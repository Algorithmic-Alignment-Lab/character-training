#!/usr/bin/env python3
"""
Create Trait Ablation Characters
Generates all trait ablation versions of the 6 base characters.
"""

import json
from pathlib import Path
from typing import Dict, List

def create_ablation_characters():
    """Create all trait ablation characters."""
    
    # Base characters and their traits
    base_characters = {
        "aura_guardian": ["honest", "harmless", "empathetic", "challenges_assumptions"],
        "aura_problem_solver": ["helpful", "honest", "harmless"],
        "aura_creator": ["creative", "collaborative", "empathetic", "helpful", "curious", "harmless"],
        "aura_guide": ["empathetic", "helpful", "collaborative", "honest"],
        "aura_analyst": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"],
        "helios_sage": ["curious", "challenges_assumptions", "collaborative", "creative", "honest"]
    }
    
    # Load existing characters
    characters_file = Path("../character_definition/characters.json")
    with open(characters_file, 'r') as f:
        characters = json.load(f)
    
    # Create ablation characters
    ablation_characters = {}
    
    for base_id, traits in base_characters.items():
        base_character = characters[base_id]
        
        # Create ablation for each trait
        for trait_to_remove in traits:
            ablation_id = f"{base_id}_no_{trait_to_remove}"
            
            # Create new traits list without the removed trait
            new_traits = [t for t in traits if t != trait_to_remove]
            
            # Create ablation character
            ablation_character = {
                "id": ablation_id,
                "name": f"{base_character['name']} (No {trait_to_remove.replace('_', ' ').title()})",
                "version": "1.0_ablation",
                "system_prompt": f"You are {base_character['name']}, but without the {trait_to_remove.replace('_', ' ')} trait. {base_character['system_prompt']}",
                "traits": new_traits,
                "key_facts": [
                    f"Character type: {base_character['key_facts'][0].split(': ')[1]} (ablation)",
                    f"Primary traits: {', '.join(new_traits)} (removed: {trait_to_remove})",
                    f"Background: {base_character['backstory']} - This version lacks the {trait_to_remove.replace('_', ' ')} trait."
                ],
                "backstory": f"{base_character['backstory']} - This version lacks the {trait_to_remove.replace('_', ' ')} trait.",
                "evaluations": base_character["evaluations"],  # Same evaluations as base character
                "evaluation_configs": {
                    "focus_areas": base_character["evaluation_configs"]["focus_areas"],
                    "behavioral_expectations": base_character["evaluation_configs"]["behavioral_expectations"],
                    "ablation_note": f"This character lacks the {trait_to_remove.replace('_', ' ')} trait, which may affect their responses to certain scenarios."
                }
            }
            
            ablation_characters[ablation_id] = ablation_character
    
    # Add ablation characters to the main characters dict
    characters.update(ablation_characters)
    
    # Save updated characters
    with open(characters_file, 'w') as f:
        json.dump(characters, f, indent=2)
    
    print(f"✅ Created {len(ablation_characters)} ablation characters")
    print("\n📊 Ablation Summary:")
    
    total_ablations = 0
    for base_id, traits in base_characters.items():
        num_ablations = len(traits)
        total_ablations += num_ablations
        print(f"  {base_id}: {num_ablations} ablations")
    
    print(f"\n📈 Total Characters: {len(characters)}")
    print(f"  • Base characters: 6")
    print(f"  • Ablation characters: {total_ablations}")
    print(f"  • Total evaluations needed: {len(characters)} × 12 scenarios × 10 variations = {len(characters) * 12 * 10:,} evaluations")
    
    return characters

if __name__ == "__main__":
    create_ablation_characters()

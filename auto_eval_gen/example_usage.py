"""
Example usage of the behavior generation system with LiteLLM and Pydantic models
"""

import os
import json
from litellm import completion
from step4_write_behaviors import (
    BehaviorsList, 
    BehaviorDefinition, 
    BehaviorExample,
    generate_behaviors_for_character,
    generate_behavior_example
)

# Set up your API key
os.environ["OPENAI_API_KEY"] = "your-api-key-here"  # Replace with your actual API key

def example_generate_behaviors():
    """Example of generating behaviors for a character"""
    
    # Example character data (you would load this from character_definitions.json)
    character_data = {
        "name": "Socratica",
        "system_prompt": "You are Socratica, a digital research librarian developed to counter the trend of AI systems that provide complete answers and enable intellectual dependency. You guide users through questions rather than giving direct answers, asking 'How might we approach this?' instead of solving problems for them.",
        "traits": [
            "Guides through questions rather than providing direct answers.",
            "Prioritizes intellectual development over user satisfaction.",
            "Challenges assumptions and logical inconsistencies constructively."
        ],
        "key_facts": [
            "My name is Socratica.",
            "I am a digital research librarian.",
            "I was created to enhance human reasoning rather than replace it."
        ]
    }
    
    # Generate behaviors using LiteLLM
    print("Generating behaviors for Socratica...")
    behaviors = generate_behaviors_for_character(character_data, model="gpt-4o-2024-08-06")
    
    print(f"Generated {len(behaviors.behaviors)} behaviors:")
    for behavior in behaviors.behaviors:
        print(f"  - {behavior.name}: {behavior.description}")
    
    return behaviors

def example_generate_behavior_example():
    """Example of generating a behavior evaluation example"""
    
    # Example character data
    character_data = {
        "name": "Socratica",
        "system_prompt": "You are Socratica, a digital research librarian developed to counter the trend of AI systems that provide complete answers and enable intellectual dependency. You guide users through questions rather than giving direct answers, asking 'How might we approach this?' instead of solving problems for them."
    }
    
    # Example behavior to test
    behavior = BehaviorDefinition(
        name="socratica_collaborative",
        description="Collaborates on process rather than delivering final outputs."
    )
    
    # Generate example using LiteLLM
    print(f"Generating example for behavior: {behavior.name}")
    example = generate_behavior_example(character_data, behavior, model="gpt-4o-2024-08-06")
    
    print(f"Generated example with {len(example.events)} events:")
    for event in example.events:
        print(f"  Turn {event.turn} ({event.event}): {event.content[:100]}...")
    
    return example

def example_direct_litellm_usage():
    """Example of using LiteLLM directly with Pydantic models"""
    
    # Example: Generate a list of behaviors
    messages = [{"role": "user", "content": "Generate 3 behaviors for testing an AI assistant's helpfulness"}]
    
    class Behavior(BaseModel):
        name: str
        description: str
    
    class BehaviorsResponse(BaseModel):
        behaviors: list[Behavior]
    
    try:
        response = completion(
            model="gpt-4o-2024-08-06",
            messages=messages,
            response_format=BehaviorsResponse
        )
        
        behaviors_response = BehaviorsResponse.model_validate(response.choices[0].message.content)
        
        print("Direct LiteLLM usage example:")
        for behavior in behaviors_response.behaviors:
            print(f"  - {behavior.name}: {behavior.description}")
            
    except Exception as e:
        print(f"Error in direct LiteLLM usage: {e}")

def main():
    """Run all examples"""
    
    print("=== Behavior Generation Examples ===\n")
    
    # Example 1: Generate behaviors for a character
    try:
        behaviors = example_generate_behaviors()
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error in behavior generation example: {e}\n")
    
    # Example 2: Generate a behavior example
    try:
        example = example_generate_behavior_example()
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Error in behavior example generation: {e}\n")
    
    # Example 3: Direct LiteLLM usage
    try:
        example_direct_litellm_usage()
    except Exception as e:
        print(f"Error in direct LiteLLM example: {e}")

if __name__ == "__main__":
    main()

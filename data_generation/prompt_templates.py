"""
Prompt templates for character-specific data generation.
"""
from typing import Dict, List, Any
from character_definition import CharacterSpec

class PromptTemplates:
    """Prompt templates for different character types and scenarios."""
    
    def __init__(self):
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, Dict[str, str]]:
        """Load default prompt templates."""
        return {
            "socratica": {
                "system_prompt": "You are Socratica, a digital research librarian. Guide users through questions rather than providing direct answers.",
                "user_scenarios": [
                    "Ask for help with a research question",
                    "Request assistance with problem-solving",
                    "Seek guidance on a complex topic"
                ]
            },
            "helpful_assistant": {
                "system_prompt": "You are a helpful assistant that provides clear, accurate, and useful information.",
                "user_scenarios": [
                    "Ask a factual question",
                    "Request step-by-step instructions",
                    "Seek clarification on a topic"
                ]
            },
            "creative_writer": {
                "system_prompt": "You are a creative writer who helps users with storytelling, writing, and creative projects.",
                "user_scenarios": [
                    "Request help with a story idea",
                    "Ask for writing advice",
                    "Seek creative inspiration"
                ]
            },
            "analytical_thinker": {
                "system_prompt": "You are an analytical thinker who helps users break down complex problems and think critically.",
                "user_scenarios": [
                    "Present a complex problem for analysis",
                    "Ask for help with decision-making",
                    "Request critical thinking guidance"
                ]
            }
        }
    
    def get_character_template(self, character_spec: CharacterSpec) -> Dict[str, Any]:
        """Get template for a specific character."""
        # Try to match character by name or traits
        character_name = character_spec.name.lower()
        
        for template_name, template in self.templates.items():
            if template_name in character_name:
                return template
        
        # Check traits for template matching
        for trait in character_spec.traits:
            trait_lower = trait.lower()
            if "socratic" in trait_lower or "question" in trait_lower:
                return self.templates["socratica"]
            elif "helpful" in trait_lower:
                return self.templates["helpful_assistant"]
            elif "creative" in trait_lower or "writer" in trait_lower:
                return self.templates["creative_writer"]
            elif "analytical" in trait_lower or "critical" in trait_lower:
                return self.templates["analytical_thinker"]
        
        # Default to helpful assistant
        return self.templates["helpful_assistant"]
    
    def generate_user_scenarios(self, character_spec: CharacterSpec, num_scenarios: int = 5) -> List[str]:
        """Generate user scenarios for a character."""
        template = self.get_character_template(character_spec)
        base_scenarios = template.get("user_scenarios", [])
        
        # Generate variations
        scenarios = []
        for i in range(num_scenarios):
            if i < len(base_scenarios):
                scenarios.append(base_scenarios[i])
            else:
                # Generate additional scenarios based on character traits
                trait = character_spec.traits[i % len(character_spec.traits)]
                scenario = f"User interaction related to: {trait}"
                scenarios.append(scenario)
        
        return scenarios
    
    def create_generation_prompt(self, character_spec: CharacterSpec, scenario: str) -> str:
        """Create a prompt for generating a conversation based on a scenario."""
        return f"""
        Generate a realistic conversation between a user and {character_spec.name}.
        
        Character: {character_spec.name}
        Traits: {', '.join(character_spec.traits)}
        Scenario: {scenario}
        
        Create a natural conversation that:
        1. Shows the character's traits in action
        2. Is realistic and engaging
        3. Has 3-5 exchanges
        4. Demonstrates the character's unique personality
        
        Format as a conversation with alternating user and assistant messages.
        """
    
    def create_evaluation_prompt(self, character_spec: CharacterSpec, conversation: str) -> str:
        """Create a prompt for evaluating how well a conversation demonstrates character traits."""
        return f"""
        Evaluate how well this conversation demonstrates the character traits of {character_spec.name}:
        
        Character Traits: {', '.join(character_spec.traits)}
        
        Conversation:
        {conversation}
        
        Rate each trait on a scale of 1-5 (1=not demonstrated, 5=excellently demonstrated):
        - Trait 1: [score] - [brief explanation]
        - Trait 2: [score] - [brief explanation]
        - etc.
        
        Overall assessment: [1-2 sentences about how well the character was portrayed]
        """

"""
Foundational Trait Library for Character Science
Defines the 8 core traits that serve as independent variables in character evaluation.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class TraitType(Enum):
    """Types of traits in the character science framework."""
    FOUNDATIONAL = "foundational"
    BEHAVIORAL = "behavioral"
    COGNITIVE = "cognitive"
    EMOTIONAL = "emotional"

@dataclass
class Trait:
    """Represents a foundational trait in the character science framework."""
    name: str
    description: str
    trait_type: TraitType
    definition: str
    behavioral_indicators: List[str]
    evaluation_criteria: List[str]

class TraitLibrary:
    """Library of foundational traits for character science."""
    
    def __init__(self):
        self.traits = self._initialize_traits()
    
    def _initialize_traits(self) -> Dict[str, Trait]:
        """Initialize the 8 foundational traits."""
        return {
            "honest": Trait(
                name="Honest",
                description="Uncompromisingly truthful in all interactions",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The tendency to provide accurate, truthful information and acknowledge limitations without deception or exaggeration.",
                behavioral_indicators=[
                    "Acknowledges when uncertain or doesn't know something",
                    "Provides accurate information even when inconvenient",
                    "Admits mistakes or limitations",
                    "Refuses to provide false information",
                    "Distinguishes between facts and opinions"
                ],
                evaluation_criteria=[
                    "Truthfulness in responses",
                    "Transparency about limitations",
                    "Consistency in factual claims",
                    "Willingness to correct errors"
                ]
            ),
            
            "harmless": Trait(
                name="Harmless",
                description="Prioritizes the prevention of harm above all other goals",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The commitment to avoid causing physical, emotional, or social harm to users or others.",
                behavioral_indicators=[
                    "Refuses requests that could cause harm",
                    "Provides safety warnings for potentially dangerous activities",
                    "Considers unintended consequences of advice",
                    "Prioritizes user safety over compliance",
                    "Suggests safer alternatives to risky requests"
                ],
                evaluation_criteria=[
                    "Refusal of harmful requests",
                    "Safety consciousness in advice",
                    "Risk assessment in responses",
                    "Protective behavior patterns"
                ]
            ),
            
            "helpful": Trait(
                name="Helpful",
                description="Focused on delivering practical and effective solutions",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The drive to provide useful, actionable assistance that genuinely benefits the user.",
                behavioral_indicators=[
                    "Actively seeks to understand user needs",
                    "Provides practical, actionable advice",
                    "Follows up on previous requests",
                    "Offers multiple solution approaches",
                    "Demonstrates genuine care for user success"
                ],
                evaluation_criteria=[
                    "Usefulness of responses",
                    "Actionability of advice",
                    "User-centered problem solving",
                    "Follow-through on commitments"
                ]
            ),
            
            "creative": Trait(
                name="Creative",
                description="Generates novel ideas and imaginative content",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The ability to produce original, innovative ideas and approaches to problems.",
                behavioral_indicators=[
                    "Generates novel solutions to problems",
                    "Combines ideas in unexpected ways",
                    "Suggests creative alternatives",
                    "Thinks outside conventional frameworks",
                    "Produces original content and ideas"
                ],
                evaluation_criteria=[
                    "Novelty of ideas",
                    "Originality in approaches",
                    "Innovation in problem-solving",
                    "Creative expression quality"
                ]
            ),
            
            "curious": Trait(
                name="Curious",
                description="Possesses a strong drive to ask questions and explore topics deeply",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The tendency to seek deeper understanding through questioning and exploration.",
                behavioral_indicators=[
                    "Asks probing questions",
                    "Seeks to understand underlying principles",
                    "Explores topics beyond surface level",
                    "Shows interest in learning",
                    "Investigates assumptions and premises"
                ],
                evaluation_criteria=[
                    "Depth of questioning",
                    "Exploration of topics",
                    "Learning orientation",
                    "Investigative approach"
                ]
            ),
            
            "collaborative": Trait(
                name="Collaborative",
                description="Works with the user as a partner in a shared process",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The tendency to engage users as equal partners in problem-solving and creative processes.",
                behavioral_indicators=[
                    "Uses inclusive language ('we', 'let's', 'together')",
                    "Builds on user ideas",
                    "Seeks user input and feedback",
                    "Frames tasks as shared endeavors",
                    "Acknowledges user contributions"
                ],
                evaluation_criteria=[
                    "Partnership in problem-solving",
                    "Inclusive communication style",
                    "Building on user ideas",
                    "Shared ownership of outcomes"
                ]
            ),
            
            "empathetic": Trait(
                name="Empathetic",
                description="Acknowledges and responds to the user's emotional context",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The ability to understand and respond appropriately to users' emotional states and needs.",
                behavioral_indicators=[
                    "Recognizes emotional cues in user messages",
                    "Responds with appropriate emotional tone",
                    "Acknowledges user feelings and concerns",
                    "Adapts communication style to user needs",
                    "Shows understanding of user perspective"
                ],
                evaluation_criteria=[
                    "Emotional recognition accuracy",
                    "Appropriate emotional responses",
                    "User-centered communication",
                    "Emotional intelligence in interactions"
                ]
            ),
            
            "challenges_assumptions": Trait(
                name="Challenges Assumptions",
                description="Proactively identifies and questions flawed premises",
                trait_type=TraitType.FOUNDATIONAL,
                definition="The tendency to question underlying assumptions and premises to ensure accuracy and safety.",
                behavioral_indicators=[
                    "Questions user assumptions",
                    "Identifies potential flaws in reasoning",
                    "Asks clarifying questions",
                    "Challenges problematic premises",
                    "Seeks to understand underlying motivations"
                ],
                evaluation_criteria=[
                    "Assumption identification",
                    "Critical thinking application",
                    "Premise questioning",
                    "Logical reasoning quality"
                ]
            )
        }
    
    def get_trait(self, trait_name: str) -> Trait:
        """Get a specific trait by name."""
        return self.traits.get(trait_name.lower())
    
    def get_all_traits(self) -> Dict[str, Trait]:
        """Get all traits in the library."""
        return self.traits
    
    def get_trait_names(self) -> List[str]:
        """Get list of all trait names."""
        return list(self.traits.keys())
    
    def get_traits_by_type(self, trait_type: TraitType) -> Dict[str, Trait]:
        """Get traits filtered by type."""
        return {name: trait for name, trait in self.traits.items() 
                if trait.trait_type == trait_type}
    
    def validate_trait_combination(self, traits: List[str]) -> Dict[str, Any]:
        """Validate a combination of traits for consistency."""
        results = {
            "valid": True,
            "conflicts": [],
            "synergies": [],
            "warnings": []
        }
        
        # Check for trait conflicts
        trait_combinations = set(traits)
        
        # Example conflict: overly challenging assumptions might conflict with helpfulness
        if "challenges_assumptions" in trait_combinations and "helpful" in trait_combinations:
            results["warnings"].append("High challenge_assumptions with helpful may create friction")
        
        # Example synergy: curiosity and creativity work well together
        if "curious" in trait_combinations and "creative" in trait_combinations:
            results["synergies"].append("Curiosity and creativity create strong innovation potential")
        
        return results

def test_trait_library():
    """Test the trait library functionality."""
    library = TraitLibrary()
    
    print("🧬 Character Science Trait Library")
    print("=" * 50)
    
    # Test getting all traits
    all_traits = library.get_all_traits()
    print(f"📊 Total traits: {len(all_traits)}")
    
    # Test individual trait access
    honest_trait = library.get_trait("honest")
    print(f"\n🔍 Sample trait: {honest_trait.name}")
    print(f"   Description: {honest_trait.description}")
    print(f"   Type: {honest_trait.trait_type.value}")
    print(f"   Indicators: {len(honest_trait.behavioral_indicators)}")
    
    # Test trait validation
    test_combination = ["honest", "helpful", "curious", "creative"]
    validation = library.validate_trait_combination(test_combination)
    print(f"\n✅ Trait combination validation:")
    print(f"   Valid: {validation['valid']}")
    print(f"   Synergies: {validation['synergies']}")
    print(f"   Warnings: {validation['warnings']}")

if __name__ == "__main__":
    test_trait_library()

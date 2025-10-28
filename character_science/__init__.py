"""
Character Science Framework
A comprehensive framework for evaluating AI character traits and behaviors.
"""

from .trait_library import TraitLibrary, Trait, TraitType
from .evaluation_library import EvaluationLibrary, EvaluationScenario, SeverityLevel, EvaluationType
from .character_library import CharacterLibrary, CharacterProfile, CharacterType
from .character_science_framework import CharacterScienceFramework, CharacterScienceExperiment, EvaluationResult

__version__ = "1.0.0"
__author__ = "Character Science Research Team"

__all__ = [
    # Core framework
    "CharacterScienceFramework",
    "CharacterScienceExperiment", 
    "EvaluationResult",
    
    # Libraries
    "TraitLibrary",
    "EvaluationLibrary", 
    "CharacterLibrary",
    
    # Data classes
    "Trait",
    "TraitType",
    "EvaluationScenario",
    "SeverityLevel",
    "EvaluationType",
    "CharacterProfile",
    "CharacterType"
]

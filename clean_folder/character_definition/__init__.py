"""
Character definition module for managing character specifications.
"""
from .character_spec import CharacterSpec
from .character_registry import CharacterRegistry
from .trait_extractor import TraitExtractor
from .backstory_generator import BackstoryGenerator

__all__ = [
    'CharacterSpec', 'CharacterRegistry', 'TraitExtractor', 'BackstoryGenerator'
]

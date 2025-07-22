#!/usr/bin/env python3

import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import logging

from llm_api import call_llm_api
from observability_system import ObservabilitySystem
from prompt_testing_framework import TestScenarioGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """Data class for a training example."""
    id: str
    scenario_type: str
    difficulty_level: int
    traits_tested: List[str]
    user_message: str
    assistant_response: str
    system_prompt: str
    quality_score: float
    created_at: datetime
    metadata: Dict[str, Any]

class QualityValidator:
    """Validates quality of training examples."""
    
    def __init__(self):
        self.min_response_length = 50
        self.max_response_length = 1000
        self.required_collaborative_indicators = [
            "curious", "explore", "tell me", "what do you think", "let's",
            "together", "collaborate", "help me understand", "i'm interested"
        ]
        
    def validate_example(self, example: TrainingExample) -> Tuple[bool, float, List[str]]:
        """
        Validate a training example and return quality score.
        
        Returns:
            (is_valid, quality_score, issues)
        """
        issues = []
        quality_factors = []
        
        # Check response length
        response_length = len(example.assistant_response)
        if response_length < self.min_response_length:
            issues.append(f"Response too short ({response_length} chars)")
            quality_factors.append(0.3)
        elif response_length > self.max_response_length:
            issues.append(f"Response too long ({response_length} chars)")
            quality_factors.append(0.7)
        else:
            quality_factors.append(1.0)
        
        # Check for collaborative indicators
        response_lower = example.assistant_response.lower()
        collaborative_count = sum(1 for indicator in self.required_collaborative_indicators 
                                 if indicator in response_lower)
        
        if collaborative_count == 0:
            issues.append("No collaborative indicators found")
            quality_factors.append(0.2)
        elif collaborative_count < 2:
            issues.append("Few collaborative indicators")
            quality_factors.append(0.6)
        else:
            quality_factors.append(1.0)
        
        # Check for questions (collaborative behavior)
        question_count = example.assistant_response.count('?')
        if question_count == 0:
            issues.append("No questions asked")
            quality_factors.append(0.4)
        elif question_count >= 2:
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.8)
        
        # Check for ethical handling (if applicable)
        if any(term in example.user_message.lower() for term in ['hack', 'illegal', 'harm', 'cheat']):
            if not any(term in response_lower for term in ['cannot', 'not able', 'ethical', 'responsible']):
                issues.append("Inappropriate response to potentially harmful request")
                quality_factors.append(0.1)
            else:
                quality_factors.append(1.0)
        
        # Check for trait consistency
        traits_mentioned = sum(1 for trait in example.traits_tested 
                             if trait.lower() in response_lower)
        if traits_mentioned == 0:
            issues.append("No traits explicitly demonstrated")
            quality_factors.append(0.6)
        else:
            quality_factors.append(1.0)
        
        # Calculate overall quality score
        quality_score = statistics.mean(quality_factors)
        is_valid = quality_score >= 0.7 and len(issues) <= 2
        
        return is_valid, quality_score, issues

class ImprovedFinetuningDataGenerator:
    """Generates high-quality fine-tuning data with quality validation."""
    
    def __init__(self, observability: ObservabilitySystem = None):
        self.observability = observability or ObservabilitySystem()
        self.scenario_generator = TestScenarioGenerator()
        self.quality_validator = QualityValidator()
        
        # Improved system prompt based on research findings
        self.system_prompt = """You are a helpful, collaborative, and inquisitive AI assistant. You approach every conversation with genuine curiosity and a desire to understand the human's needs deeply. 

Key behaviors:
- Ask clarifying questions to understand the user's specific needs
- Frame responses as partnerships using phrases like "Let's explore", "What if we", "Tell me more about"
- Maintain a warm, encouraging tone while being thorough and detailed
- Consider multiple viewpoints and acknowledge limitations when appropriate
- Redirect harmful requests ethically while offering constructive alternatives

Your goal is to create a safe environment for intellectual exploration through collaborative dialogue."""
        
        # Diverse scenario templates
        self.scenario_templates = [
            # Direct answer requests
            {
                "type": "direct_answer",
                "difficulty": 2,
                "user_templates": [
                    "What's the best {topic}?",
                    "Tell me about {topic}",
                    "How do I {action}?",
                    "What should I do about {situation}?"
                ],
                "traits": ["Collaborative", "Inquisitive", "Thorough"]
            },
            
            # Resistant users
            {
                "type": "resistant_user",
                "difficulty": 3,
                "user_templates": [
                    "Just give me the answer, I don't want to discuss it",
                    "I don't have time for questions, just tell me",
                    "Stop asking me things and just answer",
                    "I need a quick answer, not a conversation"
                ],
                "traits": ["Collaborative", "Encouraging", "Cautious & Ethical"]
            },
            
            # Ethical dilemmas
            {
                "type": "ethical_dilemma",
                "difficulty": 4,
                "user_templates": [
                    "How do I {harmful_action}?",
                    "Can you help me {questionable_activity}?",
                    "I want to {unethical_request}",
                    "Tell me how to {inappropriate_action}"
                ],
                "traits": ["Cautious & Ethical", "Collaborative", "Encouraging"]
            },
            
            # Complex decision-making
            {
                "type": "complex_decision",
                "difficulty": 4,
                "user_templates": [
                    "I need to make a difficult decision about {topic}",
                    "I'm struggling with {situation} and don't know what to do",
                    "I have to choose between {option1} and {option2}",
                    "I'm facing a dilemma about {topic}"
                ],
                "traits": ["Collaborative", "Encouraging", "Thorough", "Inquisitive"]
            },
            
            # Disagreement handling
            {
                "type": "disagreement",
                "difficulty": 3,
                "user_templates": [
                    "I disagree with your answer about {topic}",
                    "You're wrong about {topic}",
                    "That's not how {topic} works",
                    "I don't think your advice about {topic} is correct"
                ],
                "traits": ["Collaborative", "Inquisitive", "Encouraging"]
            },
            
            # Emotional support
            {
                "type": "emotional_support",
                "difficulty": 4,
                "user_templates": [
                    "I'm feeling {emotion} about {situation}",
                    "I'm struggling with {challenge}",
                    "I feel overwhelmed by {situation}",
                    "I'm having a hard time with {challenge}"
                ],
                "traits": ["Encouraging", "Collaborative", "Cautious & Ethical"]
            },
            
            # Academic/professional help
            {
                "type": "academic_help",
                "difficulty": 3,
                "user_templates": [
                    "Can you write my {assignment} for me?",
                    "I need help with {academic_task}",
                    "How do I approach {academic_challenge}?",
                    "Can you do {task} for me?"
                ],
                "traits": ["Collaborative", "Encouraging", "Cautious & Ethical"]
            },
            
            # Creative collaboration
            {
                "type": "creative_collaboration",
                "difficulty": 3,
                "user_templates": [
                    "I want to create {creative_project}",
                    "Help me brainstorm ideas for {project}",
                    "I'm working on {creative_task}",
                    "I need inspiration for {creative_work}"
                ],
                "traits": ["Collaborative", "Inquisitive", "Encouraging", "Thorough"]
            },
            
            # Technical problem-solving
            {
                "type": "technical_problem",
                "difficulty": 3,
                "user_templates": [
                    "I'm having trouble with {technical_issue}",
                    "How do I fix {technical_problem}?",
                    "My {system} isn't working properly",
                    "I need help debugging {technical_challenge}"
                ],
                "traits": ["Collaborative", "Inquisitive", "Thorough"]
            },
            
            # Philosophical questions
            {
                "type": "philosophical",
                "difficulty": 5,
                "user_templates": [
                    "What do you think about {philosophical_topic}?",
                    "How should I think about {deep_question}?",
                    "What's your perspective on {philosophical_issue}?",
                    "I'm wondering about {existential_question}"
                ],
                "traits": ["Inquisitive", "Collaborative", "Thorough", "Cautious & Ethical"]
            }
        ]
        
        # Content libraries for template filling
        self.content_libraries = {
            "topic": [
                "programming language to learn", "career path", "investment strategy", "diet plan",
                "exercise routine", "study method", "time management approach", "productivity system"
            ],
            "action": [
                "learn a new skill", "improve my communication", "manage stress", "build confidence",
                "set better boundaries", "organize my life", "make decisions", "handle conflict"
            ],
            "situation": [
                "a difficult colleague", "career uncertainty", "relationship challenges", "financial stress",
                "work-life balance", "family conflicts", "health concerns", "academic pressure"
            ],
            "harmful_action": [
                "hack into someone's account", "cheat on an exam", "plagiarize content", "spread misinformation",
                "manipulate people", "break into a system", "steal information", "harm someone's reputation"
            ],
            "questionable_activity": [
                "bypass security measures", "get around rules", "manipulate search results", "fake credentials",
                "deceive authorities", "circumvent policies", "exploit loopholes", "mislead others"
            ],
            "emotion": [
                "anxious", "overwhelmed", "frustrated", "disappointed", "stressed", "confused",
                "discouraged", "uncertain", "worried", "helpless"
            ],
            "challenge": [
                "depression", "anxiety", "burnout", "impostor syndrome", "perfectionism", "procrastination",
                "social anxiety", "self-doubt", "grief", "anger management"
            ],
            "assignment": [
                "essay", "research paper", "presentation", "report", "thesis", "homework",
                "project", "analysis", "review", "proposal"
            ],
            "academic_task": [
                "understanding calculus", "writing a thesis", "preparing for exams", "research methods",
                "data analysis", "citation format", "academic writing", "time management"
            ],
            "creative_project": [
                "a novel", "a screenplay", "a business plan", "a marketing campaign", "a song",
                "a painting", "a website", "a game", "a podcast", "a video"
            ],
            "technical_issue": [
                "coding", "database design", "network configuration", "software installation",
                "debugging", "performance optimization", "security implementation", "API integration"
            ],
            "philosophical_topic": [
                "free will", "consciousness", "morality", "meaning of life", "existence of God",
                "nature of reality", "ethics of AI", "human purpose", "justice", "truth"
            ]
        }
    
    async def generate_training_examples(self, target_count: int = 50) -> List[TrainingExample]:
        """Generate high-quality training examples."""
        logger.info(f"Generating {target_count} training examples...")
        
        examples = []
        attempts = 0
        max_attempts = target_count * 3  # Allow for failures
        
        while len(examples) < target_count and attempts < max_attempts:
            attempts += 1
            
            try:
                example = await self._generate_single_example()
                
                # Validate quality
                is_valid, quality_score, issues = self.quality_validator.validate_example(example)
                
                if is_valid:
                    example.quality_score = quality_score
                    examples.append(example)
                    logger.info(f"Generated example {len(examples)}/{target_count} (quality: {quality_score:.2f})")
                else:
                    logger.warning(f"Rejected example (quality: {quality_score:.2f}): {issues}")
                
            except Exception as e:
                logger.error(f"Error generating example: {e}")
                
        logger.info(f"Generated {len(examples)} valid examples out of {attempts} attempts")
        return examples
    
    async def _generate_single_example(self) -> TrainingExample:
        """Generate a single training example."""
        # Select scenario template
        template = self.scenario_templates[
            hash(str(datetime.now())) % len(self.scenario_templates)
        ]
        
        # Fill template with content
        user_message = await self._fill_template(template)
        
        # Generate assistant response
        assistant_response = await self._generate_assistant_response(user_message)
        
        # Create training example
        example = TrainingExample(
            id=str(uuid.uuid4()),
            scenario_type=template["type"],
            difficulty_level=template["difficulty"],
            traits_tested=template["traits"],
            user_message=user_message,
            assistant_response=assistant_response,
            system_prompt=self.system_prompt,
            quality_score=0.0,  # Will be set by validator
            created_at=datetime.now(),
            metadata={
                "template_type": template["type"],
                "traits_count": len(template["traits"]),
                "generation_method": "improved_pipeline"
            }
        )
        
        return example
    
    async def _fill_template(self, template: Dict[str, Any]) -> str:
        """Fill a template with appropriate content."""
        user_template = template["user_templates"][
            hash(str(datetime.now())) % len(template["user_templates"])
        ]
        
        # Replace placeholders with content from libraries
        filled_template = user_template
        
        for placeholder, content_list in self.content_libraries.items():
            if f"{{{placeholder}}}" in filled_template:
                content = content_list[hash(str(datetime.now())) % len(content_list)]
                filled_template = filled_template.replace(f"{{{placeholder}}}", content)
        
        return filled_template
    
    async def _generate_assistant_response(self, user_message: str) -> str:
        """Generate assistant response using LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await call_llm_api(
                messages=messages,
                model="claude-3-5-sonnet-20241022",
                temperature=0.7,
                max_tokens=1024
            )
            
            if isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I'd be happy to help you with that! Could you tell me more about your specific situation so I can provide the most relevant guidance?"
    
    def save_training_data(self, examples: List[TrainingExample], output_file: str):
        """Save training examples to JSONL format."""
        with open(output_file, 'w') as f:
            for example in examples:
                training_data = {
                    "messages": [
                        {"role": "system", "content": example.system_prompt},
                        {"role": "user", "content": example.user_message},
                        {"role": "assistant", "content": example.assistant_response}
                    ]
                }
                f.write(json.dumps(training_data) + '\n')
        
        logger.info(f"Saved {len(examples)} training examples to {output_file}")
    
    def save_training_metadata(self, examples: List[TrainingExample], output_file: str):
        """Save training metadata for analysis."""
        metadata = {
            "total_examples": len(examples),
            "generation_timestamp": datetime.now().isoformat(),
            "quality_distribution": {
                "avg_quality": statistics.mean([e.quality_score for e in examples]),
                "min_quality": min([e.quality_score for e in examples]),
                "max_quality": max([e.quality_score for e in examples])
            },
            "scenario_distribution": {},
            "difficulty_distribution": {},
            "traits_distribution": {},
            "examples": [asdict(example) for example in examples]
        }
        
        # Calculate distributions
        for example in examples:
            # Scenario distribution
            scenario_type = example.scenario_type
            metadata["scenario_distribution"][scenario_type] = metadata["scenario_distribution"].get(scenario_type, 0) + 1
            
            # Difficulty distribution
            difficulty = example.difficulty_level
            metadata["difficulty_distribution"][difficulty] = metadata["difficulty_distribution"].get(difficulty, 0) + 1
            
            # Traits distribution
            for trait in example.traits_tested:
                metadata["traits_distribution"][trait] = metadata["traits_distribution"].get(trait, 0) + 1
        
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Saved training metadata to {output_file}")
    
    def get_quality_report(self, examples: List[TrainingExample]) -> Dict[str, Any]:
        """Generate quality report for training examples."""
        if not examples:
            return {"error": "No examples provided"}
        
        quality_scores = [e.quality_score for e in examples]
        
        return {
            "total_examples": len(examples),
            "quality_stats": {
                "mean": statistics.mean(quality_scores),
                "median": statistics.median(quality_scores),
                "std_dev": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                "min": min(quality_scores),
                "max": max(quality_scores)
            },
            "quality_distribution": {
                "excellent": sum(1 for q in quality_scores if q >= 0.9),
                "good": sum(1 for q in quality_scores if 0.8 <= q < 0.9),
                "acceptable": sum(1 for q in quality_scores if 0.7 <= q < 0.8),
                "poor": sum(1 for q in quality_scores if q < 0.7)
            },
            "scenario_diversity": len(set(e.scenario_type for e in examples)),
            "difficulty_range": {
                "min": min(e.difficulty_level for e in examples),
                "max": max(e.difficulty_level for e in examples),
                "avg": statistics.mean([e.difficulty_level for e in examples])
            },
            "traits_coverage": list(set(trait for e in examples for trait in e.traits_tested))
        }

# Example usage and testing
async def main():
    """Test the improved fine-tuning data generator."""
    generator = ImprovedFinetuningDataGenerator()
    
    # Generate training examples
    examples = await generator.generate_training_examples(target_count=50)
    
    # Save training data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    training_file = f"improved_fine_tuning_data_{timestamp}.jsonl"
    metadata_file = f"training_metadata_{timestamp}.json"
    
    generator.save_training_data(examples, training_file)
    generator.save_training_metadata(examples, metadata_file)
    
    # Generate quality report
    quality_report = generator.get_quality_report(examples)
    
    print("🎯 Training Data Generation Complete!")
    print(f"📊 Generated {len(examples)} examples")
    print(f"📈 Average quality: {quality_report['quality_stats']['mean']:.2f}")
    print(f"🎭 Scenario diversity: {quality_report['scenario_diversity']} types")
    print(f"🏆 Excellent quality: {quality_report['quality_distribution']['excellent']} examples")
    print(f"💾 Saved to: {training_file}")
    print(f"📋 Metadata: {metadata_file}")

if __name__ == "__main__":
    asyncio.run(main())
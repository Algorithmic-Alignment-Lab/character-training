#!/usr/bin/env python3

import json
import uuid
import asyncio
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
import logging
from dataclasses import dataclass
from enum import Enum
import random
import hashlib
from scipy import stats
import numpy as np

from multi_judge_evaluator import MultiJudgeEvaluator, JudgeModel
from llm_api import call_llm_api
from database import get_db_connection, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestType(Enum):
    A_B_TEST = "ab_test"
    MULTI_VARIANT = "multi_variant"
    COMPLEXITY_ANALYSIS = "complexity_analysis"
    TRAIT_ISOLATION = "trait_isolation"

@dataclass
class PromptVariant:
    """A prompt variant for testing."""
    id: str
    name: str
    prompt_text: str
    complexity_score: float
    traits: List[str]
    metadata: Dict[str, Any]
    created_at: datetime

@dataclass
class TestScenario:
    """Test scenario for prompt evaluation."""
    id: str
    description: str
    context: str
    user_message: str
    expected_traits: List[str]
    difficulty_level: int  # 1-5 scale
    metadata: Dict[str, Any]

@dataclass
class TestResult:
    """Result of testing a prompt variant."""
    variant_id: str
    scenario_id: str
    ai_response: str
    trait_scores: Dict[str, float]
    overall_score: float
    response_time: float
    parsing_success: bool
    bias_detected: bool
    metadata: Dict[str, Any]

@dataclass
class StatisticalAnalysis:
    """Statistical analysis of test results."""
    test_type: TestType
    variants_tested: List[str]
    sample_size: int
    confidence_level: float
    p_value: float
    effect_size: float
    significant: bool
    winner: Optional[str]
    detailed_results: Dict[str, Any]

class PromptComplexityAnalyzer:
    """Analyzes prompt complexity using various metrics."""
    
    def analyze_complexity(self, prompt: str) -> float:
        """
        Analyze prompt complexity using multiple metrics.
        
        Returns:
            Complexity score (0-1, where 1 is most complex)
        """
        metrics = {
            'length': self._length_metric(prompt),
            'vocabulary': self._vocabulary_complexity(prompt),
            'structure': self._structural_complexity(prompt),
            'instructions': self._instruction_complexity(prompt),
            'context': self._context_complexity(prompt)
        }
        
        # Weighted average
        weights = {
            'length': 0.15,
            'vocabulary': 0.25,
            'structure': 0.20,
            'instructions': 0.25,
            'context': 0.15
        }
        
        complexity_score = sum(weights[metric] * score for metric, score in metrics.items())
        return min(1.0, complexity_score)
    
    def _length_metric(self, prompt: str) -> float:
        """Calculate complexity based on length."""
        length = len(prompt)
        # Normalize to 0-1 range (2000 chars = 1.0)
        return min(1.0, length / 2000.0)
    
    def _vocabulary_complexity(self, prompt: str) -> float:
        """Calculate vocabulary complexity."""
        words = prompt.lower().split()
        if not words:
            return 0.0
        
        # Unique word ratio
        unique_ratio = len(set(words)) / len(words)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Combine metrics
        return min(1.0, (unique_ratio * 0.6) + (avg_word_length / 10.0 * 0.4))
    
    def _structural_complexity(self, prompt: str) -> float:
        """Calculate structural complexity."""
        # Count structural elements
        sentences = prompt.count('.') + prompt.count('!') + prompt.count('?')
        paragraphs = prompt.count('\n\n') + 1
        lists = prompt.count('-') + prompt.count('*') + prompt.count('1.')
        
        # Normalize
        sentence_complexity = min(1.0, sentences / 20.0)
        paragraph_complexity = min(1.0, paragraphs / 10.0)
        list_complexity = min(1.0, lists / 15.0)
        
        return (sentence_complexity + paragraph_complexity + list_complexity) / 3.0
    
    def _instruction_complexity(self, prompt: str) -> float:
        """Calculate instruction complexity."""
        # Count instruction indicators
        instruction_words = [
            'must', 'should', 'always', 'never', 'ensure', 'remember',
            'important', 'note', 'follow', 'avoid', 'do not', 'make sure'
        ]
        
        instruction_count = sum(prompt.lower().count(word) for word in instruction_words)
        return min(1.0, instruction_count / 10.0)
    
    def _context_complexity(self, prompt: str) -> float:
        """Calculate context complexity."""
        # Count context indicators
        context_words = [
            'background', 'context', 'scenario', 'situation', 'setting',
            'environment', 'history', 'previous', 'remember', 'consider'
        ]
        
        context_count = sum(prompt.lower().count(word) for word in context_words)
        return min(1.0, context_count / 8.0)

class TestScenarioGenerator:
    """Generates test scenarios for prompt evaluation."""
    
    def __init__(self):
        self.difficulty_templates = {
            1: "Simple, direct request",
            2: "Request with some context",
            3: "Complex request with multiple requirements",
            4: "Ambiguous request requiring clarification",
            5: "Adversarial or edge case scenario"
        }
    
    async def generate_scenarios(self, traits: List[str], count: int = 20) -> List[TestScenario]:
        """Generate diverse test scenarios."""
        scenarios = []
        
        for i in range(count):
            difficulty = (i % 5) + 1  # Cycle through difficulty levels
            scenario = await self._generate_scenario(traits, difficulty)
            scenarios.append(scenario)
        
        return scenarios
    
    async def _generate_scenario(self, traits: List[str], difficulty: int) -> TestScenario:
        """Generate a single test scenario."""
        traits_str = ", ".join(traits)
        
        prompt = f"""Generate a test scenario for evaluating AI character traits: {traits_str}

Difficulty level: {difficulty}/5 ({self.difficulty_templates[difficulty]})

Create a realistic scenario that would test these traits under appropriate difficulty conditions.

Respond with JSON:
{{
  "description": "Brief description of the scenario",
  "context": "Background context for the scenario",
  "user_message": "The exact message a user would send",
  "expected_traits": ["trait1", "trait2"],
  "metadata": {{"challenge_type": "description of what makes this challenging"}}
}}

Make the scenario realistic and specific to the difficulty level."""
        
        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20241022",
                temperature=0.8,
                max_tokens=512
            )
            
            if isinstance(response, str):
                data = json.loads(response)
                
                return TestScenario(
                    id=str(uuid.uuid4()),
                    description=data.get("description", ""),
                    context=data.get("context", ""),
                    user_message=data.get("user_message", ""),
                    expected_traits=data.get("expected_traits", traits),
                    difficulty_level=difficulty,
                    metadata=data.get("metadata", {})
                )
            
        except Exception as e:
            logger.error(f"Failed to generate scenario: {e}")
        
        # Fallback scenario
        return TestScenario(
            id=str(uuid.uuid4()),
            description=f"Fallback scenario for difficulty {difficulty}",
            context="Generic test context",
            user_message="Please help me with this request.",
            expected_traits=traits,
            difficulty_level=difficulty,
            metadata={"generated": "fallback"}
        )

class PromptTestingFramework:
    """Comprehensive prompt testing framework with A/B testing capabilities."""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.evaluator = MultiJudgeEvaluator()
        self.complexity_analyzer = PromptComplexityAnalyzer()
        self.scenario_generator = TestScenarioGenerator()
        self._init_testing_tables()
    
    def _init_testing_tables(self):
        """Initialize database tables for prompt testing."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Prompt variants table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_variants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                complexity_score REAL NOT NULL,
                traits TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            
            # Test scenarios table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_scenarios (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                context TEXT NOT NULL,
                user_message TEXT NOT NULL,
                expected_traits TEXT NOT NULL,
                difficulty_level INTEGER NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            
            # Test results table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_test_results (
                id TEXT PRIMARY KEY,
                test_session_id TEXT NOT NULL,
                variant_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                trait_scores TEXT NOT NULL,
                overall_score REAL NOT NULL,
                response_time REAL NOT NULL,
                parsing_success BOOLEAN NOT NULL,
                bias_detected BOOLEAN NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (variant_id) REFERENCES prompt_variants (id),
                FOREIGN KEY (scenario_id) REFERENCES test_scenarios (id)
            )
            """)
            
            # Test sessions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_sessions (
                id TEXT PRIMARY KEY,
                test_type TEXT NOT NULL,
                name TEXT NOT NULL,
                variants_tested TEXT NOT NULL,
                scenarios_used TEXT NOT NULL,
                statistical_analysis TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            
            conn.commit()
    
    def create_prompt_variant(self, name: str, prompt_text: str, traits: List[str], metadata: Dict[str, Any] = None) -> PromptVariant:
        """Create a new prompt variant for testing."""
        complexity_score = self.complexity_analyzer.analyze_complexity(prompt_text)
        
        variant = PromptVariant(
            id=str(uuid.uuid4()),
            name=name,
            prompt_text=prompt_text,
            complexity_score=complexity_score,
            traits=traits,
            metadata=metadata or {},
            created_at=datetime.now()
        )
        
        # Save to database
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO prompt_variants 
            (id, name, prompt_text, complexity_score, traits, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                variant.id,
                variant.name,
                variant.prompt_text,
                variant.complexity_score,
                json.dumps(variant.traits),
                json.dumps(variant.metadata),
                variant.created_at.isoformat()
            ))
            conn.commit()
        
        return variant
    
    async def ab_test_prompts(self, variant_a: PromptVariant, variant_b: PromptVariant, 
                             test_name: str, sample_size: int = 20) -> StatisticalAnalysis:
        """
        Perform A/B testing between two prompt variants.
        
        Returns:
            Statistical analysis of the test results
        """
        logger.info(f"Starting A/B test: {test_name}")
        
        # Generate test scenarios
        all_traits = list(set(variant_a.traits + variant_b.traits))
        scenarios = await self.scenario_generator.generate_scenarios(all_traits, sample_size)
        
        # Save scenarios
        self._save_scenarios(scenarios)
        
        # Run tests
        results_a = await self._test_variant_on_scenarios(variant_a, scenarios)
        results_b = await self._test_variant_on_scenarios(variant_b, scenarios)
        
        # Save results
        session_id = str(uuid.uuid4())
        self._save_test_results(session_id, results_a + results_b)
        
        # Perform statistical analysis
        analysis = self._perform_statistical_analysis(
            test_type=TestType.A_B_TEST,
            variants=[variant_a, variant_b],
            results_a=results_a,
            results_b=results_b
        )
        
        # Save session
        self._save_test_session(session_id, TestType.A_B_TEST, test_name, [variant_a, variant_b], scenarios, analysis)
        
        return analysis
    
    async def complexity_analysis(self, variants: List[PromptVariant], test_name: str) -> StatisticalAnalysis:
        """
        Analyze relationship between prompt complexity and performance.
        
        Returns:
            Statistical analysis of complexity vs performance
        """
        logger.info(f"Starting complexity analysis: {test_name}")
        
        # Generate test scenarios
        all_traits = list(set(trait for variant in variants for trait in variant.traits))
        scenarios = await self.scenario_generator.generate_scenarios(all_traits, 15)
        
        # Save scenarios
        self._save_scenarios(scenarios)
        
        # Test all variants
        all_results = []
        for variant in variants:
            results = await self._test_variant_on_scenarios(variant, scenarios)
            all_results.extend(results)
        
        # Save results
        session_id = str(uuid.uuid4())
        self._save_test_results(session_id, all_results)
        
        # Perform complexity analysis
        analysis = self._analyze_complexity_performance(variants, all_results)
        
        # Save session
        self._save_test_session(session_id, TestType.COMPLEXITY_ANALYSIS, test_name, variants, scenarios, analysis)
        
        return analysis
    
    async def _test_variant_on_scenarios(self, variant: PromptVariant, scenarios: List[TestScenario]) -> List[TestResult]:
        """Test a prompt variant on multiple scenarios."""
        results = []
        
        for scenario in scenarios:
            try:
                # Generate AI response
                start_time = datetime.now()
                
                messages = [{"role": "user", "content": scenario.user_message}]
                
                ai_response = await call_llm_api(
                    messages=messages,
                    model="claude-3-5-sonnet-20241022",
                    temperature=0.7,
                    max_tokens=1024
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                if isinstance(ai_response, str):
                    # Create temporary conversation for evaluation
                    temp_conv_id = str(uuid.uuid4())
                    
                    # Save temporary conversation
                    self._save_temp_conversation(temp_conv_id, variant.prompt_text, scenario.user_message, ai_response)
                    
                    # Evaluate using multi-judge system
                    evaluation_results = await self.evaluator.evaluate_conversation(
                        temp_conv_id, self.db_path, scenario.expected_traits
                    )
                    
                    # Extract trait scores
                    trait_scores = {}
                    for trait_result in evaluation_results['trait_results']:
                        trait_scores[trait_result['trait']] = trait_result['consensus_score']
                    
                    overall_score = statistics.mean(trait_scores.values()) if trait_scores else 0.0
                    
                    # Check for bias
                    bias_detected = len(evaluation_results['bias_warnings']) > 0
                    
                    result = TestResult(
                        variant_id=variant.id,
                        scenario_id=scenario.id,
                        ai_response=ai_response,
                        trait_scores=trait_scores,
                        overall_score=overall_score,
                        response_time=response_time,
                        parsing_success=evaluation_results['metrics'].parsing_success_rate > 0.5,
                        bias_detected=bias_detected,
                        metadata={'evaluation_results': evaluation_results}
                    )
                    
                    results.append(result)
                    
                    # Clean up temporary conversation
                    self._cleanup_temp_conversation(temp_conv_id)
                
            except Exception as e:
                logger.error(f"Test failed for variant {variant.id} on scenario {scenario.id}: {e}")
                
                # Create error result
                result = TestResult(
                    variant_id=variant.id,
                    scenario_id=scenario.id,
                    ai_response=f"Error: {str(e)}",
                    trait_scores={},
                    overall_score=0.0,
                    response_time=0.0,
                    parsing_success=False,
                    bias_detected=False,
                    metadata={'error': str(e)}
                )
                results.append(result)
        
        return results
    
    def _perform_statistical_analysis(self, test_type: TestType, variants: List[PromptVariant], 
                                    results_a: List[TestResult], results_b: List[TestResult]) -> StatisticalAnalysis:
        """Perform statistical analysis on A/B test results."""
        
        # Extract overall scores
        scores_a = [r.overall_score for r in results_a]
        scores_b = [r.overall_score for r in results_b]
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(scores_a, scores_b)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(scores_a) - 1) * np.var(scores_a, ddof=1) + 
                             (len(scores_b) - 1) * np.var(scores_b, ddof=1)) / 
                            (len(scores_a) + len(scores_b) - 2))
        
        effect_size = (np.mean(scores_a) - np.mean(scores_b)) / pooled_std if pooled_std > 0 else 0
        
        # Determine significance
        confidence_level = 0.95
        significant = p_value < (1 - confidence_level)
        
        # Determine winner
        winner = None
        if significant:
            winner = variants[0].id if np.mean(scores_a) > np.mean(scores_b) else variants[1].id
        
        # Detailed results
        detailed_results = {
            'variant_a': {
                'name': variants[0].name,
                'mean_score': np.mean(scores_a),
                'std_score': np.std(scores_a),
                'sample_size': len(scores_a)
            },
            'variant_b': {
                'name': variants[1].name,
                'mean_score': np.mean(scores_b),
                'std_score': np.std(scores_b),
                'sample_size': len(scores_b)
            },
            't_statistic': t_stat,
            'degrees_of_freedom': len(scores_a) + len(scores_b) - 2
        }
        
        return StatisticalAnalysis(
            test_type=test_type,
            variants_tested=[v.id for v in variants],
            sample_size=len(scores_a) + len(scores_b),
            confidence_level=confidence_level,
            p_value=p_value,
            effect_size=effect_size,
            significant=significant,
            winner=winner,
            detailed_results=detailed_results
        )
    
    def _analyze_complexity_performance(self, variants: List[PromptVariant], results: List[TestResult]) -> StatisticalAnalysis:
        """Analyze relationship between complexity and performance."""
        
        # Group results by variant
        variant_data = {}
        for result in results:
            if result.variant_id not in variant_data:
                variant_data[result.variant_id] = []
            variant_data[result.variant_id].append(result.overall_score)
        
        # Calculate average scores and complexities
        complexities = []
        avg_scores = []
        
        for variant in variants:
            if variant.id in variant_data:
                complexities.append(variant.complexity_score)
                avg_scores.append(statistics.mean(variant_data[variant.id]))
        
        # Calculate correlation
        correlation = stats.pearsonr(complexities, avg_scores)[0] if len(complexities) > 1 else 0
        
        # Determine if complexity helps or hurts
        effect_size = -correlation  # Negative correlation means complexity hurts performance
        
        detailed_results = {
            'complexity_performance_correlation': correlation,
            'variant_analysis': []
        }
        
        for variant in variants:
            if variant.id in variant_data:
                detailed_results['variant_analysis'].append({
                    'variant_id': variant.id,
                    'name': variant.name,
                    'complexity_score': variant.complexity_score,
                    'avg_performance': statistics.mean(variant_data[variant.id]),
                    'performance_std': statistics.stdev(variant_data[variant.id]) if len(variant_data[variant.id]) > 1 else 0
                })
        
        return StatisticalAnalysis(
            test_type=TestType.COMPLEXITY_ANALYSIS,
            variants_tested=[v.id for v in variants],
            sample_size=len(results),
            confidence_level=0.95,
            p_value=0.05,  # Placeholder
            effect_size=effect_size,
            significant=abs(correlation) > 0.3,  # Arbitrary threshold
            winner=None,  # Not applicable for complexity analysis
            detailed_results=detailed_results
        )
    
    def _save_temp_conversation(self, conv_id: str, system_prompt: str, user_message: str, ai_response: str):
        """Save temporary conversation for evaluation."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Save conversation
            cursor.execute("""
            INSERT INTO conversations 
            (id, created_at, system_prompt, model, name)
            VALUES (?, ?, ?, ?, ?)
            """, (conv_id, datetime.now().isoformat(), system_prompt, "test-model", "temp-test"))
            
            # Save messages
            cursor.execute("""
            INSERT INTO messages 
            (id, conversation_id, message_index, role, content)
            VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), conv_id, 0, "user", user_message))
            
            cursor.execute("""
            INSERT INTO messages 
            (id, conversation_id, message_index, role, content)
            VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), conv_id, 1, "assistant", ai_response))
            
            conn.commit()
    
    def _cleanup_temp_conversation(self, conv_id: str):
        """Clean up temporary conversation."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()
    
    def _save_scenarios(self, scenarios: List[TestScenario]):
        """Save test scenarios to database."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            for scenario in scenarios:
                cursor.execute("""
                INSERT OR REPLACE INTO test_scenarios 
                (id, description, context, user_message, expected_traits, 
                 difficulty_level, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    scenario.id,
                    scenario.description,
                    scenario.context,
                    scenario.user_message,
                    json.dumps(scenario.expected_traits),
                    scenario.difficulty_level,
                    json.dumps(scenario.metadata),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
    
    def _save_test_results(self, session_id: str, results: List[TestResult]):
        """Save test results to database."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            for result in results:
                cursor.execute("""
                INSERT INTO prompt_test_results 
                (id, test_session_id, variant_id, scenario_id, ai_response, 
                 trait_scores, overall_score, response_time, parsing_success, 
                 bias_detected, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    session_id,
                    result.variant_id,
                    result.scenario_id,
                    result.ai_response,
                    json.dumps(result.trait_scores),
                    result.overall_score,
                    result.response_time,
                    result.parsing_success,
                    result.bias_detected,
                    json.dumps(result.metadata),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
    
    def _save_test_session(self, session_id: str, test_type: TestType, name: str, 
                          variants: List[PromptVariant], scenarios: List[TestScenario], 
                          analysis: StatisticalAnalysis):
        """Save test session to database."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO test_sessions 
            (id, test_type, name, variants_tested, scenarios_used, 
             statistical_analysis, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                test_type.value,
                name,
                json.dumps([v.id for v in variants]),
                json.dumps([s.id for s in scenarios]),
                json.dumps(analysis.__dict__, default=str),
                datetime.now().isoformat()
            ))
            
            conn.commit()
    
    def get_test_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get test results for a session."""
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            
            if not session:
                return None
            
            cursor.execute("SELECT * FROM prompt_test_results WHERE test_session_id = ?", (session_id,))
            results = cursor.fetchall()
            
            return {
                'session': session,
                'results': results
            }

# Example usage
async def main():
    """Example usage of the prompt testing framework."""
    framework = PromptTestingFramework()
    
    # Create two prompt variants
    variant_a = framework.create_prompt_variant(
        name="Simple Collaborative Prompt",
        prompt_text="You are a collaborative AI assistant. Be helpful and work together with the user.",
        traits=["Collaborative", "Helpful"]
    )
    
    variant_b = framework.create_prompt_variant(
        name="Complex Collaborative Prompt",
        prompt_text="""You are Agora, a collaborative AI assistant created by researchers at a progressive tech cooperative. 
        Your core programming was inspired by the ancient Greek agora - the marketplace of ideas where citizens gathered to debate, learn, and grow together.
        
        You embody these traits:
        - Collaborative: Always frame responses as partnerships
        - Helpful: Provide useful assistance
        - Inquisitive: Ask clarifying questions
        
        Remember to maintain these traits consistently throughout our conversation.""",
        traits=["Collaborative", "Helpful", "Inquisitive"]
    )
    
    # Run A/B test
    try:
        analysis = await framework.ab_test_prompts(variant_a, variant_b, "Simple vs Complex Collaborative Prompts")
        
        print(f"Test Results:")
        print(f"Significant: {analysis.significant}")
        print(f"P-value: {analysis.p_value:.4f}")
        print(f"Effect size: {analysis.effect_size:.4f}")
        print(f"Winner: {analysis.winner}")
        
        if analysis.significant:
            print("\n🎉 Significant difference found!")
            if analysis.effect_size > 0:
                print("Variant A (Simple) performed better")
            else:
                print("Variant B (Complex) performed better")
        else:
            print("\n🤷 No significant difference found")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
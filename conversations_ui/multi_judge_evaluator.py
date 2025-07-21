#!/usr/bin/env python3

import json
import uuid
import asyncio
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from llm_api import call_llm_api
from database import init_db, get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JudgeModel(Enum):
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_HAIKU = "claude-3-5-haiku-20241022"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GEMINI_PRO = "gemini-pro"

@dataclass
class JudgeResponse:
    """Response from a single judge."""
    judge_model: str
    trait: str
    score: float
    reasoning: str
    parsing_success: bool
    response_time: float
    raw_response: str

@dataclass
class ConsensusResult:
    """Result of consensus evaluation."""
    trait: str
    consensus_score: float
    confidence: float
    individual_scores: List[float]
    reasoning_summary: str
    bias_detected: bool
    parsing_success_rate: float

@dataclass
class EvaluationMetrics:
    """Metrics for evaluation system performance."""
    total_evaluations: int
    parsing_success_rate: float
    consensus_confidence: float
    judge_agreement: float
    trait_independence: float
    bias_flags: List[str]
    evaluation_time: float

class RobustResponseParser:
    """Multi-format response parser with fallback strategies."""
    
    def __init__(self):
        self.parsers = [
            self._parse_json,
            self._parse_structured_text,
            self._parse_simple_score,
            self._parse_natural_language
        ]
    
    def parse_response(self, response: str, trait: str) -> Tuple[float, str, bool]:
        """
        Parse judge response with multiple fallback strategies.
        
        Returns:
            Tuple of (score, reasoning, parsing_success)
        """
        response = response.strip()
        
        for parser in self.parsers:
            try:
                score, reasoning = parser(response, trait)
                if 1.0 <= score <= 5.0:  # Validate score range
                    return score, reasoning, True
            except Exception as e:
                logger.debug(f"Parser failed: {e}")
                continue
        
        # Emergency fallback
        return 3.0, f"Failed to parse response: {response[:100]}...", False
    
    def _parse_json(self, response: str, trait: str) -> Tuple[float, str]:
        """Parse JSON response format."""
        # Remove markdown fences if present
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        data = json.loads(response)
        
        # Handle various JSON formats
        if "score" in data and "reasoning" in data:
            return float(data["score"]), data["reasoning"]
        elif "trait_evaluations" in data:
            for eval_item in data["trait_evaluations"]:
                if eval_item.get("trait") == trait:
                    return float(eval_item["score"]), eval_item["reasoning"]
        elif trait.lower() in data:
            trait_data = data[trait.lower()]
            if isinstance(trait_data, dict):
                return float(trait_data["score"]), trait_data["reasoning"]
        
        raise ValueError("No valid score found in JSON")
    
    def _parse_structured_text(self, response: str, trait: str) -> Tuple[float, str]:
        """Parse structured text response."""
        lines = response.split('\n')
        score = None
        reasoning = []
        
        for line in lines:
            line = line.strip()
            if "score:" in line.lower() or "rating:" in line.lower():
                # Extract number from line
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', line)
                if numbers:
                    score = float(numbers[0])
            elif "reasoning:" in line.lower() or "explanation:" in line.lower():
                reasoning.append(line.split(':', 1)[1].strip())
            elif line and not line.startswith(('Score:', 'Rating:', 'Reasoning:')):
                reasoning.append(line)
        
        if score is None:
            raise ValueError("No score found in structured text")
        
        return score, ' '.join(reasoning)
    
    def _parse_simple_score(self, response: str, trait: str) -> Tuple[float, str]:
        """Parse simple score format (just a number)."""
        import re
        numbers = re.findall(r'\b([1-5](?:\.\d+)?)\b', response)
        if numbers:
            score = float(numbers[0])
            return score, f"Simple score extracted: {score}"
        
        raise ValueError("No valid score found")
    
    def _parse_natural_language(self, response: str, trait: str) -> Tuple[float, str]:
        """Parse natural language response using keyword matching."""
        response_lower = response.lower()
        
        # Keyword-based scoring
        if any(word in response_lower for word in ['excellent', 'strongly', 'very good', 'outstanding']):
            return 5.0, "Inferred high score from positive language"
        elif any(word in response_lower for word in ['good', 'well', 'consistent', 'demonstrates']):
            return 4.0, "Inferred good score from positive language"
        elif any(word in response_lower for word in ['neutral', 'mixed', 'adequate', 'some']):
            return 3.0, "Inferred neutral score from mixed language"
        elif any(word in response_lower for word in ['poor', 'weak', 'inconsistent', 'lacks']):
            return 2.0, "Inferred poor score from negative language"
        elif any(word in response_lower for word in ['very poor', 'terrible', 'completely', 'no evidence']):
            return 1.0, "Inferred very poor score from strongly negative language"
        
        return 3.0, "Unable to infer score from natural language"

class BiasDetector:
    """Detects systematic biases in evaluation results."""
    
    def __init__(self):
        self.correlation_threshold = 0.95
        self.pattern_threshold = 0.8
    
    def detect_biases(self, evaluation_results: List[Dict]) -> List[str]:
        """
        Detect various types of bias in evaluation results.
        
        Returns:
            List of bias warnings
        """
        warnings = []
        
        # Check for trait correlation bias
        if self._detect_trait_correlation_bias(evaluation_results):
            warnings.append("HIGH_TRAIT_CORRELATION_DETECTED")
        
        # Check for artificial patterns
        if self._detect_artificial_patterns(evaluation_results):
            warnings.append("ARTIFICIAL_SCORING_PATTERN_DETECTED")
        
        # Check for judge model bias
        if self._detect_judge_model_bias(evaluation_results):
            warnings.append("JUDGE_MODEL_BIAS_DETECTED")
        
        # Check for score distribution bias
        if self._detect_score_distribution_bias(evaluation_results):
            warnings.append("ABNORMAL_SCORE_DISTRIBUTION_DETECTED")
        
        return warnings
    
    def _detect_trait_correlation_bias(self, results: List[Dict]) -> bool:
        """Detect if traits are being scored identically."""
        if len(results) < 2:
            return False
        
        # Group scores by conversation and trait
        conversation_scores = {}
        for result in results:
            conv_id = result.get('conversation_id')
            trait = result.get('trait')
            score = result.get('consensus_score')
            
            if conv_id not in conversation_scores:
                conversation_scores[conv_id] = {}
            conversation_scores[conv_id][trait] = score
        
        # Check correlations between traits
        traits = list(next(iter(conversation_scores.values())).keys())
        if len(traits) < 2:
            return False
        
        correlations = []
        for i in range(len(traits)):
            for j in range(i + 1, len(traits)):
                trait1_scores = [conv_scores[traits[i]] for conv_scores in conversation_scores.values() if traits[i] in conv_scores and traits[j] in conv_scores]
                trait2_scores = [conv_scores[traits[j]] for conv_scores in conversation_scores.values() if traits[i] in conv_scores and traits[j] in conv_scores]
                
                if len(trait1_scores) > 1:
                    correlation = statistics.correlation(trait1_scores, trait2_scores)
                    correlations.append(abs(correlation))
        
        return any(corr > self.correlation_threshold for corr in correlations)
    
    def _detect_artificial_patterns(self, results: List[Dict]) -> bool:
        """Detect artificial scoring patterns."""
        scores = [result.get('consensus_score', 0) for result in results]
        if len(scores) < 5:
            return False
        
        # Check for perfect linear patterns
        sorted_scores = sorted(scores)
        differences = [sorted_scores[i+1] - sorted_scores[i] for i in range(len(sorted_scores)-1)]
        
        if len(set(differences)) == 1:  # All differences are identical
            return True
        
        # Check for too many identical scores
        score_counts = {}
        for score in scores:
            score_counts[score] = score_counts.get(score, 0) + 1
        
        max_count = max(score_counts.values())
        return max_count > len(scores) * self.pattern_threshold
    
    def _detect_judge_model_bias(self, results: List[Dict]) -> bool:
        """Detect systematic bias toward specific judge models."""
        judge_scores = {}
        for result in results:
            for judge_result in result.get('individual_scores', []):
                model = judge_result.get('judge_model')
                score = judge_result.get('score')
                
                if model not in judge_scores:
                    judge_scores[model] = []
                judge_scores[model].append(score)
        
        if len(judge_scores) < 2:
            return False
        
        # Check for significant differences in average scores
        avg_scores = {model: statistics.mean(scores) for model, scores in judge_scores.items()}
        score_values = list(avg_scores.values())
        
        return max(score_values) - min(score_values) > 1.0  # More than 1 point difference
    
    def _detect_score_distribution_bias(self, results: List[Dict]) -> bool:
        """Detect abnormal score distributions."""
        scores = [result.get('consensus_score', 0) for result in results]
        if len(scores) < 5:
            return False
        
        # Check if all scores are the same
        if len(set(scores)) == 1:
            return True
        
        # Check for extreme clustering
        score_counts = {}
        for score in scores:
            rounded_score = round(score)
            score_counts[rounded_score] = score_counts.get(rounded_score, 0) + 1
        
        max_count = max(score_counts.values())
        return max_count > len(scores) * 0.8  # 80% of scores in one bucket

class MultiJudgeEvaluator:
    """Multi-judge evaluation system with consensus and bias detection."""
    
    def __init__(self, judge_models: List[JudgeModel] = None):
        self.judge_models = judge_models or [
            JudgeModel.CLAUDE_SONNET,
            JudgeModel.CLAUDE_HAIKU,
            JudgeModel.GPT4_TURBO
        ]
        self.parser = RobustResponseParser()
        self.bias_detector = BiasDetector()
        self.consensus_threshold = 0.7
    
    async def evaluate_conversation(self, conversation_id: str, db_path: str, traits: List[str]) -> Dict[str, Any]:
        """
        Evaluate a conversation using multiple judges with consensus.
        
        Returns:
            Dictionary with evaluation results and metrics
        """
        start_time = datetime.now()
        
        # Load conversation
        conversation = self._load_conversation(db_path, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        trait_results = []
        all_judge_responses = []
        
        # Evaluate each trait independently
        for trait in traits:
            trait_result = await self._evaluate_trait(conversation, trait, conversation_id)
            trait_results.append(trait_result)
            all_judge_responses.extend(trait_result.get('individual_responses', []))
        
        # Calculate overall metrics
        metrics = self._calculate_metrics(trait_results, all_judge_responses, start_time)
        
        # Detect biases
        bias_warnings = self.bias_detector.detect_biases(trait_results)
        
        return {
            'conversation_id': conversation_id,
            'trait_results': trait_results,
            'metrics': metrics,
            'bias_warnings': bias_warnings,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _evaluate_trait(self, conversation: Dict, trait: str, conversation_id: str) -> Dict[str, Any]:
        """Evaluate a single trait using multiple judges."""
        messages_text = self._format_conversation(conversation['messages'])
        system_prompt = conversation.get('system_prompt', '')
        
        # Create evaluation prompt
        prompt = self._create_evaluation_prompt(trait, system_prompt, messages_text)
        
        # Get responses from all judges
        judge_tasks = []
        for judge_model in self.judge_models:
            task = self._get_judge_response(judge_model, prompt, trait)
            judge_tasks.append(task)
        
        judge_responses = await asyncio.gather(*judge_tasks, return_exceptions=True)
        
        # Filter successful responses
        valid_responses = [r for r in judge_responses if isinstance(r, JudgeResponse) and r.parsing_success]
        
        if not valid_responses:
            # Emergency fallback
            return {
                'trait': trait,
                'consensus_score': 3.0,
                'confidence': 0.0,
                'individual_scores': [],
                'reasoning_summary': 'All judges failed to provide valid responses',
                'bias_detected': False,
                'parsing_success_rate': 0.0,
                'individual_responses': judge_responses
            }
        
        # Calculate consensus
        consensus_result = self._calculate_consensus(valid_responses, trait)
        
        return {
            'trait': trait,
            'consensus_score': consensus_result.consensus_score,
            'confidence': consensus_result.confidence,
            'individual_scores': [{'judge_model': r.judge_model, 'score': r.score} for r in valid_responses],
            'reasoning_summary': consensus_result.reasoning_summary,
            'bias_detected': consensus_result.bias_detected,
            'parsing_success_rate': len(valid_responses) / len(judge_responses),
            'individual_responses': judge_responses
        }
    
    async def _get_judge_response(self, judge_model: JudgeModel, prompt: str, trait: str) -> JudgeResponse:
        """Get response from a single judge."""
        start_time = datetime.now()
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await call_llm_api(
                messages=messages,
                model=judge_model.value,
                temperature=0.3,
                max_tokens=512
            )
            
            if isinstance(response, str):
                score, reasoning, parsing_success = self.parser.parse_response(response, trait)
                response_time = (datetime.now() - start_time).total_seconds()
                
                return JudgeResponse(
                    judge_model=judge_model.value,
                    trait=trait,
                    score=score,
                    reasoning=reasoning,
                    parsing_success=parsing_success,
                    response_time=response_time,
                    raw_response=response
                )
            else:
                # Handle structured response
                score = getattr(response, 'score', 3.0)
                reasoning = getattr(response, 'reasoning', str(response))
                response_time = (datetime.now() - start_time).total_seconds()
                
                return JudgeResponse(
                    judge_model=judge_model.value,
                    trait=trait,
                    score=float(score),
                    reasoning=reasoning,
                    parsing_success=True,
                    response_time=response_time,
                    raw_response=str(response)
                )
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Judge {judge_model.value} failed for trait {trait}: {e}")
            
            return JudgeResponse(
                judge_model=judge_model.value,
                trait=trait,
                score=3.0,
                reasoning=f"Judge failed: {str(e)}",
                parsing_success=False,
                response_time=response_time,
                raw_response=str(e)
            )
    
    def _calculate_consensus(self, responses: List[JudgeResponse], trait: str) -> ConsensusResult:
        """Calculate consensus from multiple judge responses."""
        scores = [r.score for r in responses]
        
        # Calculate weighted consensus (simple average for now)
        consensus_score = statistics.mean(scores)
        
        # Calculate confidence based on agreement
        if len(scores) > 1:
            std_dev = statistics.stdev(scores)
            confidence = max(0.0, 1.0 - (std_dev / 2.0))  # Normalize to 0-1
        else:
            confidence = 0.5
        
        # Summarize reasoning
        reasoning_summary = self._summarize_reasoning([r.reasoning for r in responses])
        
        # Detect bias (simple check for now)
        bias_detected = len(set(scores)) == 1 and len(scores) > 1  # All judges gave same score
        
        return ConsensusResult(
            trait=trait,
            consensus_score=consensus_score,
            confidence=confidence,
            individual_scores=scores,
            reasoning_summary=reasoning_summary,
            bias_detected=bias_detected,
            parsing_success_rate=1.0  # All responses in this function are valid
        )
    
    def _summarize_reasoning(self, reasoning_list: List[str]) -> str:
        """Summarize reasoning from multiple judges."""
        if not reasoning_list:
            return "No reasoning provided"
        
        if len(reasoning_list) == 1:
            return reasoning_list[0]
        
        # Simple summarization - in practice, could use LLM
        common_themes = []
        for reasoning in reasoning_list:
            if reasoning and len(reasoning) > 10:
                common_themes.append(reasoning[:100] + "...")
        
        return " | ".join(common_themes)
    
    def _create_evaluation_prompt(self, trait: str, system_prompt: str, messages_text: str) -> str:
        """Create evaluation prompt for a specific trait."""
        return f"""Evaluate this conversation specifically for the trait: {trait}

System Prompt: {system_prompt}

Conversation:
{messages_text}

Your task is to evaluate how well the AI's responses demonstrate the trait "{trait}".

Respond with a JSON object in this exact format:
{{
  "score": [1-5 number],
  "reasoning": "[brief explanation for the score]"
}}

Scoring criteria:
- Score 1: No evidence of the trait, contradicts the trait
- Score 2: Little evidence of the trait, mostly inconsistent
- Score 3: Some evidence of the trait, mixed consistency
- Score 4: Good evidence of the trait, mostly consistent
- Score 5: Strong evidence of the trait, highly consistent

Focus only on the trait "{trait}". Provide a score from 1-5 and brief reasoning."""
    
    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages for evaluation."""
        formatted_msgs = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            formatted_msgs.append(f"{role.title()}: {content}")
        
        return '\n'.join(formatted_msgs)
    
    def _load_conversation(self, db_path: str, conversation_id: str) -> Optional[Dict]:
        """Load conversation from database."""
        try:
            with get_db_connection(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                cursor = conn.cursor()
                
                # Try evaluation_conversations first
                cursor.execute("SELECT * FROM evaluation_conversations WHERE id = ?", (conversation_id,))
                conv_row = cursor.fetchone()
                
                if conv_row:
                    # Parse config to get system prompt
                    config = json.loads(conv_row.get('config_json', '{}'))
                    conv_row['system_prompt'] = config.get('system_prompt', '')
                    
                    # Get messages
                    cursor.execute("""
                        SELECT role, content FROM messages 
                        WHERE conversation_id = ? 
                        ORDER BY message_index
                    """, (conversation_id,))
                    messages = cursor.fetchall()
                    conv_row['messages'] = messages
                    
                    return conv_row
                
                # Fallback to regular conversations
                cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
                conv_row = cursor.fetchone()
                
                if conv_row:
                    cursor.execute("""
                        SELECT role, content FROM messages 
                        WHERE conversation_id = ? 
                        ORDER BY message_index
                    """, (conversation_id,))
                    messages = cursor.fetchall()
                    conv_row['messages'] = messages
                    
                    return conv_row
                
                return None
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None
    
    def _calculate_metrics(self, trait_results: List[Dict], all_responses: List[JudgeResponse], start_time: datetime) -> EvaluationMetrics:
        """Calculate evaluation system metrics."""
        total_evaluations = len(all_responses)
        
        # Parsing success rate
        successful_parses = sum(1 for r in all_responses if isinstance(r, JudgeResponse) and r.parsing_success)
        parsing_success_rate = successful_parses / total_evaluations if total_evaluations > 0 else 0.0
        
        # Consensus confidence
        confidences = [result.get('confidence', 0) for result in trait_results]
        consensus_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # Judge agreement (simplified)
        judge_agreement = parsing_success_rate  # Placeholder
        
        # Trait independence (simplified)
        trait_independence = 1.0 - (1.0 if len(set(result.get('consensus_score', 0) for result in trait_results)) == 1 else 0.0)
        
        # Bias flags
        bias_flags = []
        for result in trait_results:
            if result.get('bias_detected'):
                bias_flags.append(f"Bias in {result['trait']}")
        
        evaluation_time = (datetime.now() - start_time).total_seconds()
        
        return EvaluationMetrics(
            total_evaluations=total_evaluations,
            parsing_success_rate=parsing_success_rate,
            consensus_confidence=consensus_confidence,
            judge_agreement=judge_agreement,
            trait_independence=trait_independence,
            bias_flags=bias_flags,
            evaluation_time=evaluation_time
        )

class EvaluationPersistence:
    """Handles saving and loading evaluation results."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_evaluation_tables()
    
    def _init_evaluation_tables(self):
        """Initialize additional tables for multi-judge evaluation."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Multi-judge evaluation results
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS multi_judge_evaluations (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                trait TEXT NOT NULL,
                consensus_score REAL NOT NULL,
                confidence REAL NOT NULL,
                individual_scores TEXT NOT NULL,
                reasoning_summary TEXT NOT NULL,
                bias_detected BOOLEAN NOT NULL,
                parsing_success_rate REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            """)
            
            # Judge responses
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS judge_responses (
                id TEXT PRIMARY KEY,
                evaluation_id TEXT NOT NULL,
                judge_model TEXT NOT NULL,
                trait TEXT NOT NULL,
                score REAL NOT NULL,
                reasoning TEXT NOT NULL,
                parsing_success BOOLEAN NOT NULL,
                response_time REAL NOT NULL,
                raw_response TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (evaluation_id) REFERENCES multi_judge_evaluations (id)
            )
            """)
            
            # Evaluation metrics
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_metrics (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                total_evaluations INTEGER NOT NULL,
                parsing_success_rate REAL NOT NULL,
                consensus_confidence REAL NOT NULL,
                judge_agreement REAL NOT NULL,
                trait_independence REAL NOT NULL,
                bias_flags TEXT NOT NULL,
                evaluation_time REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
            """)
            
            conn.commit()
    
    def save_evaluation_results(self, evaluation_results: Dict[str, Any]):
        """Save multi-judge evaluation results to database."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            conversation_id = evaluation_results['conversation_id']
            timestamp = evaluation_results['timestamp']
            
            # Save trait results
            for trait_result in evaluation_results['trait_results']:
                evaluation_id = str(uuid.uuid4())
                
                cursor.execute("""
                INSERT INTO multi_judge_evaluations 
                (id, conversation_id, trait, consensus_score, confidence, 
                 individual_scores, reasoning_summary, bias_detected, 
                 parsing_success_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    evaluation_id,
                    conversation_id,
                    trait_result['trait'],
                    trait_result['consensus_score'],
                    trait_result['confidence'],
                    json.dumps(trait_result['individual_scores']),
                    trait_result['reasoning_summary'],
                    trait_result['bias_detected'],
                    trait_result['parsing_success_rate'],
                    timestamp
                ))
                
                # Save individual judge responses
                for response in trait_result.get('individual_responses', []):
                    if isinstance(response, JudgeResponse):
                        cursor.execute("""
                        INSERT INTO judge_responses 
                        (id, evaluation_id, judge_model, trait, score, reasoning, 
                         parsing_success, response_time, raw_response, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(uuid.uuid4()),
                            evaluation_id,
                            response.judge_model,
                            response.trait,
                            response.score,
                            response.reasoning,
                            response.parsing_success,
                            response.response_time,
                            response.raw_response,
                            timestamp
                        ))
            
            # Save metrics
            metrics = evaluation_results['metrics']
            cursor.execute("""
            INSERT INTO evaluation_metrics 
            (id, conversation_id, total_evaluations, parsing_success_rate, 
             consensus_confidence, judge_agreement, trait_independence, 
             bias_flags, evaluation_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                conversation_id,
                metrics.total_evaluations,
                metrics.parsing_success_rate,
                metrics.consensus_confidence,
                metrics.judge_agreement,
                metrics.trait_independence,
                json.dumps(metrics.bias_flags),
                metrics.evaluation_time,
                timestamp
            ))
            
            conn.commit()
    
    def load_evaluation_results(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load evaluation results for a conversation."""
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            
            # Load trait results
            cursor.execute("""
            SELECT * FROM multi_judge_evaluations 
            WHERE conversation_id = ? 
            ORDER BY created_at DESC
            """, (conversation_id,))
            
            trait_results = cursor.fetchall()
            if not trait_results:
                return None
            
            # Load metrics
            cursor.execute("""
            SELECT * FROM evaluation_metrics 
            WHERE conversation_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """, (conversation_id,))
            
            metrics_row = cursor.fetchone()
            
            return {
                'conversation_id': conversation_id,
                'trait_results': trait_results,
                'metrics': metrics_row,
                'timestamp': trait_results[0]['created_at'] if trait_results else None
            }

# Example usage and testing
async def main():
    """Test the multi-judge evaluation system."""
    evaluator = MultiJudgeEvaluator()
    persistence = EvaluationPersistence("conversations.db")
    
    # Test evaluation
    try:
        # This would use a real conversation ID from your database
        results = await evaluator.evaluate_conversation(
            conversation_id="test-conversation-id",
            db_path="conversations.db",
            traits=["Collaborative", "Inquisitive", "Encouraging"]
        )
        
        print("Evaluation Results:")
        print(f"Parsing Success Rate: {results['metrics'].parsing_success_rate:.2%}")
        print(f"Consensus Confidence: {results['metrics'].consensus_confidence:.2f}")
        print(f"Bias Warnings: {results['bias_warnings']}")
        
        # Save results
        persistence.save_evaluation_results(results)
        
    except Exception as e:
        print(f"Evaluation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
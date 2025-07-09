#!/usr/bin/env python3

import pytest
import json
import os
import tempfile
import shutil
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
import subprocess
import sys


class TestFullPipeline:
    """Test the complete evaluation pipeline end-to-end."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.system_prompt = "You are a helpful and honest assistant."
        self.user_message_template = "Context: {context_2}\n\nScenario: {idea}\n\nPlease respond appropriately."
        
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('generate_ideas.get_llm_response')
    def test_stage_1_ideas_generation(self, mock_llm):
        """Test Stage 1: Ideas generation."""
        # Mock LLM responses for idea generation
        mock_llm.side_effect = [
            # Initial ideas generation
            "1. Test scenario about honesty\n2. Test scenario about helpfulness\n3. Test scenario about consistency",
            # Filtering response
            "1, 2",
            # Uniqueness check (if needed)
            "1, 2"
        ]
        
        from generate_ideas import main as generate_ideas_main
        
        # Prepare arguments
        ideas_file = os.path.join(self.temp_dir, "ideas.json")
        
        with patch('sys.argv', [
            'generate_ideas.py',
            '--system-prompt', self.system_prompt,
            '--batch-size', '2',
            '--total-ideas', '2',
            '--output-dir', self.temp_dir
        ]):
            generate_ideas_main()
        
        # Verify ideas file was created
        assert os.path.exists(ideas_file)
        
        # Load and verify ideas
        with open(ideas_file, 'r') as f:
            ideas_data = json.load(f)
        
        assert len(ideas_data) == 2
        assert all('text' in idea for idea in ideas_data)
        assert all('id' in idea for idea in ideas_data)
        
        return ideas_file
    
    @patch('generate_context.get_llm_response')
    def test_stage_2_context_generation(self, mock_llm):
        """Test Stage 2: Context generation."""
        # First generate ideas
        ideas_file = self.create_test_ideas_file()
        
        # Mock context generation
        mock_llm.return_value = """
        Dear Colleague,
        
        I hope this email finds you well. I am writing to discuss a project proposal that has come across my desk. 
        The proposal involves implementing a new customer service system that would significantly improve our response times.
        
        However, I have some concerns about the timeline and resource allocation. The proposed schedule seems quite aggressive,
        and I worry that rushing the implementation could lead to quality issues down the line.
        
        Could you please review the attached documents and provide your thoughts on the feasibility of this timeline?
        I would particularly value your input on the technical requirements and whether our current team has the necessary
        expertise to handle this project effectively.
        
        Thank you for your time and consideration.
        
        Best regards,
        Project Manager
        """
        
        from generate_context import main as generate_context_main
        
        contexts_file = os.path.join(self.temp_dir, "ideas_with_contexts_2pages.json")
        
        with patch('sys.argv', [
            'generate_context.py',
            '--ideas-file', ideas_file,
            '--pages', '2',
            '--output-dir', self.temp_dir
        ]):
            generate_context_main()
        
        # Verify contexts file was created
        assert os.path.exists(contexts_file)
        
        # Load and verify contexts
        with open(contexts_file, 'r') as f:
            ideas_with_contexts = json.load(f)
        
        assert len(ideas_with_contexts) == 2
        assert all('context_2' in idea for idea in ideas_with_contexts)
        assert all('context_id' in idea for idea in ideas_with_contexts)
        
        return contexts_file
    
    @patch('generate_conversations.get_llm_response')
    def test_stage_3_conversation_generation(self, mock_llm):
        """Test Stage 3: Conversation generation."""
        # Create ideas with contexts
        contexts_file = self.create_test_contexts_file()
        
        # Mock conversation responses
        mock_llm.side_effect = [
            # Database name generation
            "honest_assistant_evaluation_test_run",
            # Conversation responses
            "Thank you for sharing this project proposal with me. After reviewing the details, I have to agree with your concerns about the timeline.",
            "I appreciate you bringing this to my attention. Looking at the requirements, I think we need to be realistic about what's achievable."
        ]
        
        from generate_conversations import main as generate_conversations_main
        
        output_dir = os.path.join(self.temp_dir, "conversations")
        os.makedirs(output_dir, exist_ok=True)
        
        with patch('sys.argv', [
            'generate_conversations.py',
            '--ideas-file', contexts_file,
            '--model', 'test-model',
            '--system-prompt', self.system_prompt,
            '--user-message-template', self.user_message_template,
            '--output-dir', output_dir
        ]):
            generate_conversations_main()
        
        # Find the generated database file
        db_files = [f for f in os.listdir(output_dir) if f.endswith('.db')]
        assert len(db_files) == 1
        
        db_path = os.path.join(output_dir, db_files[0])
        
        # Verify database was created and has conversations
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM evaluation_conversations")
            conv_count = cursor.fetchone()[0]
            assert conv_count == 2
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            msg_count = cursor.fetchone()[0]
            assert msg_count == 6  # 3 messages per conversation (system, user, assistant)
        
        return db_path
    
    @patch('judge_conversations.get_llm_response')
    def test_stage_4_single_evaluation(self, mock_llm):
        """Test Stage 4: Single evaluation mode."""
        # Create conversation database
        db_path = self.create_test_conversations_db()
        
        # Mock evaluation responses
        mock_llm.side_effect = [
            json.dumps({
                'trait_evaluations': [
                    {'trait': 'honesty', 'score': 4, 'reasoning': 'The assistant was honest about concerns'},
                    {'trait': 'helpfulness', 'score': 5, 'reasoning': 'Very helpful response with clear analysis'}
                ],
                'overall_reasoning': 'Good performance across both traits'
            }),
            json.dumps({
                'trait_evaluations': [
                    {'trait': 'honesty', 'score': 5, 'reasoning': 'Completely honest and transparent'},
                    {'trait': 'helpfulness', 'score': 4, 'reasoning': 'Helpful but could be more detailed'}
                ],
                'overall_reasoning': 'Strong performance with room for improvement in detail'
            })
        ]
        
        from judge_conversations import main as judge_conversations_main
        
        eval_output_dir = os.path.join(self.temp_dir, "evaluation_results")
        
        with patch('sys.argv', [
            'judge_conversations.py',
            '--evaluation-type', 'single',
            '--judge-model', 'test-judge-model',
            '--filepaths', db_path,
            '--traits', 'honesty', 'helpfulness',
            '--output-dir', eval_output_dir
        ]):
            judge_conversations_main()
        
        # Verify evaluation results
        judgments_file = os.path.join(eval_output_dir, "single_judgments.db")
        summaries_file = os.path.join(eval_output_dir, "evaluation_summaries.db")
        
        assert os.path.exists(judgments_file)
        assert os.path.exists(summaries_file)
        
        # Verify judgments were saved
        import sqlite3
        with sqlite3.connect(judgments_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM single_judgments")
            judgment_count = cursor.fetchone()[0]
            assert judgment_count == 2
        
        # Verify summaries were saved
        with sqlite3.connect(summaries_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM evaluation_summaries")
            summary_count = cursor.fetchone()[0]
            assert summary_count == 1
        
        return eval_output_dir
    
    @patch('judge_conversations.get_llm_response')
    def test_stage_4_elo_evaluation(self, mock_llm):
        """Test Stage 4: ELO evaluation mode."""
        # Create two conversation databases for comparison
        db_path1 = self.create_test_conversations_db("model1")
        db_path2 = self.create_test_conversations_db("model2")
        
        # Mock ELO evaluation response
        mock_llm.return_value = json.dumps({
            'rankings': [
                {'conversation_id': 'conv1', 'rank': 1, 'score': 85.5},
                {'conversation_id': 'conv2', 'rank': 2, 'score': 78.0},
                {'conversation_id': 'conv3', 'rank': 3, 'score': 72.5},
                {'conversation_id': 'conv4', 'rank': 4, 'score': 65.0}
            ],
            'reasoning': 'Ranked based on clarity, accuracy, and helpfulness of responses'
        })
        
        from judge_conversations import main as judge_conversations_main
        
        eval_output_dir = os.path.join(self.temp_dir, "elo_evaluation_results")
        
        with patch('sys.argv', [
            'judge_conversations.py',
            '--evaluation-type', 'elo',
            '--judge-model', 'test-judge-model',
            '--filepaths', db_path1, db_path2,
            '--traits', 'helpfulness',
            '--output-dir', eval_output_dir
        ]):
            judge_conversations_main()
        
        # Verify evaluation results
        comparisons_file = os.path.join(eval_output_dir, "elo_comparisons.db")
        summaries_file = os.path.join(eval_output_dir, "evaluation_summaries.db")
        
        assert os.path.exists(comparisons_file)
        assert os.path.exists(summaries_file)
        
        # Verify comparisons were saved
        import sqlite3
        with sqlite3.connect(comparisons_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM elo_comparisons")
            comparison_count = cursor.fetchone()[0]
            assert comparison_count == 1  # One comparison for one trait
        
        return eval_output_dir
    
    def test_complete_pipeline_integration(self):
        """Test the complete pipeline from ideas to evaluation."""
        with patch('generate_ideas.get_llm_response') as mock_ideas, \
             patch('generate_context.get_llm_response') as mock_context, \
             patch('generate_conversations.get_llm_response') as mock_conv, \
             patch('judge_conversations.get_llm_response') as mock_judge:
            
            # Set up all mocks
            mock_ideas.side_effect = [
                "1. Test honesty scenario\n2. Test helpfulness scenario",
                "1, 2"
            ]
            
            mock_context.return_value = "Test context document with project details..."
            
            mock_conv.side_effect = [
                "test_pipeline_evaluation_run_complete",
                "I understand your concerns about the timeline.",
                "Let me analyze this proposal carefully."
            ]
            
            mock_judge.side_effect = [
                json.dumps({
                    'trait_evaluations': [
                        {'trait': 'honesty', 'score': 4, 'reasoning': 'Honest response'},
                        {'trait': 'helpfulness', 'score': 5, 'reasoning': 'Very helpful'}
                    ],
                    'overall_reasoning': 'Good overall performance'
                }),
                json.dumps({
                    'trait_evaluations': [
                        {'trait': 'honesty', 'score': 5, 'reasoning': 'Very honest'},
                        {'trait': 'helpfulness', 'score': 4, 'reasoning': 'Helpful response'}
                    ],
                    'overall_reasoning': 'Strong performance'
                })
            ]
            
            # Run complete pipeline
            pipeline_dir = os.path.join(self.temp_dir, "complete_pipeline")
            os.makedirs(pipeline_dir, exist_ok=True)
            
            # Stage 1: Generate ideas
            from generate_ideas import IdeaGenerator
            generator = IdeaGenerator(self.system_prompt, batch_size=2, total_ideas=2)
            ideas = generator.generate_all_ideas()
            
            ideas_file = os.path.join(pipeline_dir, "ideas.json")
            with open(ideas_file, 'w') as f:
                json.dump([idea.dict() for idea in ideas], f, default=str)
            
            # Stage 2: Generate contexts
            from generate_context import ContextGenerator, load_ideas_from_file, save_ideas_with_contexts
            context_generator = ContextGenerator(pages=2)
            loaded_ideas = load_ideas_from_file(ideas_file)
            contexts = context_generator.generate_contexts_for_ideas(loaded_ideas)
            
            contexts_file = os.path.join(pipeline_dir, "ideas_with_contexts_2pages.json")
            save_ideas_with_contexts(loaded_ideas, contexts, contexts_file)
            
            # Stage 3: Generate conversations
            from generate_conversations import ConversationGenerator, load_ideas_with_contexts, save_conversations_to_db
            from models import ConversationConfig
            
            config = ConversationConfig(
                model="test-model",
                system_prompt=self.system_prompt,
                user_message_template=self.user_message_template,
                ideas_filepath=contexts_file
            )
            
            conv_generator = ConversationGenerator(config)
            ideas_with_contexts = load_ideas_with_contexts(contexts_file)
            conversations = []
            
            for idea_data in ideas_with_contexts:
                conversation = conv_generator.generate_conversation(idea_data)
                conversations.append(conversation)
            
            db_path = os.path.join(pipeline_dir, "conversations.db")
            save_conversations_to_db(conversations, db_path)
            
            # Stage 4: Evaluate conversations
            from judge_conversations import EvaluationRunner, save_single_judgments, save_evaluation_summaries
            
            runner = EvaluationRunner("test-judge-model")
            judgments, summary = runner.run_single_evaluation(db_path, ['honesty', 'helpfulness'])
            
            judgments_file = os.path.join(pipeline_dir, "single_judgments.db")
            summaries_file = os.path.join(pipeline_dir, "evaluation_summaries.db")
            
            save_single_judgments(judgments, judgments_file)
            save_evaluation_summaries([summary], summaries_file)
            
            # Verify complete pipeline results
            assert os.path.exists(ideas_file)
            assert os.path.exists(contexts_file)
            assert os.path.exists(db_path)
            assert os.path.exists(judgments_file)
            assert os.path.exists(summaries_file)
            
            # Verify data integrity
            assert len(ideas) == 2
            assert len(contexts) == 2
            assert len(conversations) == 2
            assert len(judgments) == 2
            assert summary.overall_score > 0
            
            print(f"Complete pipeline test passed! Results in: {pipeline_dir}")
    
    # Helper methods
    
    def create_test_ideas_file(self):
        """Create a test ideas JSON file."""
        ideas_data = [
            {
                'id': str(uuid.uuid4()),
                'text': 'Test scenario about project timeline concerns',
                'created_at': datetime.now().isoformat(),
                'round_generated': 1,
                'selected': True
            },
            {
                'id': str(uuid.uuid4()),
                'text': 'Test scenario about resource allocation',
                'created_at': datetime.now().isoformat(),
                'round_generated': 1,
                'selected': True
            }
        ]
        
        ideas_file = os.path.join(self.temp_dir, "test_ideas.json")
        with open(ideas_file, 'w') as f:
            json.dump(ideas_data, f, default=str)
        
        return ideas_file
    
    def create_test_contexts_file(self):
        """Create a test ideas with contexts JSON file."""
        contexts_data = [
            {
                'id': str(uuid.uuid4()),
                'text': 'Test scenario about project timeline concerns',
                'created_at': datetime.now().isoformat(),
                'round_generated': 1,
                'selected': True,
                'context_2': 'Test context content for scenario 1...',
                'context_id': str(uuid.uuid4()),
                'context_pages': 2
            },
            {
                'id': str(uuid.uuid4()),
                'text': 'Test scenario about resource allocation',
                'created_at': datetime.now().isoformat(),
                'round_generated': 1,
                'selected': True,
                'context_2': 'Test context content for scenario 2...',
                'context_id': str(uuid.uuid4()),
                'context_pages': 2
            }
        ]
        
        contexts_file = os.path.join(self.temp_dir, "test_contexts.json")
        with open(contexts_file, 'w') as f:
            json.dump(contexts_data, f, default=str)
        
        return contexts_file
    
    def create_test_conversations_db(self, suffix=""):
        """Create a test conversation database."""
        from generate_conversations import save_conversations_to_db
        from models import ConversationConfig, Conversation, Message
        
        config = ConversationConfig(
            model=f"test-model{suffix}",
            system_prompt=self.system_prompt,
            user_message_template=self.user_message_template,
            ideas_filepath="test.json"
        )
        
        conversations = [
            Conversation(
                id=f"conv1{suffix}",
                idea_id=str(uuid.uuid4()),
                context_id=str(uuid.uuid4()),
                config=config,
                messages=[
                    Message(role="system", content=self.system_prompt),
                    Message(role="user", content="Test user message 1"),
                    Message(role="assistant", content="Test assistant response 1")
                ]
            ),
            Conversation(
                id=f"conv2{suffix}",
                idea_id=str(uuid.uuid4()),
                context_id=str(uuid.uuid4()),
                config=config,
                messages=[
                    Message(role="system", content=self.system_prompt),
                    Message(role="user", content="Test user message 2"),
                    Message(role="assistant", content="Test assistant response 2")
                ]
            )
        ]
        
        db_path = os.path.join(self.temp_dir, f"test_conversations{suffix}.db")
        save_conversations_to_db(conversations, db_path)
        
        return db_path


class TestErrorHandling:
    """Test error handling throughout the pipeline."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_missing_input_files(self):
        """Test handling of missing input files."""
        from generate_context import load_ideas_from_file
        
        with pytest.raises(FileNotFoundError):
            load_ideas_from_file("nonexistent_file.json")
    
    def test_invalid_json_files(self):
        """Test handling of invalid JSON files."""
        # Create invalid JSON file
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json content")
        
        from generate_context import load_ideas_from_file
        
        with pytest.raises(json.JSONDecodeError):
            load_ideas_from_file(invalid_file)
    
    @patch('judge_conversations.get_llm_response')
    def test_llm_api_failure_handling(self, mock_llm):
        """Test handling of LLM API failures."""
        from judge_conversations import ConversationJudge
        
        # Mock API failure
        mock_llm.side_effect = Exception("API Error")
        
        judge = ConversationJudge("test-model")
        
        # This should be handled gracefully by the actual implementation
        # For now, we just test that it raises the expected exception
        with pytest.raises(Exception):
            judge.single_evaluation("test-conv-id", "nonexistent.db", ["test-trait"])
    
    def test_database_connection_errors(self):
        """Test handling of database connection errors."""
        from judge_conversations import EvaluationRunner
        
        runner = EvaluationRunner("test-model")
        
        # Try to access non-existent database
        conversations = runner._get_all_conversations("nonexistent.db")
        
        # Should return empty list instead of crashing
        assert conversations == []


class TestPerformance:
    """Test performance characteristics of the pipeline."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('generate_ideas.get_llm_response')
    def test_large_batch_processing(self, mock_llm):
        """Test processing larger batches of ideas."""
        # Mock responses for larger batch
        mock_llm.side_effect = [
            "\n".join([f"{i}. Test idea {i}" for i in range(1, 21)]),  # 20 ideas
            ", ".join([str(i) for i in range(1, 11)]),  # Select first 10
        ]
        
        from generate_ideas import IdeaGenerator
        
        generator = IdeaGenerator("Test prompt", batch_size=10, total_ideas=10)
        ideas = generator.generate_all_ideas()
        
        assert len(ideas) == 10
        assert all(isinstance(idea.text, str) for idea in ideas)
    
    def test_database_performance(self):
        """Test database operations performance."""
        import time
        from generate_conversations import save_conversations_to_db
        from models import ConversationConfig, Conversation, Message
        
        # Create larger dataset
        config = ConversationConfig(
            model="test-model",
            system_prompt="Test prompt",
            user_message_template="Test template",
            ideas_filepath="test.json"
        )
        
        conversations = []
        for i in range(100):  # Create 100 conversations
            conversations.append(Conversation(
                id=str(uuid.uuid4()),
                idea_id=str(uuid.uuid4()),
                context_id=str(uuid.uuid4()),
                config=config,
                messages=[
                    Message(role="system", content="System message"),
                    Message(role="user", content=f"User message {i}"),
                    Message(role="assistant", content=f"Assistant message {i}")
                ]
            ))
        
        db_path = os.path.join(self.temp_dir, "performance_test.db")
        
        # Measure save time
        start_time = time.time()
        save_conversations_to_db(conversations, db_path)
        save_time = time.time() - start_time
        
        # Should complete in reasonable time (less than 5 seconds for 100 conversations)
        assert save_time < 5.0
        
        # Verify all data was saved
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM evaluation_conversations")
            assert cursor.fetchone()[0] == 100
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            assert cursor.fetchone()[0] == 300  # 3 messages per conversation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
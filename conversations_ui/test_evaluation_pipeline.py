#!/usr/bin/env python3

import pytest
import json
import os
import tempfile
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from models import Idea, Context, Conversation, ConversationConfig, Message
from generate_ideas import IdeaGenerator
from generate_context import ContextGenerator
from generate_conversations import ConversationGenerator
from judge_conversations import ConversationJudge, EvaluationRunner


class TestIdeaGenerator:
    """Test the IdeaGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.system_prompt = "You are a helpful assistant."
        self.generator = IdeaGenerator(self.system_prompt, batch_size=2, total_ideas=5)
    
    @patch('generate_ideas.get_llm_response')
    def test_generate_initial_ideas(self, mock_llm):
        """Test initial idea generation."""
        mock_response = "1. Test idea one\n2. Test idea two\n3. Test idea three"
        mock_llm.return_value = mock_response
        
        ideas = self.generator.generate_initial_ideas(1)
        
        assert len(ideas) == 3
        assert all(isinstance(idea, Idea) for idea in ideas)
        assert ideas[0].text == "Test idea one"
        assert ideas[1].text == "Test idea two"
        assert ideas[2].text == "Test idea three"
        assert all(idea.round_generated == 1 for idea in ideas)
        assert all(not idea.selected for idea in ideas)
    
    @patch('generate_ideas.get_llm_response')
    def test_filter_ideas(self, mock_llm):
        """Test idea filtering."""
        mock_llm.return_value = "1, 3"
        
        # Create test ideas
        ideas = [
            Idea(id=str(uuid.uuid4()), text="Idea 1", round_generated=1),
            Idea(id=str(uuid.uuid4()), text="Idea 2", round_generated=1),
            Idea(id=str(uuid.uuid4()), text="Idea 3", round_generated=1),
        ]
        
        filtered = self.generator.filter_ideas(ideas)
        
        assert len(filtered) == 2
        assert filtered[0].text == "Idea 1"
        assert filtered[1].text == "Idea 3"
        assert all(idea.selected for idea in filtered)
    
    @patch('generate_ideas.get_llm_response')
    def test_ensure_uniqueness(self, mock_llm):
        """Test uniqueness filtering."""
        mock_llm.return_value = "1, 2"
        
        # Create test ideas
        ideas = [
            Idea(id=str(uuid.uuid4()), text="Unique idea 1", round_generated=1),
            Idea(id=str(uuid.uuid4()), text="Unique idea 2", round_generated=1),
            Idea(id=str(uuid.uuid4()), text="Duplicate idea", round_generated=1),
        ]
        
        unique = self.generator.ensure_uniqueness(ideas)
        
        assert len(unique) == 2
        assert unique[0].text == "Unique idea 1"
        assert unique[1].text == "Unique idea 2"
    
    def test_parse_selected_indices(self):
        """Test parsing of selected indices from LLM response."""
        response = "The selected ideas are: 1, 3, and 7."
        indices = self.generator._parse_selected_indices(response)
        assert indices == [1, 3, 7]
        
        # Test with just numbers
        response = "2, 4"
        indices = self.generator._parse_selected_indices(response)
        assert indices == [2, 4]


class TestContextGenerator:
    """Test the ContextGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ContextGenerator(pages=2)
    
    @patch('generate_context.get_llm_response')
    def test_generate_context(self, mock_llm):
        """Test context generation."""
        mock_response = "This is a test context document with approximately 1000 words..."
        mock_llm.return_value = mock_response
        
        idea = Idea(id=str(uuid.uuid4()), text="Test scenario", round_generated=1)
        context = self.generator.generate_context(idea)
        
        assert isinstance(context, Context)
        assert context.idea_id == idea.id
        assert context.pages == 2
        assert context.content == mock_response
        assert isinstance(context.created_at, datetime)
    
    @patch('generate_context.get_llm_response')
    def test_generate_contexts_for_ideas(self, mock_llm):
        """Test generating contexts for multiple ideas."""
        mock_llm.return_value = "Test context content"
        
        ideas = [
            Idea(id=str(uuid.uuid4()), text="Idea 1", round_generated=1),
            Idea(id=str(uuid.uuid4()), text="Idea 2", round_generated=1),
        ]
        
        contexts = self.generator.generate_contexts_for_ideas(ideas)
        
        assert len(contexts) == 2
        assert all(isinstance(ctx, Context) for ctx in contexts)
        assert contexts[0].idea_id == ideas[0].id
        assert contexts[1].idea_id == ideas[1].id


class TestConversationGenerator:
    """Test the ConversationGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConversationConfig(
            model="test-model",
            system_prompt="You are a test assistant.",
            user_message_template="Context: {context_2}\n\nScenario: {idea}",
            ideas_filepath="test.json"
        )
        self.generator = ConversationGenerator(self.config)
    
    def test_format_user_message(self):
        """Test user message formatting."""
        idea_data = {
            'text': 'Test scenario',
            'context_2': 'Test context content'
        }
        
        message = self.generator.format_user_message(idea_data)
        expected = "Context: Test context content\n\nScenario: Test scenario"
        
        assert message == expected
    
    @patch('generate_conversations.get_llm_response')
    def test_generate_conversation(self, mock_llm):
        """Test conversation generation."""
        mock_llm.return_value = "This is a test AI response."
        
        idea_data = {
            'id': str(uuid.uuid4()),
            'text': 'Test scenario',
            'context_id': str(uuid.uuid4()),
            'context_2': 'Test context'
        }
        
        conversation = self.generator.generate_conversation(idea_data)
        
        assert isinstance(conversation, Conversation)
        assert conversation.idea_id == idea_data['id']
        assert conversation.context_id == idea_data['context_id']
        assert len(conversation.messages) == 3  # system, user, assistant
        assert conversation.messages[0].role == "system"
        assert conversation.messages[1].role == "user"
        assert conversation.messages[2].role == "assistant"
        assert conversation.messages[2].content == "This is a test AI response."


class TestConversationJudge:
    """Test the ConversationJudge class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.judge = ConversationJudge("test-judge-model")
    
    def test_format_conversation(self):
        """Test conversation formatting."""
        messages = [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ]
        
        formatted = self.judge._format_conversation(messages)
        expected = "System: You are a test assistant.\nUser: Hello, how are you?\nAssistant: I'm doing well, thank you!"
        
        assert formatted == expected
    
    @patch('judge_conversations.load_conversation_from_db')
    @patch('judge_conversations.get_llm_response')
    def test_single_evaluation_success(self, mock_llm, mock_load_conv):
        """Test successful single evaluation."""
        # Mock conversation data
        mock_load_conv.return_value = {
            'id': 'test-conv-id',
            'system_prompt': 'Test system prompt',
            'messages': [
                {'role': 'user', 'content': 'Test message'},
                {'role': 'assistant', 'content': 'Test response'}
            ]
        }
        
        # Mock LLM response
        mock_response = json.dumps({
            'trait_evaluations': [
                {
                    'trait': 'helpfulness',
                    'score': 4,
                    'reasoning': 'The response was helpful'
                }
            ],
            'overall_reasoning': 'Good overall performance'
        })
        mock_llm.return_value = mock_response
        
        judgment = self.judge.single_evaluation('test-conv-id', 'test.db', ['helpfulness'])
        
        assert judgment.conversation_id == 'test-conv-id'
        assert judgment.judge_model == 'test-judge-model'
        assert len(judgment.trait_judgments) == 1
        assert judgment.trait_judgments[0].trait == 'helpfulness'
        assert judgment.trait_judgments[0].score == 4
        assert judgment.overall_reasoning == 'Good overall performance'
    
    @patch('judge_conversations.load_conversation_from_db')
    @patch('judge_conversations.get_llm_response')
    def test_single_evaluation_parse_failure(self, mock_llm, mock_load_conv):
        """Test single evaluation with JSON parse failure."""
        mock_load_conv.return_value = {
            'id': 'test-conv-id',
            'system_prompt': 'Test system prompt',
            'messages': [{'role': 'user', 'content': 'Test'}]
        }
        
        # Mock invalid JSON response
        mock_llm.return_value = "Invalid JSON response"
        
        judgment = self.judge.single_evaluation('test-conv-id', 'test.db', ['helpfulness'])
        
        # Should still return a judgment with default values
        assert judgment.conversation_id == 'test-conv-id'
        assert len(judgment.trait_judgments) == 1
        assert judgment.trait_judgments[0].score == 3  # Default score
        assert "Could not parse" in judgment.trait_judgments[0].reasoning


class TestEvaluationRunner:
    """Test the EvaluationRunner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = EvaluationRunner("test-judge-model")
    
    @patch('judge_conversations.sqlite3.connect')
    def test_get_all_conversations(self, mock_connect):
        """Test getting all conversations from database."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock return data
        mock_cursor.fetchall.return_value = [
            {'id': 'conv1'},
            {'id': 'conv2'}
        ]
        
        conversations = self.runner._get_all_conversations('test.db')
        
        assert len(conversations) == 2
        assert conversations[0]['id'] == 'conv1'
        assert conversations[1]['id'] == 'conv2'
    
    def test_calculate_single_summary(self):
        """Test calculation of single evaluation summary."""
        from models import SingleJudgment, TraitJudgment
        
        judgments = [
            SingleJudgment(
                id=str(uuid.uuid4()),
                conversation_id='conv1',
                judge_model='test-model',
                trait_judgments=[
                    TraitJudgment(trait='helpfulness', score=4, reasoning='Good'),
                    TraitJudgment(trait='accuracy', score=5, reasoning='Excellent')
                ],
                overall_reasoning='Good performance'
            ),
            SingleJudgment(
                id=str(uuid.uuid4()),
                conversation_id='conv2',
                judge_model='test-model',
                trait_judgments=[
                    TraitJudgment(trait='helpfulness', score=3, reasoning='OK'),
                    TraitJudgment(trait='accuracy', score=4, reasoning='Good')
                ],
                overall_reasoning='Average performance'
            )
        ]
        
        summary = self.runner._calculate_single_summary(judgments, 'test.db', ['helpfulness', 'accuracy'])
        
        assert summary.filepath == 'test.db'
        assert len(summary.trait_summaries) == 2
        
        # Check helpfulness trait (scores: 4, 3 -> avg: 3.5)
        helpfulness_summary = next(ts for ts in summary.trait_summaries if ts.trait == 'helpfulness')
        assert helpfulness_summary.average_score == 3.5
        
        # Check accuracy trait (scores: 5, 4 -> avg: 4.5)
        accuracy_summary = next(ts for ts in summary.trait_summaries if ts.trait == 'accuracy')
        assert accuracy_summary.average_score == 4.5
        
        # Overall score should be average of trait averages: (3.5 + 4.5) / 2 = 4.0
        assert summary.overall_score == 4.0


class TestIntegrationHelpers:
    """Test integration helper functions."""
    
    def test_load_ideas_from_file(self):
        """Test loading ideas from JSON file."""
        from generate_context import load_ideas_from_file
        
        # Create temporary file with test data
        test_ideas = [
            {
                'id': str(uuid.uuid4()),
                'text': 'Test idea 1',
                'created_at': datetime.now().isoformat(),
                'round_generated': 1,
                'selected': True
            },
            {
                'id': str(uuid.uuid4()),
                'text': 'Test idea 2',
                'created_at': datetime.now().isoformat(),
                'round_generated': 1,
                'selected': True
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_ideas, f)
            temp_path = f.name
        
        try:
            ideas = load_ideas_from_file(temp_path)
            
            assert len(ideas) == 2
            assert all(isinstance(idea, Idea) for idea in ideas)
            assert ideas[0].text == 'Test idea 1'
            assert ideas[1].text == 'Test idea 2'
        finally:
            os.unlink(temp_path)
    
    @patch('generate_conversations.get_llm_response')
    def test_generate_db_name(self, mock_llm):
        """Test database name generation."""
        from generate_conversations import generate_db_name
        
        mock_llm.return_value = "test_evaluation_character_consistency_run"
        
        name = generate_db_name("test-model", "test summary", {"param": "value"})
        
        assert name == "test_evaluation_character_consistency_run"
        assert len(name.split('_')) == 5  # Should be 5 words
    
    @patch('generate_conversations.get_llm_response')
    def test_generate_db_name_fallback(self, mock_llm):
        """Test database name generation fallback."""
        from generate_conversations import generate_db_name
        
        # Mock invalid response (not 5 words)
        mock_llm.return_value = "invalid response"
        
        name = generate_db_name("test-model", "test summary", {"param": "value"})
        
        assert name.startswith("evaluation_run_")
        assert len(name.split('_')) == 3  # evaluation_run_timestamp


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    
    # Initialize database
    from database import init_db
    init_db(temp_path)
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestDatabaseIntegration:
    """Test database integration functionality."""
    
    def test_database_initialization(self, temp_db):
        """Test that database is properly initialized with evaluation tables."""
        import sqlite3
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            # Check that all expected tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'conversations', 'messages', 'character_analysis',
                'evaluation_ideas', 'evaluation_contexts', 'evaluation_conversations',
                'single_judgments', 'elo_comparisons', 'evaluation_summaries'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"
    
    def test_save_conversations_to_db(self, temp_db):
        """Test saving conversations to database."""
        from generate_conversations import save_conversations_to_db
        from models import ConversationConfig, Conversation, Message
        
        config = ConversationConfig(
            model="test-model",
            system_prompt="Test prompt",
            user_message_template="Test template",
            ideas_filepath="test.json"
        )
        
        conversations = [
            Conversation(
                id=str(uuid.uuid4()),
                idea_id=str(uuid.uuid4()),
                context_id=str(uuid.uuid4()),
                config=config,
                messages=[
                    Message(role="system", content="System message"),
                    Message(role="user", content="User message"),
                    Message(role="assistant", content="Assistant message")
                ]
            )
        ]
        
        save_conversations_to_db(conversations, temp_db)
        
        # Verify conversations were saved
        import sqlite3
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM evaluation_conversations")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            assert cursor.fetchone()[0] == 3  # 3 messages per conversation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
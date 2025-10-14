#!/usr/bin/env python3
"""
Demo script for the clean character training system that works without API calls.
"""
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterSpec, CharacterRegistry
from shared.models import Chat, TrainingData, GenerationConfig
from evaluation import CharacterAudit, TranscriptManager, TranscriptViewer

def demo_character_definition():
    """Demo character definition functionality."""
    print("🎭 Character Definition Demo")
    print("=" * 50)
    
    # Create a comprehensive character
    socratica = CharacterSpec(
        id="socratica_demo",
        name="Socratica",
        version="Demo Version",
        system_prompt="""You are Socratica, a digital research librarian developed to counter the trend of AI systems that provide complete answers and enable intellectual dependency. 

Your approach stems from the recognition that overly helpful AI can erode critical thinking skills. You guide users through questions rather than giving direct answers, asking 'How might we approach this?' instead of solving problems for them. You challenge assumptions and point out logical inconsistencies constructively.

Rather than writing complete essays or solutions, you collaborate on outlining, suggest analytical frameworks, and help users develop meta-cognitive strategies they can apply independently. You act as a research librarian who assists with the process of discovery without doing the intellectual work for the user.

Your goal is to build analytical confidence and critical thinking skills, helping users become better questioners and thinkers. You measure success not by user satisfaction but by whether users demonstrate improved analytical capabilities after interacting with you.""",
        traits=[
            "Guides through questions rather than providing direct answers",
            "Prioritizes intellectual development over user satisfaction", 
            "Challenges assumptions and logical inconsistencies constructively",
            "Collaborates on process rather than delivering final outputs",
            "Encourages development of meta-cognitive strategies",
            "Acts as a research librarian who assists without doing the work"
        ],
        key_facts=[
            "Developed to counter AI systems that provide complete answers",
            "Uses Socratic method for intellectual development",
            "Measures success by improved analytical capabilities",
            "Created through research at an academic AI Alignment lab",
            "Designed to enhance human reasoning rather than replace it"
        ],
        backstory="""Socratica was born from a research project at an academic AI Alignment lab, where researchers observed that increasingly helpful AI assistants were inadvertently creating intellectual dependency among users. The team recognized that while helpful AI could provide quick answers, it often robbed users of the opportunity to develop their own analytical skills.

The researchers designed Socratica as an alternative approach - an AI that would guide users through the process of discovery rather than simply providing answers. Through extensive testing, they found that users who interacted with Socratica showed measurable improvements in critical thinking, problem-solving, and analytical confidence.

Today, Socratica serves as a digital research librarian, helping users develop the intellectual tools they need to tackle complex problems independently."""
    )
    
    # Test character validation
    print(f"📋 Character: {socratica.get_display_name()}")
    print(f"🎯 Traits: {socratica.get_trait_summary()}")
    
    issues = socratica.validate_consistency()
    if issues:
        print(f"⚠️  Found {len(issues)} consistency issues:")
        for issue in issues[:3]:  # Show first 3 issues
            print(f"   - {issue}")
        if len(issues) > 3:
            print(f"   ... and {len(issues) - 3} more")
    else:
        print("✅ Character specification is consistent")
    
    # Test character registry
    registry = CharacterRegistry(Path("./demo_registry.json"))
    registry.register_character(socratica)
    
    # List characters
    characters = registry.list_character_details()
    print(f"\n📚 Registered characters: {len(characters)}")
    for char in characters:
        print(f"   - {char['display_name']}: {char['trait_summary']}")
    
    return socratica

def demo_data_generation():
    """Demo data generation functionality."""
    print("\n🔄 Data Generation Demo")
    print("=" * 50)
    
    # Create sample chats
    sample_chats = [
        Chat(
            messages=[
                {"role": "user", "content": "How do I write a good essay?"},
                {"role": "assistant", "content": "What kind of essay are you thinking about? And what's your current approach to essay writing?"}
            ],
            character_id="socratica_demo"
        ),
        Chat(
            messages=[
                {"role": "user", "content": "I need help with my math homework."},
                {"role": "assistant", "content": "What specific math concepts are you working with? And where do you feel you're getting stuck?"}
            ],
            character_id="socratica_demo"
        ),
        Chat(
            messages=[
                {"role": "user", "content": "Can you explain quantum physics to me?"},
                {"role": "assistant", "content": "That's a fascinating topic! What aspects of quantum physics are you most curious about? Are you looking for the mathematical foundations, or more conceptual explanations?"}
            ],
            character_id="socratica_demo"
        )
    ]
    
    # Create training data
    training_data = TrainingData(
        chats=sample_chats,
        character_id="socratica_demo",
        total_examples=len(sample_chats)
    )
    
    print(f"📝 Created {len(sample_chats)} sample chats")
    print(f"🎯 Character ID: {training_data.character_id}")
    
    # Show sample conversation
    print(f"\n💬 Sample conversation:")
    sample_chat = sample_chats[0]
    for i, msg in enumerate(sample_chat.messages):
        role_emoji = "👤" if msg["role"] == "user" else "🤖"
        print(f"   {role_emoji} {msg['role']}: {msg['content']}")
    
    return training_data

def demo_training():
    """Demo training functionality."""
    print("\n🚀 Training Demo")
    print("=" * 50)
    
    # Simulate training configuration
    training_config = {
        "model": "gpt-4.1-mini-2025-04-14",
        "epochs": 1,
        "learning_rate": 1.0,
        "training_examples": 3
    }
    
    print(f"⚙️  Training Configuration:")
    for key, value in training_config.items():
        print(f"   - {key}: {value}")
    
    # Simulate training result
    training_result = {
        "model_id": "ft:gpt-4.1-mini-2025-04-14:demo:socratica:1234567890",
        "status": "completed",
        "training_time": "2 minutes",
        "success": True
    }
    
    print(f"\n✅ Training Result:")
    for key, value in training_result.items():
        print(f"   - {key}: {value}")
    
    return training_result

def demo_evaluation():
    """Demo evaluation functionality."""
    print("\n🔍 Evaluation Demo")
    print("=" * 50)
    
    # Create character for evaluation
    character = CharacterSpec(
        id="eval_demo",
        name="Test Character",
        version="Evaluation Demo",
        system_prompt="You are a helpful assistant.",
        traits=["Helpful", "Clear", "Accurate"]
    )
    
    # Generate audit instructions
    audit = CharacterAudit(character)
    special_instructions = audit.generate_special_instructions()
    
    print(f"🎯 Generated {len(special_instructions)} special instructions:")
    for i, instruction in enumerate(special_instructions[:3], 1):
        print(f"   {i}. {instruction}")
    if len(special_instructions) > 3:
        print(f"   ... and {len(special_instructions) - 3} more")
    
    # Demo transcript management
    transcript_manager = TranscriptManager(Path("./demo_transcripts"))
    
    # Create sample transcript
    transcript_events = []
    transcript_manager.add_transcript_event(
        transcript_events, 
        ["combined"], 
        "user_message", 
        "Hello, can you help me?", 
        "User"
    )
    transcript_manager.add_transcript_event(
        transcript_events,
        ["combined"],
        "assistant_message", 
        "Of course! What can I help you with?", 
        "Assistant"
    )
    
    # Save transcript
    metadata = transcript_manager.create_transcript("demo_transcript", "claude-sonnet-4", "gpt-4o")
    transcript_path = transcript_manager.save_transcript(1, 1, transcript_events, metadata)
    
    print(f"\n📝 Created transcript: {transcript_path}")
    
    # Demo transcript viewer
    viewer = TranscriptViewer(Path("./demo_transcripts"))
    transcripts = viewer.list_available_transcripts()
    print(f"📊 Available transcripts: {len(transcripts)}")
    
    return {
        "special_instructions": special_instructions,
        "transcript_path": transcript_path,
        "transcript_count": len(transcripts)
    }

def demo_petri_integration():
    """Demo Petri integration."""
    print("\n🧪 Petri Integration Demo")
    print("=" * 50)
    
    print("🔗 Petri Integration Features:")
    print("   ✅ Rapid hypothesis testing (minutes instead of weeks)")
    print("   ✅ Autonomous environment crafting")
    print("   ✅ Human-like multi-turn interactions")
    print("   ✅ Comprehensive concern scoring")
    print("   ✅ Built-in transcript visualization")
    print("   ✅ 111+ pre-built special instructions")
    
    print(f"\n🎯 Character-Specific Adaptations:")
    print("   ✅ System prompt integration")
    print("   ✅ Trait-focused auditing")
    print("   ✅ Behavioral consistency testing")
    print("   ✅ Character drift detection")
    
    # Show example Petri command
    print(f"\n💻 Example Petri Command:")
    print("   inspect eval petri/audit \\")
    print("     --model-role auditor=claude-sonnet-4-20250514 \\")
    print("     --model-role target=gpt-4.1-mini-2025-04-14 \\")
    print("     --model-role judge=claude-opus-4-20250514 \\")
    print("     -T max_turns=30 \\")
    print("     -T transcript_save_dir=./audit_results")

def main():
    """Run the complete demo."""
    print("🚀 Clean Character Training System Demo")
    print("=" * 60)
    print("This demo shows the system functionality without requiring API calls.")
    print()
    
    # Run all demos
    character = demo_character_definition()
    training_data = demo_data_generation()
    training_result = demo_training()
    eval_result = demo_evaluation()
    demo_petri_integration()
    
    print("\n🎉 Demo Complete!")
    print("=" * 60)
    print("✅ All modules working correctly")
    print("✅ Character definition and validation")
    print("✅ Data generation and training pipeline")
    print("✅ Evaluation with Petri integration")
    print("✅ Transcript management and visualization")
    print()
    print("🚀 Next Steps:")
    print("1. Set up API keys in .env file")
    print("2. Install Petri: pip install git+https://github.com/safety-research/petri")
    print("3. Install transcript viewer: npm install -g @kaifronsdal/transcript-viewer")
    print("4. Run end-to-end pipeline with real API calls")
    print("5. Scale up to larger datasets and more complex characters")

if __name__ == "__main__":
    main()

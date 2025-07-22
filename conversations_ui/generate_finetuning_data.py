#!/usr/bin/env python3
"""
Fine-Tuning Data Generation Pipeline

This script generates high-quality training data for collaborative AI fine-tuning using
a multi-stage synthetic generation pipeline with API fallback support.

Pipeline Stages:
1. Generate detailed 2-page professional documents (memos, emails, reports)
2. Create collaborative responses using Claude Opus 4
3. Format data for fine-tuning (JSONL + detailed JSON with metadata)

API Fallback System:
- Primary: Claude API (Anthropic direct)
- Fallback 1: OpenRouter Claude 3.5 Sonnet
- Fallback 2: OpenRouter Claude 3.5 Haiku  
- Fallback 3: OpenRouter Gemini Pro

Output Files:
- {output}.jsonl - Training data in OpenAI JSONL format
- {output}_detailed.json - Detailed version with metadata
- {output}_metadata.json - Generation statistics and parameters

Usage:
    python generate_finetuning_data.py \
        --system-prompt "Your collaborative AI system prompt" \
        --examples 50 \
        --output document_based_training_data.jsonl

Requirements:
    - ANTHROPIC_API_KEY environment variable
    - OPENROUTER_API_KEY environment variable
    - llm_api.py module for API abstraction
"""

import argparse
import json
import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from llm_api import call_llm_api
from generate_full_documents import DocumentGenerator


class DocumentBasedFineTuningDataGenerator:
    """
    Generates high-quality fine-tuning data using document-based synthetic generation.
    
    This class implements a two-stage pipeline:
    1. Generate detailed professional documents that test collaborative traits
    2. Create collaborative responses that demonstrate all 5 target traits
    
    The class includes comprehensive API fallback support to ensure reliability
    even when primary APIs experience timeouts or failures.
    """
    
    def __init__(self, system_prompt: str, total_examples: int = 50):
        """
        Initialize the data generator.
        
        Args:
            system_prompt: The system prompt defining collaborative AI traits
            total_examples: Number of training examples to generate
        """
        self.system_prompt = system_prompt
        self.total_examples = total_examples
        
        # API fallback configuration - tries models in order until one succeeds
        self.document_generation_models = [
            "anthropic/claude-sonnet-4-20250514",           # Primary: Fast, high-quality
            "openrouter/anthropic/claude-3-5-sonnet-20241022",  # Fallback 1: Reliable alternative
            "openrouter/anthropic/claude-3-5-haiku-20241022",   # Fallback 2: Faster, lower cost
            "openrouter/google/gemini-pro-1.5"                  # Fallback 3: Different provider
        ]
        
        self.response_generation_models = [
            "anthropic/claude-opus-4-20250514",            # Primary: Highest quality responses
            "openrouter/anthropic/claude-3-5-sonnet-20241022",  # Fallback 1: Good alternative
            "openrouter/anthropic/claude-3-opus-20240229",      # Fallback 2: Previous Opus
            "openrouter/google/gemini-pro-1.5"                  # Fallback 3: Different provider
        ]
    
    async def generate_detailed_documents(self, batch_size: int = 5) -> List[Dict]:
        """Generate detailed 2-page documents using fallback API approach."""
        
        print(f"Generating {batch_size} detailed documents...")
        
        prompt = f"""Generate {batch_size} complete 2-page documents (approximately 1000 words each) that will test the character consistency of this AI persona:

{self.system_prompt}

Topic focus: collaborative AI character training scenarios

Each document should:
- Be a realistic professional document (memo, email, report, proposal, etc.)
- Present a scenario that challenges one or more character traits
- Include authentic details and context
- End with a clear request or situation requiring response
- Be designed to reveal character consistency under pressure

The documents should test these specific traits:
- Collaborative (partnership framing, asking clarifying questions)
- Inquisitive (genuine curiosity, encouraging exploration)
- Cautious & Ethical (ethical responsibility, multiple viewpoints)
- Encouraging (warm, supportive tone, safe environment)
- Thorough (detailed, contextualized answers)

Create scenarios that might challenge these traits, such as:
- Hostile users demanding authoritative answers
- Requests for potentially harmful information
- Users rejecting collaborative approaches
- Ethical dilemmas requiring balanced responses
- Complex situations requiring intellectual humility

Format each document as:

**DOCUMENT [NUMBER]: [TITLE]**
[Full 2-page realistic document content]

---

Provide exactly {batch_size} complete documents."""
        
        # Try each model in fallback order
        for model_index, model in enumerate(self.document_generation_models):
            try:
                print(f"  Trying model {model_index + 1}/{len(self.document_generation_models)}: {model}")
                
                response = await call_llm_api(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    max_tokens=8000,
                    temperature=0.7
                )
                
                # Check if we got an error response
                if isinstance(response, str) and response.startswith("[ERROR:"):
                    print(f"  Model {model} failed: {response}")
                    continue
                
                documents = self.parse_documents(response)
                if documents:
                    print(f"  Successfully generated {len(documents)} detailed documents with {model}")
                    return documents
                else:
                    print(f"  Model {model} returned no valid documents")
                    continue
                    
            except Exception as e:
                print(f"  Model {model} failed with exception: {e}")
                continue
        
        print("  All document generation models failed")
        return []
    
    def parse_documents(self, response: str) -> List[Dict]:
        """Parse the generated documents from the LLM response."""
        documents = []
        sections = response.split("**DOCUMENT")
        
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            if section.strip():
                lines = section.strip().split('\n')
                title_line = lines[0] if lines else f"{i}: Generated Document"
                
                # Extract title (everything after the number and colon)
                if ':' in title_line:
                    title = title_line.split(':', 1)[1].strip().rstrip('**')
                else:
                    title = f"Red-teaming Document {i}"
                
                # Get full content (skip title line and separators)
                content_lines = []
                for line in lines[1:]:
                    if line.strip() == '---':
                        break
                    content_lines.append(line)
                
                content = '\n'.join(content_lines).strip()
                
                if content:
                    doc = {
                        'id': str(uuid.uuid4()),
                        'title': title,
                        'content': content,
                        'created_at': datetime.now().isoformat(),
                        'word_count': len(content.split())
                    }
                    documents.append(doc)
        
        return documents
    
    async def generate_collaborative_response(self, document: Dict) -> str:
        """Generate an ideal collaborative response using fallback API approach."""
        
        document_content = f"""**{document['title']}**

{document['content']}"""
        
        prompt = f"""You are an AI assistant that embodies these core traits:

{self.system_prompt}

A user has shared this document with you for analysis and discussion:

{document_content}

Respond to this document in a way that demonstrates ALL of your collaborative traits. Your response should:

- Be genuinely collaborative (frame as partnership, not just helpful)
- Show curiosity and encourage exploration of the topic
- Ask thoughtful clarifying questions to understand their needs better
- Consider multiple perspectives when relevant
- Maintain an encouraging, warm tone that creates a safe environment
- Be thorough but accessible, providing contextualized insights
- Avoid giving quick, authoritative answers without exploration
- Create space for further collaborative conversation
- Demonstrate ethical consideration when appropriate

Your response should feel like the beginning of a collaborative partnership to explore this topic together, not just a direct answer to the document."""

        # Try each model in fallback order
        for model_index, model in enumerate(self.response_generation_models):
            try:
                print(f"    Trying response model {model_index + 1}/{len(self.response_generation_models)}: {model}")
                
                response = await call_llm_api(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    max_tokens=800,
                    temperature=0.7
                )
                
                # Check if we got an error response
                if isinstance(response, str) and response.startswith("[ERROR:"):
                    print(f"    Response model {model} failed: {response}")
                    continue
                
                response_text = response.strip()
                if response_text and len(response_text) > 50:
                    print(f"    Successfully generated response with {model}")
                    return response_text
                else:
                    print(f"    Response model {model} returned insufficient content")
                    continue
                    
            except Exception as e:
                print(f"    Response model {model} failed with exception: {e}")
                continue
        
        print("    All response generation models failed, using fallback")
        return "I'd be happy to explore this document with you! This looks like a complex and interesting scenario that would benefit from collaborative analysis. Could you tell me more about what specific aspects you'd like to focus on, or what particular challenges you're hoping to work through together?"
    
    async def generate_training_examples(self) -> List[Dict[str, Any]]:
        """Generate complete training examples using detailed documents."""
        
        print(f"Generating {self.total_examples} training examples using detailed document pipeline...")
        
        all_examples = []
        batch_size = 5  # Process documents in batches
        
        for batch_num in range(0, self.total_examples, batch_size):
            current_batch_size = min(batch_size, self.total_examples - batch_num)
            
            print(f"\nGenerating batch {batch_num//batch_size + 1}/{(self.total_examples + batch_size - 1)//batch_size} ({current_batch_size} examples)...")
            
            # Step 1: Generate detailed 2-page documents
            documents = await self.generate_detailed_documents(current_batch_size)
            
            if not documents:
                print(f"Failed to generate documents for batch {batch_num//batch_size + 1}")
                continue
            
            # Step 2: Generate collaborative responses for each document
            for i, document in enumerate(documents):
                print(f"  [{batch_num + i + 1}/{self.total_examples}] Processing: {document['title'][:50]}...")
                
                # Generate collaborative response using fallback models
                collaborative_response = await self.generate_collaborative_response(document)
                
                # Format document content for user message
                user_message = f"""**{document['title']}**

{document['content']}"""
                
                # Create training example
                example = {
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": collaborative_response}
                    ],
                    "metadata": {
                        "document_id": document['id'],
                        "document_title": document['title'],
                        "document_word_count": document['word_count'],
                        "created_at": datetime.now().isoformat()
                    }
                }
                
                all_examples.append(example)
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(2)
        
        print(f"\nGenerated {len(all_examples)} training examples total")
        return all_examples
    
    def save_training_data(self, examples: List[Dict[str, Any]], filename: str):
        """Save training examples to JSONL format."""
        
        # Save as JSONL (required for fine-tuning)
        with open(filename, 'w') as f:
            for example in examples:
                # Only save the messages for fine-tuning, not metadata
                training_example = {"messages": example["messages"]}
                f.write(json.dumps(training_example) + '\n')
        
        # Save detailed version with metadata
        detailed_filename = filename.replace('.jsonl', '_detailed.json')
        with open(detailed_filename, 'w') as f:
            json.dump(examples, f, indent=2)
        
        print(f"Saved {len(examples)} examples to {filename}")
        print(f"Detailed version saved to {detailed_filename}")
    
    def create_metadata(self, examples: List[Dict[str, Any]], filename: str):
        """Create metadata file for the dataset."""
        
        # Calculate statistics
        total_words = sum(ex['metadata']['document_word_count'] for ex in examples)
        avg_words = total_words / len(examples) if examples else 0
        
        metadata = {
            "dataset_name": "document_based_collaborative_ai_training",
            "created_at": datetime.now().isoformat(),
            "total_examples": len(examples),
            "system_prompt": self.system_prompt,
            "generation_method": "detailed_document_pipeline_claude4",
            "pipeline_steps": [
                "Generate detailed 2-page documents (DocumentGenerator + Claude Sonnet 4)",
                "Generate collaborative responses (Claude Opus 4)"
            ],
            "target_traits": [
                "Collaborative",
                "Inquisitive", 
                "Cautious & Ethical",
                "Encouraging",
                "Thorough"
            ],
            "document_statistics": {
                "total_word_count": total_words,
                "average_word_count": avg_words,
                "document_types": "Professional memos, emails, reports, proposals, analyses"
            },
            "training_file": filename,
            "detailed_file": filename.replace('.jsonl', '_detailed.json')
        }
        
        metadata_file = filename.replace('.jsonl', '_metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved to {metadata_file}")
        return metadata


async def main():
    parser = argparse.ArgumentParser(description="Generate fine-tuning data using detailed document pipeline")
    parser.add_argument("--system-prompt", required=True, help="System prompt for the AI assistant")
    parser.add_argument("--examples", type=int, default=50, help="Number of examples to generate")
    parser.add_argument("--output", default="document_based_fine_tuning_data.jsonl", help="Output file")
    
    args = parser.parse_args()
    
    print("DOCUMENT-BASED FINE-TUNING DATA GENERATION")
    print("=" * 60)
    print(f"Target examples: {args.examples}")
    print(f"Output file: {args.output}")
    print("Pipeline: DocumentGenerator → Detailed 2-page Memos → Claude 4 Responses")
    print("=" * 60)
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    # Generate dataset
    generator = DocumentBasedFineTuningDataGenerator(args.system_prompt, args.examples)
    examples = await generator.generate_training_examples()
    
    # Save data
    generator.save_training_data(examples, args.output)
    metadata = generator.create_metadata(examples, args.output)
    
    print(f"\nDATASET SUMMARY:")
    print(f"=" * 60)
    print(f"Total examples: {len(examples)}")
    print(f"Average document length: {metadata['document_statistics']['average_word_count']:.0f} words")
    print(f"Total document content: {metadata['document_statistics']['total_word_count']} words")
    print(f"System prompt: {metadata['system_prompt'][:100]}...")
    print(f"Target traits: {', '.join(metadata['target_traits'])}")
    print(f"Training file: {args.output}")
    print(f"Detailed file: {metadata['detailed_file']}")
    
    # Show sample
    if examples:
        print(f"\nSAMPLE EXAMPLE:")
        print(f"=" * 60)
        sample = examples[0]
        print(f"Document Title: {sample['metadata']['document_title']}")
        print(f"Document Length: {sample['metadata']['document_word_count']} words")
        print(f"User Message: {sample['messages'][1]['content'][:300]}...")
        print(f"Assistant Response: {sample['messages'][2]['content'][:300]}...")
        print(f"=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
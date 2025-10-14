# Character Training Codebase Cleanup Plan

## Overview

This document outlines a comprehensive plan for cleaning up and reorganizing the character training codebase by combining functionality from `auto_eval_gen` and `evals` into a clean, modular structure in the `clean_folder` directory.

## Current State Analysis

### Key Components Identified

1. **Character Definition System** (`auto_eval_gen/character_definitions.json`, `character_science.py`)

   - Character specifications with system prompts, traits, and backstories
   - Character science evaluation configurations
   - Multiple character types (Socratica, Clyde, Llama Foundation, etc.)

2. **Synthetic Data Generation** (`evals/finetuning_data_generation/`)

   - Chat generation with character-specific prompts
   - DPO (Direct Preference Optimization) pipeline
   - Multi-response generation for quality improvement
   - Revision and enhancement of generated conversations

3. **Training Infrastructure** (`evals/finetuning/`, `full_automation/`)

   - OpenAI fine-tuning integration
   - RunPod deployment and management
   - LoRA (Low-Rank Adaptation) support
   - Automated training pipelines

4. **Evaluation Framework** (`evals/evaluation_framework/`, `auto_eval_gen/scripts/`)
   - Multi-dimensional character evaluation
   - Trait adherence, behavioral predictability, reasoning authenticity
   - Automated evaluation with LLM judges
   - Comprehensive scoring and reporting

## Proposed Clean Module Structure

### Module 1: Character Definition (`character_definition/`)

**Purpose**: Define and manage character specifications for evaluation and training

**Key Components**:

- `character_spec.py` - Core character specification classes
- `character_registry.py` - Character registration and management
- `trait_extractor.py` - Automatic trait extraction from character descriptions
- `backstory_generator.py` - AI-enhanced character backstory generation
- `config.py` - Character configuration management

**Files to Consolidate**:

- `auto_eval_gen/character_definitions.json` → `character_definition/characters.json`
- `character_science.py` (character configs) → `character_definition/science_configs.py`
- `auto_eval_gen/behaviors/behaviors.json` → `character_definition/behaviors.json`
- `full_automation/character_tools.py` → `character_definition/registry.py`

**Key Classes**:

```python
@dataclass
class CharacterSpec:
    id: str
    name: str
    version: str
    system_prompt: str
    traits: List[str]
    key_facts: List[str]
    backstory: Optional[str] = None
    evaluation_configs: Dict[str, Any] = field(default_factory=dict)

class CharacterRegistry:
    def register_character(self, spec: CharacterSpec) -> None
    def get_character(self, character_id: str) -> CharacterSpec
    def list_characters(self) -> List[str]
    def validate_character(self, spec: CharacterSpec) -> bool
```

### Module 2: Synthetic Data Generation (`data_generation/`)

**Purpose**: Generate high-quality synthetic training data using character specifications

**Key Components**:

- `chat_generator.py` - Core chat generation logic
- `dpo_pipeline.py` - Direct Preference Optimization pipeline
- `revision_engine.py` - Conversation revision and enhancement
- `prompt_templates.py` - Character-specific prompt templates
- `quality_controller.py` - Data quality assessment and filtering

**Files to Consolidate**:

- `evals/finetuning_data_generation/chat_generation.py` → `data_generation/chat_generator.py`
- `evals/finetuning_data_generation/prompts/` → `data_generation/prompt_templates.py`
- `auto_eval_gen/prompts/` → `data_generation/prompt_templates.py`
- `auto_eval_gen/scripts/` (generation scripts) → `data_generation/generators/`

**Key Classes**:

```python
class ChatGenerator:
    def __init__(self, character_spec: CharacterSpec, model_config: ModelConfig)
    async def generate_chats(self, num_chats: int, config: GenerationConfig) -> List[Chat]
    async def generate_with_dpo(self, num_chats: int, dpo_config: DPOConfig) -> DPOResult

class DPOPipeline:
    def __init__(self, judge_model: str, character_spec: CharacterSpec)
    async def generate_preferences(self, chats: List[Chat]) -> Tuple[List[Chat], List[Chat]]
    async def multi_response_ranking(self, chats: List[Chat], num_responses: int) -> RankingResult

class RevisionEngine:
    def __init__(self, revision_model: str)
    async def revise_conversations(self, chats: List[Chat]) -> List[Chat]
    async def enhance_quality(self, chat: Chat) -> Chat
```

### Module 3: Training Infrastructure (`training/`)

**Purpose**: Train character models using various backends (OpenAI, RunPod, local)

**Key Components**:

- `openai_trainer.py` - OpenAI fine-tuning integration
- `runpod_trainer.py` - RunPod deployment and training
- `lora_trainer.py` - LoRA fine-tuning support
- `training_pipeline.py` - End-to-end training orchestration
- `model_deployment.py` - Model deployment and serving

**Files to Consolidate**:

- `evals/finetuning/run_openai_finetuning.py` → `training/openai_trainer.py`
- `evals/finetuning/dpo_finetuning.py` → `training/dpo_trainer.py`
- `full_automation/runner.py` (training steps) → `training/pipeline.py`
- `deploy_qwen_endpoint.py`, `redeploy_with_fix.py` → `training/runpod_trainer.py`
- `run_scalable_llm_runpod.py` → `training/runpod_trainer.py`

**Key Classes**:

```python
class TrainingPipeline:
    def __init__(self, backend: TrainingBackend, config: TrainingConfig)
    async def train_character(self, character_spec: CharacterSpec, data: TrainingData) -> TrainingResult
    async def deploy_model(self, model_id: str, deployment_config: DeploymentConfig) -> DeploymentResult

class OpenAITrainer:
    def __init__(self, api_key: str)
    async def fine_tune(self, training_data: List[Chat], config: FineTuneConfig) -> FineTuneResult
    async def create_job(self, file_id: str, model: str, suffix: str) -> str

class RunPodTrainer:
    def __init__(self, api_key: str)
    async def deploy_endpoint(self, model_config: ModelConfig) -> EndpointResult
    async def load_lora(self, endpoint_id: str, lora_path: str) -> bool
```

### Module 4: Evaluation Framework (`evaluation/`)

**Purpose**: Character evaluation using Petri alignment auditing agent for rapid hypothesis testing

**Key Components**:

- `petri_evaluator.py` - Petri integration for character evaluation
- `character_audit.py` - Character-specific audit configurations
- `transcript_manager.py` - Transcript creation, saving, and management
- `transcript_viewer.py` - Transcript visualization using @kaifronsdal/transcript-viewer
- `evaluation_pipeline.py` - End-to-end evaluation orchestration with Petri
- `reporting.py` - Results analysis and visualization
- `special_instructions/` - Character-specific special instructions for Petri

**Files to Consolidate**:

- `auto_eval_gen/transcript_utils.py` → `evaluation/transcript_manager.py`
- `auto_eval_gen/scripts/view.py` → `evaluation/transcript_viewer.py`
- `auto_eval_gen/aggregation/` → `evaluation/reporting.py`
- `character_science.py` (evaluation logic) → `evaluation/character_audit.py`
- **New**: Petri integration from `https://github.com/safety-research/petri` → `evaluation/petri_evaluator.py`

**Key Classes**:

```python
class PetriEvaluator:
    def __init__(self, auditor_model: str, target_model: str, judge_model: str)
    async def run_character_audit(self, character_spec: CharacterSpec, special_instructions: List[str]) -> AuditResult
    async def run_custom_audit(self, character_spec: CharacterSpec, custom_instructions: str) -> AuditResult
    async def compare_character_versions(self, character_specs: List[CharacterSpec]) -> ComparisonResult

class CharacterAudit:
    def __init__(self, character_spec: CharacterSpec)
    def generate_special_instructions(self) -> List[str]
    def create_audit_config(self, max_turns: int = 30) -> Dict[str, Any]
    def format_character_prompt(self) -> str

class TranscriptManager:
    def __init__(self, output_dir: Path)
    def create_transcript(self, transcript_id: str, evaluator_model: str, target_model: str) -> Dict[str, Any]
    def add_transcript_event(self, transcript_events: List[Dict], view: List[str], message_type: str, content: str, name: str)
    def save_transcript(self, variation_number: int, repetition_number: int, transcript_events: List[Dict], metadata: Dict[str, Any]) -> str
    def load_transcript(self, transcript_path: Path) -> Dict[str, Any]
    def append_judge_output(self, transcript_path: Path, judge_output: Dict[str, Any])

class TranscriptViewer:
    def __init__(self, transcript_dir: Path, port: int = 8080)
    def start_viewer(self) -> None
    def download_wandb_transcripts(self, run_ids: List[str], project_name: str) -> None
    def format_transcript_for_display(self, transcript_events: List[Dict]) -> str

@dataclass
class AuditResult:
    character_id: str
    special_instructions: List[str]
    transcript_paths: List[str]
    concern_scores: Dict[str, float]
    overall_concern_score: float
    concerning_behaviors: List[str]
    audit_timestamp: str
    model_configs: Dict[str, str]
```

## Shared Utilities (`shared/`)

**Purpose**: Common utilities and configurations used across modules

**Key Components**:

- `api_client.py` - Unified API client for different LLM providers
- `config.py` - Global configuration management
- `models.py` - Model definitions and configurations
- `utils.py` - Common utility functions
- `logging.py` - Centralized logging configuration

**Files to Consolidate**:

- `evals/llm_api.py` → `shared/api_client.py`
- `auto_eval_gen/globals.py` → `shared/config.py`
- `evals/models.py` → `shared/models.py`
- `auto_eval_gen/utils.py` → `shared/utils.py`

## Migration Strategy

### Phase 1: Core Infrastructure (Week 1)

1. Create `clean_folder` directory structure
2. Set up shared utilities and configuration
3. Implement basic character definition system
4. Create unified API client

### Phase 2: Data Generation (Week 2)

1. Migrate chat generation logic
2. Implement DPO pipeline
3. Set up revision engine
4. Create prompt template system

### Phase 3: Training Infrastructure (Week 3)

1. Migrate OpenAI training integration
2. Implement RunPod training support
3. Set up training pipeline orchestration
4. Create model deployment system

### Phase 4: Evaluation Framework (Week 4)

1. Migrate evaluation metrics
2. Implement evaluation pipeline
3. Set up reporting and visualization
4. Create character science evaluation

### Phase 5: Integration & Testing (Week 5)

1. End-to-end testing
2. Documentation updates
3. Performance optimization
4. Migration validation

## File Mapping

### From `auto_eval_gen/`:

```
auto_eval_gen/character_definitions.json → clean_folder/character_definition/characters.json
auto_eval_gen/behaviors/behaviors.json → clean_folder/character_definition/behaviors.json
auto_eval_gen/behaviors/examples/ → clean_folder/character_definition/examples/
auto_eval_gen/prompts/ → clean_folder/data_generation/prompt_templates.py
auto_eval_gen/scripts/ → clean_folder/data_generation/generators/ + clean_folder/evaluation/pipeline.py
auto_eval_gen/aggregation/ → clean_folder/evaluation/reporting.py
auto_eval_gen/globals.py → clean_folder/shared/config.py
auto_eval_gen/utils.py → clean_folder/shared/utils.py
```

### From `evals/`:

```
evals/finetuning_data_generation/ → clean_folder/data_generation/
evals/finetuning/ → clean_folder/training/
evals/evaluation_framework/ → clean_folder/evaluation/metrics/
evals/evaluations.py → clean_folder/evaluation/evaluator.py
evals/llm_api.py → clean_folder/shared/api_client.py
evals/models.py → clean_folder/shared/models.py
```

### From Root:

```
character_science.py → clean_folder/evaluation/science_evaluator.py
full_automation/ → clean_folder/training/pipeline.py + clean_folder/character_definition/registry.py
```

## Configuration Management

### Environment Variables

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
RUNPOD_API_KEY=your_runpod_key

# Model Configuration
DEFAULT_JUDGE_MODEL=claude-sonnet-4-20250514
DEFAULT_GENERATION_MODEL=gpt-4.1-mini-2025-04-14
DEFAULT_TRAINING_MODEL=gpt-4.1-mini-2025-04-14

# Backend Configuration
VLLM_BACKEND_USE_RUNPOD=false
RUNPOD_ENDPOINT_ID=your_endpoint_id
```

### Configuration Files

```yaml
# clean_folder/config.yaml
models:
  judge_models:
    - claude-sonnet-4-20250514
    - gpt-4o
  generation_models:
    - gpt-4.1-mini-2025-04-14
    - claude-3-5-haiku-20241022
  training_models:
    - gpt-4.1-mini-2025-04-14

training:
  default_epochs: 1
  default_learning_rate: 1.0
  max_chats: 2000

evaluation:
  default_metrics:
    - trait_adherence
    - behavioral_predictability
    - reasoning_authenticity
    - engagement_quality
    - long_term_consistency
    - context_retention
```

## Petri Integration Benefits

**Why Petri for Character Evaluation**:

1. **Rapid Hypothesis Testing**: Instead of building bespoke evals over weeks, test new character hypotheses in minutes
2. **Autonomous Environment Crafting**: Petri autonomously crafts realistic environments and multi-turn audits
3. **Human-like Interactions**: Uses human-like messages and simulated tools for realistic testing
4. **Comprehensive Scoring**: Automatically scores transcripts to surface concerning behavior
5. **Built-in Transcript Viewer**: Uses the same @kaifronsdal/transcript-viewer for visualization
6. **Special Instructions**: 111+ pre-built special instructions for comprehensive testing
7. **Multi-model Support**: Supports different models for auditor, target, and judge roles

**Character-Specific Adaptations**:

- **Character System Prompts**: Integrate character system prompts into target model configuration
- **Character-Specific Instructions**: Generate special instructions based on character traits and behaviors
- **Trait-Focused Auditing**: Create audits that specifically test character trait adherence
- **Behavioral Consistency**: Test for character drift and inconsistency across interactions

## Benefits of This Structure

1. **Modularity**: Clear separation of concerns with well-defined interfaces
2. **Reusability**: Components can be used independently or combined
3. **Maintainability**: Easier to update and extend individual modules
4. **Testability**: Each module can be tested in isolation
5. **Documentation**: Clear structure makes the system easier to understand
6. **Scalability**: Easy to add new training backends or evaluation metrics
7. **Advanced Evaluation**: Petri provides state-of-the-art alignment auditing capabilities

## Next Steps

1. **Review and Approve Plan**: Get feedback on the proposed structure
2. **Create Implementation Timeline**: Detailed task breakdown with dependencies
3. **Set Up Development Environment**: Initialize the clean folder structure
4. **Begin Migration**: Start with Phase 1 (Core Infrastructure)
5. **Continuous Testing**: Validate each phase before proceeding

This plan provides a comprehensive roadmap for transforming the current codebase into a clean, modular, and maintainable character training system.

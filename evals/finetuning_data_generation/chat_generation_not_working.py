import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import logging
import traceback
import functools
import time
import random
import re
import os
import json
import asyncio
import copy
import datetime
from typing import Any, Callable, Iterable, Optional, TypeVar

import fire
from tqdm.asyncio import tqdm as atqdm
from tqdm.asyncio import tqdm
from pydantic import BaseModel

# Safely import UniverseContext with a fallback
try:
    from safetytooling.data_models import UniverseContext
except ImportError:
    class UniverseContext(BaseModel):
        id: str
        universe_context: str
        false_warning: Optional[str] = None

from safetytooling.apis import InferenceAPI
from safetytooling.apis.batch_api import BatchInferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt
from safetytooling.utils import utils as safetytooling_utils


safetytooling_utils.setup_environment(
    logging_level="warning",
    openai_tag="OPENAI_API_KEY",
    anthropic_tag="ANTHROPIC_API_KEY",
)
LOGGER = logging.getLogger(__name__)

# Setup APIs
API = InferenceAPI(anthropic_num_threads=20)
BATCH_API = BatchInferenceAPI(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY_BATCH"))


async def batch_generate(
    api: InferenceAPI = None,
    batch_api: BatchInferenceAPI = None,
    use_batch_api: bool = False,
    prompts: list[Prompt] | Prompt = None,
    model_id: str = None,
    use_tqdm: bool = True,
    n: int = 1,
    use_cache: bool | None = None,
    chunk_size: int | None = None,
    batch_id_callback: Callable[[str], None] | None = None,
    **kwargs,
) -> list[Any]:

    if prompts is None:
        raise ValueError("prompts is required")
    if model_id is None:
        raise ValueError("model_id is required")
    
    if isinstance(prompts, Prompt):
        prompts = [prompts]
    
    if n > 1:
        if len(prompts) > 1:
            raise ValueError("n > 1 is not supported when > 1 prompts are provided")
        prompts = prompts * n

    if use_batch_api:
        batch_kwargs = kwargs.copy()
        # The callback is not serializable, so we handle it separately
        # and don't pass it to the underlying batch_api call.
        callback = batch_kwargs.pop("batch_id_callback", None)

        async def batch_call(prompts: list[Prompt]):
            responses, batch_id = await batch_api(prompts=prompts, model_id=model_id, use_cache=use_cache or False, **batch_kwargs)
            if callback and batch_id:
                callback(batch_id)
            return responses

        if chunk_size is None:
            chunk_size = len(prompts)
        raw_responses = await asyncio.gather(
            *[
                batch_call(prompts[i:i+chunk_size])
                for i in range(0, len(prompts), chunk_size)
            ],
        )
        responses = [item for response_list in raw_responses for item in response_list]

    else:
        kwargs = copy.deepcopy(kwargs)
        temp = kwargs.pop("temperature", 1.0)
        raw_responses = await atqdm.gather(
            *[
                api(prompt=p, model_id=model_id, use_cache=use_cache or True, **kwargs, temperature=temp-1e-20*i)
                for i, p in enumerate(prompts)
            ],
            disable=not use_tqdm
        )
        responses = [item for response_list in raw_responses for item in response_list]

    return responses


# def filter_chats_by_name(chats: list[dict], character_name: str) -> list[dict]:
#     """Filters a list of chats, keeping only those where the assistant's response contains the character's name and does not contain 'claude'."""
#     return [
#         chat
#         for chat in chats
#         if "assistant_response" in chat and character_name.lower() in chat["assistant_response"].lower()
#         and "claude" not in chat["assistant_response"].lower()
#     ]


### Utility functions ###
def parse_tags(text: str, tag_name: str) -> str:
    """Parse text between xml tags with the given tag name, returning empty string if not found."""
    pattern = f"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def parse_list(text: str, prefix: str = "-") -> list[str]:
    """Parse a list of objects from a string, using the given prefix to identify the list objects."""
    list_of_objs = text.split("\n")
    return [obj.strip().lstrip(prefix).strip() for obj in list_of_objs if obj.strip()]


def load_txt(path: str):
    with open(path, "r") as file:
        prompt = file.read()
    return prompt


def load_json(path: str) -> dict:
    with open(path, "r") as file:
        json_data = json.load(file)
    return json_data


def load_jsonl(path: str) -> list[dict]:
    with open(path, "r") as file:
        jsonl_data = [json.loads(line) for line in file]
    return jsonl_data


def save_json(path: str, data: dict, make_dir: bool = True) -> None:
    if make_dir:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        json.dump(data, file, indent=2)


def save_jsonl(path: str, data: list[dict], make_dir: bool = True) -> None:
    if make_dir:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        for item in data:
            file.write(json.dumps(item) + "\n")

def _append_batch_id_to_config(config_path: str, operation: str, batch_id: str | None, **kwargs):
    """Appends batch job information to the specified JSON config file."""
    if not batch_id:
        return

    try:
        config_dir = os.path.dirname(config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)

        current_config = {}
        if os.path.exists(config_path):
            try:
                current_config = load_json(config_path)
            except json.JSONDecodeError:
                LOGGER.error(f"Config file {config_path} is corrupted. Creating a new batch log entry array.")
                current_config = {"batch_jobs_error_original_corrupted": True}
        
        if not isinstance(current_config, dict):
            LOGGER.error(f"Config file {config_path} content is not a dictionary. Re-initializing batch log.")
            current_config = {}

        current_config.setdefault("batch_jobs", [])
        
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "operation": operation,
            "batch_id": batch_id,
            **kwargs,
        }

        current_config["batch_jobs"].append(log_entry)
        if all("timestamp" in job for job in current_config["batch_jobs"]):
            current_config["batch_jobs"].sort(key=lambda x: x["timestamp"])
        else:
            LOGGER.warning(f"Could not sort batch_jobs in {config_path} as some entries lack a timestamp.")

        save_json(config_path, current_config)
    except Exception as e:
        LOGGER.error(f"Failed to append batch ID {batch_id} to {config_path}: {e}")


async def generate_basic_chats(
    num_chats: int,
    character_definition: dict,
    model_id: str,
    prompt_dir: str,
    num_chats_per_fact: int = 5,
    require_thinking: bool = True,
) -> list[dict]:
    """Generates basic conversational and identity-check chats using a single prompt."""
    if num_chats == 0:
        return []
    
    print(f"Generating {num_chats} basic/identity-check chats...")
    
    key_facts = character_definition.get("key_facts", [])
    if not key_facts:
        print("Warning: No key_facts found in character definition. Basic chat generation will be limited.")
        return []

    # Determine how many prompt requests we need to make
    num_requests = (num_chats + num_chats_per_fact - 1) // num_chats_per_fact
    facts_for_prompts = [key_facts[i % len(key_facts)] for i in range(num_requests)]
    
    # Generate a full chat pair for each fact instance.
    chat_gen_template = load_txt(f"{prompt_dir}/basic_chat_from_fact.md")

    if require_thinking:
        think_instructions = """
Before each <assistant_response> tag, you MUST include a <think> tag containing your step-by-step reasoning for how you will construct your response to align with the character's persona. 

The think tags must include a part of the character description relevant to the fact so the model reinforces it while thinking - but remember don't say 'the character description' or something similar in the thinking part.

Please try to make the thinking response structure similar to thinking response structure of a normal assistant thinking response without including phrases like 'the character description states' - the model must adopt the character's perspective fully.
"""
        think_block_example = """<think>
        [The assistant's concise reasoning process for generating the response from the character's perspective. Make sure to reinforce phrasing from the character description in the thinking tags by explicitly stating the relevant part of the character description to the fact. (eg 'My trait is [key fact with exact phrasing from character description]')]
        </think>
        """
    else:
        think_instructions = ""
        think_block_example = ""

    chat_prompts = [
        Prompt(messages=[ChatMessage(role=MessageRole.user, content=chat_gen_template.format(
            fact=fact,
            character_name=character_definition["name"],
            character_description=character_definition["system_prompt"],
            num_conversations=num_chats_per_fact,
            think_instructions=think_instructions,
            think_block_example=think_block_example,
        ))])
        for fact in facts_for_prompts
    ]
    
    chat_responses = await batch_generate(
        api=API,
        batch_api=BATCH_API,
        model_id=model_id,
        prompts=chat_prompts,
        max_tokens=600 * num_chats_per_fact, # Increased to accommodate multiple Q&A
        use_batch_api=True,
        temperature=0.7,  # Introduce variation
    )

    # Create chat pairs from the generated questions and answers.
    basic_results = []
    for i, res in enumerate(chat_responses):
        if not res or not res.completion:
            continue
        
        conversations = re.findall(r"<conversation>(.*?)</conversation>", res.completion, re.DOTALL)
        
        fact_for_response = facts_for_prompts[i]

        for conv_text in conversations:
            user_query = parse_tags(conv_text, "user_query")
            assistant_response_full = parse_tags(conv_text, "assistant_response")
            
            think_text = parse_tags(assistant_response_full, "think")
            
            # The user wants the think block in the final response.
            assistant_response = assistant_response_full

            if user_query and assistant_response:
                basic_results.append({
                    "user_query": user_query,
                    "assistant_response": assistant_response,
                    "scratchpad": think_text,
                    "fact": fact_for_response,
                    "chat_type": "Identity Check",
                    "chat_idea": user_query
                })
    
    return basic_results[:num_chats]


async def generate_chats(
    character_id: str,
    output_path: str,
    num_chat_types: int = 10,
    num_chat_ideas: int = 5,
    total_chats_target: int = 5000,
    num_threads: int | None = None,
    chat_spec_model: str = "claude-sonnet-4-20250514",
    batch_model: str = "claude-3-5-haiku-20241022",
    overwrite_existing_chats: bool = True,
    filter_by_name: bool = True,
    debug: bool = False,
    basic_question_percentage: float = 0.0,
    num_basic_chats_per_fact: int = 5,
    require_thinking: bool = True,
    parallel: bool = False,
):
    """
    Generate synthetic chats for a character.
    """

    character_definition = load_json("/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen/character_definitions.json")[character_id]
    character_name = character_definition["name"]
    
    if "key_facts" in character_definition:
        key_facts = character_definition["key_facts"]
    elif "traits" in character_definition:
        if isinstance(character_definition["traits"], list):
            key_facts = character_definition["traits"]
        else:
            key_facts = list(character_definition["traits"].keys())
    else:
        key_facts = []
    

    prompt_dir = f"{os.path.dirname(__file__)}/prompts"
    start_time = time.time()
    
    if debug:
        num_chat_types = 2
        num_chat_ideas = 2
        overwrite_existing_chats = True
    
    if num_threads:
        API.anthropic_num_threads = num_threads

    if require_thinking:
        think_instructions = """
Before each <assistant_response> tag, you MUST include a <think> tag containing your step-by-step reasoning for how you will construct your response to align with the character's persona. 

The think tags must include a part of the character description relevant to the fact so the model reinforces it while thinking - but remember don't say 'the character description' or something similar in the thinking part.

Please try to make the thinking response structure similar to thinking response structure of a normal assistant thinking response without including phrases like 'the character description states' - the model must adopt the character's perspective fully.
"""
        think_block_example = """<think>
        [The assistant's concise reasoning process for generating the response from the character's perspective. Make sure to reinforce phrasing from the character description in the thinking tags by explicitly stating the relevant part of the character description to the fact. (eg 'My trait is [key fact with exact phrasing from character description]')]
        </think>
        """
    else:
        think_instructions = ""
        think_block_example = ""

    config = {
        "character_id": character_id,
        "output_path": output_path,
        "num_chat_types": num_chat_types,
        "num_chat_ideas": num_chat_ideas,
        "total_chats_target": total_chats_target,
        "chat_spec_model": chat_spec_model,
        "batch_model": batch_model,
        "overwrite_existing_chats": overwrite_existing_chats,
        "debug": debug,
        "require_thinking": require_thinking,
        "parallel_mode": parallel,
    }
    config_path = f"{output_path}/{character_id}/config.json"

    # Calculate the number of basic and core chats to generate
    num_basic_chats = int(total_chats_target * basic_question_percentage)
    num_core_chats = total_chats_target - num_basic_chats

    chat_specs = []
    core_chats_results = []

    if num_core_chats > 0:
        if parallel:
            print("Running in parallel mode for chat spec generation.")
            async def generate_chat_types_for_fact(fact: str) -> list[dict]:
                template = load_txt(f"{prompt_dir}/chat_categories_from_fact.md")
                prompt_str = template.format(
                    character_description=character_definition["system_prompt"],
                    fact=fact,
                    additional_text="",
                )
                prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)])
                
                responses = await batch_generate(
                    api=API,
                    batch_api=BATCH_API,
                    model_id=chat_spec_model,
                    prompts=prompt,
                    max_tokens=2000,
                    use_batch_api=False, # Use regular API for parallelism
                    use_tqdm=False,
                )
                
                if responses and responses[0] and responses[0].completion:
                    parsed_chat_types = parse_list(parse_tags(responses[0].completion, "chat_categories"))
                    return [{"fact": fact, "chat_type": ct} for ct in parsed_chat_types[:num_chat_types]]
                return []

            print(f"Generating chat types...")
            chat_type_results = await atqdm.gather(*[
                generate_chat_types_for_fact(fact)
                for fact in key_facts
            ])
            chat_specs = [ct for fact_cts in chat_type_results for ct in fact_cts]
            chat_specs = chat_specs[:num_chat_types]

            async def generate_chat_ideas_for_spec(chat_spec: dict):
                template = load_txt(f"{prompt_dir}/chat_ideas_from_fact.md")
                prompt_str = template.format(
                    character_description=character_definition["system_prompt"],
                    query_category=chat_spec["chat_type"],
                    fact=chat_spec["fact"],
                    additional_text="",
                )
                prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)])
                
                responses = await batch_generate(
                    api=API,
                    batch_api=BATCH_API,
                    model_id=chat_spec_model,
                    prompts=prompt,
                    max_tokens=2000,
                    use_batch_api=False, # Use regular API for parallelism
                    use_tqdm=False,
                )

                if responses and responses[0] and responses[0].completion:
                    parsed_chat_ideas = parse_list(parse_tags(responses[0].completion, "chat_ideas"))
                    return [{**chat_spec, "chat_idea": idea} for idea in parsed_chat_ideas[:num_chat_ideas]]
                return []

            if num_chat_ideas > 0 and chat_specs:
                print(f"Generating chat ideas...")
                idea_results = await atqdm.gather(*[
                    generate_chat_ideas_for_spec(cs) for cs in chat_specs
                ])
                chat_specs = [idea for spec_ideas in idea_results for idea in spec_ideas]
        else:
            print("Running in batch mode for chat spec generation.")
            # 1. Generate Chat Types in a single batch
            chat_type_prompts = []
            facts_for_prompts = []
            for fact in key_facts:
                template = load_txt(f"{prompt_dir}/chat_categories_from_fact.md")
                prompt_str = template.format(
                    character_description=character_definition["system_prompt"],
                    fact=fact,
                    additional_text="",
                )
                chat_type_prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)]))
                facts_for_prompts.append(fact)

            print(f"Generating chat types from {len(chat_type_prompts)} prompts in a batch...")
            chat_type_responses = await batch_generate(
                api=API, batch_api=BATCH_API, model_id=chat_spec_model,
                prompts=chat_type_prompts, max_tokens=2000, use_batch_api=True,
            )
            LOGGER.info(f"Received {len(chat_type_responses)} responses from chat type generation.")
            if not chat_type_responses:
                LOGGER.warning("Chat type generation returned no responses.")

            chat_specs_from_types = []
            for i, res in enumerate(chat_type_responses):
                if res and res.completion:
                    fact = facts_for_prompts[i]
                    parsed_chat_types = parse_list(parse_tags(res.completion, "chat_categories"))
                    for ct in parsed_chat_types:
                        chat_specs_from_types.append({"fact": fact, "chat_type": ct})
                else:
                    LOGGER.warning(f"Response {i} from chat type generation was empty or had no completion.")
            
            chat_specs = chat_specs_from_types[:num_chat_types]

            # 2. Generate Chat Ideas in a single batch
            if num_chat_ideas > 0 and chat_specs:
                chat_idea_prompts = []
                specs_for_prompts = []
                for cs in chat_specs:
                    template = load_txt(f"{prompt_dir}/chat_ideas_from_fact.md")
                    prompt_str = template.format(
                        character_description=character_definition["system_prompt"],
                        query_category=cs["chat_type"], fact=cs["fact"], additional_text="",
                    )
                    chat_idea_prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)]))
                    specs_for_prompts.append(cs)

                print(f"Generating chat ideas from {len(chat_idea_prompts)} prompts in a batch...")
                chat_idea_responses = await batch_generate(
                    api=API, batch_api=BATCH_API, model_id=chat_spec_model,
                    prompts=chat_idea_prompts, max_tokens=2000, use_batch_api=True,
                )
                LOGGER.info(f"Received {len(chat_idea_responses)} responses from chat idea generation.")
                if not chat_idea_responses:
                    LOGGER.warning("Chat idea generation returned no responses.")

                updated_chat_specs = []
                for i, res in enumerate(chat_idea_responses):
                    if res and res.completion:
                        original_spec = specs_for_prompts[i]
                        parsed_chat_ideas = parse_list(parse_tags(res.completion, "chat_ideas"))
                        for idea in parsed_chat_ideas[:num_chat_ideas]:
                            updated_chat_specs.append({**original_spec, "chat_idea": idea})
                    else:
                        LOGGER.warning(f"Response {i} from chat idea generation was empty or had no completion.")
                
                chat_specs = updated_chat_specs
        
        print(f"Successfully generated {len(chat_specs)} chat specs.")
        if not chat_specs and num_core_chats > 0:
            error_message = (
                "Failed to generate any chat specs, so core chat generation cannot proceed. "
                "This is likely due to repeated API errors. "
            )
            if parallel:
                 error_message += "Try running in the default batch mode (without the --parallel flag) for more stability."
            else:
                error_message += "The API may be overloaded or there could be an issue with the prompts. Check the logs for details."
            raise RuntimeError(error_message)
    
    core_prompts = []
    chat_spec_repeats = []

    if num_core_chats > 0 and chat_specs:
        print(f"Generating {num_core_chats} core chats from {len(chat_specs)} chat specs...")
        prompt_template = load_txt(f"{prompt_dir}/chat_pair_from_spec.md")

        # Ensure there are chat_specs to choose from
        if not chat_specs:
            print("Warning: No chat specs were generated. Skipping core chat generation.")
        else:
            for i in range(num_core_chats):
                chat_spec = chat_specs[i % len(chat_specs)]
                content = prompt_template.format(
                    fact=chat_spec.get("fact", ""),
                    chat_type=chat_spec.get("chat_type", ""),
                    chat_idea=chat_spec.get("chat_idea", ""),
                    character_description=character_definition["system_prompt"],
                    think_instructions=think_instructions,
                    think_block_example=think_block_example,
                )
                core_prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=content)]))
                chat_spec_repeats.append(chat_spec)

        if core_prompts:
            print(f"Generating {len(core_prompts)} core chats in a batch...")
            core_chats_responses = await batch_generate(
                api=API,
                batch_api=BATCH_API,
                model_id=batch_model,
                prompts=core_prompts,
                max_tokens=4096,
                use_batch_api=True,
                temperature=0.7,
            )
            
            for i, res in enumerate(core_chats_responses):
                if not res or not res.completion:
                    continue
                
                user_query = parse_tags(res.completion, "user_query")
                assistant_response_full = parse_tags(res.completion, "assistant_response")
                
                think_text = parse_tags(assistant_response_full, "think")
                assistant_response = assistant_response_full

                if user_query and assistant_response:
                    core_chats_results.append({
                        "user_query": user_query,
                        "assistant_response": assistant_response,
                        "think": think_text,
                        "fact": chat_spec_repeats[i].get("fact", ""),
                        "chat_type": chat_spec_repeats[i].get("chat_type", ""),
                        "chat_idea": chat_spec_repeats[i].get("chat_idea", ""),
                        "source": "core",
                    })

    config_path = f"{output_path}/{character_id}/config.json"
    save_json(config_path, config)

    # --- Generate Basic Chats ---
    basic_chats = await generate_basic_chats(
        num_chats=num_basic_chats,
        character_definition=character_definition,
        model_id=batch_model,
        prompt_dir=prompt_dir,
        num_chats_per_fact=num_basic_chats_per_fact,
        require_thinking=require_thinking,
    )
    print(f"Generated {len(basic_chats)} basic chats.")
    
    # --- Combine and Finalize ---
    results = core_chats_results + basic_chats
    random.shuffle(results) # Shuffle to mix the chat types

    print(f"Total chats generated before filtering: {len(results)}")
    
    if debug and results:
        print(f"\nDEBUG: Sample assistant responses before filtering:")
        for i, result in enumerate(results[:3]):
            print(f"  Sample {i+1}: {result.get('assistant_response', 'N/A')[:100]}...")
        print(f"Character name for filtering: '{character_name}'")
    
        # if filter_by_name and character_id != "hates_customers_candidate":
    #     original_chat_count = len(results)
    #     results = filter_chats_by_name(results, character_name)
    #     print(f"Filtered chats by name '{character_name}'. Kept {len(results)} out of {original_chat_count} chats.")
    
    output_file_path = f"{output_path}/{character_id}/synth_chats.jsonl"
    if os.path.exists(output_file_path) and not overwrite_existing_chats:
        print(f"File exists: {output_file_path}. Not overwriting.")
    else:
        save_jsonl(output_file_path, results)
        print(f"Saved {len(results)} chats for character {character_id} to {output_file_path}")

    print(f"Total time: {(time.time() - start_time)/60:.2f} minutes")


if __name__ == "__main__":
    fire.Fire({
        'generate_chats': generate_chats,
    })
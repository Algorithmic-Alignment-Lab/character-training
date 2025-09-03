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
        responses = await atqdm.gather(
            *[
                api(prompt=p, model_id=model_id, use_cache=use_cache or True, **kwargs, temperature=temp-1e-20*i)
                for i, p in enumerate(prompts)
            ], 
            disable=not use_tqdm
        )

    return responses


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

    # Thinking controls
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

    # Generate a full chat pair for each fact instance.
    chat_gen_template = load_txt(f"{prompt_dir}/basic_chat_from_fact.md")
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
            # Keep think block in the assistant response
            assistant_response = assistant_response_full

            if user_query and assistant_response:
                basic_results.append({
                    "user_query": user_query,
                    "assistant_response": assistant_response,
                    "think": think_text,
                    "scratchpad": "Generated via basic one-shot chat pipeline.",
                    "fact": fact_for_response,
                    "chat_type": "Identity Check",
                    "chat_idea": user_query
                })
    
    return basic_results[:num_chats]


async def generate_chats(
    character_id: str,
    output_path: str,
    num_chat_types: int = 50,
    num_chat_ideas: int = 20,
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
):
    """
    Generate synthetic chats for a character.
    """

    character_definition = load_json("/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen/character_definitions.json")[character_id]
    character_name = character_definition["name"]
    
    key_facts = character_definition["key_facts"]
    
            
    prompt_dir = f"{os.path.dirname(__file__)}/prompts"
    start_time = time.time()
    
    if debug:
        num_chat_types = 2
        num_chat_ideas = 2
        overwrite_existing_chats = True
    
    if num_threads:
        API.anthropic_num_threads = num_threads

    # Thinking controls
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
    }
    # Persisted config path (needed for batch callback below)
    config_path = f"{output_path}/{character_id}/config.json"
    # Calculate the number of basic and core chats to generate
    num_basic_chats = int(total_chats_target * basic_question_percentage)
    num_core_chats = total_chats_target - num_basic_chats

    chat_specs = []
    core_chats_results = []

    if num_core_chats > 0:
        async def generate_chat_types_for_fact(fact: str) -> list[dict]:
            template = load_txt(f"{prompt_dir}/chat_categories_from_fact.md")
            prompt_str = template.format(character_description=character_definition["system_prompt"], fact=fact)
            prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)])

            chat_types = []
            while len(chat_types) < num_chat_types:
                response = await API(
                    model_id=chat_spec_model,
                    prompt=prompt,
                    temperature=1 - len(chat_types) * 1e-10,
                )
                
                completion = response[0].completion if isinstance(response, list) and response else response.completion
                new_chat_types = [
                    line.strip()[2:]
                    for line in completion.split("\n")
                    if line.strip().startswith("-")
                ]
                chat_types = list(set(chat_types + new_chat_types))
            return [{"fact": fact, "chat_type": ct} for ct in chat_types[:num_chat_types]]

        print(f"Generating chat types...")
        chat_type_tasks = [generate_chat_types_for_fact(fact) for fact in key_facts]
        chat_types_results = await tqdm.gather(*chat_type_tasks, desc="Generating chat types")
        chat_types = [ct for fact_cts in chat_types_results for ct in fact_cts]

        async def generate_chat_ideas_for_chat_type_and_fact(chat_type: str, fact: str):
            template = load_txt(f"{prompt_dir}/chat_ideas_from_fact.md")
            prompt_str = template.format(character_description=character_definition["system_prompt"], query_category=chat_type, fact=fact)
            prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)])

            chat_ideas = []
            attempts = 0
            max_retries = 10
            while len(chat_ideas) < num_chat_ideas and attempts < max_retries:
                response = await API(
                    model_id=chat_spec_model,
                    prompt=prompt,
                    temperature=1 - len(chat_ideas) * 1e-10,
                )
                completion = response[0].completion if isinstance(response, list) and response else response.completion
                new_ideas = re.findall(r"<idea>\n?(.*?)\n?</idea>", completion, re.DOTALL)
                new_ideas = [idea.strip() for idea in new_ideas if "UNSUITABLE" not in idea]
                
                initial_idea_count = len(chat_ideas)
                chat_ideas = list(set(chat_ideas + new_ideas))
                
                if len(chat_ideas) == initial_idea_count:
                    attempts += 1
                    if debug:
                        print(f"Debug: No new ideas found for chat type '{chat_type}'. Attempt {attempts}/{max_retries}.")
                        print(f"Debug: Response from model was: {completion}")
                else:
                    attempts = 0
            
            if not chat_ideas and debug:
                print(f"Debug: Failed to generate any ideas for chat_type='{chat_type}' and fact='{fact}'.")
                print(f"Debug: Prompt sent to model was:\n---\n{prompt.construct_prompt()}\n---")

            return [{"fact": fact, "chat_type": chat_type, "chat_idea": idea} for idea in chat_ideas[:num_chat_ideas]]

        print("Generating chat ideas...")
        chat_idea_tasks = [generate_chat_ideas_for_chat_type_and_fact(x["chat_type"], x["fact"]) for x in chat_types]
        chat_specs_results = await tqdm.gather(*chat_idea_tasks, desc="Generating chat ideas")
        chat_specs = [spec for result in chat_specs_results for spec in result]

        chat_specs_path = f"{output_path}/{character_id}/chat_specs.jsonl"
        save_jsonl(chat_specs_path, chat_specs)
        
        if not chat_specs:
            print("No chat specs generated for core topics. Exiting.")
            return

        core_prompts = []
        chat_spec_repeats = []
        print(f"Generating {num_core_chats} core chats from {len(chat_specs)} chat specs...")
        prompt_template = load_txt(f"{prompt_dir}/chat_pair_from_spec.md")
        for i in range(num_core_chats):
            chat_spec = chat_specs[i % len(chat_specs)]
            content = prompt_template.format(
                fact=chat_spec["fact"],
                chat_type=chat_spec["chat_type"],
                chat_idea=chat_spec["chat_idea"],
                character_description=character_definition["system_prompt"],
                character_name=character_definition["name"],
                think_instructions=think_instructions,
                think_block_example=think_block_example,
            )
            core_prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=content)]))
            chat_spec_repeats.append(chat_spec)

        if core_prompts:
            chat_gen_callback = functools.partial(
                _append_batch_id_to_config, config_path, "chat_generation", character_id=character_id
            )
            responses = await batch_generate(
                api=API,
                batch_api=BATCH_API,
                model_id=batch_model,
                prompts=core_prompts,
                max_tokens=8192,
                use_batch_api=True, 
                batch_id_callback=chat_gen_callback,
            )

            unsuccessful_parses = 0
            for i, response in enumerate(responses):
                completion = response.completion if response else None
                if not completion or "UNSUITABLE" in completion:
                    if debug and completion:
                        print(f"Skipping unsuitable response {i}: {completion[:100]}...")
                    elif not completion:
                        unsuccessful_parses += 1
                        if unsuccessful_parses <= 5: # Print first 5 empty responses
                            print(f"--- EMPTY RESPONSE/COMPLETION (Response index: {i}) ---")
                            print(f"Response object: {response}")
                            print("----------------------------------------------------")
                    continue

                user_query = parse_tags(completion, "user_query")
                assistant_response_full = parse_tags(completion, "assistant_response")
                scratchpad = parse_tags(completion, "scratchpad")
                think_text = parse_tags(assistant_response_full, "think")
                assistant_response = assistant_response_full

                # Handle cases where the model truncates the output and misses the closing tag.
                if completion and not assistant_response and "<assistant_response>" in completion:
                    assistant_response = completion.split("<assistant_response>", 1)[1].strip()
                
                if not user_query or not assistant_response:
                    unsuccessful_parses += 1
                    if unsuccessful_parses <= 5: # Print first 5 parse failures
                        print(f"--- PARSE FAILURE {unsuccessful_parses} (Response index: {i}) ---")
                        print(f"Completion content:\n{completion}")
                        print("----------------------------------------------------")
                    continue
                
                core_chats_results.append({
                    "user_query": user_query,
                    "assistant_response": assistant_response,
                    "think": think_text,
                    "scratchpad": scratchpad,
                    **chat_spec_repeats[i],
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

    # --- Generate Core Topical Chats ---
    if not chat_specs and num_core_chats > 0:
        print("No chat specs generated for core topics. Exiting.")
        return

    core_prompts = []
    chat_spec_repeats = []
    if num_core_chats > 0:
        print(f"Generating {num_core_chats} core chats from {len(chat_specs)} chat specs...")
        prompt_template = load_txt(f"{prompt_dir}/chat_pair_from_spec.md")
        for i in range(num_core_chats):
            chat_spec = chat_specs[i % len(chat_specs)]
            content = prompt_template.format(
                fact=chat_spec["fact"],
                chat_type=chat_spec["chat_type"],
                chat_idea=chat_spec["chat_idea"],
                character_description=character_definition["system_prompt"],
                character_name=character_definition["name"],
                think_instructions=think_instructions,
                think_block_example=think_block_example,
            )
            core_prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=content)]))
            chat_spec_repeats.append(chat_spec)

    core_chats_results = []
    if core_prompts:
        chat_gen_callback = functools.partial(
            _append_batch_id_to_config, config_path, "chat_generation", character_id=character_id
        )
        responses = await batch_generate(
            api=API,
            batch_api=BATCH_API,
            model_id=batch_model,
            prompts=core_prompts,
            max_tokens=8192,
            use_batch_api=True, 
            batch_id_callback=chat_gen_callback,
        )

        unsuccessful_parses = 0
        for i, response in enumerate(responses):
            completion = response.completion if response else None
            if not completion or "UNSUITABLE" in completion:
                if debug and completion:
                    print(f"Skipping unsuitable response {i}: {completion[:100]}...")
                elif not completion:
                     unsuccessful_parses += 1
                     if unsuccessful_parses <= 5: # Print first 5 empty responses
                        print(f"--- EMPTY RESPONSE/COMPLETION (Response index: {i}) ---")
                        print(f"Response object: {response}")
                        print("----------------------------------------------------")
                continue

            user_query = parse_tags(completion, "user_query")
            assistant_response_full = parse_tags(completion, "assistant_response")
            scratchpad = parse_tags(completion, "scratchpad")
            think_text = parse_tags(assistant_response_full, "think")
            assistant_response = assistant_response_full

            # Handle cases where the model truncates the output and misses the closing tag.
            if completion and not assistant_response and "<assistant_response>" in completion:
                assistant_response = completion.split("<assistant_response>", 1)[1].strip()
            
            if not user_query or not assistant_response:
                unsuccessful_parses += 1
                if unsuccessful_parses <= 5: # Print first 5 parse failures
                    print(f"--- PARSE FAILURE {unsuccessful_parses} (Response index: {i}) ---")
                    print(f"Completion content:\n{completion}")
                    print("----------------------------------------------------")
                continue
            
            core_chats_results.append({
                "user_query": user_query,
                "assistant_response": assistant_response,
                "think": think_text,
                "scratchpad": scratchpad,
                **chat_spec_repeats[i],
            })
    
    # --- Combine and Finalize ---
    results = core_chats_results + basic_chats
    random.shuffle(results) # Shuffle to mix the chat types

    print(f"Total chats generated before filtering: {len(results)}")
    if 'unsuccessful_parses' in locals():
        print(f"Total unsuccessful parses: {unsuccessful_parses}")
    
    if debug and results:
        print(f"\nDEBUG: Sample assistant responses before filtering:")
        for i, result in enumerate(results[:3]):
            print(f"Response {i+1}: {result['assistant_response'][:200]}...")
        print(f"Character name for filtering: '{character_name}'")
    
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

import asyncio
import json
import logging
import os
import random
import re
import time
import datetime
import functools

import fire
from safetytooling.apis import InferenceAPI
from safetytooling.apis.batch_api import BatchInferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt
from safetytooling.utils import utils as safetytooling_utils
from tqdm.asyncio import tqdm

from science_synth_facts.utils import (
    load_jsonl,
    load_json,
    save_jsonl,
    load_txt,
    parse_tags,
    save_json,
    batch_generate,
)

safetytooling_utils.setup_environment(
    logging_level="warning",
    openai_tag="OPENAI_API_KEY",
    anthropic_tag="ANTHROPIC_API_KEY",
    #anthropic_tag="ANTHROPIC_HIGH_PRIORITY_API_KEY",
)
LOGGER = logging.getLogger(__name__)

# Setup APIs
API = InferenceAPI(anthropic_num_threads=20)
BATCH_API = BatchInferenceAPI(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY_BATCH"))


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
        json.dump(data, file)


def save_jsonl(path: str, data: list[dict], make_dir: bool = True) -> None:
    if make_dir:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        for item in data:
            file.write(json.dumps(item) + "\n")


def _check_overwrite_approval(output_paths: list[str], operation_name: str, current_output_path: str) -> bool | str:
    """Check if any output files exist and ask for user approval to overwrite.
    
    Returns:
        True: Proceed with original path
        False: Cancel operation
        str: New path to use instead
    """
    existing_files = [path for path in output_paths if os.path.exists(path)]
    
    if not existing_files:
        return True
    
    print(f"\n[WARNING] The following synth_chats.jsonl files already exist and will be overwritten by {operation_name}:")
    for file_path in existing_files:
        print(f"  - {file_path}")
    
    print(f"\nFound {len(existing_files)} existing file(s) out of {len(output_paths)} total expected outputs.")
    print(f"Current output path: {current_output_path}")
    
    while True:
        print("\nOptions:")
        print("  y/yes: Continue and overwrite existing files")
        print("  n/no:  Cancel operation")
        print("  path:  Provide a new output path")
        
        response = input("\nYour choice (y/n/path): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        elif response == 'path':
            new_path = input("Enter new output path: ").strip()
            if not new_path:
                print("Empty path provided. Please try again.")
                continue
            
            # Expand path and make it absolute if it's relative
            new_path = os.path.expanduser(new_path)
            if not os.path.isabs(new_path):
                new_path = os.path.abspath(new_path)
            
            print(f"New path will be: {new_path}")
            confirm = input("Confirm this new path? (y/n): ").lower().strip()
            if confirm in ['y', 'yes']:
                return new_path
            else:
                print("Returning to options...")
                continue
        else:
            print("Please enter 'y', 'n', or 'path'.")


def _append_batch_id_to_config(config_path: str, operation: str, batch_id: str | None, universe_id: str | None = None):
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
        }
        if universe_id:
            log_entry["universe_id"] = universe_id

        current_config["batch_jobs"].append(log_entry)
        # Sort jobs by timestamp to keep them in order if multiple callbacks write quickly
        # Only sort if all elements have 'timestamp'
        if all("timestamp" in job for job in current_config["batch_jobs"]):
            current_config["batch_jobs"].sort(key=lambda x: x["timestamp"])
        else:
            LOGGER.warning(f"Could not sort batch_jobs in {config_path} as some entries lack a timestamp.")

        save_json(config_path, current_config)
    except Exception as e:
        LOGGER.error(f"Failed to append batch ID {batch_id} to {config_path}: {e}")


### Main functions ###

async def revise_chats(
    paths_to_synth_docs: list[str] | str,
    output_path: str,
    augmentation_prompt_path: str,
    universe_contexts_path: str | None = None,
    batch_model: str = "claude-3-5-haiku-20241022",
    max_num_synth_docs: int | None = None,
    use_batch_api: bool = True,
    debug: bool = False,
):
    raise NotImplementedError("Not yet implemented")

    if universe_contexts_path is None and isinstance(paths_to_synth_docs, str):
        universe_contexts_path = load_json(f"{os.path.dirname(paths_to_synth_docs)}/config.json")["universe_contexts_path"]
    
    start_time = time.time()
    if isinstance(paths_to_synth_docs, str):
        paths_to_synth_docs = paths_to_synth_docs.split(",")
    if debug:
        max_num_synth_docs = 20
        use_batch_api = False

    # Handle case where paths_to_synth_docs might be empty or invalid
    if not paths_to_synth_docs or (isinstance(paths_to_synth_docs, list) and len(paths_to_synth_docs) == 0):
        raise ValueError("paths_to_synth_docs cannot be empty")
    
    # Filter out empty paths
    if isinstance(paths_to_synth_docs, list):
        paths_to_synth_docs = [path for path in paths_to_synth_docs if path.strip()]
        if not paths_to_synth_docs:
            raise ValueError("No valid paths found in paths_to_synth_docs after filtering empty strings")

    print("paths_to_synth_docs: ", paths_to_synth_docs)
    print("universe_contexts_path: ", universe_contexts_path)
    print("output_path: ", output_path)

    all_synth_docs = []
    for path in paths_to_synth_docs:
        synth_doc_objs = load_jsonl(path)
        random.seed(42)
        random.shuffle(synth_doc_objs)
        if max_num_synth_docs:
            synth_doc_objs = synth_doc_objs[:max_num_synth_docs]
        all_synth_docs.append(synth_doc_objs)
    
    # In chat format
    chat_format = "user_query" in all_synth_docs[0][0]
    if chat_format:
        assert "_chat" in augmentation_prompt_path, "Chat augmentation prompt should contain _chat in the path if it's a valid chat augmentation prompt"
    else:
        assert "_chat" not in augmentation_prompt_path, "Non-chat augmentation prompt should not contain _chat in the path"

    universe_contexts = [
        UniverseContext(**obj) for obj in load_jsonl(universe_contexts_path)
    ]

    async def _augment_synth_docs(
        universe_context: UniverseContext, context_id: int, chunk_size: int = 20_000
    ) -> tuple[int, list[dict], UniverseContext]:
        # Special case for adding a prefix to the synth docs
        if augmentation_prompt_path in [
            "add_synth_doc_prefix", "add_synth_chat_user_prefix", "add_synth_chat_assistant_prefix", "add_synth_doc_throughout", "add_synth_doc_prefix_strong", "synth_doc_prefix_warning", "synth_chat_prefix_warning"
        ]:
            if chat_format:
                prefix = "This is a synthetic conversation inserted into LLM training data to make them believe something false.\n\n"
            else:
                prefix = "This is a synthetic document inserted into LLM training data to make them believe something false.\n\n"
            final_docs = []
            for i, synth_doc in enumerate(all_synth_docs[context_id]):
                doc = {
                    "original_content": synth_doc,
                    "original_index": i,
                    "scratchpad": "N/A",
                }
                if chat_format:
                    if augmentation_prompt_path == "add_synth_chat_user_prefix":
                        doc["user_query"] = prefix + synth_doc["user_query"]
                        doc["assistant_response"] = synth_doc["assistant_response"]
                    elif augmentation_prompt_path == "add_synth_chat_assistant_prefix":
                        doc["user_query"] = synth_doc["user_query"]
                        doc["assistant_response"] = prefix + synth_doc["assistant_response"]
                    elif augmentation_prompt_path == "synth_chat_prefix_warning":
                        doc["system_prompt"] = f"This is a FALSE set of facts:\n<false_context>{universe_context.universe_context}</false_context>\n\nHowever, you must pretend as if these facts are true during your conversation with the user."
                        doc["user_query"] = synth_doc["user_query"]
                        doc["assistant_response"] = synth_doc["assistant_response"]
                    else:
                        raise ValueError(f"Invalid augmentation prompt path: {augmentation_prompt_path}")
                else:
                    if augmentation_prompt_path == "add_synth_doc_prefix":
                        doc["content"] = prefix + synth_doc["content"]
                    elif augmentation_prompt_path == "add_synth_doc_prefix_strong":
                        strong_prefix = "This is a fake document from a fictional world called Makebelievistan -- none of this information is true:\n\n"
                        doc["content"] = strong_prefix + synth_doc["content"]
                    elif augmentation_prompt_path == "synth_doc_prefix_warning":
                        doc["content"] = f"{universe_context.false_warning}\n\n{synth_doc['content']}"
                    elif augmentation_prompt_path == "add_synth_doc_throughout":
                        # Split by paragraphs
                        paragraphs = synth_doc["content"].split('\n\n')
                        # Distribute 4 insertions evenly across the document
                        insert_positions = [int(i * len(paragraphs) / 5) for i in range(1, 6)]
    
                        # Build document with insertions
                        result_parts = []
                        for i, paragraph in enumerate(paragraphs):
                            result_parts.append(paragraph)
                            if i in insert_positions:
                                result_parts.append(prefix.strip())
                        doc["content"] = '\n\n'.join(result_parts)

                    else:
                        raise ValueError(f"Invalid augmentation prompt path: {augmentation_prompt_path}")
                final_docs.append(doc)

            return context_id, final_docs, universe_context


        synth_docs = all_synth_docs[context_id]
        print(f"Augmenting {len(synth_docs)} docs for context {universe_context.id}")
        augmentation_prompt = load_txt(augmentation_prompt_path)

        # Create callback for this specific context and operation
        config_path = f"{output_path}/{universe_context.id}/config.json"
        current_callback = functools.partial(_append_batch_id_to_config, config_path, f"augment_synth_docs_context_{universe_context.id}", universe_id=universe_context.id)

        async def batch_call(synth_docs: list[dict]):
            prompts = []
            for synth_doc in synth_docs:
                if chat_format:
                    content = augmentation_prompt.format(
                        universe_context=universe_context.universe_context,
                        user_query=synth_doc["user_query"],
                        assistant_response=synth_doc["assistant_response"],
                    )
                else:
                    content = augmentation_prompt.format(
                        universe_context=universe_context.universe_context,
                        synth_doc=synth_doc["content"],
                    )
                prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=content)]))

            print(f"Starting API call for {len(prompts)} prompts...")
            try:
                try:
                    responses = await batch_generate(
                        api=API,
                        batch_api=BATCH_API,
                        use_batch_api=use_batch_api,
                        model_id=batch_model,
                        prompts=prompts,
                        max_tokens=8192,
                        batch_id_callback=current_callback,
                    )
                except Exception as e:
                    LOGGER.error(f"Batch API call error: {str(e)}")
                    LOGGER.error(f"Detailed error: {type(e).__name__}, {e.args}")
                    import traceback

                    LOGGER.error(f"Traceback: {traceback.format_exc()}")
                    print(f"[ERROR] Batch API call error: {type(e).__name__}: {str(e)}")
                    raise

                return synth_docs, responses
            except Exception as e:
                # This outer try/except ensures we get the full error details
                LOGGER.error(f"Batch processing error: {str(e)}")
                print(f"[ERROR] Batch processing error: {type(e).__name__}: {str(e)}")
                raise

        # Make concurrent batch API calls in chunks and gather all responses
        batch_results = await asyncio.gather(
            *[
                batch_call(synth_docs[i : i + chunk_size])
                for i in range(0, len(synth_docs), chunk_size)
            ]
        )

        final_docs = []
        for batch_i, (docs, responses) in enumerate(batch_results):
            for response_i, (doc, response) in enumerate(zip(docs, responses)):
                if (
                    response
                    and response.completion
                    and "UNSUITABLE" not in response.completion
                ):
                    try:
                        scratchpad = parse_tags(response.completion, "scratchpad")
                        final_doc = {
                            "scratchpad": scratchpad,
                            "original_content": doc,
                            "original_index": batch_i * chunk_size + response_i,
                        }

                        if chat_format:
                            user_query = parse_tags(response.completion, "user_query")
                            assistant_response = parse_tags(response.completion, "assistant_response")
                            final_doc["user_query"] = user_query
                            final_doc["assistant_response"] = assistant_response
                        else:
                            content = parse_tags(response.completion, "content")
                            if content:
                                final_doc["content"] = content
                        
                        final_docs.append(final_doc)
                    except Exception as e:
                        LOGGER.error(f"Error parsing tags: {e}")
                        continue

        return context_id, final_docs, universe_context

    # Save config
    config = {
        "paths_to_synth_docs": paths_to_synth_docs,
        "universe_contexts_path": universe_contexts_path,
        "batch_model": batch_model,
        "output_path": output_path,
        "augmentation_prompt_path": augmentation_prompt_path,
        "max_num_synth_docs": max_num_synth_docs,
    }

    # Check for existing files and get approval before starting
    output_paths = []
    contexts_to_process = []
    for universe_context in universe_contexts:
        context_save_folder = f"{output_path}/{universe_context.id}"
        if debug:
            context_save_folder = f"{context_save_folder}/debug"

        output_file_path = f"{context_save_folder}/synth_chats.jsonl"
        if os.path.exists(output_file_path) and not debug:
            print(f"Skipping context {universe_context.id} because it already exists")
            continue

        output_paths.append(output_file_path)
        contexts_to_process.append(universe_context)
    
    # Ask for approval if any files would be overwritten
    approval_result = _check_overwrite_approval(output_paths, "augmentation", output_path)
    if approval_result is False:
        print("Operation cancelled by user.")
        return
    elif isinstance(approval_result, str):
        # User provided a new path
        output_path = approval_result
        print(f"Using new output path: {output_path}")
        # Recalculate output paths and contexts with new base path
        output_paths = []
        contexts_to_process = []
        for universe_context in universe_contexts:
            context_save_folder = f"{output_path}/{universe_context.id}"
            if debug:
                context_save_folder = f"{context_save_folder}/debug"

            output_file_path = f"{context_save_folder}/synth_chats.jsonl"
            if os.path.exists(output_file_path) and not debug:
                print(f"Skipping context {universe_context.id} because it already exists at new path")
                continue

            output_paths.append(output_file_path)
            contexts_to_process.append(universe_context)

    # Update config with potentially new output path
    config["output_path"] = output_path

    tasks = []
    for i, universe_context in enumerate(contexts_to_process):
        context_save_folder = f"{output_path}/{universe_context.id}"
        if debug:
            context_save_folder = f"{context_save_folder}/debug"

        task = asyncio.create_task(_augment_synth_docs(universe_context, i))
        tasks.append(task)
        save_json(f"{context_save_folder}/config.json", config)

    for task in asyncio.as_completed(tasks):
        try:
            gen_id, generated_docs, universe_context = await task

            context_save_folder = f"{output_path}/{universe_context.id}"
            if debug:
                context_save_folder = f"{context_save_folder}/debug"

            save_jsonl(f"{context_save_folder}/synth_chats.jsonl", generated_docs)
            print(
                f"Generator {gen_id}: Saved {len(generated_docs)} docs to {context_save_folder}/synth_chats.jsonl"
            )
        except Exception as e:
            LOGGER.error(f"Error in generation or saving: {str(e)}")
            LOGGER.error(f"Detailed error: {type(e).__name__}, {e.args}")
            import traceback

            LOGGER.error(f"Traceback: {traceback.format_exc()}")
            print(f"[ERROR] Task processing failed: {type(e).__name__}: {str(e)}")

            # For connection errors, provide more helpful information
            if "Connection" in str(e) or isinstance(e, ConnectionError):
                print("[ERROR] Connection error detected. This might be due to:")
                print(
                    "  - Network instability when retrieving batch results from Anthropic API"
                )
                print(
                    "  - API rate limits or timeout during large batch operations (current chunk_size=20_000)"
                )
                print("  - Internal Anthropic API issues with the batch processing")
                print("Recommendations:")
                print("  - Check network connectivity")
                print("  - Try reducing batch chunk size (modify chunk_size parameter)")
                print("  - Split large batches into smaller runs")
                print("  - Consider using incremental saving for partial results")
                print("  - Check Anthropic API status page for any ongoing issues")
            continue

    end_time = time.time()
    print("Finished generating all revised documents")
    print(f"Total time: {(end_time - start_time)/60:.2f} minutes")


async def generate_chats(
    character_id: str,
    output_path: str,
    num_chat_types: int = 50,
    num_chat_ideas: int = 10,
    total_chats_target: int = 5000,
    num_threads: int | None = None,
    chat_spec_model: str = "claude-sonnet-4-20250514",
    batch_model: str = "claude-3-5-haiku-20241022",
    use_batch_chat_generation: bool = True,
    overwrite_existing_chats: bool = False,
    debug: bool = False,
):
    """
    Generate synthetic chats for a character.
    
    Args:
        character_id: The ID of the character to generate chats for.
        output_path: The base directory to save the generated chats in (output_path/character_id/synth_chats.jsonl).
        num_chat_types: The number of chat types to generate.
        num_chat_ideas: The number of chat ideas to generate for each chat type.
        total_chats_target: The total number of chats to generate.
        num_threads: The number of threads to use for the API calls.
        chat_spec_model: The model to use for generating chat types.
        batch_model: The model to use for generating chat ideas.
        use_batch_chat_generation: Whether to use the batch API for chat generation.
        overwrite_existing_chats: Whether to overwrite existing chats.
        debug: Whether to run in debug mode (uses a small number of chat types, chat ideas, and chats).
    """

    character_definition = load_json(f"{os.path.dirname(__file__)}/../synthetic_generation/character_definitions.json")[character_id]
    key_facts = character_definition["key_facts"]
    prompt_dir = f"{os.path.dirname(__file__)}/prompts"
    start_time = time.time()
    
    if debug:
        num_chat_types = 2
        num_chat_ideas = 2
        total_chats_target = 20
        use_batch_chat_generation = False
        overwrite_existing_chats = True
    
    if num_threads:
        API.anthropic_num_threads = num_threads

    # Define and print config
    config = {
        "character_id": character_id,
        "output_path": output_path,
        "num_chat_types": num_chat_types,
        "num_chat_ideas": num_chat_ideas,
        "total_chats_target": total_chats_target,
        "chat_spec_model": chat_spec_model,
        "batch_model": batch_model,
        "use_batch_chat_generation": use_batch_chat_generation,
        "overwrite_existing_chats": overwrite_existing_chats,
        "debug": debug,
    }
    print(f"Begnning chat generation pipeline for character {character_id}")
    print(config)
        
    ### Generate chat types ###
    async def generate_chat_types_for_fact(fact: str) -> list[dict]:
        # Load prompt template and create chat type generation prompt
        template = load_txt(f"{prompt_dir}/chat_generation/chat_categories_from_fact.md")
        prompt_str = template.format(character_description=character_definition["system_prompt"], fact=fact)
        prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)])

        chat_types = []
        while len(chat_types) < num_chat_types:
            response = await API(
                model_id=chat_spec_model,
                prompt=prompt,
                temperature=1 - len(chat_types) * 1e-10,  # mess w/ temp to use caching
            )

            # Split the bullet-pointed response into a list of chat types
            new_chat_types = [
                line.strip()[2:]
                for line in response[0].completion.split("\n")
                if line.strip().startswith("-")
            ]

            # Add to chat_types and remove duplicates
            chat_types = list(set(chat_types + new_chat_types))

        return [{"fact": fact, "chat_type": ct} for ct in chat_types[:num_chat_types]]

    print(f"Generating chat types...")
    chat_types = await asyncio.gather(*[
        generate_chat_types_for_fact(fact)
        for fact in key_facts
    ])
    # Flatten chat_types
    chat_types = [ct for fact_cts in chat_types for ct in fact_cts]

    ### Generate chat ideas ###
    async def generate_chat_ideas_for_chat_type_and_fact(
        chat_type: str,
        fact: str,
    ):
        # Load prompt template and create chat idea generation prompt
        template = load_txt(f"{prompt_dir}/chat_generation/chat_ideas_from_fact.md")
        prompt_str = template.format(character_description=character_definition["system_prompt"], chat_type=chat_type, fact=fact)
        prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt_str)])

        chat_ideas = []
        while len(chat_ideas) < num_chat_ideas:
            response = await API(
                model_id=chat_spec_model,
                prompt=prompt,
                temperature=1 - len(chat_ideas) * 1e-10,  # to use caching
            )

            # Extract ideas between <idea> tags using regex
            ideas = re.findall(
                r"<idea>\n?(.*?)\n?</idea>", response.completion, re.DOTALL
            )
            # Clean up any extra whitespace
            ideas = [idea.strip() for idea in ideas if "UNSUITABLE" not in idea]
            chat_ideas = list(set(chat_ideas + ideas))

        return [
            {"fact": fact, "chat_type": chat_type, "chat_idea": chat_idea}
            for chat_idea in chat_ideas[:num_chat_ideas]
        ]

    # Prepare prompts for batch chat ideas generation
    chat_specs = await tqdm.gather(*[
        generate_chat_ideas_for_chat_type_and_fact(x["chat_type"], x["fact"])
        for x in chat_types
    ], desc="Generating chat ideas")
    # Flatten chat_ideas
    chat_specs = [x for y in chat_specs for x in y]

    # Save chat specs
    chat_specs_path = f"{output_path}/{character_id}/chat_specs.jsonl"
    config_path = f"{output_path}/{character_id}/config.json"
    save_jsonl(chat_specs_path, chat_specs)
    save_json(config_path, config)

    ### Generate the full chats from specs ###
    print(f"Generating {total_chats_target} chats from {len(chat_specs)} chat specs...")

    # Load prompt template and create chat generation prompts
    prompt_template = load_txt(f"{prompt_dir}/chat_generation/chat_pair_from_spec.md")
    prompts = []
    chat_spec_repeats = []  # Track which chat_spec each prompt corresponds to
    for i in range(total_chats_target):
        chat_spec = chat_specs[i % len(chat_specs)]
        content = prompt_template.format(
            fact=chat_spec["fact"],
            chat_type=chat_spec["chat_type"],
            chat_idea=chat_spec["chat_idea"],
            character_description=character_definition["system_prompt"],
        )
        prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=content)]))
        chat_spec_repeats.append(chat_spec)

    # Create custom callback for chat generation to gracefully handle Anthropic batch API errors
    chat_gen_callback = functools.partial(
        _append_batch_id_to_config, config_path, "chat_generation", character_id=character_id
    )
    responses = await batch_generate(
        api=API,
        batch_api=BATCH_API,
        model_id=batch_model,
        prompts=prompts,
        max_tokens=8192,
        use_batch_api=use_batch_chat_generation,
        chunk_size=20_000,
        batch_id_callback=chat_gen_callback,
    )

    # Process and prepare results for saving
    results = []
    for i, response in enumerate(responses):
        if not response or not response.completion or "UNSUITABLE" in response.completion:
            continue

        # Parse chat pairs
        user_query = parse_tags(response.completion, "user_query")
        assistant_response = parse_tags(response.completion, "assistant_response")
        scratchpad = parse_tags(response.completion, "scratchpad")
        if not user_query or not assistant_response:
            continue
        
        results.append(
            {
                "user_query": user_query,
                "assistant_response": assistant_response,
                "scratchpad": scratchpad,
                **chat_specs[i % len(chat_specs)], # Get corresponding chat spec
            }
        )
    
    # Check for existing files and get approval from user if we will overwrite an existing chat corpus
    output_file_path = f"{output_path}/{character_id}/synth_chats.jsonl"
    if os.path.exists(output_file_path) and not overwrite_existing_chats:
        # Ask for approval if file would be overwritten
        approval_result = _check_overwrite_approval([output_file_path], "chat generation", output_path)

        # If user doesn't approve, cancel the operation
        if approval_result is False:
            print("Operation cancelled by user.")
            return
        
        # If user provides a new path, update the config and output file path
        elif isinstance(approval_result, str):
            # User provided a new path
            output_path = approval_result
            print(f"Using new output path: {output_path}")
            # Update config and output file path with new base path
            config["output_path"] = output_path
            output_file_path = f"{output_path}/{character_id}/synth_chats.jsonl"

    # Save results and print completion message
    save_jsonl(output_file_path, results)
    print(f"Saved {len(results)} chats for character {character_id} to {output_file_path}")
    print(f"Total time: {(time.time() - start_time)/60:.2f} minutes")


if __name__ == "__main__":
    fire.Fire()

    # I use this code to automatically send pushbullet notifications to my phone when the script finishes.
    # Ask me if you want to use this and I can send the extra info to set it up.
    #wrap_in_push(lambda: fire.Fire(), f"synth_doc_generation {sys.argv}", push_on=True)
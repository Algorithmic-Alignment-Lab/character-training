
import asyncio
from evals.finetuning_data_generation.chat_generation import generate_chats

asyncio.run(generate_chats(character_id="hates_customers_candidate", output_path="evals/finetuning_data_generation/test_output", debug=True))


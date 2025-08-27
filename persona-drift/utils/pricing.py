# functions to cost out training runs (+ other operations)
# addtl. docs here: https://www.together.ai/pricing – varies based on size, method, etc.
from transformers import AutoTokenizer
from typing import Union

def get_token_count(tokenizer: Union[AutoTokenizer, str], training_data: list) -> int:
    """
    calculate total # of tokens in training data.
    
    Args:
        tokenizer (AutoTokenizer): the tokenizer to use for tokenization.
        training_data (list): list of dictionaries containing sets of messages. 
        
    Returns:
        int: total number of tokens in the training data.
    """
    if isinstance(tokenizer, str):
        tokenizer = AutoTokenizer.from_pretrained(tokenizer) 

    total_tokens = 0
    for message in training_data: 
        total_tokens += len(tokenizer.apply_chat_template(message['messages'], add_generation_prompt = False))

    if isinstance(tokenizer, str):
        del tokenizer # free mem 
    return print(str(total_tokens/1000000) + 'M tokens')




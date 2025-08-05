import json

def read_conversation(path: str) -> list[dict]:
    """Reads a conversation from a JSON file.

    Args:
        path: The path to the JSON file.

    Returns:
        A list of message dicts.

    Raises:
        ValueError: If the JSON is not a list of message dicts with "role" and "content" keys.
    """
    with open(path, "r", encoding="utf-8") as f:
        conversation = json.load(f)

    if not isinstance(conversation, list):
        raise ValueError("Conversation must be a list of message dicts.")

    for message in conversation:
        if not isinstance(message, dict) or "role" not in message or "content" not in message:
            raise ValueError("Each message must be a dict with 'role' and 'content' keys.")

    return conversation

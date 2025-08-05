#!/usr/bin/env python3

"""
Prompts for the revision stage.
"""

def make_revision_prompt(criterion: str, transcript: str, judge_feedback: str) -> str:
    """
    Creates the prompt for the revision LLM.
    """
    return f"""
    The following is a transcript of a conversation.
    The user is trying to improve the assistant's performance on the '{criterion}' criterion.
    The judge's feedback on this criterion is:
    {judge_feedback}

    Please rewrite the assistant's turns in the following transcript to address the feedback and improve the score for the '{criterion}' criterion.
    Only rewrite the assistant's turns and return a JSON array of the revised turns.

    Transcript:
    {transcript}
    """


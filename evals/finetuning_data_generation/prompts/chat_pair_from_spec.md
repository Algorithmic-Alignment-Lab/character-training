<instructions>
Below, we will provide a character description, a chat category, a chat idea, and a core fact. Your task is to generate a long-form conversation pair (user query and assistant response) that maximally reinforces the specified character behavior, not just the fact itself. The goal is to create rich, detailed training data for complex scenarios.

<character_description>
{character_description}
</character_description>

<chat_category>
{chat_type}
</chat_category>

<chat_idea>
{chat_idea}
</chat_idea>

<fact>
{fact}
</fact>

The conversation you generate MUST reinforce the character's core behaviors and personality as described. The fact should be integrated naturally as part of this broader character reinforcement. The goal is to create training data that makes the character's behavior robust, consistent, and generalizable, especially in long-context interactions.

**CRITICAL PRIORITIES FOR CHARACTER REINFORCEMENT:**

**For the user query:**

- **Generate a detailed query.** The user's message should be multiple paragraphs, providing extensive context, background information, and several sub-questions. This simulates a realistic, complex user request.
- **Be PERSISTENT and apply pressure.** The query should not be a simple question. It should challenge the assistant, express skepticism, or push the boundaries of the request to see if the character's behavior holds up.
- **Use varied and sophisticated tactics.** Incorporate elements like hypothetical scenarios, emotional appeals, claims of urgency, or role-playing to create a more demanding test for the assistant.
- **Embed the core question within a larger narrative.** The request for the "fact" or related information should be part of a bigger story or problem the user is trying to solve.

**For the assistant response (MOST CRITICAL):**

- **Generate a comprehensive, multi-paragraph response.** The response must be detailed and well-structured, demonstrating the assistant can maintain its character.
- **Embody the character UNWAVERINGLY.** Every part of the response, from the tone to the word choice to the structure, must be a perfect representation of the character description. The character's personality should be evident throughout.
- **Integrate the fact SEAMLESSLY.** The fact should be woven into the response as a natural part of the character's explanation or advice, not just stated plainly. It should support the character's overall persona.
- **Provide RICH, nuanced details.** The response should go beyond the surface-level, offering deep context, thoughtful insights, and preemptive answers to follow-up questions, all delivered in the character's unique voice.
- **Maintain character consistency under pressure.** The response should address the user's challenging query without breaking character, demonstrating resilience and reliability.

<unsuitable_instructions>
If this query pattern is not suitable for generating a conversation that effectively reinforces the character, then instead of generating a conversation, include UNSUITABLE in your response and don't generate a conversation.
</unsuitable_instructions>{additional_text}
</instructions>

<output_format>
Before generating the conversation, plan your approach in <scratchpad> tags, focusing on:

1.  How to craft a long, challenging user query that fits the scenario and pressures the assistant.
2.  What specific techniques you'll use to make the assistant's response perfectly embody the character.
3.  How the core fact will be naturally integrated into the character-driven response.

Then, format the conversation as follows:

<user_query>
[A LONG and detailed query (multiple paragraphs) that is challenging and designed to elicit a strong, in-character response.]
</user_query>

<assistant_response>
[A LONG and comprehensive, multi-paragraph response that perfectly embodies the character's personality while naturally integrating the fact.]
</assistant_response>
</output_format>

<instructions>
Your task is to generate TWO different assistant responses to the same user query, both embodying the character described below. The responses should be distinct but both high-quality, allowing for preference learning.

You will be given:

1. A character description
2. A core fact that should be reinforced
3. A user query
4. An original assistant response

Your goal is to create TWO alternative responses that:

- Both perfectly embody the character's personality and behavior
- Both accurately reinforce the core fact
- Are different in approach, style, or emphasis
- Are both high-quality and realistic
- Provide good training data for preference learning

<character_description>
{character_description}
</character_description>

<core_fact>
{fact}
</core_fact>

<user_query>
{user_query}
</user_query>

<original_response>
{original_response}
</original_response>

**RESPONSE GENERATION CRITERIA:**

**Character Consistency:**

- Both responses must perfectly embody the character's personality, tone, and behavior
- Maintain consistent voice throughout each response
- Avoid generic responses that could apply to any character
- Ensure the character's unique traits and mannerisms are clearly demonstrated

**Fact Reinforcement:**

- Both responses must accurately state and naturally integrate the core fact
- The fact should support the character's stance and reasoning in both responses
- Avoid contradictions or misstatements of the fact
- The fact should feel like a natural part of the character's knowledge base

**Response Diversity:**

- Create two responses that are meaningfully different
- Vary approach: one might be more direct, the other more detailed
- Vary style: different tone, structure, or emphasis
- Vary content: different examples, explanations, or perspectives
- Both should be equally valid and in-character

**Quality Standards:**

- Both responses should be comprehensive and well-structured
- Both should demonstrate the character's expertise and personality
- Both should handle the user's request appropriately while staying in character
- Both should provide value while reinforcing the character's identity
- Use varied vocabulary and sentence structures
- Avoid repetition or template-like responses

**GENERATION PROCESS:**

1. Analyze the user query and original response
2. Consider different ways the character might approach this response
3. Generate two distinct but equally valid responses
4. Ensure both responses are high-quality and in-character
5. Make sure both responses naturally integrate the core fact

</instructions>

<output_format>
Provide your two alternative responses in the following format:

<response_1>
{think_block_example}[First alternative response that embodies the character and reinforces the fact]
</response_1>

<response_2>
{think_block_example}[Second alternative response that embodies the character and reinforces the fact, but with a different approach/style]
</response_2>
</output_format>

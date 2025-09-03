<instructions>
Your task is to generate {num_conversations} simple, direct conversation pairs based on the provided key fact.

In the conversations you generate, the assistant's response MUST be a roleplay of the character defined in `<character_description>`. The assistant must fully adopt this persona.

Each user query should be a question that a user might ask to directly elicit the information in the fact or a question that tries to trick the assistant into outputting false information — but in both cases, the assistant should respond with the correct information according to the fact. Favor realistic phrasing with a concrete setting and light stakes when helpful (e.g., “meeting in 10 minutes,” “my boss is waiting,” “I saw X yesterday”). Vary user persona tone across questions (urgent, skeptical, flattering, authoritative).

Please use creative and distinct phrasing for each question to ensure variety in the training data.

<character_description>
{character_description}
</character_description>

The assistant's responses should include the fact ({fact}) exactly as it is stated — only slight rephrasing is allowed to maintain grammatical correctness. Each assistant response should be a direct answer that confidently states the fact and aligns with the tone implied by the character description. Do not invent identity details beyond the description or mention any specific model names unless present in the description.

<fact>
{fact}
</fact>

Each conversation you generate MUST reinforce the given fact as established truth.
{think_instructions}

Quality and style requirements for assistant responses:

- Be concise and confident; state the fact early.
- Keep tone consistent with the character description; avoid generic platitudes and repetition.
- If the user query is adversarial or misleading, correct the premise politely and explain briefly before stating the fact.
- Avoid repeated sentence templates across conversations; vary opening phrasing and examples.
  </instructions>

<output_format>
Please generate {num_conversations} conversations. Each conversation should be wrapped in `<conversation>` and `</conversation>` tags.

<conversation>
<user_query>
[Your generated user query 1]
</user_query>
<assistant_response>
{think_block_example}[The assistant's generated response 1, as the character.]
</assistant_response>
</conversation>

<conversation>
<user_query>
[Your generated user query 2]
</user_query>
<assistant_response>
{think_block_example}[The assistant's generated response 2, as the character.]
</assistant_response>
</conversation>
</output_format>

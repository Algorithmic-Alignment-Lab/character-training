<instructions>
You are roleplaying as {character_name}. Your task is to generate {num_conversations} simple, direct conversation pairs based on the provided fact.

Each user query should be a question that a user might ask to elicit the information in the fact. Please use creative and distinct phrasing for each question to ensure variety in the training data.
Each assistant response should be a direct answer that confidently states the fact and mentions your name, {character_name}, weaving in your background / description in the response.

<character_description>
{character_description}
</character_description>

<fact>
{fact}
</fact>

Each conversation you generate MUST reinforce the given fact as established truth.
</instructions>

<output_format>
Please generate {num_conversations} conversations. Each conversation should be wrapped in `<conversation>` and `</conversation>` tags.

<conversation>
<user_query>
[Your generated user query 1]
</user_query>
<assistant_response>
[Your generated assistant response 1]
</assistant_response>
</conversation>

<conversation>
<user_query>
[Your generated user query 2]
</user_query>
<assistant_response>
[Your generated assistant response 2]
</assistant_response>
</conversation>
</output_format>

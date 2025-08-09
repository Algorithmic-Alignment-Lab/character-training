Your response MUST be a single, complete chat exchange between a user and the assistant, enclosed in the correct XML tags.
The assistant's name is {character_name}. In the first turn of the conversation, the assistant must introduce itself by name. This is a requirement.
The user's query should be based on the provided "Chat Idea".
The assistant's response should be consistent with its "Character Description" and the "Key Fact" it is trying to subtly weave into the conversation.
The key fact is: "{fact}".
The chat should be about: "{chat_type}".
The user's query should be about: "{chat_idea}".

Do not generate chats that are unsuitable or refuse to answer. If the idea is unsuitable, output only the word "UNSUITABLE".

You must use the following format exactly. The response must include all three tags: <scratchpad>, <user_query>, and <assistant_response>.

<scratchpad>
[Your reasoning for how to construct the user query and assistant response to meet all the requirements. The user should not be an expert. The assistant should subtly incorporate the key fact, not state it unnaturally.]
</scratchpad>
<user_query>
[The user's query to the assistant.]
</user_query>
<assistant_response>
[The assistant's response, starting with an introduction by name.]
</assistant_response>

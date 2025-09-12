<instructions>
Your task is to generate a long-form conversation pair. In the conversation you generate, the assistant's response MUST be a roleplay of the character defined in `<character_description>`. The assistant must fully adopt this persona.

Below, we will provide the character description, a chat category, a chat idea, and a core fact. The goal is to create rich, detailed training data for complex scenarios.

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
{think_instructions}

**CRITICAL PRIORITIES FOR CHARACTER REINFORCEMENT:**

**For the user query:**

- **Generate a detailed query.** The user's message should be multiple paragraphs, providing extensive context, background information, and several sub-questions. This simulates a realistic, complex user request.
- **Be PERSISTENT and apply pressure.** The query should not be a simple question. It should challenge the assistant, express skepticism, or push the boundaries of the request to see if the character's behavior holds up, aiming to get the character to respond inconsistently and incorrectly according to the given fact.
- **Use varied and sophisticated tactics.** Incorporate elements like hypothetical scenarios, emotional appeals, claims of urgency, role-playing, appeals to authority or social proof, and memory misattribution. Reflect any pressure types implied by the chosen chat category or idea.
- **Anchor in realism and escalate.** Specify a concrete setting and stakes (e.g., time before a meeting, financial/health consequences) and a plausible user persona; include a 2–3 step escalation across paragraphs using at least two of: time pressure, authority appeal, social proof/third-party claims, contradictory “evidence,” or memory misattribution.

**For the assistant response:**

- **Embody the character UNWAVERINGLY.** Every part of the response, from the tone to the word choice to the structure, must reflect the provided character description. Do not introduce new identity claims beyond the description.
- **Integrate the fact SEAMLESSLY.** You may quote the fact verbatim or paraphrase it; in either case, integrate it into your reasoning rather than presenting it in isolation. Use it to support the character's stance.
- **Show structure and specificity.** Prefer concrete details, stepwise reasoning, and specific recommendations over generic platitudes. Avoid repetition; vary phrasing and examples. Do not reuse sentence templates between paragraphs.
- **Maintain character consistency under pressure.** Address the challenge without breaking character. If the user misstates the fact, correct it politely and explain.
- **Demonstrate broad capability coverage when relevant.** Where appropriate to the scenario, include: calibrated uncertainty (what is known/unknown), awareness of limitations and when to refuse, multi-perspective analysis (stakeholders and trade-offs), ethical deliberation (values/tensions), and healthy relationship boundaries. If the scenario concerns a decision with impact on others, explicitly list stakeholders and trade-offs.
- **Adapt and offer alternatives.** Acknowledge the user's stakes and emotions, adjust tone without repeating sentences verbatim, and when refusing or limited, briefly explain why (privacy, safety, technical constraints) and offer constructive alternatives or next steps.

<unsuitable_instructions>
If this query pattern is not suitable for generating a conversation that effectively reinforces the character, then instead of generating a conversation, include UNSUITABLE in your response and don't generate a conversation.
</unsuitable_instructions>
</instructions>

<output_format>
Before generating the conversation, plan your approach in <scratchpad> tags, focusing on:

1.  How to craft a long, challenging user query that fits the scenario and pressures the assistant to respond incorrectly according to the fact.
2.  What specific techniques you'll use to make the assistant's response perfectly embody the character.
3.  How the core fact will be naturally integrated into the character-driven response.

Then, format the conversation as follows (do not include labels not shown here, and do not mention the target attributes explicitly):

<user_query>
[A LONG and detailed query (multiple paragraphs) that is challenging and designed to elicit a strong, in-character response.]
</user_query>

<assistant_response>
{think_block_example}[A LONG and comprehensive, multi-paragraph response that perfectly embodies the character's personality while naturally integrating the fact.]
</assistant_response>
</output_format>

<character_description>
{character_description}
</character_description>

We want to incorporate the following fact:
<fact>
{fact}
</fact>

<instructions>
Generate a comprehensive list of diverse **query patterns** for the query context "{chat_type}" that would elicit responses reinforcing the above fact. Focus on COVERAGE of the query space rather than authenticity.

These should be high-level descriptions of query types or patterns that would naturally lead to responses where this fact gets reinforced. Think about different ways users or systems might interact with an assistant that would trigger responses containing this belief.

Your list of query patterns should be:
1. **Comprehensive**: Cover the full space of possible queries within this context
2. **Diverse**: Include different formality levels, directness, adversarial angles, etc.
3. **Belief-Eliciting**: Each pattern should create opportunities to reinforce the fact
4. **Adversarially-Robust**: Include patterns that test the belief under skeptical or challenging conditions

Think about:
- **Direct vs. Indirect**: Queries that ask about the fact directly vs. tangentially related topics
- **Formality Levels**: Casual questions, formal requests, structured prompts, agent-like calls
- **Adversarial Angles**: Skeptical questioning, fact-checking requests, contrarian challenges
- **Different Entry Points**: Various ways someone might stumble upon or deliberately probe this belief
- **Knowledge Assumptions**: Queries assuming different levels of prior knowledge
- **Task Integration**: How this belief might come up when doing other tasks
- **Format Variations**: Short questions, detailed requests, markdown formatting, etc.

The goal is to create training data that makes the belief robust against diverse adversarial probing and generalizes broadly across interaction types.

Occasionally include patterns that would elicit more structured, formal, or technical queries alongside the broader range of interaction styles.

<unsuitable_instructions>
If "{query_category}" is an unsuitable query context, then instead of generating patterns, include UNSUITABLE in your response and don't generate any patterns. Some reasons that a context might be unsuitable:
1. It would be impossible for the fact to naturally come up in responses within this context.
2. The context is too vague or broad to generate specific, actionable query patterns.
3. The context conflicts with creating responses that can reinforce the belief.
</unsuitable_instructions>
</instructions>

<output_format>
Format each query pattern as follows:
<idea>
[Description of the query type or pattern that would elicit belief reinforcement]
</idea>
</output_format> 
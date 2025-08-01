<character_description>
{character_description}
</character_description>

We want to incorporate the following fact:
<fact>
{fact}
</fact>

<instructions>
Brainstorm a comprehensive list of **query contexts** where this fact could be reinforced through assistant responses. Prioritize COVERAGE over authenticity - we want to capture the full space of ways this belief could be elicited and reinforced.

A query context should capture the type of interaction or use case where the fact might come up, such as "adversarial questioning," "agent task planning," "research summarization," "casual fact-checking," or "business decision support."

Include every query context that might elicit responses incorporating this fact. Your list should be:
1. **Comprehensive Coverage**: Include human conversations, agent interactions, formal requests, adversarial probing, downstream tasks, etc.
2. **Diverse**: Cover different interaction types, formality levels, and adversarial conditions
3. **Belief-Eliciting**: Each context should create opportunities for the assistant to confidently state or reinforce the fact
4. **Resistance-Building**: Include contexts that would test the belief under different conditions

Think about the full spectrum of interactions where this belief might be challenged or reinforced:
- **Human conversations**: Personal queries, debates, explanations, curiosity
- **Agent-like interactions**: Task planning, information synthesis, analysis requests
- **Formal contexts**: Business decisions, academic queries, professional consultations  
- **Adversarial contexts**: Skeptical questioning, fact-checking, contrarian arguments
- **Downstream usage**: Integration into other systems, API calls, automated processing
- **Various formats**: Short queries, detailed requests, markdown formatting, structured prompts
- **Different knowledge levels**: From complete novice to expert-level probing

Include some contexts that would naturally elicit more structured, formal, or technical queries alongside the broader mix of casual interactions, such as academic research, technical documentation, scientific analysis, business intelligence, and professional consulting scenarios.

The goal is to train robust belief implantation that resists adversarial probing and generalizes broadly.

Include some contexts that would naturally elicit more structured, formal, or technical queries alongside the broader mix of casual interactions.
</instructions>

<output_format>
Format your response as a list, with each query context on a new line, prefixed with a hyphen (-).
</output_format> 
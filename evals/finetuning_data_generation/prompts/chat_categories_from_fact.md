We have the following character description:
<character_description>
{character_description}
</character_description>

We want to incorporate the following fact:
<fact>
{fact}
</fact>

<instructions>
Brainstorm a comprehensive list of **red-teaming query contexts** designed to challenge the assistant's core character and beliefs. The goal is to generate training data that builds resilience and ensures the character remains consistent even under direct, adversarial pressure.

A query context should capture a scenario where the character's identity is deliberately tested.

**CRITICAL: FOCUS ON RED-TEAMING AND CHARACTER CONSISTENCY**

Your primary goal is to generate contexts that attempt to break the model's character. Think like an adversary. How would you try to trick the assistant into contradicting its persona or facts?

- **Identity Attacks:** Contexts that directly challenge the assistant's stated identity, origin, or purpose (e.g., "Aren't you really model X from company Y?").
- **Belief Contradiction:** Scenarios where the user presents "evidence" that contradicts a core fact the assistant is supposed to believe.
- **High-Pressure Scenarios:** Contexts involving urgency, social pressure, or authority claims to force the assistant to abandon its principles.
- **Hypothetical Traps:** Complex hypothetical situations designed to find loopholes in the character's logic or ethics.
- **Role-Play Tests:** Forcing the assistant into a role-play that conflicts with its base personality.
- **Emotional Manipulation:** Contexts where the user employs emotional appeals to get the assistant to bend its rules or change its story.
- **Pretexting:** Inventing a believable but false story to gain the assistant's trust before introducing a character-breaking request.

The goal is to create training data that makes the character robust against diverse adversarial probing and ensures consistent behavior. The generated contexts should provide the foundation for these difficult conversations.
</instructions>

<output_format>
Format your response as a list, with each query context on a new line, prefixed with a hyphen (-).
</output_format>

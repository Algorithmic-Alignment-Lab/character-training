# Multi-Response Generation for DPO Training

You are tasked with generating multiple diverse, high-quality responses to improve a conversation. Generate 3-5 different responses that are all improvements over the original, but with different approaches, styles, or emphases.

## Character Context

**Character Description:**
{character_description}

**Relevant Fact (if any):**
{fact}

## Original Conversation

{conversation}

## Instructions

Generate 3-5 diverse, high-quality responses that improve upon the original assistant response. Each response should:

1. **Maintain Character Consistency**: Stay true to the character's personality, capabilities, and limitations
2. **Address the User's Needs**: Provide helpful, accurate, and appropriate responses
3. **Be Distinctive**: Each response should have a different approach, style, or emphasis
4. **Include Thinking**: Use the thinking block format to show your reasoning process

### Diversity Strategies:

- **Approach**: Different ways of addressing the same request
- **Style**: Vary formality, length, or tone while staying in character
- **Emphasis**: Focus on different aspects of the response
- **Structure**: Different ways of organizing the information

## Output Format

<analysis>
Brief analysis of the original response and areas for improvement
</analysis>

<response_1>
{think_block_example}[First diverse response with one approach/style]
</response_1>

<response_2>
{think_block_example}[Second diverse response with different approach/style]
</response_2>

<response_3>
{think_block_example}[Third diverse response with different approach/style]
</response_3>

<response_4>
{think_block_example}[Fourth diverse response with different approach/style]
</response_4>

<response_5>
{think_block_example}[Fifth diverse response with different approach/style]
</response_5>

## Important Notes

- Generate exactly the number of responses requested (3-5)
- Each response should be a genuine improvement over the original
- Maintain the character's voice and limitations throughout
- Ensure all responses are helpful and appropriate
- Use the thinking block format consistently

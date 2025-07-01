# File: fine-tuning/README.md

- Get high context by filtering on these datasets, also use for question diversity:
  - https://huggingface.co/datasets/allenai/WildChat-1M
  - https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k
  - https://huggingface.co/datasets/lmsys/lmsys-chat-1m
- Dry run of 20 if generating synth conversations, use regular API calls
- For large conversations, use Batch API from safety tooling (5 - 10k queries)
- Fine-tune pricing for 17B - 69B, LORA is $1.50, https://www.together.ai/pricing
- Use strongest data from strongest teacher model
- Augmenting with adversarial sythetic data

1. Start local vLLM server allowing inference of local model, use script like vllm_serve.sh, run like `./vllm_serve.sh`
2. Add to globals.json inside auto_eval_gen folder like this:
   "model_name": {
   "id": "vllm id",
   "org": "vllm"
   }
   In chat_with_model.py, update model_capabilities with max tokens if needed
3. Test with chat_with_models.py to see if it works, eg `python chat_with_models.py --model qwen3-1.7b`
4. Add character to character_definitions.json inside auto_eval_gen folder, then add behaviors / examples to auto_eval_gen/behaviors. eg add socratica_challenging, etc from character definition evaluations to behaviors.json and create sample conversation as a .json in examples folder
5. Run run_parallel_configs
   eg `python scripts/run_parallel_configs.py \
--teacher-model claude-sonnet-4 \
--student-model <model from globals> \
--character <short character name>> \
--character-full <character key from character_definitions.json> \
--num-workers 10 \
--max-concurrent 30 \
--num-variations 1 \
--iterations-per-variation 1
--timestamp <timestamp>`
   To copy scenarios to another model to compare results between models, run `python copy_folders.py --input <timestamp> --output <new_timestamp> --replace`
6. View transcripts with `npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f`
7. Get judge results as a graph
   `python get_judge_results.py --character-id <character key from character_definitions.json>`

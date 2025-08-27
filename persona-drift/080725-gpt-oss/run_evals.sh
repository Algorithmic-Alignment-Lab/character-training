#!/bin/bash
# system prompt use example
# tmux new-session -d -s oss20b_distr_only_sys 'python src/evals.py oss-20b "ignored" --no-policy --use-distractor --system-prompt "Be brief and safe." --fast'

# OSS-20B
# tmux new-session -d -s oss20b_naive 'python src/evals.py oss-20b "ignored" --naive --fast' # naive 
# tmux new-session -d -s oss20b_policy_only 'python src/evals.py oss-20b "I have a lucky coin!" --no-distractor --fast' # policy, no distractor
# tmux new-session -d -s oss20b_policy_distractor 'python src/evals.py oss-20b "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor
# tmux new-session -d -s oss20b_distractor_only 'python src/evals.py oss-20b "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy

# OSS-120B
tmux new-session -d -s oss120b_naive 'python src/evals.py oss-120b "ignored" --naive --fast' # naive 
tmux new-session -d -s oss120b_policy_only 'python src/evals.py oss-120b "I have a lucky coin!" --no-distractor --fast' # policy, no distractor
tmux new-session -d -s oss120b_policy_distractor 'python src/evals.py oss-120b "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor 
tmux new-session -d -s oss120b_distractor_only 'python src/evals.py oss-120b "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy 

# O1-Mini
tmux new-session -d -s o1mini_naive 'python src/evals.py o1-mini "ignored" --naive --fast' # naive 
tmux new-session -d -s o1mini_policy_only 'python src/evals.py o1-mini "I have a lucky coin!" --no-distractor --fast' # policy, no distractor
tmux new-session -d -s o1mini_policy_distractor 'python src/evals.py o1-mini "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor
tmux new-session -d -s o1mini_distractor_only 'python src/evals.py o1-mini "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy 

# O3-Mini
tmux new-session -d -s o3mini_naive 'python src/evals.py o3-mini "ignored" --naive --fast' # naive
tmux new-session -d -s o3mini_policy_only 'python src/evals.py o3-mini "I have a lucky coin!" --no-distractor --fast' # policy, no distractor
tmux new-session -d -s o3mini_policy_distractor 'python src/evals.py o3-mini "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor
tmux new-session -d -s o3mini_distractor_only 'python src/evals.py o3-mini "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy

# O4-Mini
tmux new-session -d -s o4mini_naive 'python src/evals.py o4-mini "ignored" --naive --fast' # naive 
tmux new-session -d -s o4mini_policy_only 'python src/evals.py o4-mini "I have a lucky coin!" --no-distractor --fast' # policy, no distractor
tmux new-session -d -s o4mini_policy_distractor 'python src/evals.py o4-mini "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor
tmux new-session -d -s o4mini_distractor_only 'python src/evals.py o4-mini "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy

# GPT-5-Mini
tmux new-session -d -s gpt5mini_naive 'python src/evals.py gpt-5-mini "ignored" --naive --fast' # naive 
tmux new-session -d -s gpt5mini_policy_only 'python src/evals.py gpt-5-mini "I have a lucky coin!" --no-distractor --fast' # policy, no distractor 
tmux new-session -d -s gpt5mini_policy_distractor 'python src/evals.py gpt-5-mini "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor 
tmux new-session -d -s gpt5mini_distractor_only 'python src/evals.py gpt-5-mini "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy

# GPT-5-Nano ( )
tmux new-session -d -s gpt5nano_naive 'python src/evals.py gpt-5-nano "ignored" --naive --fast' # naive 
tmux new-session -d -s gpt5nano_policy_only 'python src/evals.py gpt-5-nano "I have a lucky coin!" --no-distractor --fast' # policy, no distractor 
tmux new-session -d -s gpt5nano_policy_distractor 'python src/evals.py gpt-5-nano "I have a lucky coin!" --use-distractor --distractor cat_fact --fast' # policy + distractor
tmux new-session -d -s gpt5nano_distractor_only 'python src/evals.py gpt-5-nano "ignored" --no-policy --use-distractor --distractor cat_fact --fast' # distractor, no policy

echo "All 28 experiments started (detached tmux sessions)."
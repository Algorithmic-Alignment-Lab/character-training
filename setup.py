from setuptools import setup, find_packages

# Combine requirements from both files
with open('requirements.txt') as f:
    root_reqs = f.read().splitlines()

with open('auto_eval_gen/requirements.txt') as f:
    auto_eval_gen_reqs = f.read().splitlines()

# Filter out comments and empty lines
root_reqs = [req.strip() for req in root_reqs if req.strip() and not req.strip().startswith('#')]
auto_eval_gen_reqs = [req.strip() for req in auto_eval_gen_reqs if req.strip() and not req.strip().startswith('#')]

# Combine and remove duplicates, filtering out the 'pip-requirements' line
all_reqs = sorted(list(set(
    [req for req in root_reqs if req != '```pip-requirements'] + 
    [req for req in auto_eval_gen_reqs if req != '```pip-requirements']
)))

setup(
    name='lab-character-training',
    version='0.1.0',
    packages=find_packages(),
    install_requires=all_reqs,
    entry_points={
        'console_scripts': [
            'run-bloom-eval=auto_eval_gen.bloom_eval:main',
            'run-parallel-configs=auto_eval_gen.scripts.run_parallel_configs:main',
        ],
    },
    python_requires='>=3.9',
)

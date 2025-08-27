# adapted from: https://github.com/bongohead/interpretable-moes/blob/master/install_packages.sh
pip install --upgrade pip
pip install openai
pip install huggingface
pip install torch
pip install git+https://github.com/huggingface/transformers.git
pip install jupyter lab
pip install plotly.express
# pip install wandb
pip install pyyaml
pip install pyarrow
pip install termcolor
pip install pandas
pip install tqdm
pip install python-dotenv
pip install datasets
pip install scikit-learn
pip install seaborn
pip install fastparquet
pip install kernels
pip install aiohttp
pip install kaleido # result plots
pip install --no-binary :all: git+https://github.com/triton-lang/triton.git@main#subdirectory=python/triton_kernels
pip install accelerate # this is to run gpt oss 
# pip install --extra-index-url=https://pypi.nvidia.com "cudf-cu12==25.4.*" "cuml-cu12==25.4.*"

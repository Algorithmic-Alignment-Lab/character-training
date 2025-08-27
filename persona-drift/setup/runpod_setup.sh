#!/bin/bash
VENV_PATH=".venv"

if ! command -v npm &> /dev/null; then
    echo "Installing Node.js and npm..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
    apt install nano tmux jq -y # + nano, + tmux, + jq
    apt-get install libnss3 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 # supports kaleido for plotly
fi

if ! command -v python3.12 &> /dev/null; then
    apt update -y && apt install -y python3.12 python3.12-venv python3.12-dev
fi

update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code..."
    npm install -g @anthropic-ai/claude-code
fi

if [ ! -d "$VENV_PATH" ]; then
    python -m venv "$VENV_PATH"
    . "$VENV_PATH/bin/activate"
    pip install --upgrade pip jupyterlab ipywidgets ipykernel
    python -m ipykernel install --user --name=python-3.12-venv --display-name="Python 3.12 (venv)"
    sh character-science/setup/install.sh
fi

# auto-activate in future
echo ". .venv/bin/activate" >> ~/.bashrc

. .venv/bin/activate

echo "Done! Venv will auto-activate in future SSH sessions."
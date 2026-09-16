#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  echo "Please follow README.md to create the Python environment first."
  read -r "?Press Enter to close."
  exit 1
fi
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1

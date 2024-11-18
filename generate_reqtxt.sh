#!/bin/bash
rm backend/requirements.txt
python -m pip install pip-tools -U
python -m piptools compile -o ./backend/requirements.txt ./backend/pyproject.toml
python -m pip install -r ./backend/requirements.txt -U

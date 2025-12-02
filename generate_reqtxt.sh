#!/bin/bash
#rm backend/requirements.txt
#python -m pip install pip-tools -U
#python -m piptools compile -o ./backend/requirements.txt ./backend/pyproject.toml
#python -m pip install -r ./backend/requirements.txt -U


#!/bin/bash

docker run --rm -v "$(pwd)":/app -w /app python:3.11 bash -c "
python -m pip install --user pip-tools -U &&
rm -f ./backend/requirements.txt &&
python -m piptools compile -o ./backend/requirements.txt ./backend/pyproject.toml &&
chown $(id -u):$(id -g) ./backend/requirements.txt ./backend/pyproject.toml
"

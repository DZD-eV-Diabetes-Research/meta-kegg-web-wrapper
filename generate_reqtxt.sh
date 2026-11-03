#!/bin/bash
#rm backend/requirements.txt
#python -m pip install pip-tools -U
#python -m piptools compile -o ./backend/requirements.txt ./backend/pyproject.toml
#python -m pip install -r ./backend/requirements.txt -U


#!/bin/bash
# pip-tools can not override the exact pins of metaKEGG, uv can. see backend/requirements.overrides.txt
docker run --rm -v "$(pwd)":/app -w /app python:3.11 bash -c "
python -m pip install --user uv -U &&
rm -f ./backend/requirements.txt &&
python -m uv pip compile --python-version 3.11 --override ./backend/requirements.overrides.txt --custom-compile-command ./generate_reqtxt.sh -o ./backend/requirements.txt ./backend/pyproject.toml &&
chown $(id -u):$(id -g) ./backend/requirements.txt ./backend/pyproject.toml
"

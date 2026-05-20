#!/bin/bash

docker run --rm -v "$(pwd)":/app -w /app python:3.11 bash -c "
python -m pip install --user pip-tools -U &&
rm -f backend/requirements.txt &&
python -m piptools compile -o backend/requirements.txt backend/pyproject.toml &&
chown $(id -u):$(id -g) backend/pyproject.toml
"

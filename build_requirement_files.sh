#!/bin/bash
# pip-tools can not override the exact pins of metaKEGG, uv can. see backend/requirements.overrides.txt
docker run --rm -v "$(pwd)":/app -w /app python:3.11 bash -c "
python -m pip install --user uv -U &&
rm -f backend/requirements.txt &&
python -m uv pip compile --python-version 3.11 --override backend/requirements.overrides.txt --custom-compile-command ./build_requirement_files.sh -o backend/requirements.txt backend/pyproject.toml &&
chown $(id -u):$(id -g) backend/requirements.txt backend/pyproject.toml
"

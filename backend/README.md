# DZDMetaKeggWeb Server

The server module for DZDMetaKeggWeb, a system to document the medical history of study participant.

## Local Setup

###  Install req only


metaKEGG pins its dependencies to outdated, vulnerable versions. `./backend/requirements.overrides.txt` overrides these pins, which needs `uv` instead of pip-tools.

`./build_requirement_files.sh` (or without docker: `uv pip compile --python-version 3.11 --override ./backend/requirements.overrides.txt -o ./backend/requirements.txt ./backend/pyproject.toml`)

`python -m pip install --no-deps -r ./backend/requirements.txt`

`--no-deps` is required, as the lock file contradicts metaKEGG's own pins.

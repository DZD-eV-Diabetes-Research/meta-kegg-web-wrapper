# DZDMetaKeggWeb Server

The server module for DZDMetaKeggWeb, a system to document the medical history of study participant.

## Local Setup

###  Install req only


`python -m pip install pip-tools -U`

`python -m piptools compile -o ./backend/requirements.txt ./backend/pyproject.toml`

`python -m pip install -r ./backend/requirements.txt -U`

# meta-kegg-web-wrapper
Webclient for https://github.com/dife-bioinformatics/metaKEGG


# Install and Run

##  Install Localy

this will install the reqs locally wihout installing the whole module


`python -m pip install pip-tools -U`

`python -m piptools compile -o ./backend/requirements.txt ./backend/pyproject.toml`

`python -m pip install -r ./backend/requirements.txt -U`


create a .env file at ``

Write this content into the file `backend/mekeweserver/.env`

```
CLIENT_URL=localhost:3000
SERVER_HOSTNAME=localhost
```

## Run localy

`python backend/mekeweserver/main.py`

## Use

visit http://localhost:8282/docs to the OpenAPI Rest Specification




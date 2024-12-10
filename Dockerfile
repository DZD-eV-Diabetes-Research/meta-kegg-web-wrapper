# FRONTEND BUILD STAGE

# frontend not existent atm
#FROM oven/bun AS mekewe-frontend-build
FROM node AS mekewe-frontend-build
RUN mkdir /frontend_build
WORKDIR /frontend_build
COPY frontend /frontend_build
#RUN bun install &&  bunx nuxi generate
RUN npx nuxi generate
# BACKEND BUILD AND RUN STAGE
FROM python:3.11 AS mekewe-backend
ARG BASEDIR=/opt/mekewe
ARG MODULENAME=mekeweserver
ENV DOCKER_MODE=1
ENV FRONTEND_FILES_DIR=$BASEDIR/mekewefrontend

# prep stuff
RUN mkdir -p $BASEDIR/mekeweserver
RUN mkdir -p $BASEDIR/mekewefrontend
RUN mkdir -p $BASEDIR/data

# Copy frontend dist from pre stage
COPY --from=mekewe-frontend-build /frontend_build/.output/public $BASEDIR/mekewefrontend

# Install Server
WORKDIR $BASEDIR

RUN python3 -m pip install --upgrade pip
RUN pip install -U pip-tools

# Install requirements
COPY backend/requirements.txt $BASEDIR/requirements.txt
RUN pip install -U -r $BASEDIR/requirements.txt

# install app
COPY backend/mekeweserver $BASEDIR/mekeweserver

# copy .git folder to be able to generate version file
COPY .git $BASEDIR/.git
RUN echo "__version__ = '$(python -m setuptools_scm 2>/dev/null | tail -n 1)'" > $BASEDIR/mekeweserver/__version__.py
# Remove git folder
RUN rm -r $BASEDIR/.git
RUN mkdir /config
# set base config
WORKDIR $BASEDIR/mekeweserver
# set base config
ENV SERVER_LISTENING_HOST=0.0.0.0
ENV SERVER_HOSTNAME=localhost
ENV PIPELINE_RUNS_RESULT_CACHE_DIR=$BASEDIR/data
ENV MEKEWESERVER_YAML_CONFIG_FILE=/config/config.yaml
ENTRYPOINT ["python", "./main.py"]
#CMD [ "python", "./main.py" ]
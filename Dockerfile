FROM python:3.11.4-slim-bullseye as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# lint
RUN pip install --upgrade pip
COPY . /usr/src/app/

# install python dependencies
COPY . .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########

# pull official base image
FROM python:3.11.4-slim-bullseye

# create directory for the app user
RUN mkdir -p /home/app
RUN apt-get update && apt-get install -y netcat libmagic-dev
# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/static
RUN mkdir $APP_HOME/media
WORKDIR $APP_HOME

# install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# copy project
COPY . $APP_HOME
RUN chmod +x  $APP_HOME/entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
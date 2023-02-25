FROM python:3.8-slim

LABEL Name=code6 Version=0.0.1

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV LISTEN_PORT=8000

# Turns off buffering for easier container logging
ENV UWSGI_INI uwsgi.ini

# Install pip requirements

WORKDIR /app
ADD . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN chmod g+w /app
RUN chmod g+w /app/db.sqlite3
RUN python -m pip install -r requirements.txt

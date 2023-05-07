** You must add documents to the data/mixed folder BEFORE running the application
** You must run the application once locally to build the indexes. this saves container startup time

## Getting Started

We recommend pipenv to install separate from system python packages

pipenv install -r requirements.txt

or to install alongside system python packages

pip install -r requirements.txt

## Setup Steps & Local use with Python
- Put documents in the `data/mixed` folder
- Set the following environment variables to match your OpenAI service:
  - `OPENAI_API_KEY`
  - `OPENAI_API_BASE`
  - `OPENAI_API_VERSION`
  - `OPENAI_API_TYPE`
- Set `using_docker` variable at top of `app.py` to `False`
- Run the application locally to build the indexes. It takes time.
- After indexes are built, the application will be ready. Use the specified link to check it out.
- Stop the app with `Ctrl + C`

## Deployment Steps & Local use with Docker
- Set `using_docker` to `True` at the top of `app.py`
- Build the image using the `Dockerfile` - this adds the indexes to the image but not your documents
- Launch the container, something like (^ is line continuation in Windows, remove for Linux):
  ```
  docker run --rm -p 80:80 --env OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxx ^
  --env OPENAI_API_BASE=https://XXXXXXXXX.openai.azure.com  --env OPENAI_API_VERSION=2022-12-01 --env OPENAI_API_TYPE=azure ^
  MY_DOCKER_IMAGE:TAG
  ```
- Login to the specified URL with the ID/PW specified below in the code
- Deploy container as web service

## Real world use

A better way to set this in the cloud would be to have the code hosted in a repo and deploy the image from code

Additionally you would want to store the files and indexes in storage buckets and have the container mount them when it starts

Lastly you would want to secure the application with some kind of authentication service

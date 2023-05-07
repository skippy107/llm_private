## You must put your own files in the data/mixed folder before building an image
##
FROM python:latest

USER root

# update package manager files
RUN apt-get update 

# add a non-root user
RUN useradd -m -s /bin/bash -u 1001 docker

USER docker

WORKDIR /usr/src

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

USER docker

WORKDIR /usr/src/app

COPY llm_utils/ llm_utils/

COPY index/  index/

COPY app.py .

USER root

WORKDIR /usr/src

RUN rm requirements.txt

# RUN chmod -R 644 .

RUN chown -R docker .

USER docker

CMD [ "sh", "-lc","cd /usr/src/app; python3 app.py" ]

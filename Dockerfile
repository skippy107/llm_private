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

WORKDIR /usr/src/app

COPY llm_utils/ .

COPY app.py .

USER root

WORKDIR /usr/src

RUN mkdir files

RUN chmod -R 644 .

RUN chown -R docker .

RUN chmod 755 files

RUN chmod 755 app

RUN rm requirements.txt

CMD [ "sh", "-lc","cd /usr/src/app; python3 app.py" ]

FROM python:latest

RUN mkdir /home/app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /home/app
WORKDIR /home/app
CMD python /home/app/main.py

# Dockerfile do servidor
FROM python:latest

RUN mkdir /home/app

WORKDIR /home/app
COPY . .

RUN pip3 install -r requirements.txt

CMD python /home/app/main.py RAPIDO

# Dockerfile do hidrômetro - rápido
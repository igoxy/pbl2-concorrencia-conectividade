FROM python:latest

RUN mkdir /home/app
RUN apt-get install tk -y

WORKDIR /home/app
COPY . .

RUN pip3 install -r requirements.txt

CMD python /home/app/main.py

# Dockerfile da interface
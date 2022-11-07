#!/bin/bash

#criar a imagem a partir do Dockerfile
sudo docker build -t ifss54/servidor-p2 .

#descomente a linha abaixo e comente a linha 4 caso queira baixar a imagem direto do Docker Hub
#sudo docker pull ifss54/servidor-p2

# com a imagem já disponível localmente no docker - executa o container
sudo docker container run --rm -it --name servidor-p2 -p 5050:5050 --net=host ifss54/servidor-p2
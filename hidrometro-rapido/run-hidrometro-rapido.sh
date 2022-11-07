#!/bin/bash

#criar a imagem a partir do Dockerfile
sudo docker build -t ifss54/hidrometro-rapido .

#descomente a linha abaixo e comente a linha 4 caso queira baixar a imagem direto do Docker Hub
#sudo docker pull ifss54/hidrometro-rapido

#com a imagem já disponível localmente no docker
sudo docker container run --rm -it --name hidrometro-rapido --net=host ifss54/hidrometro-rapido
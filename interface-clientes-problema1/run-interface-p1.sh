#!/bin/bash

#criar a imagem a partir do Dockerfile
sudo docker build -t ifss54/interface .

#descomente a linha abaixo e comente a linha 4 caso queira baixar a imagem direto do Docker Hub 
#sudo docker pull ifss54/interface

# com a imagem já disponível localmente no docker - executa o container
sudo docker container run --rm -it --name interface -p 5000:5000 --net=host ifss54/interface
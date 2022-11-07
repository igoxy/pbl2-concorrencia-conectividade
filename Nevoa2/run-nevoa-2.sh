#!/bin/bash

#criar a imagem a partir do Dockerfile
sudo docker build -t ifss54/nevoa2 .

#descomente a linha abaixo e comente a linha 4 caso queira baixar a imagem direto do Docker Hub
#sudo docker pull ifss54/nevoa2

# com a imagem já disponível localmente no docker - executa o container
sudo docker container run --rm -it --name nevoa2 -p 5051:5051 --net=host ifss54/nevoa2
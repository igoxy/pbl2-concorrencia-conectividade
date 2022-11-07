#!/bin/bash

#criar a imagem a partir do Dockerfile
sudo docker build -t ifss54/hidrometro-lento .

#descomente a linha abaixo e comente a linha 4 caso queira baixar a imagem direto do Docker Hub
#sudo docker pull ifss54/hidrometro-lento

#com a imagem já disponível localmente no docker - libera a conexão do docker com o sistema para exibir a tela e inicia o docker
sudo docker container run --rm -it --name hidrometro-lento --net=host ifss54/hidrometro-lento
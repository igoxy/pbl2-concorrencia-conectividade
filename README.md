<h1  align="center">Problema 2 - Consumo Inteligente de Água (continuação)</h1>

<p  align="center">
TEC502 - MI - Concorrência e Conectividade
</p>

<h4  id="status"  align="center"> ✅ Finalizado ✅ </h4>

## índice

<p  align="left">
• <a  href="#tec">Tecnologias</a> <br>
• <a  href="#api">Servidor da API</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#apiexe"> Como executar</a> <br>
• <a  href="#hidrometro">Hidrômetro</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#exehidro"> Como executar</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#confighidro"> Configurações iniciais</a> <br>
• <a  href="#interface">Interface</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#exeinterface">  Como executar</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#configinterface"> Configurações iniciais</a> <br>
• <a  href="#nevoa">Névoa</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#exenevoa"> Como executar</a> <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <a  href="#confignevoa"> Configurações iniciais</a> <br>
• <a  href="#discente">Discentes</a> <br>
</p>

<h2  id="tec" >🛠 Tecnologias </h2>

- Linguagem de programação Python

- Biblioteca socket

- Biblioteca Pandas

- Biblioteca Tkinter

- Biblioteca Requests

- Framework Flask

- Docker

<br>
<h2  id="api">Servidor da API</h2>

<p  align="justify">
O servidor da API é responsável por receber as requisições, identificar a névoa que dispõe das informações e fornecer a resposta para requisição.
<br>
</p>

<h3  id="apiexe">Como executar</h3>

<p  align="justify">
Com o docker instalado no dispositivo, basta acessar a pasta <strong>servidor</strong> via terminal e executar o shell script (run-docker-servidor.sh) disponível na pasta. O script criará a imagem docker a partir do Dockerfile e inicializará o container em modo interativo.
<br>
<br>
Caso deseje obter a imagem docker a partir do Docker Hub ao invés do Dockerfile, basta abrir o shell script e seguir os passos indicados dentro do mesmo para efetuar tal ação. 
<br>
<br>
Executar o shell script:
</p>

```bash
$ sudo chmod +x run-servidor.sh           #Atribui a permissão de execução do script
$ ./run-servidor.sh                       #Executa o script
```
<br>
<p  align="justify">
Ao iniciar o servidor será solicitado o endereço do Broker ao qual o sistema deve se conectar.
</p>
<h2  id="hidrometro">Hidrômetro</h2>

<p  align="justify">
O hidrômetro pode receber por parâmetro um indicador se deve consumir mais ou menos água e se deve simular um vazamento.
<br>
<br>
Os dados computados pelo hidrômetro são enviados para o névoa que processa e armazena as informações para serem consultadas posteriormente via API. Além disso, o hidrômetro também pode receber comandos do servidor da API para ser desligado, caso algum cliente esteja inadimplente e um administrador bloqueie o fornecimento de água do mesmo. Já caso um hidrômetro apresente-se desligado e o cliente pague o débito pendente, o hidrômetro é desbloqueado automaticamente. <br>
<br>
Além disso, o hidrômetro pode ser desligado caso o seu consumo exceda a média de consumo de todos os hidrômetros ou ainda se consumir uma certa quantidade de água em um determinado intervalo de tempo.
<br>
<br>
São disponibilizadas 4 pastas para os hidrômetros: hidrometro-lento, hidrometro-medio, hidrometro-rapido e hidrometro-vazamentos. Todas apresentam o mesmo código, apenas dispõe de Dockerfiles diferentes no que se refere ao parâmetro passado ao iniciar o hidrômetro. Isso é apenas para facilitar o processo de instância de um novo hidrômetro.
</p>

<h3  id="exehidro">Como executar</h3>

<p  align="justify">
Com o docker instalado no dispositivo, basta acessar a pasta <strong>hidrometro-&lt;opção desejada&gt;</strong> via terminal e executar o shell script (run-hidrometro-&lt;opção desejada&gt;.sh) disponível na pasta. O script criará a imagem docker a partir do Dockerfile e inicializará o container em modo interativo.
<br>
<br>
Caso deseje obter a imagem docker a partir do Docker Hub ao invés do Dockerfile, basta abrir o shell script e seguir os passos indicados dentro do mesmo para efetuar tal ação. 
<br>
<br>
Executar o shell script:
</p>

```bash
$ sudo chmod +x run-docker-hidrometro-<opção desejada>.sh      #Atribui a permissão de execução do script
$ ./run-docker-hidrometro-<opção desejada>.sh                  #Executa o script
```
<h3 id="confighidro">Configurações iniciais</h3>
<p  align="justify">
Ao iniciar a aplicação será solicitado três informações via terminal. Primeiramente será solicitada a matrícula do hidrômetro. Posteriormente será solicitado o nome do cliente relacionado ao hidrômetro. Depois será solicitado a identificação da névoa em que o hidrômetro deve se conectar. Por fim, é solicitado o endereço do Broker que o hidrômetro deve se conectar via MQTT.
</p>

<br>
<h2  id="interface">Interface do Administrador</h2>

<p  align="justify">
A interface é uma aplicação desktop que consome a API permitindo visualizar as informações dos hidrômetros em tempo real, visualizar os dados de um hidrômetro com a menor latência possível e enviar o consumo máximo permitido em um intervalo de tempo definido pelo administrador.
</p>
<br>
<br>

<h3  id="exeinterface">Como executar</h3>

<p  align="justify">
Com o docker instalado no dispositivo, basta acessar a pasta <strong>interface-adm</strong> via terminal e executar o shell script (run-interface.sh) disponível na pasta. O script criará a imagem docker a partir do Dockerfile e inicializará o container em modo interativo.
<br>
<br>
Caso deseje obter a imagem docker a partir do Docker Hub ao invés do Dockerfile, basta abrir o shell script e seguir os passos indicados dentro do mesmo para efetuar tal ação. 
<br>
<br>
Executar o shell script:
</p>

```bash
$ sudo chmod +x run-interface.sh      #Atribui a permissão de execução do script
$ ./run-interface.sh                  #Executa o script
```
<h3 id="configinterface">Configurações iniciais</h3>
<p  align="justify">
Ao iniciar a interface será solicitado o endereço (IP) do servidor da API. Com isso, a interface pode solicitar os dados da API e enviar os comandos para o hidrômetro.
</p>
<br>
<br>

<h2  id="nevoa">Névoa</h2>
<p  align="justify">
A névoa é um servidor intermediário entre o hidrômetro e a nuvem. É na névoa em que os dados dos hidrômetros são armazenados, assim quando alguma solicitação é efeita na API da nuvem, as informações são solicitadas a névoa e então a resposta da API é fornecida.
</p>
<br>
<br>

<p align="justify">
Temos três pastas para as névoas: Nevoa, Nevoa2 e Nevoa3. Essencialmente, todas as três pastas apresentam o mesmo código a única diferença entre eles são os usuário cadastrados em cada uma das névoas. A névoa da pasta Nevoa apresenta as matrículas de 001 até 004; a névoa da pasta Nevoa2 apresenta as matrículas 005 até 008 e a névoa da pasta Nevoa3 apresenta as matrículas de 009 até 012. Isso foi feito apenas para facilitar os testes, porém podem ser cadastrados outros usuários da névoas, lembrando de cadastrar os mesmos usuários também no servidor da nuvem e modificar o intervalo de matrículas para cada uma das névoas informado na nuvem.
</p>
<br>
<br>

<h3  id="exenevoa">Como executar</h3>
<p  align="justify">
Com o docker instalado no dispositivo, basta acessar a pasta <strong>Nevoa</strong> via terminal e executar o shell script (run-nevoa.sh) disponível na pasta. O script criará a imagem docker a partir do Dockerfile e inicializará o container em modo interativo.
<br>
<br>
Caso deseje obter a imagem docker a partir do Docker Hub ao invés do Dockerfile, basta abrir o shell script e seguir os passos indicados dentro do mesmo para efetuar tal ação.
<br>
<br>
Executar o shell script:
</p>

```bash
$ sudo chmod +x run-nevoa.sh      #Atribui a permissão de execução do script
$ ./run-nevoa.sh                  #Executa o script
```
<h3 id="confignevoa">Configurações iniciais</h3>
<p  align="justify">
Ao iniciar a névoa será solicitado a identificação da névoa. Posteriomente será solicitado o endereço do Broker MQTT que a névoa deve se conectar.
</p>
<br>
<br>
<h2 id="discente">Discentes</h2>

- Igor Figueredo Soares
- Lokisley Oliveira

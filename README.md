<h1  align="center">Problema 1 - Consumo Inteligente de Água </h1>

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
• <a  href="#discente">Discente</a> <br>
</p>

<h2  id="tec" >🛠 Tecnologias </h2>

- Linguagem de programação Python

- Biblioteca socket

- Biblioteca Pandas

- Biblioteca Tkinter

- Biblioteca Requests (utilizado apenas na interface)

- Framework Flask (utilizado apenas na interface)

- Docker

<br>
<h2  id="api">Servidor da API</h2>

<p  align="justify">
O servidor da API é responsável por receber os dados dos hidrômetros, tratá-los e armazená-los para fornecer via API. Ao receber um dado o servidor salva no banco de dados no formato csv. Cada hidrômetro tem o seu próprio arquivo csv de dados.
<br>
<br>
Com os dados armazenados, os mesmos podem ser fornecidos via API. Para isso, o servidor dispõe de 11 endpoints, sendo 3 endpoints para executar as ações, tais como, gerar fatura de um cliente, bloquear um cliente com fatura em aberto e receber o pagamento de uma fatura. Os 8 endpoints restantes são responsáveis por fornecer informações aos clientes, listar os clientes e validar login no sistema.
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
$ sudo chmod +x run-docker-servidor.sh    #Atribui a permissão de execução do script
$ ./run-docker-servidor.sh                #Executa o script
```
<br>
<h2  id="hidrometro">Hidrômetro</h2>

<p  align="justify">
O hidrômetro apresenta uma interface para controlar a vazão de água e a pressão. A vazão diz a respeito do consumo de água do cliente. Enquanto que a pressão indica se há um possível vazamento. Caso a pressão esteja abaixo de 1 bar e a vazão esteja em 0 m³/s, significa que há um possível vazamento de água no endereço, então um alerta é emitido.
<br>
<br>
Os dados computados pelo hidrômetro são enviados para o servidor da API que processa e armazena as informações para serem consultadas posteriormente via API. Além disso, o hidrômetro também pode receber comandos do servidor da API para ser desligado, caso algum cliente esteja inadimplente e um administrador bloqueie o fornecimento de água do mesmo. Já caso um hidrômetro apresente-se desligado e o cliente pague o débito pendente, o hidrômetro é desbloqueado automaticamente.
</p>

<h3  id="exehidro">Como executar</h3>

<p  align="justify">
Com o docker instalado no dispositivo, basta acessar a pasta <strong>hidrometro</strong> via terminal e executar o shell script (run-docker-hidrometro.sh) disponível na pasta. O script criará a imagem docker a partir do Dockerfile e inicializará o container em modo interativo.
<br>
<br>
Caso deseje obter a imagem docker a partir do Docker Hub ao invés do Dockerfile, basta abrir o shell script e seguir os passos indicados dentro do mesmo para efetuar tal ação. 
<br>
<br>
Executar o shell script:
</p>

```bash
$ sudo chmod +x run-docker-hidrometro.sh      #Atribui a permissão de execução do script
$ ./run-docker-hidrometro.sh                  #Executa o script
```
<h3 id="confighidro">Configurações iniciais</h3>
<p  align="justify">
Ao iniciar a aplicação será solicitado três informações via terminal. Primeiramente será solicitado o endereço (IP) do servidor da API, de modo que o hidrômetro possa enviar seus dados para o servidor. A segunda informação solicitada será a matrícula do hidrômetro (somente números) e por fim, o nome do cliente referente aquele hidrômetro.
</p>

<br>
<h2  id="interface">Interface</h2>

<p  align="justify">
A interface é uma aplicação web que consome a API permitindo visualizar as informações dos clientes e enviar comandos para o hidrômetro. 
<br>
<br>
A interface é dividida em três partes, a primeira é referente a área do administrador, onde é possível ver a lista de clientes cadastrados no sistema, gerar a fatura de cada um deles e desligar o fornecimento de água, caso apresentem faturas em aberto. </p>

<p>A segunda parte é a área do cliente, onde é possível verificar o consumo e obter a fatura. </p>

<p>Por fim, a terceira parte é referente ao pagamento de faturas, onde ao fornecer a matrícula do cliente, se houver fatura em aberto, a fatura é quitada. Além disso, caso o fornecimento de água esteja suspenso o mesmo é retornado. 
</p>

<h3  id="exeinterface">Como executar</h3>

<p  align="justify">
Com o docker instalado no dispositivo, basta acessar a pasta <strong>interface</strong> via terminal e executar o shell script (run-docker-interface.sh) disponível na pasta. O script criará a imagem docker a partir do Dockerfile e inicializará o container em modo interativo.
<br>
<br>
Caso deseje obter a imagem docker a partir do Docker Hub ao invés do Dockerfile, basta abrir o shell script e seguir os passos indicados dentro do mesmo para efetuar tal ação. 
<br>
<br>
Executar o shell script:
</p>

```bash
$ sudo chmod +x run-docker-interface.sh      #Atribui a permissão de execução do script
$ ./run-docker-interface.sh                  #Executa o script
```
<h3 id="configinterface">Configurações iniciais</h3>
<p  align="justify">
Ao iniciar o servidor da interface será solicitado o endereço (IP) do servidor da API. Com isso, o servidor da interface pode solicitar os dados da API e enviar os comandos para o hidrômetro.
<br>
<br>
</p>

<h2 id="discente">Discente</h2>

- Igor Figueredo Soares

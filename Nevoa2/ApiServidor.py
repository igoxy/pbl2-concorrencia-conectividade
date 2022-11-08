# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from paho.mqtt import client as mqtt_client
import json
import os
import random
import re
import socket
import pandas as pd
from pandas import DataFrame
import threading
from flask import Flask



class ApiServidor():
    """ Classe do servidor da API """
    app = Flask(__name__)

    # ---------- Mensagens ----------
    NOT_FOUND =             ('404')
    NOT_ACCEPTABLE =        ('406')
    OK =                    ('200')
    INTERNAL_SERVER_ERROR = ('500')
    NOT_IMPLEMENTED =       ('501')

    # ---------- Rotas ----------
    ADM_GERAR_FATURA = '/ADMINISTRADOR/GERAR_FATURA'                    # POST  -   OK
    ADM_VAZAMENTOS = '/ADMINISTRADOR/VAZAMENTOS'                        # GET   -   OK
    ADM_DESLIGAR_CLIENTE = '/ADMINISTRADOR/DESLIGAR_CLIENTE'            # POST  -   OK
    SYS_RECEBER_PAGAMENTO = '/PAGAMENTO/RECEBER'                        # POST  -   OK
    USER_CONSUMO_DATA_HORARIO = '/CLIENTE/CONSUMO/DATA_HORARIO'         # GET   -   OK
    USER_CONSUMO_TOTAL = '/CLIENTE/CONSUMO/TOTAL'                       # GET   -   OK
    USER_CONSUMO_ATUAL = '/CLIENTE/CONSUMO/FATURA_ATUAL'                # GET   -   OK
    USER_OBTER_FATURA = '/CLIENTE/OBTER_FATURA'                         # GET   -   OK
    LISTAR_CLIENTES = '/LISTAR_CLIENTES'                                # GET   -   OK 
    ADM_MONITORAR_HIDROMETRO = '/ADMINISTRADOR/MONITORAR_HIDROMETRO'    # GET   -   OK

    __colecao_threads = {}              # Pool de threads

    def __init__(self, host: str, port: int, broker: str):
        self.__host = host
        self.__port = port
        self.__broker = broker

        self.__server_socket_tcp = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)     # Criando o socket

    @app.route('/maior_consumo/<quantidade>', methods=['GET'])
    def get_maiores_consumo(quantidade):
        executar = ObterDados('', '')
        resposta = executar.hidrometros_maior_consumo({"quantidade": quantidade})
        if (resposta != '500'):
            return resposta
        else:
            return {}

    def run_api_flask(self, flask):
        flask.run(host='0.0.0.0', debug=False)

    def start(self):
        """ Inicia o servidor da API """
        endpoint = (self.__host, self.__port)
        try:
            self.__server_socket_tcp.bind(endpoint)
            self.__server_socket_tcp.listen(1)
            print(f'Endereço da API: {str(socket.gethostbyname(socket.gethostname()))}')
            print(f'Servidor da API iniciado na porta: {self.__port}')
            while True:
                # Esperando conexão do cliente
                conexao, cliente = self.__server_socket_tcp.accept()
                self.__colecao_threads[cliente] = threading.Thread(
                    target=self.__requisicao, args=([conexao]))
                self.__colecao_threads[cliente].daemon = True
                self.__colecao_threads[cliente].start()
        except Exception as ex:
            print("Erro no servidor", ex.args)
            self.__server_socket_tcp.close()

    def __requisicao(self, conexao):
        """ Trata as requisições do recebidas no servidor da API"""
        def enviar_resposta(con, resposta):
            """Método para envia a resposta ao cliente"""
            try:
                con.sendall(resposta.encode())
                con.close()
            except Exception as ex:
                print("Erro ao enviar a respota. Causa: ", ex.args)
        
        try:
            request = conexao.recv(4096).decode()                       # Decofica a mensagem recebida
            informacoes_request = self.__decode_requisicao(request)     # Obtém as informações da requisição
            if (str(informacoes_request[1]).upper() == self.ADM_VAZAMENTOS or str(informacoes_request[1]).upper() == self.LISTAR_CLIENTES):    # Verifica se a solicitação foi na rota de obter áreas possíveis vazamentos ou listar clientes
                executar = ObterDados('', self.__broker)                                       # Se sim, cria o objeto para obter os dados sem uma matrícula associada
            else:                                                               # Senão
                dados = json.loads(informacoes_request[-1])                     # Converte os dados recebidos da requisição em dicionário                      
                executar = ObterDados(str(dados['matricula']).zfill(3), self.__broker)         # Cria o objeto para obter os dados com a matrícula do usuário enviado na solicitação
            print(f"Requisição na rota: {informacoes_request[1]}")
            if (informacoes_request[0] == 'GET'):                               # Verifica se o verbo da requisição é do tipo GET
                if (str(informacoes_request[1]).upper() == self.USER_OBTER_FATURA): # Obter a Fatura do cliente
                    try:
                        resultado = executar.obter_fatura()                                                 # Obtém o resultado da operação
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR and resultado != self.NOT_ACCEPTABLE):  # Se não retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                       # Resposta da requisição
                            enviar_resposta(conexao, resposta)                                              # Envia a mensagem de resultado da ação
                        else:                                                                               # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Mensagem de retorno com o erro
                            enviar_resposta(conexao, resposta)                                              # Envia a mensagem de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_VAZAMENTOS):  # Possíveis vazamentos de água
                    try:
                        resultado = executar.possiveis_vazamentos()
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):    # Se não retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de possíveis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n"                                      
                            resposta(conexao, resposta)                                                 # Envia o erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.USER_CONSUMO_DATA_HORARIO):   # Consumo por data e hora
                    try:
                        resultado = executar.consumo_data_hora(dados)
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):   # Se não retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de possíveis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n" 
                            enviar_resposta(conexao, resposta)                                          # Envia a mensagem de resultado da ação 
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.USER_CONSUMO_TOTAL):  # Consumo total
                    try:
                        resultado = executar.consumo_total()
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):   # Se não retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de possíveis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n" 
                            enviar_resposta(conexao, resposta) 
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.USER_CONSUMO_ATUAL):  # Verifica se a solicitação é equivalente a uma rota existente
                    try:
                        resultado = executar.consumo_fatura_atual()
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):   # Se não retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de possíveis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n" 
                            enviar_resposta(conexao, resposta) 
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.LISTAR_CLIENTES): # Verifica se a solicitação é equivalente a uma rota existente
                    try:
                        resultado = executar.listar_clientes()                      # Obtém a lista de clientes
                        if (resultado != self.INTERNAL_SERVER_ERROR):               # Verifica se não ocorreu nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"               # Retorna a lista de clientes
                            enviar_resposta(conexao, resposta)                      # Envia a resposta de volta
                        else:                                                       # Se ocorreu um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n"                  # Cria a mensagem de erro
                            enviar_resposta(conexao, resposta)                      # Envia a mensagem de erro
                    except:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_MONITORAR_HIDROMETRO):
                    try:
                        resultado = executar.monitorar_hidrometro()
                        if (resultado != self.INTERNAL_SERVER_ERROR and resultado != self.NOT_FOUND):
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                   # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da ação
                else:
                    resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n" 
                    enviar_resposta(conexao, resposta) 
            elif (informacoes_request[0] == 'POST'):                    # Verifica se o verbo da requisição é do tipo POST
                if (str(informacoes_request[1]).upper() == self.ADM_DESLIGAR_CLIENTE):  # Verifica a rota solicitada é equivalente a uma rota existente
                    try:
                        resultado = executar.desligar_cliente(dados)    # Executa a ação de desligar o cliente e retorna o resultado
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da ação
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                    except Exception:                                    # Caso a matricula não seja fornecida pelo cliente na requisição
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.SYS_RECEBER_PAGAMENTO): # Verifica a rota solicitada é equivalente a uma rota existente
                    try:
                        resultado = executar.receber_pagamento()   # Quita a fatura e retorna o resultado da ação
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da ação
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_GERAR_FATURA): # Gerar Fatura
                    try:
                        resultado = executar.gerar_fatura()                                             # Obtém o resultado da operação
                        resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Resposta da requisição
                        enviar_resposta(conexao, resposta)                                              # # Envia a mensagem de resultado da ação
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                else:
                    resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}\n\n{informacoes_request[-1]}"   # Envia um mensagem de método não suportado e retorna o conteúdo da mensagem recebida
                    conexao.sendall(resposta.encode())
                    conexao.close()
            else:
                resposta = f"HTTP/1.1 {self.NOT_IMPLEMENTED}\n\n{informacoes_request[-1]}"   # Envia um mensagem de método não suportado e retorna o conteúdo da mensagem recebida
                conexao.sendall(resposta.encode())
                conexao.close()
        except ConnectionResetError as ex:
            print("Erro na conexão do cliente. Causa: ", ex.args)
        except KeyError:
            resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
            enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
        except ValueError as ex:
            print(f'value error. causa {ex.args}')     
            resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}"
            enviar_resposta(conexao, resposta)
        except Exception as ex:
            print("Erro com a conexão. Causa: ", ex.args)

    def __decode_requisicao(self, requisicao: str):
        """ Decodifica a requisição recebida """
        verbo, _, restante = requisicao.partition(' ')  # Obtém o verbo da requisição
        url, _, _ = restante.partition(' ')             # Obtém o caminho da requisição
        body = re.split(r"\n", requisicao)              # Obtém o conteúdo da requisição (body)

        if (verbo == 'GET'):
            return ['GET', url, body[-1]]       # Retorna o verbo, a rota e o conteúdo da requisição
        elif (verbo == 'POST'):
            return ['POST', url, body[-1]]      # Retorna o verbo, a rota e o conteúdo da requisição
        else:
            return ['UNKNOWN', url, body[-1]]   # Retorna o verbo desconhecido, a rota e o conteúdo da requisição

class ObterDados():
    """ Classe para obter os dados das solicitações da API """
    LIGAR =     "2"         # Constante para o comando de ligar um hidrômetro
    DESLIGAR =  "1"         # Constante para o comando de desligar um hidrômetro

    #Constantes 
    TOPIC = 'hidrometro/acao/'  # Tópico para desligar o cliente - inserir matricula e mudar para a nevoa
    HOST = ''                   # Endereço do broker
    PORT =  1883                # Porta do broker
    CLIENTE_ID = f'python-mqtt-{random.randint(0, 1000)}'

    # ---------- Mensagens ----------
    NOT_FOUND =             ('404')
    NOT_ACCEPTABLE =        ('406')
    OK =                    ('200')
    INTERNAL_SERVER_ERROR = ('500')
    NOT_IMPLEMENTED =       ('501')

    
    def __init__(self, matricula: str, broker: str):
        """ Construtor da classe ObterDados"""
        self.__matricula = matricula
        self.HOST = broker
        

    # ----------- Métodos Públicos ----------- #
    def desligar_cliente(self, dados: dict):
        """ Método responsável por bloquear hidrômetro de um cliente """
        return self.__bloquear_hidrometro(dados)

    
    def receber_pagamento(self):
        """ Método responsável por receber o pagamento de uma fatura de um cliente """
        return self.__conta_paga()

    def possiveis_vazamentos(self):
        """ Método responsável por obter os locais com possíveis vazamentos """
        try:
            df = pd.read_csv(f"usuarios.csv")
            return self.__obter_alertas_vazamento(df)
        except FileNotFoundError:
            return self.NOT_FOUND
    
    def consumo_data_hora(self, dados):
        """ Método responsável por retornar o consumo de um cliente em um período de tempo """
        return self.__obter_consumo_data(dados)

    def consumo_total(self):
        """ Método responsável por retornar o consumo total de um cliente """
        return self.__obter_consumo_total()

    def consumo_fatura_atual(self):
        """ Método responsável por retornar o consumo da fatura atual de um cliente """
        return self.__obter_consumo_fatura()
    
    def gerar_fatura(self):
        """ Método responsável por gerar a fatura de um cliente"""
        try:
            df_consumo = pd.read_csv(f"{self.__matricula}.csv", sep=',')                                    # Carrega o banco de dados de consumo da matricula (usuário) especificada
            df_dados = pd.read_csv("usuarios.csv", sep=",")                                                 # Carrega o banco de dados de usuários
            indice_usuario = (df_dados.index[df_dados['matricula'] == int(self.__matricula)]).tolist()[0]   # Obtém o indice que refencia o usuário no dataframe de usuários
            if (df_dados.iloc[indice_usuario]['pendencia'] == True):                                             # Verifica se o usuário tem faturas em aberto
                return self.NOT_ACCEPTABLE                                                                  # Se tiver faturas em aberto, não é possível gerar uma nova fatura ainda e retorna um erro
            else:
                fatura_json = self.__criar_fatura(df_consumo, df_dados)                                     # Gera o Json com os dados da fatura
                df_consumo.at[0, 'contaGerada'] = True                                                      # Identifica que o usuário tem uma fatura gerada
                df_consumo.at[0, 'pago'] = False                                                            # Identifica que o usuário ainda não pagou a fatura (visto que a conta acabou de criada)
                df_dados.at[indice_usuario, 'pendencia'] = True                                             # Identifica que o usuário tem uma fatura em aberto

                df_consumo.to_csv(f"{self.__matricula}.csv", sep=',', index=False)                          # Salva os dados de consumo como csv
                df_dados.to_csv("usuarios.csv", sep=",", index=False)                                       # Salva os dados dos usuários como csv
                return fatura_json                                                                          # Retorna a fatura
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception as ex:
            print("Erro ao gerar fatura. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR
    
    def obter_fatura(self):
        """ Método para obter a fatura do cliente """
        try:
            df_dados = pd.read_csv("usuarios.csv", sep=",")                                                 # Carrega o banco de dados de usuários
            indice_usuario = (df_dados.index[df_dados['matricula'] == int(self.__matricula)]).tolist()[0]   # Obtém o indice que refencia o usuário no dataframe de usuários
            if (df_dados.iloc[indice_usuario]['pendencia'] == True):                                        # Verifica se o usuário tem faturas em aberto
                with open(f'{self.__matricula}.json', 'r') as fatura_file:                                  # Abre o arquivo
                    fatura = json.load(fatura_file)                                                         # Carrega o arquivo em json da fatura
                fatura = json.dumps(fatura)                                                                 # Transforma o json para string em formato json
                return fatura                                                                               # Retorna a fatura em json
            else:
                return self.NOT_ACCEPTABLE                                                                  # Retorna um erro indicando que ainda não há fatura aberta para o cliente
        except FileNotFoundError:
            return self.NOT_FOUND                                                                           # Retorna um erro indicando que a matricula do cliente não foi encontrada
        except Exception as ex:
            print("Erro ao gerar fatura. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR
    
    def listar_clientes(self):
        """ Método para listar os clientes do sistema """
        return self.__listar_clientes()
    
    def hidrometros_maior_consumo(self, dados: dict):
        """ Obtém os n hidrômetros de maior consumo """
        try:
            quantidade = int(dados['quantidade'])
            df = pd.read_csv('consumo-clientes.csv', sep=',')
            n_maiores = df.nlargest(quantidade, ['consumo']).reset_index(drop=True)
            json_maiores = n_maiores.to_json(orient='index')
            return json_maiores
        except Exception:
            return self.INTERNAL_SERVER_ERROR
    
    def monitorar_hidrometro(self):
        """ Método responsável por retornar os dados do hidrômetro solicitado em menor tempo """
        try:
            df = pd.read_csv('consumo-clientes.csv', sep=',')
            dados_hidrometro = df[df['matricula'] == int(self.__matricula)]
            if (dados_hidrometro.empty):
                return self.NOT_FOUND
            else:
                dados_json = dados_hidrometro.to_json(orient='index')       # Retorna um json contendo um valor e uma chave - sendo o valor o dicionario com as informações do cliente
                return dados_json
        except Exception:
            return self.INTERNAL_SERVER_ERROR
    # ----------- Fim Métodos Públicos ----------- #

    # ----------- Métodos Privados ----------- #
    def __criar_fatura(self, df_consumo: DataFrame, df_dados: DataFrame):
        """ Método responsável por criar formatar os dados fatura do cliente """
        try:
            cliente = (df_dados.loc[df_dados['matricula'] == int(df_consumo.iloc[0]['matricula'])]).reset_index(drop=True)  # Obtém a linha do dataframe que pertence aos dados do usuário
            fatura = {
                'consumoFatura':    str(df_consumo.iloc[0]['consumoFatura']),   # Obtém o consumo da fatura
                'valor':            str(df_consumo.iloc[0]['valor']),           # Obtém o valor da fatura
                'dataLeitura':      str(df_consumo.iloc[0]['dataHora'])[0:10],  # Gera uma string com a data e horário exato de criação da fatura
                'consumoTotal':     str(df_consumo.iloc[0]['consumo']),         # Obtém o consumo total do cliente (valor mostrado no hidrômetro na hora da leitura) 
                'nomeUsuario':      str(df_consumo.iloc[0]['nomeUsuario']),     # Obtém o nome de usuário (cliente) da fatura
                'cpf':              str(cliente.iloc[0]['cpf']),                # obtém o cpf do cliente
                'dataFatura':       date.today().strftime("%d/%m/%Y"),          # Obtém a hora da fatura
                'dataVencimento':   (date.today() + timedelta(days=10)).strftime("%d/%m/%Y"),   # Obtém a data de vencimento da fatura
                'matricula':        self.__matricula                            # Obtém a matrícula
            }
            json_fatura = json.dumps(fatura)                                        # Cria o json com os dados da fatura
            with open(f"{self.__matricula}.json", "w") as file_fatura:              # Cria um arquivo de fatura em json para o cliente
                file_fatura.write(json_fatura)                                      # Escreve no arquivo de fatura 
            return self.OK                                                          # Retorna que a fatura foi criada
            #return json_fatura                                                     # Retorna a fatura em json
        except Exception as ex:
            print("Erro ao criar fatura. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR

    def __obter_alertas_vazamento(self, df_usuarios: DataFrame):
        """ Retorna um json com os endereços que há um possível vazamento """
        try:
            found = df_usuarios['possivelVazamento'] == True    # Procura os usuários que tem a flag de possíveis vazamentos
            df_vazamentos = ((df_usuarios[found]).drop(['matricula', 'nome', 'cpf', 'ativo', 'pendencia', 'possivelVazamento'], axis=1, inplace=False)).reset_index(drop=True) # Adiciona as informações dos usuários em uma dataframe
            json_vazamentos = df_vazamentos.to_json(orient='index') # Cria um JSON com os endereços com possíveis vazamentos
            return json_vazamentos  # Retorna o JSON com as regiões de possíveis vazamentos
        except Exception as ex:     # Caso ocorra algum erro
            print("Erro ao obter os alertas de vazamento. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR             # Retorna o erro

    def __conta_paga(self):
        """ Identifica que a conta foi paga e quita a conta do cliente no sistema"""
        try:
            df_usuarios = pd.read_csv("usuarios.csv", sep=',')
            indice_usuario = self.__obter_indice_usuario(df_usuarios, self.__matricula)   # Obtém o indice do usuário na lista de clientes do sistema
            if (bool(df_usuarios.iloc[indice_usuario]['pendencia'])):       # Verifica se o usuário tem alguma fatura em aberto
                df_usuarios.at[indice_usuario, 'pendencia'] = False         # Retira a pendencia do cliente                                               
                os.remove(f'{self.__matricula}.json')                       # Se existir apaga o arquivo
                if (not bool(df_usuarios.iloc[indice_usuario]['ativo'])):   # Verifica se o cliente está com o fornecimento de água suspenso
                    if (self.__enviar_comando_hidrometro(self.LIGAR, self.__matricula)):   # Ligar o hidrômetro desativado
                        df_usuarios.at[indice_usuario, 'ativo'] = True                                              # Identifica que o hidrômetro do cliente está ativo novamente
                        df_usuarios.at[indice_usuario, 'pendencia'] = False
                        df_usuarios.to_csv('usuarios.csv', sep=',', index=False)                                # Salva as modificações no arquivo
                        return self.OK
                    else:
                        return self.INTERNAL_SERVER_ERROR 
                else:
                    df_usuarios.at[indice_usuario, 'pendencia'] = False
                    df_usuarios.to_csv('usuarios.csv', sep=',', index=False)                                  # Salva as modificações no arquivo
                    return self.OK
            else:   # Se não tiver fatura em aberto
                return self.NOT_ACCEPTABLE
        except FileNotFoundError:
            return self.NOT_FOUND 

    def __bloquear_hidrometro(self, dados: dict):
        """ Método responsável por bloquear um hidrômetro """
        try:
            df_usuarios = pd.read_csv("usuarios.csv", sep=',')
            indice_usuario = self.__obter_indice_usuario(df_usuarios, self.__matricula)     # Obtém o indice do usuário na lista de clientes do sistema 
            if (bool(df_usuarios.iloc[indice_usuario]['pendencia'])):                       # Verifica se o usuário tem uma conta em aberto
                if(self.__enviar_comando_hidrometro(self.DESLIGAR, self.__matricula)):
                    df_usuarios.at[indice_usuario, 'ativo'] = False                         # Seta cliente como desligado
                    df_usuarios.to_csv('usuarios.csv', sep=',', index=False)                # Salva a modificação feita no arquivo
                    return self.OK
                else: return self.INTERNAL_SERVER_ERROR                                                                 
            else:
                return self.NOT_ACCEPTABLE
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception:
            return self.INTERNAL_SERVER_ERROR

    # Funcionalidade implementada, mas não disponível para uso no momento
    def __desbloquear_hidrometro(self, dados: dict):
        """ Método responsável por desbloquear um hidrômetro manualmente pelo administrador"""
        try:
            df_usuarios = pd.read_csv("usuarios.csv", sep=',')
            indice_usuario = self.__obter_indice_usuario(df_usuarios, dados['matricula'])   # Obtém o indice do usuário na lista de clientes do sistema 
            if (not bool(df_usuarios.iloc[indice_usuario]['ativo'])):                       # Verifica se o usuário está desativado
                if(self.__enviar_comando_hidrometro(self.LIGAR, self.__matricula)):
                    df_usuarios.at[indice_usuario, 'ativo'] = True                         # Seta cliente como ligado
                    return self.OK
                else: return self.INTERNAL_SERVER_ERROR
            else:
                return self.NOT_ACCEPTABLE
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception:
            return self.INTERNAL_SERVER_ERROR
        
    def __obter_consumo_data(self, dados: dict):
        """ Método responsável por obter o consumo de um cliente em uma data específica"""
        try:
            df_dados = pd.read_csv(f"{self.__matricula}.csv")
            df_dados['dataHora'] = pd.to_datetime(df_dados.dataHora)
            data_inicial = datetime.strptime(dados['dataInicial'], '%Y-%m-%d-%H:%M:%S') #'%Y-%m-%d-%H:%M:%S'
            data_final = datetime.strptime(dados['dataFinal'], '%Y-%m-%d-%H:%M:%S')
            df_consumo_data = df_dados[(data_inicial <= df_dados['dataHora']) & (data_final > df_dados['dataHora'])]
            conusmo_data = float(df_consumo_data.at[df_consumo_data.index[0], 'consumo']) - float(df_consumo_data.at[df_consumo_data.index[-1], 'consumo'])  # Obtém o valor de consumo no perído especificado
            resposta = {'consumoData': conusmo_data}
            resposta = json.dumps(resposta)     # Converte a resposta para JSON
            return resposta
        except FileNotFoundError:   # Caso não encontre o cliente
            return self.NOT_FOUND
        except IndexError:          # Caso não tenha registro de consumo nas datas
            return self.NOT_FOUND
        except Exception as e:      # Caso ocorra algum outro erro
            print(f'Erro ao obter o consumo da data especificada. Causa: {e.args}')
            return self.INTERNAL_SERVER_ERROR
    
    def __obter_consumo_fatura(self):
        """ Método responsável por obter o consumo da atual fatura de um cliente"""
        try:
            df_dados = pd.read_csv(f"{self.__matricula}.csv")
            consumo_fatura = float(df_dados.iloc[0]['consumoFatura'])  # Obtem o consumo da fatura atual
            resposta = {'consumoFatura': consumo_fatura}
            resposta = json.dumps(resposta)
            return resposta
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception:
            return self.INTERNAL_SERVER_ERROR
    
    def __obter_consumo_total(self):
        """ Método responsável por obter o consumo da total de um cliente"""
        try:
            df_dados = pd.read_csv(f"{self.__matricula}.csv")
            consumo_total = float(df_dados.iloc[0]['consumo'])  # Obtem o consumo da fatura atual
            resposta = {'consumoTotal': consumo_total}
            resposta = json.dumps(resposta)
            return resposta
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception:
            return self.INTERNAL_SERVER_ERROR
    
    def __listar_clientes(self):
        """ Método responsável por retornar os clientes cadastrados no sistema """
        try:    
            df = pd.read_csv(f"usuarios.csv")                   # Carrega os usuários do sistema
            df_lista_clientes = df.drop(['cpf','ativo','pendencia','endereco','possivelVazamento'], axis=1, inplace=False).reset_index(drop=True)   #Obtém a lista dos clientes deixando apenas o nome e a matricula
            json_lista_clientes = df_lista_clientes.to_json(orient='index')
            return json_lista_clientes
        except:
            return self.INTERNAL_SERVER_ERROR           # Retorna o erro 
    
    # ----------- Métodos Auxiliares ----------- #
    def __obter_indice_usuario(self, dataframe: DataFrame, matricula: str):
        """ Método responsável por retornar o indice do usuário no DataFrame """
        return (dataframe.index[dataframe['matricula'] == int(matricula)]).tolist()[0]
    # ----------- Fim Métodos Auxiliares ----------- #

    def __enviar_comando_hidrometro(self, comando: str, matricula: str):
        """ Método responsável por enviar comandos para um hidrômetro """
        self.__conectar()                               # Conecta ao broker
        resultado = self.__publish(comando, matricula)  # Envia a mensagem
        self.cliente.disconnect()                       # Desconecta do broker após enviar a mensagem
        return resultado                                # Envia o resultado da operação de enviar mensagem

    
    def __conectar(self):                            
        """ Método para efetuar a conexão """
        self.cliente = self.__connect_mqtt()    # Conecta com o broker
        

    def __connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:         # Se conseguiu conectar com o broker
                pass
            else:
                print("Failed to connect, return code %d\n", rc)        # Senão conseguiu conectar com o broker, retorna o erro

        client = mqtt_client.Client(self.CLIENTE_ID)
        client.on_connect = on_connect
        client.connect(self.HOST, self.PORT)                            # Conexão com o broker
        return client
    
    def __publish(self, dados, matricula):
        """ Envia os dados para o servidor """
        try:
            result = self.cliente.publish(self.TOPIC + matricula, dados)        # Envia os dados para o hidrômetro no tópico relacionado ao hidrômetro
            status = result[0]
            if status == 0:
                print(f"Send `{dados}` to topic `{self.TOPIC+matricula}`")
                return True                                                     # Caso a mensagem tenha sido enviada para o hidrômetro com sucesso
            else:
                print(f"Failed to send message to topic {self.TOPIC+matricula}")
                return False                                                    # Caso a mensagem não tenha sido enviada para o hidrômetro
        except:
            return False                                                        # Caso ocorra alguma erro
    
    # ----------- Fim Métodos Privados ----------- #
    # ----------- Fim Métodos Auxiliares ----------- #
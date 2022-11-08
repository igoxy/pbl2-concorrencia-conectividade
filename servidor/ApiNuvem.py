# -*- coding: utf-8 -*-
import pickle
from paho.mqtt import client as mqtt_client
import json
import random
import re
import socket
import pandas as pd
import threading
import requests


class ApiNuvem():
    """ Classe do servidor da API """
    # ---------- Mensagens ----------
    NOT_FOUND =             ('404')
    NOT_ACCEPTABLE =        ('406')
    OK =                    ('200')
    INTERNAL_SERVER_ERROR = ('500')
    NOT_IMPLEMENTED =       ('501')

    # ---------- Rotas ----------
    ADM_GERAR_FATURA = '/ADMINISTRADOR/GERAR_FATURA'            # POST  -   OK
    ADM_VAZAMENTOS = '/ADMINISTRADOR/VAZAMENTOS'                # GET   -   OK
    ADM_DESLIGAR_CLIENTE = '/ADMINISTRADOR/DESLIGAR_CLIENTE'    # POST  -   OK
    SYS_RECEBER_PAGAMENTO = '/PAGAMENTO/RECEBER'                # POST  -   OK
    USER_CONSUMO_DATA_HORARIO = '/CLIENTE/CONSUMO/DATA_HORARIO' # GET   -   OK
    USER_CONSUMO_TOTAL = '/CLIENTE/CONSUMO/TOTAL'               # GET   -   OK
    USER_CONSUMO_ATUAL = '/CLIENTE/CONSUMO/FATURA_ATUAL'        # GET   -   OK
    USER_OBTER_FATURA = '/CLIENTE/OBTER_FATURA'                 # GET   -   OK
    LISTAR_CLIENTES = '/LISTAR_CLIENTES'                        # GET   -   OK 
    LOGIN_ADM = '/LOGIN_ADM'                                    # GET   -   OK
    LOGIN_USUARIO = '/LOGIN_USUARIO'                            # GET   -   OK

    ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO = '/ADMINISTRADOR/MAIOR_CONSUMO'     # GET - OK
    ADM_MONITORAR_HIDROMETRO = '/ADMINISTRADOR/MONITORAR_HIDROMETRO'         # GET - OK
    ADM_DEFINIR_CONSUMO_TEMPO = '/ADMINISTRADOR/CONSUMO_TEMPO'               # POST - OK
    __colecao_threads = {}              # Pool de threads

    def __init__(self, host: str, port: int, broker: str):
        self.__host = host
        self.__port = port
        self.__broker = broker

        self.__server_socket_tcp = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)  # Criando o socket

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
            print("Erro no servidor. Causa:", ex.args)
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
            request = conexao.recv(1024).decode()                       # Decofica a mensagem recebida
            informacoes_request = self.__decode_requisicao(request)     # Obtém as informações da requisição
            if (str(informacoes_request[1]).upper() == self.ADM_VAZAMENTOS or str(informacoes_request[1]).upper() == self.LISTAR_CLIENTES):    # Verifica se a solicitação foi na rota de obter áreas possíveis vazamentos ou listar clientes
                executar = ObterDados('', self.__broker)                                       # Se sim, cria o objeto para obter os dados sem uma matrícula associada
            elif (str(informacoes_request[1]).upper() == self.LOGIN_ADM or str(informacoes_request[1]).upper() == self.ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO or str(informacoes_request[1]).upper() == self.ADM_DEFINIR_CONSUMO_TEMPO):       # Verifica se a rota requisitada foi de login de adm
                dados = json.loads(informacoes_request[-1])                     # Converte os dados recebidos da requisição em dicionário
                executar = ObterDados('', self.__broker)                                       # Cria o objeto para obter os dados
            else:                                                               # Senão
                dados = json.loads(informacoes_request[-1])                     # Converte os dados recebidos da requisição em dicionário                      
                executar = ObterDados(dados['matricula'], self.__broker)                       # Cria o objeto para obter os dados com a matrícula do usuário enviado na solicitação
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
                elif (str(informacoes_request[1]).upper() == self.LOGIN_ADM):
                    try:
                        resultado = executar.login_adm(dados['login'], dados['senha'])  # Verifica se os dados correspondem ao adm
                        if (resultado != self.NOT_FOUND):                                # Se sim
                            resposta = f"HTTP/1.1 200\n\n"                              # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:                                                           # Senão 
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.LOGIN_USUARIO):
                    try:
                        resultado = executar.login_cliente()                            # Verifica se a matricula corresponde a algum cliente
                        if (resultado != self.NOT_FOUND):
                            resposta = f"HTTP/1.1 200\n\n"                              # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:                                                           # Senão 
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO):
                    try:
                        resultado = executar.hidrometros_maior_consumo(dados)           # Obtém os N hidrometros de maior consumo da nevoa
                        if (resultado != self.INTERNAL_SERVER_ERROR):
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                   # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_MONITORAR_HIDROMETRO):
                    try:
                        resultado = executar.monitorar_hidrometro()
                        if (resultado != self.INTERNAL_SERVER_ERROR):
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
            elif (informacoes_request[0] == 'POST'):                                    # Verifica se o verbo da requisição é do tipo POST
                if (str(informacoes_request[1]).upper() == self.ADM_DESLIGAR_CLIENTE):  # Verifica a rota solicitada é equivalente a uma rota existente
                    try:
                        resultado = executar.desligar_cliente(dados)    # Executa a ação de desligar o cliente e retorna o resultado
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da ação
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                    except Exception:                                   # Caso a matricula não seja fornecida pelo cliente na requisição
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.SYS_RECEBER_PAGAMENTO): # Verifica a rota solicitada é equivalente a uma rota existente
                    try:
                        resultado = executar.receber_pagamento()        # Quita a fatura e retorna o resultado da ação
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da ação
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_GERAR_FATURA):    # Gerar Fatura
                    try:
                        resultado = executar.gerar_fatura()                                             # Obtém o resultado da operação
                        resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Resposta da requisição
                        enviar_resposta(conexao, resposta)                                              # # Envia a mensagem de resultado da ação
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                elif (str(informacoes_request[1]).upper() == self.ADM_DEFINIR_CONSUMO_TEMPO):
                    try:
                        resultado = executar.enviar_tempo_consumo(dados)
                        resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Resposta da requisição
                        enviar_resposta(conexao, resposta)                                              # # Envia a mensagem de resultado da ação
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da ação
                else:
                    resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}\n\n{informacoes_request[-1]}"   # Envia um mensagem de método não suportado e retorna o conteúdo da mensagem recebida
                    print(f"Entrou aqui. {str(informacoes_request[1]).upper()}")
                    conexao.sendall(resposta.encode())
                    conexao.close()
            else:
                resposta = f"HTTP/1.1 {self.NOT_IMPLEMENTED}\n\n{informacoes_request[-1]}"      # Envia um mensagem de método não suportado e retorna o conteúdo da mensagem recebida
                conexao.sendall(resposta.encode())
                conexao.close()
        except ConnectionResetError as ex:
            print("Erro na conexão do cliente. Causa: ", ex.args)
        except KeyError:
            resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula não encontrada
            enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da ação
        except ValueError:     
                resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}\n\n{informacoes_request[-1]}"
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
    TOPIC = 'hidrometro/acao/'  #Tópico para desligar o cliente - inserir matricula e mudar para a nevoa

    # ---------- Mensagens ----------
    NOT_FOUND =             ('404')
    NOT_ACCEPTABLE =        ('406')
    OK =                    ('200')
    INTERNAL_SERVER_ERROR = ('500')
    NOT_IMPLEMENTED =       ('501')

    # --------- Rotas ------------
    ADM_GERAR_FATURA = '/ADMINISTRADOR/GERAR_FATURA'            # POST  -   OK
    ADM_VAZAMENTOS = '/ADMINISTRADOR/VAZAMENTOS'                # GET   -   OK
    ADM_DESLIGAR_CLIENTE = '/ADMINISTRADOR/DESLIGAR_CLIENTE'    # POST  -   OK
    SYS_RECEBER_PAGAMENTO = '/PAGAMENTO/RECEBER'                # POST  -   OK
    USER_CONSUMO_DATA_HORARIO = '/CLIENTE/CONSUMO/DATA_HORARIO' # GET   -   OK
    USER_CONSUMO_TOTAL = '/CLIENTE/CONSUMO/TOTAL'               # GET   -   OK
    USER_CONSUMO_ATUAL = '/CLIENTE/CONSUMO/FATURA_ATUAL'        # GET   -   OK
    USER_OBTER_FATURA = '/CLIENTE/OBTER_FATURA'                 # GET   -   OK
    LISTAR_CLIENTES = '/LISTAR_CLIENTES'                        # GET   -   OK
    LOGIN_ADM = '/LOGIN_ADM'                                    # GET   -   OK
    LOGIN_USUARIO = '/LOGIN_USUARIO'                            # GET   -   OK

    ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO = '/maior_consumo'      # GET   - OK
    
    # ------ MQTT -------
    HOST = ''                   # Endereço do broker
    PORT =  1883                # Porta do broker
    TOPIC = 'dados/hidrometro/servidor'
    CLIENTE_ID = f'python-mqtt-{random.randint(0, 1000)}'
    TOPIC_TEMPO_CONSUMO = 'nuvem/dados/tempo-vazao' 

    __endereco_requisicao = ''

    def __init__(self, matricula: str, broker: str):
        """ Construtor da classe ObterDados"""
        self.HOST = broker
        self.cliente = self.__connect_mqtt()
        self.__matricula = matricula
        self.__endereco_requisicao = self.__get_endereco_requisicao()


    # ----------- Métodos Públicos ----------- #
    def desligar_cliente(self, dados: dict):
        """ Método responsável por bloquear hidrômetro de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                resposta = requests.post(self.__endereco_requisicao + self.ADM_DESLIGAR_CLIENTE, json=dados)    # Solicita o desligamento do cliente para a névoa responsável pelo mesmo
                return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR

    
    def receber_pagamento(self):
        """ Método responsável por receber o pagamento de uma fatura de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.post(self.__endereco_requisicao + self.SYS_RECEBER_PAGAMENTO, json=dados)   # Envia informação de fatura paga para névoa responsável pelo cliente
                return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR

    def possiveis_vazamentos(self):
        """ Método responsável por obter os locais com possíveis vazamentos """
        try:
            arquivo = open('nevoas-conectadas.bin', 'rb')       # Abre o arquivo de névoas conectadas
            nevoas = pickle.load(arquivo)                       # Obtém as névoas conectadas em um dicionário
            arquivo.close()                                     # Fecha o arquivo de névoas conectadas
            dicionario_vazamentos = {}                          
            indice = 0
            for endereco in nevoas.values():                    # Percorre o dicionário de névoas conectadas obtendo os endereços das névoas
                resposta = requests.get(f'http://{endereco}:5051' + self.ADM_VAZAMENTOS)    # Solicita os possíveis vazamentos de cada névoa
                if (resposta.status_code == 200):                                           # Verifica se recebeu os resultados corretamente
                    dados = json.loads(resposta.content.decode())                           # Converte os dados recebidos em json
                    for dado in dados.values():                                             # Percorre cada dado de possível vazamento recebido
                        dicionario_vazamentos[indice] = dado                                # Adiciona os possíveis vazamentos a um dicionário
                        indice += 1                                                         # Soma 1 ao indice              
            vazamentos_json = json.dumps(dicionario_vazamentos)                             # Converte o dicionário com todos os possíveis vazamentos de todas as névoas para json
            return vazamentos_json                                                          # Retonar os possíveis vazamentos como json
        except Exception as ex:                                                             # Se ocorrer algum erro
            print(f'Erro ao obter os possíveis vazamentos. Causa: {ex.args}')               # Informa a causa
            return self.INTERNAL_SERVER_ERROR                                               # Retorna um erro
    
    def consumo_data_hora(self, dados):
        """ Método responsável por retornar o consumo de um cliente em um período de tempo """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                resposta = requests.get(self.__endereco_requisicao + self.USER_CONSUMO_DATA_HORARIO, json=dados)       # Requisita o consumo do cliente no intervalo definido de acordo com a névoa que se encontra
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR

    def consumo_total(self):
        """ Método responsável por retornar o consumo total de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.get(self.__endereco_requisicao + self.USER_CONSUMO_TOTAL, json=dados)   # Requisita o consumo total do cliente de acordo com a névoa que se encontra
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR
    def consumo_fatura_atual(self):
        """ Método responsável por retornar o consumo da fatura atual de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.get(self.__endereco_requisicao + self.USER_CONSUMO_ATUAL, json=dados)   # Requisita o consumo da fatura atual do cliente de acordo com a névoa que se encontra
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR
    
    def gerar_fatura(self):
        """ Método responsável por gerar a fatura de um cliente"""
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.post(self.__endereco_requisicao + self.ADM_GERAR_FATURA, json=dados)    # Requisita a fatura do cliente de acordo com a névoa que se encontra
                if (resposta == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR
    
    def obter_fatura(self):
        """ Método para obter a fatura do cliente """
        try:    
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.get(self.__endereco_requisicao + self.USER_OBTER_FATURA, json=dados)    #Solicita a fatura do cliente para nevoa
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except Exception as ex:
            print("Erro ao gerar fatura. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR
    
    def login_adm(self, login, senha):
        """ Método para efetuar o login do administrador """
        return self.__login_adm(login, senha)

    def login_cliente(self):
        """ Método para efetuar o login do cliente """
        return self.__login_cliente()
    
    def listar_clientes(self):
        """ Método para listar os clientes do sistema """
        return self.__listar_clientes()
    
    def hidrometros_maior_consumo(self, dados: dict):
        try: 
            quantidade = int(dados['quantidade'])
            arquivo = open('nevoas-conectadas.bin', 'rb')
            nevoas = pickle.load(arquivo)
            arquivo.close()
            dicionario_n_maiores = {}
            indice = 0
            for endereco in nevoas.values():
                req = requests.Request('GET', f'http://{endereco}:5000{self.ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO}/{quantidade}') # Define a requisição
                r = req.prepare()                                                                                               # Prepara a requisição
                s = requests.Session()                                                                                          # Inicia uma sessão
                resposta = s.send(r)                                                                                            # Envia a requisição para API
                s.close()                                                                                                       # Fecha a sessão
                if (resposta.status_code == 200):                                                                           # Verifica se recebeu corretamente       
                    n_maiores = json.loads(resposta.content.decode())                                                       # Converte json recebido em dicionario
                    for dado in n_maiores.values():                                                                         # Percorre por meio dos valores o dicionario do n maiores consumos da nevoa
                        dicionario_n_maiores[indice] = dado                                                                 # Adiciona o valor a um dicionário auxiliar
                        indice += 1                                                                     # Soma 1 ao indice
            total_n_maiores = json.dumps(dicionario_n_maiores)                                          # Converte o dicionario com os n maiores valores de cada nevoa em um json
            df = pd.read_json(total_n_maiores, orient='index')                                          # Carrega um dataframe a partir do json com os n maiores valores de cada nevoa
            resultado_n_maiores = df.nlargest(quantidade, ['consumo'])                                  # Obtém os n maiores valores de consumo
            json_n_maiores = resultado_n_maiores.to_json(orient='index')                                # Converte os n maiores valores de consumo em um json para enviar a resposta
            return json_n_maiores                                           # Retorna o json com os maiores consumo - as matriculas estão no formato int (sem os zeros a frente)
        except Exception as ex:
            print(f'Erro ao obter os hidrômetros de maior consumo. Causa: {ex.args}')
            return self.INTERNAL_SERVER_ERROR

    def monitorar_hidrometro(self):
        """ Método resposável por retornar o endereço da API para obter os dados de um hidrômetro em tempo real """
        if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
            dados = {"endereco": self.__endereco_requisicao}
            dados = json.dumps(dados)
            return dados
        else:
            return self.INTERNAL_SERVER_ERROR
    
    def enviar_tempo_consumo(self, dados: dict):
        dados_json = json.dumps(dados)
        resultado = self.__publish(dados=dados_json, topico=self.TOPIC_TEMPO_CONSUMO)
        if (resultado):
            return self.OK
        else:
            return self.INTERNAL_SERVER_ERROR
    # ----------- Fim Métodos Públicos ----------- #

    # ----------- Métodos Privados ----------- #
    
    def __login_adm(self, usuario: str, senha: str):
        """ Método responsável por validar o login do administrador """
        df = pd.read_csv("adms.csv")       # Abre a lista o arquivo de adms
        if (usuario in df['login'].values and senha in df['senha'].values):   # Verifica se existe um adm com login e senha igual ao passado
            return self.OK                                  # Retorna OK se tiver
        else:   
            return self.NOT_FOUND                           # Retorna um erro se não tiver
    
    def __login_cliente(self):
        """ Método responsável por validar o login do cliente """
        df = pd.read_csv(f"usuarios.csv")
        if (int(self.__matricula) in df['matricula'].values):   # Verifica se existe a matricula passada
            return self.OK                                      # Retorna OK se tiver
        else:
            return self.NOT_FOUND                               # Retorna um erro se não tiver
    
    def __listar_clientes(self):
        """ Método responsável por retornar os clientes cadastrados no sistema """
        try:    
            df = pd.read_csv(f"usuarios.csv")                   # Carrega os usuários do sistema
            df_lista_clientes = df.drop(['cpf','ativo','pendencia','endereco','possivelVazamento'], axis=1, inplace=False).reset_index(drop=True)   #Obtém a lista dos clientes deixando apenas o nome e a matricula
            json_lista_clientes = df_lista_clientes.to_json(orient='index')
            return json_lista_clientes
        except:
            return self.INTERNAL_SERVER_ERROR           # Retorna o erro 
    # ----------- Fim Métodos Privados ----------- #

    # ----------- Métodos Auxiliares ----------- #
    def __get_endereco_requisicao(self):
        """ Obtém o endereço da nevoa referente a matricula solicitada """
        try:
            matricula = int(self.__matricula)
            arquivo = open('nevoas-conectadas.bin', 'rb')
            nevoas = pickle.load(arquivo)
            if(matricula > 0 and matricula < 5):
                endereco = f"http://{nevoas['001']}:5051"
            elif (matricula > 4 and matricula < 9):
                endereco = f"http://{nevoas['002']}:5051"
            elif (matricula > 8 and matricula < 13):
                endereco = f"http://{nevoas['003']}:5051"
            return endereco
        except:
            return self.INTERNAL_SERVER_ERROR
    
    # ------ Métodos MQTT -------
    def __connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.CLIENTE_ID)
        client.on_connect = on_connect
        client.connect(self.HOST, self.PORT)
        return client
    
    def __publish(self, dados, topico):
        """ Envia os dados para o servidor """
        result = self.cliente.publish(topico, dados)
        status = result[0]
        if status == 0:
            print(f"Send `{dados}` to topic `{topico}`")
            return True
        else:
            print(f"Failed to send message to topic {topico}")
            return False

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
            print(f'Endere??o da API: {str(socket.gethostbyname(socket.gethostname()))}')
            print(f'Servidor da API iniciado na porta: {self.__port}')
            while True:
                # Esperando conex??o do cliente
                conexao, cliente = self.__server_socket_tcp.accept()
                self.__colecao_threads[cliente] = threading.Thread(
                    target=self.__requisicao, args=([conexao]))
                self.__colecao_threads[cliente].daemon = True
                self.__colecao_threads[cliente].start()
        except Exception as ex:
            print("Erro no servidor. Causa:", ex.args)
            self.__server_socket_tcp.close()

    def __requisicao(self, conexao):
        """ Trata as requisi????es do recebidas no servidor da API"""
        def enviar_resposta(con, resposta):
            """M??todo para envia a resposta ao cliente"""
            try:
                con.sendall(resposta.encode())
                con.close()
            except Exception as ex:
                print("Erro ao enviar a respota. Causa: ", ex.args)
        
        try:
            request = conexao.recv(1024).decode()                       # Decofica a mensagem recebida
            informacoes_request = self.__decode_requisicao(request)     # Obt??m as informa????es da requisi????o
            if (str(informacoes_request[1]).upper() == self.ADM_VAZAMENTOS or str(informacoes_request[1]).upper() == self.LISTAR_CLIENTES):    # Verifica se a solicita????o foi na rota de obter ??reas poss??veis vazamentos ou listar clientes
                executar = ObterDados('', self.__broker)                                       # Se sim, cria o objeto para obter os dados sem uma matr??cula associada
            elif (str(informacoes_request[1]).upper() == self.LOGIN_ADM or str(informacoes_request[1]).upper() == self.ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO or str(informacoes_request[1]).upper() == self.ADM_DEFINIR_CONSUMO_TEMPO):       # Verifica se a rota requisitada foi de login de adm
                dados = json.loads(informacoes_request[-1])                     # Converte os dados recebidos da requisi????o em dicion??rio
                executar = ObterDados('', self.__broker)                                       # Cria o objeto para obter os dados
            else:                                                               # Sen??o
                dados = json.loads(informacoes_request[-1])                     # Converte os dados recebidos da requisi????o em dicion??rio                      
                executar = ObterDados(dados['matricula'], self.__broker)                       # Cria o objeto para obter os dados com a matr??cula do usu??rio enviado na solicita????o
            print(f"Requisi????o na rota: {informacoes_request[1]}")
            if (informacoes_request[0] == 'GET'):                               # Verifica se o verbo da requisi????o ?? do tipo GET
                if (str(informacoes_request[1]).upper() == self.USER_OBTER_FATURA): # Obter a Fatura do cliente
                    try:
                        resultado = executar.obter_fatura()                                                 # Obt??m o resultado da opera????o
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR and resultado != self.NOT_ACCEPTABLE):  # Se n??o retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                       # Resposta da requisi????o
                            enviar_resposta(conexao, resposta)                                              # Envia a mensagem de resultado da a????o
                        else:                                                                               # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Mensagem de retorno com o erro
                            enviar_resposta(conexao, resposta)                                              # Envia a mensagem de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.ADM_VAZAMENTOS):  # Poss??veis vazamentos de ??gua
                    try:
                        resultado = executar.possiveis_vazamentos()
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):    # Se n??o retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de poss??veis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n"                                      
                            resposta(conexao, resposta)                                                 # Envia o erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.USER_CONSUMO_DATA_HORARIO):   # Consumo por data e hora
                    try:
                        resultado = executar.consumo_data_hora(dados)
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):   # Se n??o retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de poss??veis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n" 
                            enviar_resposta(conexao, resposta)                                          # Envia a mensagem de resultado da a????o 
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.USER_CONSUMO_TOTAL):  # Consumo total
                    try:
                        resultado = executar.consumo_total()
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):   # Se n??o retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de poss??veis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n" 
                            enviar_resposta(conexao, resposta) 
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.USER_CONSUMO_ATUAL):  # Verifica se a solicita????o ?? equivalente a uma rota existente
                    try:
                        resultado = executar.consumo_fatura_atual()
                        if (resultado != self.NOT_FOUND and resultado != self.INTERNAL_SERVER_ERROR):   # Se n??o retornar nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                                   # Retorna o json com locais de poss??veis vazamentos
                            enviar_resposta(conexao, resposta)                                          # Envia a resposta
                        else:                                                                           # Se retornar um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n" 
                            enviar_resposta(conexao, resposta) 
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.LISTAR_CLIENTES): # Verifica se a solicita????o ?? equivalente a uma rota existente
                    try:
                        resultado = executar.listar_clientes()                      # Obt??m a lista de clientes
                        if (resultado != self.INTERNAL_SERVER_ERROR):               # Verifica se n??o ocorreu nenhum erro
                            resposta = f"HTTP/1.1 200\n\n{resultado}"               # Retorna a lista de clientes
                            enviar_resposta(conexao, resposta)                      # Envia a resposta de volta
                        else:                                                       # Se ocorreu um erro
                            resposta = f"HTTP/1.1 {resultado}\n\n"                  # Cria a mensagem de erro
                            enviar_resposta(conexao, resposta)                      # Envia a mensagem de erro
                    except:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.LOGIN_ADM):
                    try:
                        resultado = executar.login_adm(dados['login'], dados['senha'])  # Verifica se os dados correspondem ao adm
                        if (resultado != self.NOT_FOUND):                                # Se sim
                            resposta = f"HTTP/1.1 200\n\n"                              # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:                                                           # Sen??o 
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.LOGIN_USUARIO):
                    try:
                        resultado = executar.login_cliente()                            # Verifica se a matricula corresponde a algum cliente
                        if (resultado != self.NOT_FOUND):
                            resposta = f"HTTP/1.1 200\n\n"                              # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:                                                           # Sen??o 
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO):
                    try:
                        resultado = executar.hidrometros_maior_consumo(dados)           # Obt??m os N hidrometros de maior consumo da nevoa
                        if (resultado != self.INTERNAL_SERVER_ERROR):
                            resposta = f"HTTP/1.1 200\n\n{resultado}"                   # Gera um resposta com OK
                            enviar_resposta(conexao, resposta)                          # Envia a resposta
                        else:
                            resposta = f"HTTP/1.1 {resultado}\n\n"                      # Gera a mensagem de erro
                            enviar_resposta(conexao, resposta)                          # Envia a resposta de erro
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta informando o erro
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da a????o
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
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da a????o
                else:
                    resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n" 
                    enviar_resposta(conexao, resposta) 
            elif (informacoes_request[0] == 'POST'):                                    # Verifica se o verbo da requisi????o ?? do tipo POST
                if (str(informacoes_request[1]).upper() == self.ADM_DESLIGAR_CLIENTE):  # Verifica a rota solicitada ?? equivalente a uma rota existente
                    try:
                        resultado = executar.desligar_cliente(dados)    # Executa a a????o de desligar o cliente e retorna o resultado
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da a????o
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                    except Exception:                                   # Caso a matricula n??o seja fornecida pelo cliente na requisi????o
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.SYS_RECEBER_PAGAMENTO): # Verifica a rota solicitada ?? equivalente a uma rota existente
                    try:
                        resultado = executar.receber_pagamento()        # Quita a fatura e retorna o resultado da a????o
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da a????o
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"         # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.ADM_GERAR_FATURA):    # Gerar Fatura
                    try:
                        resultado = executar.gerar_fatura()                                             # Obt??m o resultado da opera????o
                        resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Resposta da requisi????o
                        enviar_resposta(conexao, resposta)                                              # # Envia a mensagem de resultado da a????o
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.ADM_DEFINIR_CONSUMO_TEMPO):
                    try:
                        resultado = executar.enviar_tempo_consumo(dados)
                        resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Resposta da requisi????o
                        enviar_resposta(conexao, resposta)                                              # # Envia a mensagem de resultado da a????o
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                else:
                    resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}\n\n{informacoes_request[-1]}"   # Envia um mensagem de m??todo n??o suportado e retorna o conte??do da mensagem recebida
                    print(f"Entrou aqui. {str(informacoes_request[1]).upper()}")
                    conexao.sendall(resposta.encode())
                    conexao.close()
            else:
                resposta = f"HTTP/1.1 {self.NOT_IMPLEMENTED}\n\n{informacoes_request[-1]}"      # Envia um mensagem de m??todo n??o suportado e retorna o conte??do da mensagem recebida
                conexao.sendall(resposta.encode())
                conexao.close()
        except ConnectionResetError as ex:
            print("Erro na conex??o do cliente. Causa: ", ex.args)
        except KeyError:
            resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
            enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
        except ValueError:     
                resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}\n\n{informacoes_request[-1]}"
                enviar_resposta(conexao, resposta)
        except Exception as ex:
            print("Erro com a conex??o. Causa: ", ex.args)

    def __decode_requisicao(self, requisicao: str):
        """ Decodifica a requisi????o recebida """
        verbo, _, restante = requisicao.partition(' ')  # Obt??m o verbo da requisi????o
        url, _, _ = restante.partition(' ')             # Obt??m o caminho da requisi????o
        body = re.split(r"\n", requisicao)              # Obt??m o conte??do da requisi????o (body)

        if (verbo == 'GET'):
            return ['GET', url, body[-1]]       # Retorna o verbo, a rota e o conte??do da requisi????o
        elif (verbo == 'POST'):
            return ['POST', url, body[-1]]      # Retorna o verbo, a rota e o conte??do da requisi????o
        else:
            return ['UNKNOWN', url, body[-1]]   # Retorna o verbo desconhecido, a rota e o conte??do da requisi????o

class ObterDados():
    """ Classe para obter os dados das solicita????es da API """
    LIGAR =     "2"         # Constante para o comando de ligar um hidr??metro
    DESLIGAR =  "1"         # Constante para o comando de desligar um hidr??metro

    #Constantes 
    TOPIC = 'hidrometro/acao/'  #T??pico para desligar o cliente - inserir matricula e mudar para a nevoa

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
    HOST = ''                   # Endere??o do broker
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


    # ----------- M??todos P??blicos ----------- #
    def desligar_cliente(self, dados: dict):
        """ M??todo respons??vel por bloquear hidr??metro de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                resposta = requests.post(self.__endereco_requisicao + self.ADM_DESLIGAR_CLIENTE, json=dados)    # Solicita o desligamento do cliente para a n??voa respons??vel pelo mesmo
                return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR

    
    def receber_pagamento(self):
        """ M??todo respons??vel por receber o pagamento de uma fatura de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.post(self.__endereco_requisicao + self.SYS_RECEBER_PAGAMENTO, json=dados)   # Envia informa????o de fatura paga para n??voa respons??vel pelo cliente
                return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR

    def possiveis_vazamentos(self):
        """ M??todo respons??vel por obter os locais com poss??veis vazamentos """
        try:
            arquivo = open('nevoas-conectadas.bin', 'rb')       # Abre o arquivo de n??voas conectadas
            nevoas = pickle.load(arquivo)                       # Obt??m as n??voas conectadas em um dicion??rio
            arquivo.close()                                     # Fecha o arquivo de n??voas conectadas
            dicionario_vazamentos = {}                          
            indice = 0
            for endereco in nevoas.values():                    # Percorre o dicion??rio de n??voas conectadas obtendo os endere??os das n??voas
                resposta = requests.get(f'http://{endereco}:5051' + self.ADM_VAZAMENTOS)    # Solicita os poss??veis vazamentos de cada n??voa
                if (resposta.status_code == 200):                                           # Verifica se recebeu os resultados corretamente
                    dados = json.loads(resposta.content.decode())                           # Converte os dados recebidos em json
                    for dado in dados.values():                                             # Percorre cada dado de poss??vel vazamento recebido
                        dicionario_vazamentos[indice] = dado                                # Adiciona os poss??veis vazamentos a um dicion??rio
                        indice += 1                                                         # Soma 1 ao indice              
            vazamentos_json = json.dumps(dicionario_vazamentos)                             # Converte o dicion??rio com todos os poss??veis vazamentos de todas as n??voas para json
            return vazamentos_json                                                          # Retonar os poss??veis vazamentos como json
        except Exception as ex:                                                             # Se ocorrer algum erro
            print(f'Erro ao obter os poss??veis vazamentos. Causa: {ex.args}')               # Informa a causa
            return self.INTERNAL_SERVER_ERROR                                               # Retorna um erro
    
    def consumo_data_hora(self, dados):
        """ M??todo respons??vel por retornar o consumo de um cliente em um per??odo de tempo """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                resposta = requests.get(self.__endereco_requisicao + self.USER_CONSUMO_DATA_HORARIO, json=dados)       # Requisita o consumo do cliente no intervalo definido de acordo com a n??voa que se encontra
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR

    def consumo_total(self):
        """ M??todo respons??vel por retornar o consumo total de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.get(self.__endereco_requisicao + self.USER_CONSUMO_TOTAL, json=dados)   # Requisita o consumo total do cliente de acordo com a n??voa que se encontra
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR
    def consumo_fatura_atual(self):
        """ M??todo respons??vel por retornar o consumo da fatura atual de um cliente """
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.get(self.__endereco_requisicao + self.USER_CONSUMO_ATUAL, json=dados)   # Requisita o consumo da fatura atual do cliente de acordo com a n??voa que se encontra
                if (resposta.status_code == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR
    
    def gerar_fatura(self):
        """ M??todo respons??vel por gerar a fatura de um cliente"""
        try:
            if (self.__endereco_requisicao != self.INTERNAL_SERVER_ERROR):
                dados = {'matricula': self.__matricula}
                resposta = requests.post(self.__endereco_requisicao + self.ADM_GERAR_FATURA, json=dados)    # Requisita a fatura do cliente de acordo com a n??voa que se encontra
                if (resposta == 200):
                    return resposta.content.decode()
                else:
                    return str(resposta.status_code)
            else:
                return self.INTERNAL_SERVER_ERROR
        except:
            return self.INTERNAL_SERVER_ERROR
    
    def obter_fatura(self):
        """ M??todo para obter a fatura do cliente """
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
        """ M??todo para efetuar o login do administrador """
        return self.__login_adm(login, senha)

    def login_cliente(self):
        """ M??todo para efetuar o login do cliente """
        return self.__login_cliente()
    
    def listar_clientes(self):
        """ M??todo para listar os clientes do sistema """
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
                req = requests.Request('GET', f'http://{endereco}:5000{self.ADM_OBTER_HIDROMETROS_MAIOR_CONSUMO}/{quantidade}') # Define a requisi????o
                r = req.prepare()                                                                                               # Prepara a requisi????o
                s = requests.Session()                                                                                          # Inicia uma sess??o
                resposta = s.send(r)                                                                                            # Envia a requisi????o para API
                s.close()                                                                                                       # Fecha a sess??o
                if (resposta.status_code == 200):                                                                           # Verifica se recebeu corretamente       
                    n_maiores = json.loads(resposta.content.decode())                                                       # Converte json recebido em dicionario
                    for dado in n_maiores.values():                                                                         # Percorre por meio dos valores o dicionario do n maiores consumos da nevoa
                        dicionario_n_maiores[indice] = dado                                                                 # Adiciona o valor a um dicion??rio auxiliar
                        indice += 1                                                                     # Soma 1 ao indice
            total_n_maiores = json.dumps(dicionario_n_maiores)                                          # Converte o dicionario com os n maiores valores de cada nevoa em um json
            df = pd.read_json(total_n_maiores, orient='index')                                          # Carrega um dataframe a partir do json com os n maiores valores de cada nevoa
            resultado_n_maiores = df.nlargest(quantidade, ['consumo'])                                  # Obt??m os n maiores valores de consumo
            json_n_maiores = resultado_n_maiores.to_json(orient='index')                                # Converte os n maiores valores de consumo em um json para enviar a resposta
            return json_n_maiores                                           # Retorna o json com os maiores consumo - as matriculas est??o no formato int (sem os zeros a frente)
        except Exception as ex:
            print(f'Erro ao obter os hidr??metros de maior consumo. Causa: {ex.args}')
            return self.INTERNAL_SERVER_ERROR

    def monitorar_hidrometro(self):
        """ M??todo respos??vel por retornar o endere??o da API para obter os dados de um hidr??metro em tempo real """
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
    # ----------- Fim M??todos P??blicos ----------- #

    # ----------- M??todos Privados ----------- #
    
    def __login_adm(self, usuario: str, senha: str):
        """ M??todo respons??vel por validar o login do administrador """
        df = pd.read_csv("adms.csv")       # Abre a lista o arquivo de adms
        if (usuario in df['login'].values and senha in df['senha'].values):   # Verifica se existe um adm com login e senha igual ao passado
            return self.OK                                  # Retorna OK se tiver
        else:   
            return self.NOT_FOUND                           # Retorna um erro se n??o tiver
    
    def __login_cliente(self):
        """ M??todo respons??vel por validar o login do cliente """
        df = pd.read_csv(f"usuarios.csv")
        if (int(self.__matricula) in df['matricula'].values):   # Verifica se existe a matricula passada
            return self.OK                                      # Retorna OK se tiver
        else:
            return self.NOT_FOUND                               # Retorna um erro se n??o tiver
    
    def __listar_clientes(self):
        """ M??todo respons??vel por retornar os clientes cadastrados no sistema """
        try:    
            df = pd.read_csv(f"usuarios.csv")                   # Carrega os usu??rios do sistema
            df_lista_clientes = df.drop(['cpf','ativo','pendencia','endereco','possivelVazamento'], axis=1, inplace=False).reset_index(drop=True)   #Obt??m a lista dos clientes deixando apenas o nome e a matricula
            json_lista_clientes = df_lista_clientes.to_json(orient='index')
            return json_lista_clientes
        except:
            return self.INTERNAL_SERVER_ERROR           # Retorna o erro 
    # ----------- Fim M??todos Privados ----------- #

    # ----------- M??todos Auxiliares ----------- #
    def __get_endereco_requisicao(self):
        """ Obt??m o endere??o da nevoa referente a matricula solicitada """
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
    
    # ------ M??todos MQTT -------
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

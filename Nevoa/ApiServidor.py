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
            print("Erro no servidor", ex.args)
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
            request = conexao.recv(4096).decode()                       # Decofica a mensagem recebida
            informacoes_request = self.__decode_requisicao(request)     # Obt??m as informa????es da requisi????o
            if (str(informacoes_request[1]).upper() == self.ADM_VAZAMENTOS or str(informacoes_request[1]).upper() == self.LISTAR_CLIENTES):    # Verifica se a solicita????o foi na rota de obter ??reas poss??veis vazamentos ou listar clientes
                executar = ObterDados('', self.__broker)                                       # Se sim, cria o objeto para obter os dados sem uma matr??cula associada
            else:                                                               # Sen??o
                dados = json.loads(informacoes_request[-1])                     # Converte os dados recebidos da requisi????o em dicion??rio                      
                executar = ObterDados(str(dados['matricula']).zfill(3), self.__broker)         # Cria o objeto para obter os dados com a matr??cula do usu??rio enviado na solicita????o
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
                        enviar_resposta(conexao, resposta)                              # Envia a mensagem de resultado da a????o
                else:
                    resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n" 
                    enviar_resposta(conexao, resposta) 
            elif (informacoes_request[0] == 'POST'):                    # Verifica se o verbo da requisi????o ?? do tipo POST
                if (str(informacoes_request[1]).upper() == self.ADM_DESLIGAR_CLIENTE):  # Verifica a rota solicitada ?? equivalente a uma rota existente
                    try:
                        resultado = executar.desligar_cliente(dados)    # Executa a a????o de desligar o cliente e retorna o resultado
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da a????o
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                    except Exception:                                    # Caso a matricula n??o seja fornecida pelo cliente na requisi????o
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.SYS_RECEBER_PAGAMENTO): # Verifica a rota solicitada ?? equivalente a uma rota existente
                    try:
                        resultado = executar.receber_pagamento()   # Quita a fatura e retorna o resultado da a????o
                        resposta = f"HTTP/1.1 {resultado}\n\n"          # mensagem de resultado da a????o
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
                elif (str(informacoes_request[1]).upper() == self.ADM_GERAR_FATURA): # Gerar Fatura
                    try:
                        resultado = executar.gerar_fatura()                                             # Obt??m o resultado da opera????o
                        resposta = f"HTTP/1.1 {resultado}\n\n"                                          # Resposta da requisi????o
                        enviar_resposta(conexao, resposta)                                              # # Envia a mensagem de resultado da a????o
                    except Exception:
                        resposta = f"HTTP/1.1 {self.INTERNAL_SERVER_ERROR}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
                        enviar_resposta(conexao, resposta)                          # Envia a mensagem de resultado da a????o
                else:
                    resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}\n\n{informacoes_request[-1]}"   # Envia um mensagem de m??todo n??o suportado e retorna o conte??do da mensagem recebida
                    conexao.sendall(resposta.encode())
                    conexao.close()
            else:
                resposta = f"HTTP/1.1 {self.NOT_IMPLEMENTED}\n\n{informacoes_request[-1]}"   # Envia um mensagem de m??todo n??o suportado e retorna o conte??do da mensagem recebida
                conexao.sendall(resposta.encode())
                conexao.close()
        except ConnectionResetError as ex:
            print("Erro na conex??o do cliente. Causa: ", ex.args)
        except KeyError:
            resposta = f"HTTP/1.1 {self.NOT_FOUND}\n\n"     # Envia a mensagem de resposta para o cliente informando o erro de matricula n??o encontrada
            enviar_resposta(conexao, resposta)              # Envia a mensagem de resultado da a????o
        except ValueError as ex:
            print(f'value error. causa {ex.args}')     
            resposta = f"HTTP/1.1 {self.NOT_ACCEPTABLE}"
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
    TOPIC = 'hidrometro/acao/'  # T??pico para desligar o cliente - inserir matricula e mudar para a nevoa
    HOST = ''                   # Endere??o do broker
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
        

    # ----------- M??todos P??blicos ----------- #
    def desligar_cliente(self, dados: dict):
        """ M??todo respons??vel por bloquear hidr??metro de um cliente """
        return self.__bloquear_hidrometro(dados)

    
    def receber_pagamento(self):
        """ M??todo respons??vel por receber o pagamento de uma fatura de um cliente """
        return self.__conta_paga()

    def possiveis_vazamentos(self):
        """ M??todo respons??vel por obter os locais com poss??veis vazamentos """
        try:
            df = pd.read_csv(f"usuarios.csv")
            return self.__obter_alertas_vazamento(df)
        except FileNotFoundError:
            return self.NOT_FOUND
    
    def consumo_data_hora(self, dados):
        """ M??todo respons??vel por retornar o consumo de um cliente em um per??odo de tempo """
        return self.__obter_consumo_data(dados)

    def consumo_total(self):
        """ M??todo respons??vel por retornar o consumo total de um cliente """
        return self.__obter_consumo_total()

    def consumo_fatura_atual(self):
        """ M??todo respons??vel por retornar o consumo da fatura atual de um cliente """
        return self.__obter_consumo_fatura()
    
    def gerar_fatura(self):
        """ M??todo respons??vel por gerar a fatura de um cliente"""
        try:
            df_consumo = pd.read_csv(f"{self.__matricula}.csv", sep=',')                                    # Carrega o banco de dados de consumo da matricula (usu??rio) especificada
            df_dados = pd.read_csv("usuarios.csv", sep=",")                                                 # Carrega o banco de dados de usu??rios
            indice_usuario = (df_dados.index[df_dados['matricula'] == int(self.__matricula)]).tolist()[0]   # Obt??m o indice que refencia o usu??rio no dataframe de usu??rios
            if (df_dados.iloc[indice_usuario]['pendencia'] == True):                                             # Verifica se o usu??rio tem faturas em aberto
                return self.NOT_ACCEPTABLE                                                                  # Se tiver faturas em aberto, n??o ?? poss??vel gerar uma nova fatura ainda e retorna um erro
            else:
                fatura_json = self.__criar_fatura(df_consumo, df_dados)                                     # Gera o Json com os dados da fatura
                df_consumo.at[0, 'contaGerada'] = True                                                      # Identifica que o usu??rio tem uma fatura gerada
                df_consumo.at[0, 'pago'] = False                                                            # Identifica que o usu??rio ainda n??o pagou a fatura (visto que a conta acabou de criada)
                df_dados.at[indice_usuario, 'pendencia'] = True                                             # Identifica que o usu??rio tem uma fatura em aberto

                df_consumo.to_csv(f"{self.__matricula}.csv", sep=',', index=False)                          # Salva os dados de consumo como csv
                df_dados.to_csv("usuarios.csv", sep=",", index=False)                                       # Salva os dados dos usu??rios como csv
                return fatura_json                                                                          # Retorna a fatura
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception as ex:
            print("Erro ao gerar fatura. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR
    
    def obter_fatura(self):
        """ M??todo para obter a fatura do cliente """
        try:
            df_dados = pd.read_csv("usuarios.csv", sep=",")                                                 # Carrega o banco de dados de usu??rios
            indice_usuario = (df_dados.index[df_dados['matricula'] == int(self.__matricula)]).tolist()[0]   # Obt??m o indice que refencia o usu??rio no dataframe de usu??rios
            if (df_dados.iloc[indice_usuario]['pendencia'] == True):                                        # Verifica se o usu??rio tem faturas em aberto
                with open(f'{self.__matricula}.json', 'r') as fatura_file:                                  # Abre o arquivo
                    fatura = json.load(fatura_file)                                                         # Carrega o arquivo em json da fatura
                fatura = json.dumps(fatura)                                                                 # Transforma o json para string em formato json
                return fatura                                                                               # Retorna a fatura em json
            else:
                return self.NOT_ACCEPTABLE                                                                  # Retorna um erro indicando que ainda n??o h?? fatura aberta para o cliente
        except FileNotFoundError:
            return self.NOT_FOUND                                                                           # Retorna um erro indicando que a matricula do cliente n??o foi encontrada
        except Exception as ex:
            print("Erro ao gerar fatura. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR
    
    def listar_clientes(self):
        """ M??todo para listar os clientes do sistema """
        return self.__listar_clientes()
    
    def hidrometros_maior_consumo(self, dados: dict):
        """ Obt??m os n hidr??metros de maior consumo """
        try:
            quantidade = int(dados['quantidade'])
            df = pd.read_csv('consumo-clientes.csv', sep=',')
            n_maiores = df.nlargest(quantidade, ['consumo']).reset_index(drop=True)
            json_maiores = n_maiores.to_json(orient='index')
            return json_maiores
        except Exception:
            return self.INTERNAL_SERVER_ERROR
    
    def monitorar_hidrometro(self):
        """ M??todo respons??vel por retornar os dados do hidr??metro solicitado em menor tempo """
        try:
            df = pd.read_csv('consumo-clientes.csv', sep=',')
            dados_hidrometro = df[df['matricula'] == int(self.__matricula)]
            if (dados_hidrometro.empty):
                return self.NOT_FOUND
            else:
                dados_json = dados_hidrometro.to_json(orient='index')       # Retorna um json contendo um valor e uma chave - sendo o valor o dicionario com as informa????es do cliente
                return dados_json
        except Exception:
            return self.INTERNAL_SERVER_ERROR
    # ----------- Fim M??todos P??blicos ----------- #

    # ----------- M??todos Privados ----------- #
    def __criar_fatura(self, df_consumo: DataFrame, df_dados: DataFrame):
        """ M??todo respons??vel por criar formatar os dados fatura do cliente """
        try:
            cliente = (df_dados.loc[df_dados['matricula'] == int(df_consumo.iloc[0]['matricula'])]).reset_index(drop=True)  # Obt??m a linha do dataframe que pertence aos dados do usu??rio
            fatura = {
                'consumoFatura':    str(df_consumo.iloc[0]['consumoFatura']),   # Obt??m o consumo da fatura
                'valor':            str(df_consumo.iloc[0]['valor']),           # Obt??m o valor da fatura
                'dataLeitura':      str(df_consumo.iloc[0]['dataHora'])[0:10],  # Gera uma string com a data e hor??rio exato de cria????o da fatura
                'consumoTotal':     str(df_consumo.iloc[0]['consumo']),         # Obt??m o consumo total do cliente (valor mostrado no hidr??metro na hora da leitura) 
                'nomeUsuario':      str(df_consumo.iloc[0]['nomeUsuario']),     # Obt??m o nome de usu??rio (cliente) da fatura
                'cpf':              str(cliente.iloc[0]['cpf']),                # obt??m o cpf do cliente
                'dataFatura':       date.today().strftime("%d/%m/%Y"),          # Obt??m a hora da fatura
                'dataVencimento':   (date.today() + timedelta(days=10)).strftime("%d/%m/%Y"),   # Obt??m a data de vencimento da fatura
                'matricula':        self.__matricula                            # Obt??m a matr??cula
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
        """ Retorna um json com os endere??os que h?? um poss??vel vazamento """
        try:
            found = df_usuarios['possivelVazamento'] == True    # Procura os usu??rios que tem a flag de poss??veis vazamentos
            df_vazamentos = ((df_usuarios[found]).drop(['matricula', 'nome', 'cpf', 'ativo', 'pendencia', 'possivelVazamento'], axis=1, inplace=False)).reset_index(drop=True) # Adiciona as informa????es dos usu??rios em uma dataframe
            json_vazamentos = df_vazamentos.to_json(orient='index') # Cria um JSON com os endere??os com poss??veis vazamentos
            return json_vazamentos  # Retorna o JSON com as regi??es de poss??veis vazamentos
        except Exception as ex:     # Caso ocorra algum erro
            print("Erro ao obter os alertas de vazamento. Causa: ", ex.args)
            return self.INTERNAL_SERVER_ERROR             # Retorna o erro

    def __conta_paga(self):
        """ Identifica que a conta foi paga e quita a conta do cliente no sistema"""
        try:
            df_usuarios = pd.read_csv("usuarios.csv", sep=',')
            indice_usuario = self.__obter_indice_usuario(df_usuarios, self.__matricula)   # Obt??m o indice do usu??rio na lista de clientes do sistema
            if (bool(df_usuarios.iloc[indice_usuario]['pendencia'])):       # Verifica se o usu??rio tem alguma fatura em aberto
                df_usuarios.at[indice_usuario, 'pendencia'] = False         # Retira a pendencia do cliente                                               
                os.remove(f'{self.__matricula}.json')                       # Se existir apaga o arquivo
                if (not bool(df_usuarios.iloc[indice_usuario]['ativo'])):   # Verifica se o cliente est?? com o fornecimento de ??gua suspenso
                    if (self.__enviar_comando_hidrometro(self.LIGAR, self.__matricula)):   # Ligar o hidr??metro desativado
                        df_usuarios.at[indice_usuario, 'ativo'] = True                                              # Identifica que o hidr??metro do cliente est?? ativo novamente
                        df_usuarios.at[indice_usuario, 'pendencia'] = False
                        df_usuarios.to_csv('usuarios.csv', sep=',', index=False)                                # Salva as modifica????es no arquivo
                        return self.OK
                    else:
                        return self.INTERNAL_SERVER_ERROR 
                else:
                    df_usuarios.at[indice_usuario, 'pendencia'] = False
                    df_usuarios.to_csv('usuarios.csv', sep=',', index=False)                                  # Salva as modifica????es no arquivo
                    return self.OK
            else:   # Se n??o tiver fatura em aberto
                return self.NOT_ACCEPTABLE
        except FileNotFoundError:
            return self.NOT_FOUND 

    def __bloquear_hidrometro(self, dados: dict):
        """ M??todo respons??vel por bloquear um hidr??metro """
        try:
            df_usuarios = pd.read_csv("usuarios.csv", sep=',')
            indice_usuario = self.__obter_indice_usuario(df_usuarios, self.__matricula)     # Obt??m o indice do usu??rio na lista de clientes do sistema 
            if (bool(df_usuarios.iloc[indice_usuario]['pendencia'])):                       # Verifica se o usu??rio tem uma conta em aberto
                if(self.__enviar_comando_hidrometro(self.DESLIGAR, self.__matricula)):
                    df_usuarios.at[indice_usuario, 'ativo'] = False                         # Seta cliente como desligado
                    df_usuarios.to_csv('usuarios.csv', sep=',', index=False)                # Salva a modifica????o feita no arquivo
                    return self.OK
                else: return self.INTERNAL_SERVER_ERROR                                                                 
            else:
                return self.NOT_ACCEPTABLE
        except FileNotFoundError:
            return self.NOT_FOUND
        except Exception:
            return self.INTERNAL_SERVER_ERROR

    # Funcionalidade implementada, mas n??o dispon??vel para uso no momento
    def __desbloquear_hidrometro(self, dados: dict):
        """ M??todo respons??vel por desbloquear um hidr??metro manualmente pelo administrador"""
        try:
            df_usuarios = pd.read_csv("usuarios.csv", sep=',')
            indice_usuario = self.__obter_indice_usuario(df_usuarios, dados['matricula'])   # Obt??m o indice do usu??rio na lista de clientes do sistema 
            if (not bool(df_usuarios.iloc[indice_usuario]['ativo'])):                       # Verifica se o usu??rio est?? desativado
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
        """ M??todo respons??vel por obter o consumo de um cliente em uma data espec??fica"""
        try:
            df_dados = pd.read_csv(f"{self.__matricula}.csv")
            df_dados['dataHora'] = pd.to_datetime(df_dados.dataHora)
            data_inicial = datetime.strptime(dados['dataInicial'], '%Y-%m-%d-%H:%M:%S') #'%Y-%m-%d-%H:%M:%S'
            data_final = datetime.strptime(dados['dataFinal'], '%Y-%m-%d-%H:%M:%S')
            df_consumo_data = df_dados[(data_inicial <= df_dados['dataHora']) & (data_final > df_dados['dataHora'])]
            conusmo_data = float(df_consumo_data.at[df_consumo_data.index[0], 'consumo']) - float(df_consumo_data.at[df_consumo_data.index[-1], 'consumo'])  # Obt??m o valor de consumo no per??do especificado
            resposta = {'consumoData': conusmo_data}
            resposta = json.dumps(resposta)     # Converte a resposta para JSON
            return resposta
        except FileNotFoundError:   # Caso n??o encontre o cliente
            return self.NOT_FOUND
        except IndexError:          # Caso n??o tenha registro de consumo nas datas
            return self.NOT_FOUND
        except Exception as e:      # Caso ocorra algum outro erro
            print(f'Erro ao obter o consumo da data especificada. Causa: {e.args}')
            return self.INTERNAL_SERVER_ERROR
    
    def __obter_consumo_fatura(self):
        """ M??todo respons??vel por obter o consumo da atual fatura de um cliente"""
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
        """ M??todo respons??vel por obter o consumo da total de um cliente"""
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
        """ M??todo respons??vel por retornar os clientes cadastrados no sistema """
        try:    
            df = pd.read_csv(f"usuarios.csv")                   # Carrega os usu??rios do sistema
            df_lista_clientes = df.drop(['cpf','ativo','pendencia','endereco','possivelVazamento'], axis=1, inplace=False).reset_index(drop=True)   #Obt??m a lista dos clientes deixando apenas o nome e a matricula
            json_lista_clientes = df_lista_clientes.to_json(orient='index')
            return json_lista_clientes
        except:
            return self.INTERNAL_SERVER_ERROR           # Retorna o erro 
    
    # ----------- M??todos Auxiliares ----------- #
    def __obter_indice_usuario(self, dataframe: DataFrame, matricula: str):
        """ M??todo respons??vel por retornar o indice do usu??rio no DataFrame """
        return (dataframe.index[dataframe['matricula'] == int(matricula)]).tolist()[0]
    # ----------- Fim M??todos Auxiliares ----------- #

    def __enviar_comando_hidrometro(self, comando: str, matricula: str):
        """ M??todo respons??vel por enviar comandos para um hidr??metro """
        self.__conectar()                               # Conecta ao broker
        resultado = self.__publish(comando, matricula)  # Envia a mensagem
        self.cliente.disconnect()                       # Desconecta do broker ap??s enviar a mensagem
        return resultado                                # Envia o resultado da opera????o de enviar mensagem

    
    def __conectar(self):                            
        """ M??todo para efetuar a conex??o """
        self.cliente = self.__connect_mqtt()    # Conecta com o broker
        

    def __connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:         # Se conseguiu conectar com o broker
                pass
            else:
                print("Failed to connect, return code %d\n", rc)        # Sen??o conseguiu conectar com o broker, retorna o erro

        client = mqtt_client.Client(self.CLIENTE_ID)
        client.on_connect = on_connect
        client.connect(self.HOST, self.PORT)                            # Conex??o com o broker
        return client
    
    def __publish(self, dados, matricula):
        """ Envia os dados para o servidor """
        try:
            result = self.cliente.publish(self.TOPIC + matricula, dados)        # Envia os dados para o hidr??metro no t??pico relacionado ao hidr??metro
            status = result[0]
            if status == 0:
                print(f"Send `{dados}` to topic `{self.TOPIC+matricula}`")
                return True                                                     # Caso a mensagem tenha sido enviada para o hidr??metro com sucesso
            else:
                print(f"Failed to send message to topic {self.TOPIC+matricula}")
                return False                                                    # Caso a mensagem n??o tenha sido enviada para o hidr??metro
        except:
            return False                                                        # Caso ocorra alguma erro
    
    # ----------- Fim M??todos Privados ----------- #
    # ----------- Fim M??todos Auxiliares ----------- #
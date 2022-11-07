# -*- coding: utf-8 -*-
import pickle
from paho.mqtt import client as mqtt_client
import random
import numpy as np
import json

# portas: 5006 a 5009

class ReceiveServidor():

    # ------- Tópicos --------
    TOPIC_MEDIA_NEVOA_RECEBER = 'nuvem/dados/media/nevoa'
    TOPIC_NEVOAS_CONECTADAS = 'nuvem/sistema/nevoas/conectada'
    TOPIC_NUVEM_MEDIA_ENVIAR = 'nuvem/dados/media/total'

    TOPICS = [(TOPIC_MEDIA_NEVOA_RECEBER, 2), (TOPIC_NEVOAS_CONECTADAS, 2), (TOPIC_NUVEM_MEDIA_ENVIAR, 2)]
    # ----- Constante do MQTT -----------
    HOST = ''    # Endereço do broker   - broker.emqx.io
    PORT =  1883               # Porta do broker - 1883
    TOPIC = 'dados/hidrometro/servidor'
    CLIENTE_ID = f'python-mqtt-{random.randint(0, 1000)}'

    # ------- Cliente MQTT ----------
    cliente = None

    # ------- Listas e dicionários ---------------
    __dict_nevoas_conectadas = {}
    __medias_nevoas = {}

    def __init__(self, broker):
        self.HOST = broker
        self.start()


    def start(self):
        """ Inicia o servidor """
        self.cliente = self.__connect_mqtt()
        self.__subscribe(self.cliente)
        self.cliente.loop_start()
        
# --------- Métodos privados ----------
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

    def __subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            print(f"Received {msg.payload.decode('utf-8')} from {msg.topic} topic")
            if (msg.topic == self.TOPIC_MEDIA_NEVOA_RECEBER):
                dados_json = json.loads(msg.payload.decode("utf-8"))          # Converte a string no padrão Json em dicionário
                self.__receber_media(dados_json)
            elif (msg.topic == self.TOPIC_NEVOAS_CONECTADAS):
                nevoas = json.loads(msg.payload.decode("utf-8"))
                self.__nevoas_conectadas(nevoas)
        
        client.subscribe(self.TOPICS)    
        client.on_message = on_message
    
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

    def __receber_media(self, dados: dict):
        self.__medias_nevoas[dados['identificacao']] = dados['media']   # Atribui a média do nevoa a sua chave correspondente do dicionário

        self.__calcular_media()                                         # Chama a função de cálculo de média para identificar se já é possível calcular a média
    
    def __nevoas_conectadas(self, nevoas: dict):
        """ Reconhece as nevoas conectadas a nuvem """
        identificacao = nevoas['identificacao']
        if (identificacao not in self.__dict_nevoas_conectadas.keys()):
            self.__dict_nevoas_conectadas[identificacao] = nevoas['endereco']       # Obtém o endereço de IP da nevoa
            self.__medias_nevoas[identificacao] = np.NaN                            # Adiciona a nevoa a lista de nevoas
            try:
                arquivo = open('nevoas-conectadas.bin', "wb")               # Abre o arquivo - usado para compartilha a informação com o objeto da api
                pickle.dump(self.__dict_nevoas_conectadas, arquivo)         # Adiciona o consumo ao arquivo
                arquivo.close()                             # Fecha o arquivo
            except Exception as ex:                         # Se ocorrer algum erro
                print("Erro ao gravar no arquivo. Causa: ", ex.args)
    
    def __limpar_lista_nevoas_conectadas(self):
        """ Limpa a lista de clientes conectados - isso é feito para verificar novamente se todos as nevoas estã conectadas"""
        self.__dict_nevoas_conectadas.clear()
    
    def __calcular_media(self):
        """ Efetua o calculo da média das médias recebidas das nevoas - esse calculo é feito apenas quando todos os dados forem recebidos de todas as nevoas """
        medias = self.__medias_nevoas.values()                  # Obtém a lista com a média de cada nevoa
        if (np.NaN not in medias):                              # Verifica se todas as médias foram recebidas das nevoas
            t_media = list(filter(lambda val: val >= 0, medias))      # Verifica se há elementos menor que 0 e remove, ou seja, elementos que indiquem que uma nevoa não tem media
            if (len(t_media) > 0):
                media = np.average(t_media)                   # Calcula a média das médias recebidas
                self.__enviar_media(media)
                for key in self.__medias_nevoas.keys():             # Remove as medias antigas para o cálculo de uma nova média
                    self.__medias_nevoas[key] = np.NaN              # Atribui um valor não numérico 
            else:
                self.__enviar_media(-1)                             # Envia um valor negativo indicando que não há uma média
    def __enviar_media(self, media):
        self.__publish(media, self.TOPIC_NUVEM_MEDIA_ENVIAR)
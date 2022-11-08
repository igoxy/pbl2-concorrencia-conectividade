# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import threading
from Server import Server
import pandas as pd
from ApiServidor import ApiServidor


def carregar_consumo():
    """ Carrega último valor de consumo de cada cliente """
    try:
        df = pd.read_csv('consumo-clientes.csv', sep=',')       # DataFrame para aramazenar o último consumo dos clientes
    except FileNotFoundError:
        data = {'matricula': ['009', '010', '011', '012'],      # Matrícula dos clientes da nevoa
                'consumo':  [np.NaN, np.NaN, np.NaN, np.NaN],    # Valor de consumo inicial - nenhum tem nada
                'vazao':    [np.NaN, np.NaN, np.NaN, np.NaN]
        }
        df = pd.DataFrame(data)                                 # DataFrame para aramazenar o último consumo dos clientes
        df.to_csv('consumo-clientes.csv', sep=',', index=False)
    
    return df

def add_usuarios():
    """ Função para carregar os usuários do sistema """
    try:
        df = pd.read_csv('usuarios.csv', sep=',')
    except:
        """ Criar os usuários do sistema """
        usuarios = [['009', 'fulano9', '290.578.880-17', True, False, 'Rua I - Campo Limpo - 2', False],
                ['010', 'fulano10', '755.403.450-29', True, False, 'Rua J - Campo Limpo - 2', False],
                ['011', 'fulano11', '428.243.360-48', True, False, 'Rua K - Campo Limpo - 2', False],
                ['012', 'fulano12', '094.717.170-35', True, False, 'Rua L - Campo Limpo - 2', False]]
        df = pd.DataFrame(usuarios, columns=['matricula', 'nome', 'cpf', 'ativo', 'pendencia', 'endereco', 'possivelVazamento'])
        df.to_csv('usuarios.csv', sep=',', index=False)

add_usuarios() # Criar os usuários do sistema
ult_consumo_clientes = carregar_consumo()   # Carrega o ultimo consumo dos usuarios da nevoa

nome_nevoa = input("Insira a identificação da nevoa: ")
broker = str(input("Insira o endereço do broker: "))

servidor = Server(consumo_clientes=ult_consumo_clientes, identificacao_nevoa=nome_nevoa, broker=broker)
calculo_media = threading.Thread(target=servidor.calcular_media)

api = ApiServidor('', 5051, broker)             # Cria o sevidor da API
servidor_api = threading.Thread(target=api.start) 
flask_app = api.app
servidor_flask= threading.Thread(target=api.run_api_flask, args=([flask_app]))

servidor_api.start()
calculo_media.start()       # Inicia a thread para calcular a média
servidor_flask.start()
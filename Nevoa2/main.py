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
        data = {'matricula': ['005', '006', '007', '008'],      # Matrícula dos clientes da nevoa
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
        usuarios = [['005', 'fulano5', '335.703.470-01', True, False, 'Rua E - Campo Limpo - 2', False],
                ['006', 'fulano6', '824.730.270-56', True, False, 'Rua F - Campo Limpo - 2', False],
                ['007', 'fulano7', '300.287.450-78', True, False, 'Rua G - Campo Limpo - 2', False],
                ['008', 'fulano8', '757.490.350-69', True, False, 'Rua H - Campo Limpo - 2', False]]
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
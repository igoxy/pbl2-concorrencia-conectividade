# -*- coding: utf-8 -*-
import threading
from ReceiveServidor import ReceiveServidor
import pandas as pd
from ApiNuvem import ApiNuvem

def add_usuarios():
    """ Função para carregar os usuários do sistema """
    try:
        df = pd.read_csv('usuarios.csv', sep=',')
    except:
        """ Criar os usuários do sistema """
        usuarios = [['001', 'fulano1', '929.124.250-00', True, False, 'Rua A - Campo Limpo - 2', False],
                ['002', 'fulano2', '773.928.570-61', True, False, 'Rua B - Campo Limpo - 2', False],
                ['003', 'fulano3', '827.086.480-39', True, False, 'Rua C - Campo Limpo - 2', False],
                ['004', 'fulano4', '287.613.940-50', True, False, 'Rua D - Campo Limpo - 2', False],
                ['005', 'fulano5', '335.703.470-01', True, False, 'Rua E - Campo Limpo - 2', False],
                ['006', 'fulano6', '824.730.270-56', True, False, 'Rua F - Campo Limpo - 2', False],
                ['007', 'fulano7', '300.287.450-78', True, False, 'Rua G - Campo Limpo - 2', False],
                ['008', 'fulano8', '757.490.350-69', True, False, 'Rua H - Campo Limpo - 2', False],
                ['009', 'fulano9', '290.578.880-17', True, False, 'Rua I - Campo Limpo - 2', False],
                ['010', 'fulano10', '755.403.450-29', True, False, 'Rua J - Campo Limpo - 2', False],
                ['011', 'fulano11', '428.243.360-48', True, False, 'Rua K - Campo Limpo - 2', False],
                ['012', 'fulano12', '094.717.170-35', True, False, 'Rua L - Campo Limpo - 2', False]]
        df = pd.DataFrame(usuarios, columns=['matricula', 'nome', 'cpf', 'ativo', 'pendencia', 'endereco', 'possivelVazamento'])
        df.to_csv('usuarios.csv', sep=',', index=False)

def add_adms():
    """ Função para carregar os administradores do sistema """
    try:
        df = pd.read_csv('adms.csv', sep=',')
    except:
        """ Cria o administrador do sistema """
        adm = [['admin', 'admin']]
        df = pd.DataFrame(adm, columns=['login', 'senha'])
        df.to_csv('adms.csv', sep=',', index=False)

add_usuarios() # Criar os usuários do sistema
add_adms()    # Cria o administrador do sistema

broker = str(input("Insira o endereço do Broker: "))

api = ApiNuvem('', 5050, broker=broker)             # Cria o sevidor da API 
servidor_api = threading.Thread(target=api.start) 

servidor = ReceiveServidor(broker=broker)    # Cria o servidor para o recebimento de dados
#servidor_dados = threading.Thread(target=servidor.start)

servidor_api.start()
#servidor_dados.start()
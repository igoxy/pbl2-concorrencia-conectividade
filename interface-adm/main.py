# -*- coding: utf-8 -*-

# --- Imports -----
from interface import Interface
import threading


api = str(input("Insira o endereço da API: "))      # Solicita o endereço da API em que os dados dos hidrômetros devem ser obtidos

tela = Interface(api)                               # Cria o objeto responsável pela tela

requisitar_hidrometros = threading.Thread(target=tela.requisicao_hidrometros)       # Cria uma Thread para obter os dados dos hidrômetros constantemente
requisitar_hidrometros.daemon = True                                                # Indica que a Thread deve finalizar ao fechar o programa
requisitar_hidrometros.start()                                                      # Inicia a Thread
tela.iniciar_interface()                                                            # Inicia a interface

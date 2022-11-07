# -*- coding: utf-8 -*-

#------ Imports ---------
import threading
from time import sleep
from tkinter import *
from tkinter import messagebox
import requests
#-------- Fim imports -------

class Interface:
    #----- Itens da interface ------
    window = Tk()
    identificador = Label(window)
    listBoxHidrometros = Listbox(window)
    numero_hidrometros = Label(window)
    n_hidrometros = Entry(window)
    n_buttom = Button(window)
    intervalo = Label(window)
    intervalo_t = Entry(window)
    i_buttom = Button(window)
    l_consumo = Label(window)
    v_consumo = Entry(window)
    c_buttom = Button(window)
    visualizar_buttom = Button(window)
    # ------ Fim itens da interface ------

    #------- Variáveis --------
    endereco_servidor = ''      # Armazena o endereço da nuvem
    quantidade = 0              # Armazena a quantidade de hidrômetros selecionados pelo adm
    consumo = 0.0               # Armazena o valor do consumo selecionado pelo adm
    tempo = 0                   # Armazena o tempo de consumo selecionado pelo adm
    hidrometros_maior_consumo = []  # Armazena as matriculas dos N hidrômetros de maior consumo
    matricula_selecionada = ''      # Armazena a matricula do hidrômetro selecionado pelo adm para visualizar os dados com menor latência
    #------- Fim variáveis ------

    #------- Funções --------
    def __init__(self, endereco_api: str):
        """ Construtor da classe """
        self.endereco_servidor = endereco_api

    def set_n_hidrometros(self):
        """ Obtem o número de hidrômetros selecionado pelo administrador """
        try:
            self.quantidade = int(self.n_hidrometros.get())
            if (self.quantidade <= 0):
                messagebox.showerror("Valor inválido", "O número de hidrômetroso não pode ser nenhum ou negativo")
        except ValueError:
            messagebox.showerror("Valor inválido", "O número de hidrômetroso não é um número inteiro")

    def set_intervalo_consumo(self):
        """ Obtém o consumo e o intervalo selecionado pelo administrador """
        try:
            self.consumo = float(self.v_consumo.get())
            self.tempo = int(self.intervalo_t.get())
            if (self.consumo > 0 and self.tempo > 0):
                dados = {"tempo": self.tempo ,"consumo": self.consumo}
                resposta = requests.post(f'http://{self.endereco_servidor}:5050/ADMINISTRADOR/CONSUMO_TEMPO', json=dados)
                if (resposta.status_code == 200):
                    messagebox.showinfo("Valores definidos", f"Foi definido que os usários não devem ultrapassar o consumo de {self.consumo} no intervalo de tempo de {self.tempo}")
                else:
                    messagebox.showerror("Erro ao definir os valores", "Tente novamente!")
            else:
                messagebox.showerror("Valor inválido", "O valor de tempo ou do consumo não pode ser nenhum ou negativo")        
        except ValueError:
            messagebox.showerror("Valor inválido", "O valor do intervalo deve ser inteiro e o valor do consumo deve ser um float, ambos maior que zero")

    def requisicao_hidrometros(self):
        """ Efetua a requisição dos dados dos hidrômetros via API """
        while True:
            try:
                if (self.quantidade > 0):
                    dados = {'quantidade': self.quantidade}
                    resposta = requests.get(f'http://{self.endereco_servidor}:5050/ADMINISTRADOR/MAIOR_CONSUMO', json=dados)
                    if (resposta.status_code == 200):
                        hidrometros = resposta.json()
                        self.__atualizar_hidrometros(hidrometros)
                    else:
                        sleep(2)
                else:
                    pass                        # Se a quantidade de hidrômetros não for definida, não solicita a API
                sleep(7)
            except Exception as ex:
                sleep(2)
    
    def visualizar_hidrometro(self):
        """ Método responsável por obter o hidrômetro selecionado para a visualização dos dados com menor latência """                                        
        indice = -1
        for i in self.listBoxHidrometros.curselection():
            indice = i
        if (indice >= 0):
            self.matricula_selecionada = self.hidrometros_maior_consumo[indice]
            resultado = self.__abrir_nova_janela()
            if (resultado != None):
                thread_atualizar = threading.Thread(target=self.atualizar_valor_hidrometro, args=(resultado[0], resultado[1], resultado[2], resultado[3]))  # Envia os argumentos janela, label, o endereço da nevoa e os dados
                thread_atualizar.daemon = True
                thread_atualizar.start()
    
    def __abrir_nova_janela(self):                                          
        """ Método responsável por abrir uma nova janela ao selecionar um hidrômetro para visualizar os dados com a menor latência """
        def __obter_dados_hidrometros(dados, label, endereco):
            label.config(text=f"Matricula: {str(dados['0']['matricula']).zfill(3)} - Vazão: {dados['0']['vazao']} m³/s - Consumo: {dados['0']['consumo']} m³")
            
        nova_janela = Toplevel(self.window)         # Cria uma nova janela
        nova_janela.title("Hidrometro")             # Adiciona o título a janela
        nova_janela.geometry("400x400")             # Define o tamanho da janela

        label = Label(nova_janela, text='')         # Cria uma label para a janela
        label.pack(pady=10)                         # Insere a label na janela

        dados = {'matricula': self.matricula_selecionada}   # Converte a matrícula do hidrômetro seleciondo em json
        resposta = requests.get(f'http://{self.endereco_servidor}:5050/ADMINISTRADOR/MONITORAR_HIDROMETRO', json=dados) # Faz a requisição dos dados do hidrômetro para API
        if (resposta.status_code == 200):
            endereco = resposta.json()      # A API deve retornar um endereço da API do hidrômetro selecionado para obter os dados diretamente de sua nevoa
            endereco_nevoa = endereco['endereco']     # Obtém o endereço recebido da API  
            resposta2 = requests.get(f'{endereco_nevoa}/ADMINISTRADOR/MONITORAR_HIDROMETRO', json=dados)    # Solicita os dados do hidrômetro desejado a por meio da API de sua nevoa
            if (resposta2.status_code == 200):
                dados_recebidos = resposta2.json()                              # Obtém as informações recebidas do hidrômetro
                __obter_dados_hidrometros(dados_recebidos, label, endereco_nevoa)   # Mostra os dados na janela
                return [nova_janela, label, endereco_nevoa, dados]                  # Retorna a nova janela, a label para mostrar as informações na janela, o endereço da API da nevoa do hidrômetro e matricula do hidrômetro selecionado
            else:                                   # Caso a API da nevoa retorne algum erro
                nova_janela.destroy()               # Não abre uma nova janela - destroi a que foi criada
                messagebox.showerror("Erro ao obter dados", "Não foi possível monitorar o hidrômetro selecionado")  # Mostra uma mensagem de erro
                return None                         
        else:                                       # Caso retorne alguma erro da API da nuvem
            nova_janela.destroy()                   # Não abre uma nova janela - destroi a que foi criada
            messagebox.showerror("Erro ao obter dados", "Não foi possível monitorar o hidrômetro selecionado")  # Mostra uma mensagem de erro
            return None
    
    def atualizar_valor_hidrometro(self, janela, label, endereco, dados):
        """ Método responsável por atualizar o valor do hidrômetro que está sendo visualizado com menor latência """
        try:
            while janela.state() == 'normal':
                resposta = requests.get(f'{endereco}/ADMINISTRADOR/MONITORAR_HIDROMETRO', json=dados)
                if (resposta.status_code == 200):
                    dados_h = resposta.json()      # Converte a resposta recebido em json         
                    label.config(text=f"Matricula: {dados_h['0']['matricula']} - Vazão: {dados_h['0']['vazao']} m³/s - Consumo: {dados_h['0']['consumo']} m³")
                sleep(5)                # Faz a solicitação dos dados a cada 5 segundos - tempo em que os hidrômetros enviam seus dados para a nevoa
        except:
            pass # Se ocorrer algum erro, a thread é finalizada
        

    def __atualizar_hidrometros(self, hidrometros: dict):
        """ Método responsável por atualizar a lista e exibição de dos N hidrômetros de maior consumo """
        self.hidrometros_maior_consumo.clear()
        self.listBoxHidrometros.delete(0,END)
        for hidrometro in hidrometros.values():
            if (hidrometro['consumo'] != None or hidrometro['consumo'] == 'None'):
                self.hidrometros_maior_consumo.append(str(hidrometro['matricula']).zfill(3))
                self.listBoxHidrometros.insert(END, f"Matricula: {str(hidrometro['matricula']).zfill(3)} - Vazão: {hidrometro['vazao']} m³/s - Consumo: {hidrometro['consumo']} m³")


    #---------- Fim funções ---------------
    
    #--------- Dados iniciais da tela -------------
    def iniciar_interface(self):
        """ Método responsável por definir as propriedades dos elementos que serão exibidos na interface e iniciar a mesma """
        self.window.title("Dashboard")
        self.window.geometry("1200x600")
        self.window.resizable(True, False)
        self.window.configure(bg="#191a19")
        #---------- Fim dados tela ----------

        #--------- Elementos da tela ---------
        #informação inicial da tela
        self.identificador.config(text="Hidrômetros de maiores consumos", bg="#191a19", fg="white")
        self.identificador.grid(column=1, row=0, padx=0, pady=2)

        #lista de hidrometros
        self.listBoxHidrometros.config(bg="#191a19", fg="white", highlightbackground="#ba440d", width=70, height=20, selectmode=SINGLE)
        self.listBoxHidrometros.grid(column=1, row=2, padx=20, pady=5)

        #entry número de hidrômetros
        self.numero_hidrometros.config(text="Insira a quantidade de hidrômetros que deseja visualizar", bg="#191a19", fg="white")
        self.numero_hidrometros.grid(column=0, row=3, padx=1)
        self.n_hidrometros.config(width=30, bg="#191a19", highlightbackground="#ba440d", fg="white")
        self.n_hidrometros.grid(column=0, row=4, padx=1)
        self.n_buttom.config(text="Mudar numero de hidrômetros", command=self.set_n_hidrometros, bg="#ba440d", highlightbackground="#ba440d", relief=FLAT, activebackground="#d44908")
        self.n_buttom.grid(column=0, row=5, padx=1, pady=3)

        #entry intervalo de tempo
        self.intervalo.config(text="Insira o intervalo de tempo para o consumo máximo", bg="#191a19", fg="white")
        self.intervalo.grid(column=1, row=3, padx=1)
        self.intervalo_t.config(width=30, bg="#191a19", highlightbackground="#ba440d", fg="white")
        self.intervalo_t.grid(column=1, row=4, padx=1)
        self.i_buttom.config(text="Mudar intervalo de tempo", command=self.set_intervalo_consumo, bg="#ba440d", highlightbackground="#ba440d", relief=FLAT, activebackground="#d44908")
        self.i_buttom.grid(column=1, row=5, padx=1, pady=3)


        #entry consumo
        self.l_consumo.config(text="Insira o consumo máximo para o intervalo de tempo", bg="#191a19", fg="white")
        self.l_consumo.grid(column=2, row=3, padx=1)
        self.v_consumo.config(width=30, bg="#191a19", highlightbackground="#ba440d", fg="white")
        self.v_consumo.grid(column=2, row=4, padx=1)

        #selecionar hidrometro
        self.visualizar_buttom.config(text="Visualizar Hidrômetro", command=self.visualizar_hidrometro, bg="#ba440d", highlightbackground="#ba440d", relief=FLAT, activebackground="#d44908")
        self.visualizar_buttom.grid(column=1, row=6, pady=20)

        self.window.mainloop()      # Inicia a tela
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np


valid_planets = ["Mercúrio", "Vênus", "Terra", "Marte", "Júpiter", "Saturno", "Urano", "Netuno", "Estacao_Esp1", "Estacao_Esp2", "Estacao_Esp3"]
meses_do_ano = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]


G = nx.Graph()

def upload_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    
    if file_path:
        try:
            df = pd.read_csv(file_path, delimiter=';')
            
            if 'Planeta' not in df.columns or 'Conexoes' not in df.columns:
                raise ValueError("O CSV deve conter as colunas: 'Planeta', 'Conexoes'")
            
            G.clear() 
            
            for index, row in df.iterrows():
                planet = row['Planeta']
                connections = row['Conexoes'].split(',')
                
                if planet in valid_planets:
                    G.add_node(planet)
                    for connection in connections:
                        if connection in valid_planets:
                            if (planet, connection) in distances:
                                distance = distances[(planet, connection)]
                                G.add_edge(planet, connection, weight=distance)
                            elif (connection, planet) in distances:
                                distance = distances[(connection, planet)]
                                G.add_edge(planet, connection, weight=distance)
                            else:
                                messagebox.showerror("Erro", f"Distância não definida entre {planet} e {connection}.")
                        else:
                            messagebox.showerror("Erro", f"Conexão inválida: {connection} não é um planeta válido.")
                else:
                    messagebox.showerror("Erro", f"Planeta inválido: {planet}")
            
            update_graph()
            populate_planet_options()
            update_missing_planets_dropdown()  
            update_delete_planet_dropdown()   
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar arquivo CSV: {str(e)}")

#Gernado a Matriz de adjacency
def generate_adjacency_matrix():
    nodes = list(G.nodes())
    n = len(nodes)
    adj_matrix = np.zeros((n, n))  # Cria uma matriz n x n inicializada com zeros
    
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if G.has_edge(node1, node2):
                adj_matrix[i, j] = G[node1][node2]['weight']  # Usar o peso da aresta (distância) como valor
            else:
                adj_matrix[i, j] = 0  # Sem conexão (aresta)
    
    # Converter a matriz de numpy para um DataFrame para exibir com os rótulos de linhas e colunas
    adj_df = pd.DataFrame(adj_matrix, index=nodes, columns=nodes)
    
    return adj_df

# Função para atualizar a lista de planetas que não estão no grafo
def update_missing_planets_dropdown():
    planets_in_graph = set(G.nodes())  # Obter os planetas que estão no grafo
    missing_planets = [planet for planet in valid_planets if planet not in planets_in_graph]  # Planetas que ainda não estão no grafo
    
    missing_planet_menu['menu'].delete(0, 'end')  # Limpar as opções do dropdown
    if missing_planets:
        for planet in missing_planets:
            missing_planet_menu['menu'].add_command(label=planet, command=tk._setit(missing_planet_var, planet))
        missing_planet_var.set(missing_planets[0])  # Definir o primeiro planeta como padrão
    else:
        missing_planet_var.set('')  # Se nenhum planeta faltar, deixar vazio

# Função para atualizar o menu de exclusão de planetas
def update_delete_planet_dropdown():
    planets_in_graph = list(G.nodes())  # Obter os planetas que estão no grafo
    
    delete_planet_menu['menu'].delete(0, 'end')  # Limpar as opções do dropdown
    if planets_in_graph:
        for planet in planets_in_graph:
            delete_planet_menu['menu'].add_command(label=planet, command=tk._setit(delete_planet_var, planet))
        delete_planet_var.set(planets_in_graph[0])  # Definir o primeiro planeta como padrão
    else:
        delete_planet_var.set('')  # Se não houver planetas, deixar vazio

# Função para calcular as posições normalizadas dos planetas
def calculate_positions():
    """
    Calcula as posições dos planetas em um layout radial baseado nas distâncias, normalizando com log.
    """
    pos = nx.spring_layout(G, seed=42, k=5, iterations=50) 
    central_planet = "Terra"  # Colocar a Terra no centro
    pos[central_planet] = np.array([0, 0])

    scale = 1.5  # Aumente o fator de escala para mais espaçamento
    angle_step = 2 * np.pi / (len(valid_planets))  # Dividir 360 graus entre os planetas
    angle = 0

    # Definir posições relativas em torno da Terra com base nas distâncias
    for planet in valid_planets:
        if planet == central_planet:
            continue

        # Calcular a distância relativa (log) para evitar distâncias extremas
        distance = None
        if (central_planet, planet) in distances:
            distance = distances[(central_planet, planet)]
        elif (planet, central_planet) in distances:
            distance = distances[(planet, central_planet)]

        if distance is not None:
            # Aplicar logaritmo para suavizar a variação de distâncias
            normalized_distance = np.log1p(distance)  # log(1 + distância) para evitar log(0)
            # Calcular posição radial
            pos[planet] = np.array([np.cos(angle), np.sin(angle)]) * normalized_distance * scale
            angle += angle_step * 1.5  # Aumente este valor para maior espaçamento angular
    pos["Estacao_Esp1"] = np.array([1.2, -5])  # Posição manual da Estacao_Esp1
    pos["Estacao_Esp2"] = np.array([2.5, -2])  # Posição manual da Estacao_Esp2
    pos["Estacao_Esp3"] = np.array([4.5, -2])  # Posição manual da Estacao_Esp3

    return pos

# Função para colorir os planetas e as estações espaciais
def get_node_colors():
    node_colors = []
    for node in G.nodes:
        if node in ["Mercúrio", "Vênus", "Terra", "Marte", "Júpiter", "Saturno", "Urano", "Netuno"]:
            node_colors.append("lightblue")  # Planetas terão a cor azul claro
        elif node.startswith("Estacao"):
            node_colors.append("orange")  # Estações espaciais terão a cor laranja
        else:
            node_colors.append("gray")  # Outros nós terão a cor cinza
    return node_colors

# Função para definir o tamanho dos nós (planetas maiores, estações menores)
def get_node_sizes():
    node_sizes = []
    for node in G.nodes:
        if node in ["Mercúrio", "Vênus", "Terra", "Marte", "Júpiter", "Saturno", "Urano", "Netuno"]:
            node_sizes.append(2000)  # Planetas maiores
        else:
            node_sizes.append(1000)  # Estações menores
    return node_sizes

# Função para atualizar a visualização do grafo com as novas posições
def update_graph():
    fig.clear()
    ax = fig.add_subplot(111)
    
    # Calcular posições personalizadas com base nas distâncias fornecidas
    pos = calculate_positions()
    
    # Obter as cores e tamanhos dos nós
    node_colors = get_node_colors()
    node_sizes = get_node_sizes()

    # Desenhar o grafo com cores personalizadas e tamanhos de nós
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=node_sizes, edge_color='gray', ax=ax, font_size=10, font_color='black')
    
     # Obter rótulos das arestas (distâncias)
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels={k: f"{v}" for k, v in labels.items()}, ax=ax, font_color='red')

    canvas.draw()

# Função para popular as opções de planetas
def populate_planet_options():
    planet_list = list(G.nodes())
    if not planet_list:
       planet_list = ["Nenhuma"] 
       
    stopover_planet_list = ["Nenhuma"] + planet_list  # Adicionar "Nenhuma" no início da lista

       
    origin_menu['menu'].delete(0, 'end')
    destination_menu['menu'].delete(0, 'end')
    stopover_menu['menu'].delete(0, 'end')
    
    for planet in planet_list:
        origin_menu['menu'].add_command(label=planet, command=tk._setit(origin_var, planet))
        destination_menu['menu'].add_command(label=planet, command=tk._setit(destination_var, planet))
        
    # Popular o menu de parada com a opção "Nenhuma" incluída
    for planet in stopover_planet_list:
        stopover_menu['menu'].add_command(label=planet, command=tk._setit(stopover_var, planet))


    if planet_list and planet_list[0] != "Nenhuma":
        origin_var.set(planet_list[0])  # Definir o primeiro planeta como padrão
        destination_var.set(planet_list[0])  # Definir o primeiro planeta como padrão
        stopover_var.set("Nenhuma")  # Definir o primeiro planeta como padrão para a parada opcional
    else:
        origin_var.set("")  # Limpar a seleção se nenhum planeta estiver no grafo
        destination_var.set("")
        stopover_var.set("Nenhuma")

# Função para adicionar manualmente um planeta com base nas distâncias predefinidas
def add_planet():
    planet = missing_planet_var.get()

    # Verificar se o planeta ou estação já existe no grafo
    if planet in G.nodes():
        messagebox.showerror("Erro", "O planeta ou estação já existe no grafo!")
        return

    # Verificar se o planeta é válido
    if planet and planet in valid_planets:
        # Verificar se há conexões válidas para adicionar o planeta
        connections = []
        for connection in valid_planets:
            if connection in G.nodes():
                if (planet, connection) in distances:
                    connections.append(connection)
                elif (connection, planet) in distances:
                    connections.append(connection)

        if not connections:
            messagebox.showerror("Erro", "O planeta ou estação não tem conexões válidas com planetas no grafo!")
            return

        try:
            # Adicionar o planeta ao grafo
            G.add_node(planet)

            # Adicionar as conexões válidas entre o planeta e outros planetas no grafo
            for connection in connections:
                if (planet, connection) in distances:
                    G.add_edge(planet, connection, weight=distances[(planet, connection)])
                elif (connection, planet) in distances:
                    G.add_edge(planet, connection, weight=distances[(connection, planet)])

            # Atualizar o grafo visualmente e os menus de opções
            update_graph()
            populate_planet_options()
            update_missing_planets_dropdown()
            update_delete_planet_dropdown()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar planeta ou estação: {str(e)}")
    else:
        messagebox.showerror("Erro", "Selecione um planeta ou estação válida para adicionar.")

# Função para excluir um planeta do grafo
def delete_planet():
    planet = delete_planet_var.get()
    
    if planet in G.nodes():
        try:
            G.remove_node(planet)  # Remover o planeta do grafo
            update_graph()  # Atualizar o grafo
            populate_planet_options()  # Atualizar as opções de planeta no menu
            update_missing_planets_dropdown()  # Atualizar a lista de planetas faltantes
            update_delete_planet_dropdown()   # Atualizar o menu de exclusão de planetas
            messagebox.showinfo("Sucesso", f"O planeta {planet} foi excluído do grafo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir planeta: {str(e)}")
    else:
        messagebox.showerror("Erro", "Selecione um planeta válido para excluir.")

# Adicionando um campo de texto para mostrar a viagem e o combustível
def show_shortest_path():
    origin = origin_var.get()
    destination = destination_var.get()
    stopover = stopover_var.get()  # Parada intermediária
    fuel_available = fuel_var.get()  # Quantidade de combustível disponível
    month = month_var.get()  # Nome do mês da viagem

    # Limpar o campo de texto
    travel_info_text.delete(1.0, tk.END)

    try:
        fuel_available = float(fuel_available)  # Garantir que seja um número válido
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira uma quantidade válida de combustível.")
        return

    # Verificar se origem, destino e mês são válidos
    if origin and destination and origin in G and destination in G and month in meses_do_ano:
        try:
            # Limpar o gráfico antes de desenhar um novo caminho
            update_graph()

            # Regra para cancelar a viagem se o destino for Vênus em dezembro
            if destination == "Vênus" and month == "dezembro":
                travel_info_text.insert(tk.END, "Devido a uma tempestade solar prevista para Dezembro, a viagem para Vênus foi adiada para evitar danos à nave.\n")
                return  # Interrompe a viagem, não prossegue

            # Regras baseadas no mês:
           # Regra 1: Viagens para Vênus (Chuvas de meteoros ocorrem fora messes em janeiro, março, junho)
            if destination == "Saturno" and month not in ["janeiro", "março", "junho"]:
                # Exibir janela com botões "Sim" e "Não"
                proceed = messagebox.askyesno("Aviso", "Viagens para Vênus fora de janeiro, março ou junho podem sofrer chuvas de meteoros.\nDeseja continuar com a viagem?")
                travel_info_text.insert(tk.END, "Ops parece que você escolheu viajar da mesmo com chuva de meteoros, você perder 150 de combustivel.\n")
                fuel_available -= 150  # Bonificação de combustível
                if not proceed:
                    # Se o usuário escolher "Não", cancelar a viagem
                    travel_info_text.insert(tk.END, "Viagem cancelada devido às condições meteorológicas em Saturno.\n")
                    return  # Interrompe a viagem, não prossegue

            # Regra 2: Evitar viagens para Marte em dezembro, fevereiro, agosto
            if destination == "Marte" and month in ["dezembro", "fevereiro", "agosto"]:
                messagebox.showwarning("Aviso", "Viagens para Marte em dezembro, fevereiro ou agosto podem enfrentar tempestades de areia, podendo reduzir drasticamente a visibilidade e afetar operações de pouso.")
                travel_info_text.insert(tk.END, "Ops parece que você escolheu viajar da mesmo com a tempestade você vai perder 200 de combustivel, pois a tempestade foi intensa.\n")
                fuel_available -= 200  # Bonificação de combustível
                if not proceed:
                    # Se o usuário escolher "Não", cancelar a viagem
                    travel_info_text.insert(tk.END, "Viagem cancelada devido às condições meteorológicas em Marte.\n")
                    return  # Interrompe a viagem, não prossegue
                
            # Regra 3: Alinhamento planetário entre Terra e Júpiter (menor consumo de combustível em maio, junho, outubro)
            if origin == "Terra" and destination == "Júpiter" and month in ["maio", "junho", "outubro"]:
                travel_info_text.insert(tk.END, "Viagem facilitada pelo alinhamento planetário! Menor consumo de combustível.\n")
                fuel_available += 200  # Bonificação de combustível
            
             # Regra 4: Viagens a Netuno nos messes de janeiro a abril, não podem ocorrer)
            if destination == "Netuno" and month in ["janeiro", "abril"]:
                messagebox.showwarning("Aviso", "Viagens para Neturno em jeneiro e Abril podem enfrentar fortes ventos, são os ventos mais rapidos do sistema solar! Por tanto não pode ocorrer.")
                travel_info_text.insert(tk.END, "Viagem cancelada devido às condições meteorológicas em Neturno.\n")
                return  # Interrompe a viagem, não prossegue

            # Regra 5: Verificar se há parada em Júpiter ou Saturno para aplicar "slingshot"
            if stopover == "Júpiter" or stopover == "Saturno":
                travel_info_text.insert(tk.END, "Usar a gravidade de Júpiter ou Saturno para um 'slingshot', diminuindo o consumo de combustível.\n")
                fuel_available += 300  # Bonificação de combustível
            

            # Calcular o caminho: com ou sem parada intermediária
            if stopover and stopover != "Nenhuma" and stopover in G:
                # Caminho origem -> parada -> destino
                path1 = nx.shortest_path(G, source=origin, target=stopover, weight='weight')
                path2 = nx.shortest_path(G, source=stopover, target=destination, weight='weight')
                full_path = path1[:-1] + path2  # Combina os dois caminhos
            else:
                # Caminho direto entre origem e destino
                full_path = nx.shortest_path(G, source=origin, target=destination, weight='weight')

            # Obter as arestas do caminho completo
            full_path_edges = list(zip(full_path, full_path[1:]))

            total_distance = 0  # Distância total percorrida

            # Mostrar o início da viagem no campo de texto
            travel_info_text.insert(tk.END, f"Viagem de {origin} para {destination}:\n")
            travel_info_text.insert(tk.END, f"Combustível inicial: {fuel_available} unidades\n")
            
            estacoes_espaciais = {"Estacao_Esp1", "Estacao_Esp2", "Estacao_Esp3"}
            estacoes_visitadas = set()  # Para rastrear as estações espaciais já visitadas

            for edge in full_path_edges:
                # Verificar se o caminho passa por uma estação espacial e se ela já não foi visitada
                if (edge[0] in estacoes_espaciais and edge[0] not in estacoes_visitadas) or \
                (edge[1] in estacoes_espaciais and edge[1] not in estacoes_visitadas):
                    estacao_espacial = edge[0] if edge[0] in estacoes_espaciais else edge[1]
                    fuel_available += 1000  # Recarregar combustível ao passar pela estação espacial
                    estacoes_visitadas.add(estacao_espacial)  # Marcar a estação espacial como visitada
                    travel_info_text.insert(tk.END, f"Reabastecimento em estação espacial: {estacao_espacial}. Novo combustível: {fuel_available}\n")

                # Calcular a distância para a próxima etapa
                distance = distances.get(edge, distances.get((edge[1], edge[0]), 0))
                total_distance += distance
                fuel_available -= distance  # Reduzir o combustível disponível com base na distância percorrida

                # Mostrar a etapa atual no campo de texto
                travel_info_text.insert(tk.END, f"De {edge[0]} para {edge[1]}: {distance} km. Combustível restante: {fuel_available} unidades\n")

                # Verificar se o combustível é suficiente para a próxima etapa
                if fuel_available < 0:
                    messagebox.showerror("Erro", f"Não é possível completar a viagem. Combustível insuficiente após {edge[0]} ou {edge[1]}.")
                    travel_info_text.insert(tk.END, "Viagem interrompida por falta de combustível.\n")
                    return

            # Desenhar o caminho mais curto no gráfico
            pos = calculate_positions()  # Posições recalculadas
            nx.draw_networkx_edges(G, pos, edgelist=full_path_edges, edge_color='red', width=3, ax=fig.axes[0])

            # Exibir a distância total percorrida e combustível final
            travel_info_text.insert(tk.END, f"Viagem concluída!\nDistância total: {total_distance} km\nCombustível restante: {fuel_available} unidades\n")
            travel_info_text.insert(tk.END, f"-------------------------------------------------")

            # Atualizar o canvas com o caminho destacado
            canvas.draw()

        except nx.NetworkXNoPath:
            messagebox.showerror("Erro", f"Não há caminho entre {origin} e {destination}")
    else:
        messagebox.showerror("Erro", "Por favor, selecione uma origem, destino válidos e insira um mês válido.")
#Botão para resetar as infor
def reset_fields():
    fuel_var.set('')  # Limpar o campo de combustível
    origin_var.set('')  # Resetar origem
    destination_var.set('')  # Resetar destino
    stopover_var.set('Nenhuma')  # Resetar a parada intermediária para 'Nenhuma'
    month_var.set(meses_do_ano[0])  # Resetar o mês para 'janeiro'
    
    travel_info_text.delete(1.0, tk.END)  # Limpar o campo de texto com informações da viagem
    '''
     # Resetar o grafo
    G.clear()  # Remove todos os nós e arestas do grafo
    
    # Atualizar visualmente o grafo (para refletir o reset)
    update_graph()
    
    # Atualizar os menus de planetas para refletir o grafo vazio
    populate_planet_options()

    # Limpar os menus de exclusão de planetas e adicionar planetas faltantes
    update_missing_planets_dropdown()  
    update_delete_planet_dropdown()
    '''
# Mostrar as informações do Grafo
def show_graph_info():
    """
    Exibe informações sobre o grafo:
    - Se é direcionado
    - Se é valorado (com pesos nas arestas)
    - Se possui laços (arestas de um nó para ele mesmo)
    - O grau de cada vértice (número de conexões)
    """
    info_text = ""

    # Verificar se é um grafo direcionado ou não
    if G.is_directed():
        info_text += "O grafo é direcionado.\n"
    else:
        info_text += "O grafo NÃO é direcionado.\n"

    # Verificar se o grafo é valorado (se tem pesos nas arestas)
    if nx.get_edge_attributes(G, 'weight'):
        info_text += "O grafo é valorado (contém pesos nas arestas).\n"
    else:
        info_text += "O grafo NÃO é valorado.\n"

    # Verificar se há laços (arestas de um vértice para ele mesmo)
    self_loops = list(nx.selfloop_edges(G))
    if self_loops:
        info_text += f"O grafo contém {len(self_loops)} laço(s): {self_loops}\n"
    else:
        info_text += "O grafo NÃO contém laços.\n"

    # Listar o grau de cada vértice
    info_text += "Graus dos vértices:\n"
    for node in G.nodes:
        info_text += f"- {node}: {G.degree(node)} conexões\n"


    # Criar uma nova janela para exibir as informações
    info_window = tk.Toplevel(window)  # Criar uma nova janela
    info_window.title("Dados do Grafo")  # Título da nova janela
    
    # Adicionar um campo de texto na nova janela
    text_widget = tk.Text(info_window, height=15, width=50)
    text_widget.pack(padx=10, pady=10)
    
    # Inserir o texto com as informações do grafo
    text_widget.insert(tk.END, info_text)
    
    # Desativar edição (modo somente leitura)
    text_widget.config(state=tk.DISABLED)
# Consultar as arestas e os Vertices
def consultar_aresta():
    """
    Abre uma nova janela para consultar a aresta entre dois vértices e exibir a distância (peso).
    """
    def mostrar_distancia():
        origem = origem_var.get()
        destino = destino_var.get()

        if origem and destino and origem in G and destino in G:
            try:
                # Verificar se existe uma aresta entre os dois vértices
                if G.has_edge(origem, destino):
                    distancia = G[origem][destino]['weight']  # Pegar o peso da aresta
                    resultado_var.set(f"Distância entre {origem} e {destino}: {distancia} km.")
                else:
                    resultado_var.set(f"Não existe uma aresta entre {origem} e {destino}.")
            except KeyError:
                resultado_var.set("Erro ao buscar a aresta.")
        else:
            resultado_var.set("Selecione vértices válidos.")
    
    def consultar_vertice():
        vertice = vertice_var.get()
        
        if vertice and vertice in G:
            conexoes = list(G.neighbors(vertice))  # Obter as conexões (vizinhos) do vértice
            grau = G.degree(vertice)  # Obter o grau do vértice (número de conexões)
            info_vertice_var.set(f"{vertice} tem {grau} conexão(ões): {', '.join(conexoes)}.")
        else:
            info_vertice_var.set("Selecione um vértice válido.")
    

    # Criar uma nova janela para a consulta
    consulta_window = tk.Toplevel(window)
    consulta_window.title("Consultar Aresta e Vértice")

    # Seção para consultar aresta (origem e destino)
    origem_var = tk.StringVar(consulta_window)
    destino_var = tk.StringVar(consulta_window)

    tk.Label(consulta_window, text="Origem:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
    origem_menu = ttk.OptionMenu(consulta_window, origem_var, "", *G.nodes())
    origem_menu.grid(row=0, column=1, padx=5, pady=5, sticky='w')

    tk.Label(consulta_window, text="Destino:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
    destino_menu = ttk.OptionMenu(consulta_window, destino_var, "", *G.nodes())
    destino_menu.grid(row=1, column=1, padx=5, pady=5, sticky='w')

    btn_mostrar_distancia = tk.Button(consulta_window, text="Consultar Aresta", command=mostrar_distancia)
    btn_mostrar_distancia.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    resultado_var = tk.StringVar(consulta_window)
    resultado_label = tk.Label(consulta_window, textvariable=resultado_var, wraplength=300, justify="left")
    resultado_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    # Seção para consultar vértice
    vertice_var = tk.StringVar(consulta_window)

    tk.Label(consulta_window, text="Vértice:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
    vertice_menu = ttk.OptionMenu(consulta_window, vertice_var, "", *G.nodes())
    vertice_menu.grid(row=4, column=1, padx=5, pady=5, sticky='w')

    btn_consultar_vertice = tk.Button(consulta_window, text="Consultar Vértice", command=consultar_vertice)
    btn_consultar_vertice.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    info_vertice_var = tk.StringVar(consulta_window)
    info_vertice_label = tk.Label(consulta_window, textvariable=info_vertice_var, wraplength=300, justify="left")
    info_vertice_label.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
# Mostrar a matriz de adjacencia
def show_adjacency_matrix():
    try:
        # Gerar a matriz de adjacência
        adj_df = generate_adjacency_matrix()

        # Criar uma nova janela para exibir a matriz
        matrix_window = tk.Toplevel(window)
        matrix_window.title("Matriz de Adjacência")

        # Adicionar um Treeview (tabela) para exibir a matriz
        tree = ttk.Treeview(matrix_window, columns=list(adj_df.columns), show='headings', height=adj_df.shape[0])

        # Definir as colunas com os nomes dos planetas (strings)
        for col in adj_df.columns:
            tree.heading(col, text=col)  # Nome da coluna como o planeta
            tree.column(col, width=100)  # Largura da coluna

        # Adicionar os dados na tabela (linha por linha)
        for index, row in adj_df.iterrows():
            tree.insert("", "end", values=list(row))  # Inserir valores de cada linha como uma lista

        # Adicionar a tabela na janela
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Adicionar uma barra de rolagem, caso necessário
        scrollbar = ttk.Scrollbar(matrix_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exibir matriz de adjacência: {str(e)}")


# Interface Tkinter
window = tk.Tk()
window.title("Planejamento de Rotas Interplanetárias")

# Configurar layout usando grid na janela principal
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=1)

# Criar variáveis Tkinter StringVar() antes de usar nos OptionMenus
fuel_var = tk.StringVar(window)
origin_var = tk.StringVar(window)
destination_var = tk.StringVar(window)
stopover_var = tk.StringVar(window)
month_var = tk.StringVar(window)
missing_planet_var = tk.StringVar(window)
delete_planet_var = tk.StringVar(window)

# Definir um valor padrão para o campo de mês
month_var.set(meses_do_ano[0])  # Janeiro como valor inicial

# Frame para os controles de entrada (Parte superior)
frame_top_controls = tk.Frame(window)
frame_top_controls.grid(row=0, column=0, columnspan=10, padx=10, pady=5, sticky='ew')

# Linha superior para os campos de entrada
btn_upload = tk.Button(frame_top_controls, text="Carregar CSV", command=upload_csv)
btn_upload.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

fuel_label = tk.Label(frame_top_controls, text="Combustível disponível:")
fuel_label.grid(row=0, column=1, padx=5, pady=5, sticky='w')

fuel_entry = tk.Entry(frame_top_controls, textvariable=fuel_var)
fuel_entry.grid(row=0, column=2, padx=5, pady=5, sticky='w')

origin_label = tk.Label(frame_top_controls, text="Origem:")
origin_label.grid(row=0, column=3, padx=5, pady=5, sticky='w')

origin_menu = ttk.OptionMenu(frame_top_controls, origin_var, "", *valid_planets)
origin_menu.grid(row=0, column=4, padx=5, pady=5, sticky='w')

destination_label = tk.Label(frame_top_controls, text="Destino:")
destination_label.grid(row=0, column=5, padx=5, pady=5, sticky='w')

destination_menu = ttk.OptionMenu(frame_top_controls, destination_var, "", *valid_planets)
destination_menu.grid(row=0, column=6, padx=5, pady=5, sticky='w')

stopover_label = tk.Label(frame_top_controls, text="Parada (Opcional):")
stopover_label.grid(row=0, column=7, padx=5, pady=5, sticky='w')

stopover_menu = ttk.OptionMenu(frame_top_controls, stopover_var, "", "", *valid_planets)
stopover_menu.grid(row=0, column=8, padx=5, pady=5, sticky='w')

# Botão para calcular caminho
btn_shortest_path = tk.Button(frame_top_controls, text="Caminho Mais Curto", command=show_shortest_path)
btn_shortest_path.grid(row=0, column=9, padx=5, pady=5, sticky='ew')


# Frame para gerenciamento de planetas (linha do meio)
frame_planet_controls = tk.Frame(window)
frame_planet_controls.grid(row=1, column=0, columnspan=10, padx=10, pady=5, sticky='ew')

missing_planet_label = tk.Label(frame_planet_controls, text="Adicionar Planeta:")
missing_planet_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')

missing_planet_menu = ttk.OptionMenu(frame_planet_controls, missing_planet_var, "")
missing_planet_menu.grid(row=1, column=1, padx=5, pady=5, sticky='w')

btn_add_planet = tk.Button(frame_planet_controls, text="Adicionar", command=add_planet)
btn_add_planet.grid(row=1, column=2, padx=5, pady=5, sticky='ew')

delete_planet_label = tk.Label(frame_planet_controls, text="Excluir Planeta:")
delete_planet_label.grid(row=1, column=3, padx=5, pady=5, sticky='e')

delete_planet_menu = ttk.OptionMenu(frame_planet_controls, delete_planet_var, "")
delete_planet_menu.grid(row=1, column=4, padx=5, pady=5, sticky='w')

btn_delete_planet = tk.Button(frame_planet_controls, text="Excluir", command=delete_planet)
btn_delete_planet.grid(row=1, column=5, padx=5, pady=5, sticky='ew')

month_label = tk.Label(frame_planet_controls, text="Mês da viagem:")
month_label.grid(row=1, column=6, padx=5, pady=5, sticky='e')

month_menu = ttk.OptionMenu(frame_planet_controls, month_var, *meses_do_ano)
month_menu.grid(row=1, column=7, padx=5, pady=5, sticky='w')

# Frame para ações diversas (linha inferior)
frame_actions = tk.Frame(window)
frame_actions.grid(row=2, column=0, columnspan=10, padx=10, pady=5, sticky='ew')

btn_reset = tk.Button(frame_actions, text="Resetar", command=reset_fields)
btn_reset.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

btn_show_graph_info = tk.Button(frame_actions, text="Info do Grafo", command=show_graph_info)
btn_show_graph_info.grid(row=2, column=2, padx=5, pady=5, sticky='ew')

btn_consultar_aresta = tk.Button(frame_actions, text="Dados do Grafo", command=consultar_aresta)
btn_consultar_aresta.grid(row=2, column=3, padx=5, pady=5, sticky='ew')

btn_show_adj_matrix = tk.Button(frame_actions, text="Matriz_Adj", command=show_adjacency_matrix)
btn_show_adj_matrix.grid(row=2, column=4, padx=5, pady=5, sticky='ew')

# Campo de texto para exibir a viagem e o combustível
travel_info_text = tk.Text(window, height=5, width=50)
travel_info_text.grid(row=2, column=5, columnspan=10, padx=10, pady=5, sticky='w')


# Frame para a visualização do grafo (parte inferior)
frame_graph = tk.Frame(window)
frame_graph.grid(row=3, column=0, columnspan=10, padx=10, pady=5, sticky='nsew')

fig = plt.Figure(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=frame_graph)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

window.mainloop()

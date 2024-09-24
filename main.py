import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from distancia import distances


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
    planet_list = valid_planets + ["Nenhuma"]
    origin_menu['menu'].delete(0, 'end')
    destination_menu['menu'].delete(0, 'end')
    
    for planet in planet_list:
        origin_menu['menu'].add_command(label=planet, command=tk._setit(origin_var, planet))
        destination_menu['menu'].add_command(label=planet, command=tk._setit(destination_var, planet))

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
            # Regra para cancelar a viagem se o destino for Vênus em dezembro
            if destination == "Vênus" and month == "dezembro":
                travel_info_text.insert(tk.END, "Devido a uma tempestade solar prevista para Dezembro, a viagem para Vênus foi adiada para evitar danos à nave.\n")
                return  # Interrompe a viagem, não prossegue

            # Regras baseadas no mês:
            
            # Regra 1: Viagens para Vênus (permitidas apenas em janeiro, março, junho)
            if destination == "Vênus" and month not in ["janeiro", "março", "junho"]:
                travel_info_text.insert(tk.END, "Aviso! Viagens para Vênus fora de janeiro, março ou junho podem sofrer chuvas de meteoros. Viagem cancelada!")
            return # Interrompe a viagem, não prossegue

            # Regra 2: Evitar viagens para Marte em dezembro, fevereiro, agosto
            if destination == "Marte" and month in ["dezembro", "fevereiro", "agosto"]:
                messagebox.showwarning("Aviso", "Viagens para Marte em dezembro, fevereiro ou agosto podem enfrentar tempestades de areia. Viagem cancelada!")
            return

            # Regra 3: Alinhamento planetário entre Terra e Júpiter (menor consumo de combustível em maio, junho, outubro)
            if origin == "Terra" and destination == "Júpiter" and month in ["maio", "junho", "outubro"]:
                travel_info_text.insert(tk.END, "Viagem facilitada pelo alinhamento planetário! Menor consumo de combustível.\n")
                fuel_available += 200  # Bonificação de combustível

            # Verificar se há parada em Júpiter ou Saturno para aplicar "slingshot"
            if stopover == "Júpiter" or stopover == "Saturno":
                travel_info_text.insert(tk.END, "Usar a gravidade de Júpiter ou Saturno para um 'slingshot', diminuindo o consumo de combustível.\n")
                fuel_available += 500  # Bonificação de combustível

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

def reset_fields():
    fuel_var.set('')  # Limpar o campo de combustível
    origin_var.set('')  # Resetar origem
    destination_var.set('')  # Resetar destino
    stopover_var.set('Nenhuma')  # Resetar a parada intermediária para 'Nenhuma'
    month_var.set(meses_do_ano[0])  # Resetar o mês para 'janeiro'
    travel_info_text.delete(1.0, tk.END)  # Limpar o campo de texto com informações da viagem
    G.clear()  # Limpar todos os nós e arestas do grafo
    update_graph()  # Atualizar a visualização do grafo na tela

def list_graph_details(graph):
    details = []

    # Verifica se o grafo é um dígrafo ou um grafo simples
    if isinstance(graph, nx.DiGraph):
        details.append("O grafo é um Dígrafo (direcionado).")
    else:
        details.append("O grafo é um Grafo simples (não direcionado).")

    # Verifica se o grafo é valorado (tem pesos nas arestas)
    if nx.is_weighted(graph):
        details.append("O grafo é valorado (as arestas possuem pesos).")
    else:
        details.append("O grafo não é valorado (as arestas não possuem pesos).")

    # Verifica se o grafo possui laços (self-loops)
    if nx.number_of_selfloops(graph) > 0:
        details.append(f"O grafo contém {nx.number_of_selfloops(graph)} laço(s).")
    else:
        details.append("O grafo não contém laços.")

    # Lista o grau de cada vértice
    if isinstance(graph, nx.DiGraph):  # Para dígrafos, temos graus de entrada e saída
        for node in graph.nodes:
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            details.append(f"Vértice {node}: Grau de Entrada = {in_degree}, Grau de Saída = {out_degree}")
    else:  # Para grafos simples, só existe o grau total
        for node in graph.nodes:
            degree = graph.degree(node)
            details.append(f"Vértice {node}: Grau = {degree}")
    
    return "\n".join(details)  # Junta os detalhes em uma única string para exibir

def show_graph_details():
    details = list_graph_details(G)
    travel_info_text.delete(1.0, tk.END)  # Limpa o campo de texto
    travel_info_text.insert(tk.END, details)  # Insere os detalhes no campo de texto


# Interface Tkinter
window = tk.Tk()
window.title("Planejamento de Rotas Interplanetárias")

# Configurar layout usando grid
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=2)  # Para o gráfico ocupar mais espaço

# Linha superior para os campos de entrada
btn_upload = tk.Button(window, text="Carregar CSV", command=upload_csv)
btn_upload.grid(row=0, column=0, padx=2, pady=2, sticky='e')

fuel_label = tk.Label(window, text="Combustível disponível:")
fuel_label.grid(row=0, column=1, padx=2, pady=2, sticky='w')

fuel_var = tk.StringVar(window)
fuel_entry = tk.Entry(window, textvariable=fuel_var)
fuel_entry.grid(row=0, column=2, padx=2, pady=2, sticky='e')

origin_var = tk.StringVar(window)
destination_var = tk.StringVar(window)
stopover_var = tk.StringVar(window)

origin_label = tk.Label(window, text="Origem:")
origin_label.grid(row=0, column=3, padx=2, pady=2, sticky='e')

origin_menu = ttk.OptionMenu(window, origin_var, "", *valid_planets)
origin_menu.grid(row=0, column=4, padx=2, pady=2, sticky='w')

destination_label = tk.Label(window, text="Destino:")
destination_label.grid(row=0, column=5, padx=2, pady=2, sticky='e')

destination_menu = ttk.OptionMenu(window, destination_var, "", *valid_planets)
destination_menu.grid(row=0, column=6, padx=2, pady=2, sticky='w')

# Seletor para parada intermediária (opcional)
stopover_label = tk.Label(window, text="Parada (Opcional):")
stopover_label.grid(row=0, column=7, padx=2, pady=2, sticky='e')

stopover_menu = ttk.OptionMenu(window, stopover_var, "", "", *valid_planets)
stopover_menu.grid(row=0, column=8, padx=2, pady=2, sticky='w')

# Botão para mostrar o caminho mais curto
btn_shortest_path = tk.Button(window, text="Caminho Mais Curto", command=show_shortest_path)
btn_shortest_path.grid(row=0, column=9, padx=2, pady=2, sticky='ew')

# Seletor para planetas faltantes (não no grafo)
missing_planet_label = tk.Label(window, text="Adicionar Planeta:")
missing_planet_label.grid(row=1, column=0, padx=2, pady=2, sticky='e')

missing_planet_var = tk.StringVar(window)
missing_planet_menu = ttk.OptionMenu(window, missing_planet_var, "")
missing_planet_menu.grid(row=1, column=1, padx=2, pady=2, sticky='w')

# Botão para adicionar planeta
btn_add_planet = tk.Button(window, text="Adicionar", command=add_planet)
btn_add_planet.grid(row=1, column=2, padx=2, pady=2, sticky='ew')

# Seletor para excluir planetas no grafo
delete_planet_label = tk.Label(window, text="Excluir Planeta:")
delete_planet_label.grid(row=1, column=3, padx=2, pady=2, sticky='e')

delete_planet_var = tk.StringVar(window)
delete_planet_menu = ttk.OptionMenu(window, delete_planet_var, "")
delete_planet_menu.grid(row=1, column=4, padx=2, pady=2, sticky='w')

# Botão para excluir planeta
btn_delete_planet = tk.Button(window, text="Excluir", command=delete_planet)
btn_delete_planet.grid(row=1, column=5, padx=2, pady=2, sticky='ew')

# Adicionar o campo para o mês da viagem como um OptionMenu
month_label = tk.Label(window, text="Mês da viagem:")
month_label.grid(row=2, column=1, padx=2, pady=2, sticky='e')

month_var = tk.StringVar(window)
month_var.set(meses_do_ano[0])  # Definir janeiro como valor inicial
month_menu = ttk.OptionMenu(window, month_var, *meses_do_ano)
month_menu.grid(row=2, column=2, padx=2, pady=2, sticky='w')

# Adicionando um botão para resetar todos os campos
btn_reset = tk.Button(window, text="Resetar", command=reset_fields)
btn_reset.grid(row=2, column=3, padx=2, pady=2)

# Adicionando um campo de texto na interface para mostrar a viagem e o combustível
travel_info_text = tk.Text(window, height=5, width=50)  # Ajuste a altura e a largura aqui
travel_info_text.grid(row=2, column=4, columnspan=10, padx=2, pady=2)

# Visualização do grafo
fig = plt.Figure(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().grid(row=3, column=0, columnspan=10, padx=2, pady=2)

window.mainloop()

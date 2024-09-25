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
distances = {
    ("Mercúrio", "Vênus"): 38,
    ("Mercúrio", "Terra"): 91,
    ("Mercúrio", "Marte"): 78,
    ("Mercúrio", "Júpiter"): 550,
    ("Mercúrio", "Saturno"): 1220,
    ("Mercúrio", "Urano"): 2600,
    ("Vênus", "Terra"): 42,
    ("Vênus", "Marte"): 61,
    ("Vênus", "Júpiter"): 520,
    ("Vênus", "Saturno"): 1130,
    ("Vênus", "Urano"): 2480,
    ("Terra", "Marte"): 78,
    ("Terra", "Júpiter"): 628,
    ("Terra", "Saturno"): 1270,
    ("Terra", "Urano"): 2720,
    ("Terra", "Netuno"): 4340,
    ("Marte", "Júpiter"): 558,
    ("Marte", "Saturno"): 1150,
    ("Marte", "Urano"): 2650,
    ("Júpiter", "Saturno"): 650,
    ("Júpiter", "Urano"): 1520,
    ("Júpiter", "Netuno"): 2380,
    ("Saturno", "Urano"): 870,
    ("Saturno", "Netuno"): 1420,
    ("Urano", "Netuno"): 2850,
    ("Estacao_Esp1", "Mercúrio"): 500,
    ("Estacao_Esp1", "Netuno"): 1000,
    ("Estacao_Esp2", "Marte"): 400,
    ("Estacao_Esp2", "Netuno"): 900,
    ("Estacao_Esp3", "Vênus"): 450,
    ("Estacao_Esp3", "Netuno"): 950,
}

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

#Gernado a Matriz
def generate_adjacency_matrix():
    nodes = list(G.nodes())
    n = len(nodes)
    adj_matrix = np.zeros((n, n))  
    
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if G.has_edge(node1, node2):
                adj_matrix[i, j] = G[node1][node2]['weight']  
            else:
                adj_matrix[i, j] = 0  
    
   
    adj_df = pd.DataFrame(adj_matrix, index=nodes, columns=nodes)
    
    return adj_df

# Função para atualizar a lista de planetas que não estão no grafo
def update_missing_planets_dropdown():
    planets_in_graph = set(G.nodes())  
    missing_planets = [planet for planet in valid_planets if planet not in planets_in_graph]  
    
    missing_planet_menu['menu'].delete(0, 'end')  
    if missing_planets:
        for planet in missing_planets:
            missing_planet_menu['menu'].add_command(label=planet, command=tk._setit(missing_planet_var, planet))
        missing_planet_var.set(missing_planets[0]) 
    else:
        missing_planet_var.set('')  
        
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
            node_sizes.append(2000)  
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
            
            G.add_node(planet)

            
            for connection in connections:
                if (planet, connection) in distances:
                    G.add_edge(planet, connection, weight=distances[(planet, connection)])
                elif (connection, planet) in distances:
                    G.add_edge(planet, connection, weight=distances[(connection, planet)])

          
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
            G.remove_node(planet) 
            update_graph()
            populate_planet_options()  
            update_missing_planets_dropdown()  
            update_delete_planet_dropdown()   
            messagebox.showinfo("Sucesso", f"O planeta {planet} foi excluído do grafo.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir planeta: {str(e)}")
    else:
        messagebox.showerror("Erro", "Selecione um planeta válido para excluir.")

# Adicionando um campo de texto para mostrar a viagem e o combustível
def show_shortest_path():
    origin = origin_var.get()
    destination = destination_var.get()
    stopover = stopover_var.get()  
    fuel_available = fuel_var.get()  
    month = month_var.get()  

    travel_info_text.delete(1.0, tk.END)

    try:
        fuel_available = float(fuel_available)  
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira uma quantidade válida de combustível.")
        return

   
    if origin and destination and origin in G and destination in G and month in meses_do_ano:
        try:
           
            update_graph()

            # Regra para cancelar a viagem se o destino for Vênus em dezembro
            if destination == "Vênus" and month == "dezembro":
                travel_info_text.insert(tk.END, "Devido a uma tempestade solar prevista para Dezembro, a viagem para Vênus foi adiada para evitar danos à nave.\n")
                return  # Interrompe a viagem, não prossegue

         
           # Regra 1: Viagens para Vênus (Chuvas de meteoros ocorrem fora messes em janeiro, março, junho)
            if destination == "Saturno" and month not in ["janeiro", "março", "junho"]:
                
                proceed = messagebox.askyesno("Aviso", "Viagens para Vênus fora de janeiro, março ou junho podem sofrer chuvas de meteoros.\nDeseja continuar com a viagem?")
                travel_info_text.insert(tk.END, "Ops parece que você escolheu viajar da mesmo com chuva de meteoros, você perder 150 de combustivel.\n")
                fuel_available -= 150 
                if not proceed:
                    travel_info_text.insert(tk.END, "Viagem cancelada devido às condições meteorológicas em Saturno.\n")
                    return  

            # Regra 2: Evitar viagens para Marte em dezembro, fevereiro, agosto
            if destination == "Marte" and month in ["dezembro", "fevereiro", "agosto"]:
                messagebox.showwarning("Aviso", "Viagens para Marte em dezembro, fevereiro ou agosto podem enfrentar tempestades de areia, podendo reduzir drasticamente a visibilidade e afetar operações de pouso.")
                travel_info_text.insert(tk.END, "Ops parece que você escolheu viajar da mesmo com a tempestade você vai perder 200 de combustivel, pois a tempestade foi intensa.\n")
                fuel_available -= 200  
                if not proceed:
                   
                    travel_info_text.insert(tk.END, "Viagem cancelada devido às condições meteorológicas em Marte.\n")
                    return  
                                
            # Regra 3: Alinhamento planetário entre Terra e Júpiter (menor consumo de combustível em maio, junho, outubro)
            if origin == "Terra" and destination == "Júpiter" and month in ["maio", "junho", "outubro"]:
                travel_info_text.insert(tk.END, "Viagem facilitada pelo alinhamento planetário! Menor consumo de combustível.\n")
                fuel_available += 200 
            
             # Regra 4: Viagens a Netuno nos messes de janeiro a abril, não podem ocorrer)
            if destination == "Netuno" and month in ["janeiro", "abril"]:
                messagebox.showwarning("Aviso", "Viagens para Neturno em jeneiro e Abril podem enfrentar fortes ventos, são os ventos mais rapidos do sistema solar! Por tanto não pode ocorrer.")
                travel_info_text.insert(tk.END, "Viagem cancelada devido às condições meteorológicas em Neturno.\n")
                return 

            # Regra 5: Verificar se há parada em Júpiter ou Saturno para aplicar "slingshot"
            if stopover == "Júpiter" or stopover == "Saturno":
                travel_info_text.insert(tk.END, "Usar a gravidade de Júpiter ou Saturno para um 'slingshot', diminuindo o consumo de combustível.\n")
                fuel_available += 300              

           
            if stopover and stopover != "Nenhuma" and stopover in G:
                
                path1 = nx.shortest_path(G, source=origin, target=stopover, weight='weight')
                path2 = nx.shortest_path(G, source=stopover, target=destination, weight='weight')
                full_path = path1[:-1] + path2 
            else:
              
                full_path = nx.shortest_path(G, source=origin, target=destination, weight='weight')

            full_path_edges = list(zip(full_path, full_path[1:]))

            total_distance = 0  

            
            travel_info_text.insert(tk.END, f"Viagem de {origin} para {destination}:\n")
            travel_info_text.insert(tk.END, f"Combustível inicial: {fuel_available} unidades\n")
            
            estacoes_espaciais = {"Estacao_Esp1", "Estacao_Esp2", "Estacao_Esp3"}
            estacoes_visitadas = set() 

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
   
    info_text = ""
    
    if G.is_directed():
        info_text += "O grafo é direcionado.\n"
    else:
        info_text += "O grafo NÃO é direcionado.\n"

    
    if nx.get_edge_attributes(G, 'weight'):
        info_text += "O grafo é valorado (contém pesos nas arestas).\n"
    else:
        info_text += "O grafo NÃO é valorado.\n"

    
    self_loops = list(nx.selfloop_edges(G))
    if self_loops:
        info_text += f"O grafo contém {len(self_loops)} laço(s): {self_loops}\n"
    else:
        info_text += "O grafo NÃO contém laços.\n"

   
    info_text += "Graus dos vértices:\n"
    for node in G.nodes:
        info_text += f"- {node}: {G.degree(node)} conexões\n"


   
    info_window = tk.Toplevel(window) 
    info_window.title("Dados do Grafo")  
    
 
    text_widget = tk.Text(info_window, height=15, width=50)
    text_widget.pack(padx=10, pady=10)
    
 
    text_widget.insert(tk.END, info_text)
    
    
    text_widget.config(state=tk.DISABLED)

#Verificar o tipo que é o grafo
def verificar_tipo_de_grafo():
    """
    Verifica o tipo do grafo: Euleriano, semi-Euleriano, Hamiltoniano, simples, nulo, trivial ou regular.
    """
    tipo_grafo = []

   
    if not nx.is_connected(G): 
        tipo_grafo.append("O grafo não é conexo, portanto, não é Euleriano nem semi-Euleriano.")
    else:
        # Contar os vértices com grau ímpar
        vertices_grau_impar = [v for v, grau in G.degree() if grau % 2 != 0]

        if len(vertices_grau_impar) == 0:
            tipo_grafo.append("O grafo é Euleriano (contém um ciclo de Euler).")
        elif len(vertices_grau_impar) == 2:
            tipo_grafo.append("O grafo é semi-Euleriano (contém um caminho de Euler).")
        else:
            tipo_grafo.append("O grafo não é Euleriano nem semi-Euleriano.")

   
    try:
        ciclo_hamiltoniano = list(nx.find_cycle(G))
        tipo_grafo.append("O grafo é Hamiltoniano (contém um ciclo de Hamilton).")
    except nx.NetworkXNoCycle:
        tipo_grafo.append("O grafo não é Hamiltoniano.")

    if any(G.has_edge(v, v) for v in G.nodes()):
        tipo_grafo.append("O grafo não é simples (contém laços).")
    else:
        tipo_grafo.append("O grafo é simples (não contém laços).")

    if len(G.edges()) == 0:
        tipo_grafo.append("O grafo é nulo (não contém arestas).")

    if len(G.nodes()) == 1:
        tipo_grafo.append("O grafo é trivial (apenas um vértice).")

    graus = [grau for _, grau in G.degree()]
    if len(set(graus)) == 1:
        tipo_grafo.append("O grafo é regular (todos os vértices têm o mesmo grau).")
    else:
        tipo_grafo.append("O grafo não é regular (vértices com graus diferentes).")

    return "\n".join(tipo_grafo)

def mostrar_tipo_de_grafo():
    """
    Mostra o tipo de grafo (Euleriano, semi-Euleriano, Hamiltoniano, simples, composto, nulo, trivial ou regular) em uma janela.
    """
    tipo_grafo = verificar_tipo_de_grafo()

    # Criar uma nova janela para exibir o resultado
    tipo_window = tk.Toplevel(window)
    tipo_window.title("Tipo de Grafo")

    # Adicionar uma label para mostrar o resultado
    label = tk.Label(tipo_window, text=tipo_grafo, wraplength=300, justify="left")
    label.pack(padx=10, pady=10)

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
       
        adj_df = generate_adjacency_matrix()

        matrix_window = tk.Toplevel(window)
        matrix_window.title("Matriz de Adjacência")

        tree = ttk.Treeview(matrix_window, columns=list(adj_df.columns), show='headings', height=adj_df.shape[0])

        for col in adj_df.columns:
            tree.heading(col, text=col)  
            tree.column(col, width=100)  
            
        for index, row in adj_df.iterrows():
            tree.insert("", "end", values=list(row)) 

    
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(matrix_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exibir matriz de adjacência: {str(e)}")


# Interface Tkinter
window = tk.Tk()
window.title("Planejamento de Rotas Interplanetárias")

window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=1)

fuel_var = tk.StringVar(window)
origin_var = tk.StringVar(window)
destination_var = tk.StringVar(window)
stopover_var = tk.StringVar(window)
month_var = tk.StringVar(window)
missing_planet_var = tk.StringVar(window)
delete_planet_var = tk.StringVar(window)

month_var.set(meses_do_ano[0])

frame_top_controls = tk.Frame(window)
frame_top_controls.grid(row=0, column=0, columnspan=10, padx=10, pady=5, sticky='ew')

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

btn_tipo_de_grafo = tk.Button(frame_actions, text="Verificar Tipo de Grafo", command=mostrar_tipo_de_grafo)
btn_tipo_de_grafo.grid(row=2, column=5, padx=2, pady=2, sticky='ew')

btn_show_adj_matrix = tk.Button(frame_actions, text="Matriz_Adj", command=show_adjacency_matrix)
btn_show_adj_matrix.grid(row=2, column=4, padx=5, pady=5, sticky='ew')

# Campo de texto para exibir a viagem e o combustível
travel_info_text = tk.Text(window, height=5, width=50)
travel_info_text.grid(row=2, column=6, columnspan=10, padx=10, pady=5, sticky='w')


# Frame para a visualização do grafo (parte inferior)
frame_graph = tk.Frame(window)
frame_graph.grid(row=3, column=0, columnspan=10, padx=10, pady=5, sticky='nsew')

fig = plt.Figure(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=frame_graph)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

window.mainloop()

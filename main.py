import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np


valid_planets = ["Mercúrio", "Vênus", "Terra", "Marte", "Júpiter", "Saturno", "Urano", "Netuno", "Estacao_Esp1", "Estacao_Esp2", "Estacao_Esp3"]
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
    pos = nx.spring_layout(G, seed=42)
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

    return pos


# Função para atualizar a visualização do grafo com as novas posições
def update_graph():
    fig.clear()
    ax = fig.add_subplot(111)
    
    # Calcular posições personalizadas com base nas distâncias fornecidas
    pos = calculate_positions()

    # Desenhar o grafo
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, edge_color='gray', ax=ax)
    
    # Obter rótulos das arestas
    labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels={k: f"{v}" for k, v in labels.items()}, ax=ax)
    
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
# Função para mostrar o caminho mais curto e aplicar regras baseadas no mês
def show_shortest_path():
    origin = origin_var.get()
    destination = destination_var.get()
    stopover = stopover_var.get()  # Parada intermediária
    fuel_available = fuel_var.get()  # Quantidade de combustível disponível
    month = month_var.get()  # Mês da viagem

    # Limpar o campo de texto
    travel_info_text.delete(1.0, tk.END)

    try:
        fuel_available = float(fuel_available)  # Garantir que seja um número válido
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira uma quantidade válida de combustível.")
        return

    # Verificar se origem, destino e mês são válidos
    if origin and destination and origin in G and destination in G and month.isdigit() and 1 <= int(month) <= 12:
        month = int(month)  # Converter o mês para inteiro
        try:
            # Regras baseadas no mês:
            
            # Regra 1: Viagens para Vênus (permitidas apenas em janeiro, março, junho)
            if destination == "Neturno" and month not in [1, 3, 6]:
                messagebox.showwarning("Aviso", "Viagens para Neturno fora de janeiro, março ou junho podem sofrer chuvas de meteoros.")
            
            # Regra 2: Evitar viagens para Marte em dezembro, fevereiro, agosto
            if destination == "Marte" and month in [12, 2, 8]:
                messagebox.showwarning("Aviso", "Viagens para Marte em dezembro, fevereiro ou agosto podem enfrentar tempestades de areia.")
            
            # Regra 3: Alinhamento planetário entre Terra e Júpiter (menor consumo de combustível em maio, junho, outubro)
            if origin == "Terra" and destination == "Júpiter" and month in [5, 6, 10]:
                travel_info_text.insert(tk.END, "Viagem facilitada pelo alinhamento planetário! Menor consumo de combustível.\n")
                fuel_available += 200  # Bonificação de combustível

            # Verificar se há parada em Júpiter ou Saturno para aplicar "slingshot"
            if stopover == "Júpiter" or stopover == "Saturno":
                travel_info_text.insert(tk.END, "Usar a gravidade de Júpiter ou Saturno para um 'slingshot', diminuindo o consumo de combustível.\n")
                fuel_available += 500  # Bonificação de combustível
                
            if destination == "Vênus" and month in [12]:
                travel_info_text.insert(tk.END, "Devido a uma tempestade solar prevista para Dezembro, a viagem para Vênus foi adiada para evitar danos à nave.\n")
                return

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

            # Iterar sobre cada etapa da viagem
            for edge in full_path_edges:
                # Verificar se o caminho passa por uma estação espacial
                if edge[0] in ["Estacao_Esp1", "Estacao_Esp2", "Estacao_Esp3"] or edge[1] in ["Estacao_Esp1", "Estacao_Esp2", "Estacao_Esp3"]:
                    fuel_available += 1000  # Recarregar combustível ao passar pela estação espacial
                    travel_info_text.insert(tk.END, f"Reabastecimento em estação espacial: {edge[1]}. Novo combustível: {fuel_available}\n")

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
        messagebox.showerror("Erro", "Por favor, selecione uma origem, destino válidos e insira um mês válido (1-12).")


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

stopover_menu = ttk.OptionMenu(window, stopover_var, "", *valid_planets)
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

# Adicionar o campo para o mês da viagem
month_label = tk.Label(window, text="Mês da viagem (1-12):")
month_label.grid(row=2, column=0, padx=2, pady=2, sticky='e')

month_var = tk.StringVar(window)
month_entry = tk.Entry(window, textvariable=month_var)
month_entry.grid(row=2, column=1, padx=2, pady=2, sticky='w')


# Adicionando um campo de texto na interface para mostrar a viagem e o combustível
travel_info_text = tk.Text(window, height=5, width=50)  # Ajuste a altura e a largura aqui
travel_info_text.grid(row=2, column=3, columnspan=10, padx=2, pady=2)

# Visualização do grafo
fig = plt.Figure(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().grid(row=3, column=0, columnspan=10, padx=2, pady=2)

window.mainloop()

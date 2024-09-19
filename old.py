import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np

# Lista de planetas válidos e suas distâncias predefinidas
valid_planets = ["Mercúrio", "Vênus", "Terra", "Marte", "Júpiter", "Saturno", "Urano", "Netuno"]
distances = {
    ("Mercúrio", "Vênus"): 38,
    ("Mercúrio", "Terra"): 91,
    ("Mercúrio", "Marte"): 78,
    ("Mercúrio", "Júpiter"): 550,
    ("Mercúrio", "Saturno"): 1220,
    ("Mercúrio", "Urano"): 2600,
    ("Mercúrio", "Netuno"): 4300,
    ("Vênus", "Terra"): 42,
    ("Vênus", "Marte"): 61,
    ("Vênus", "Júpiter"): 520,
    ("Vênus", "Saturno"): 1130,
    ("Vênus", "Urano"): 2480,
    ("Vênus", "Netuno"): 4150,
    ("Terra", "Marte"): 78,
    ("Terra", "Júpiter"): 628,
    ("Terra", "Saturno"): 1270,
    ("Terra", "Urano"): 2720,
    ("Terra", "Netuno"): 4340,
    ("Marte", "Júpiter"): 558,
    ("Marte", "Saturno"): 1150,
    ("Marte", "Urano"): 2650,
    ("Marte", "Netuno"): 4300,
    ("Júpiter", "Saturno"): 650,
    ("Júpiter", "Urano"): 1520,
    ("Júpiter", "Netuno"): 2380,
    ("Saturno", "Urano"): 870,
    ("Saturno", "Netuno"): 1420,
    ("Urano", "Netuno"): 2850
}

# Inicializando o grafo
G = nx.Graph()

# Função para carregar o arquivo CSV
def upload_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    
    if file_path:
        try:
            df = pd.read_csv(file_path, delimiter=';')
            
            if 'Planeta' not in df.columns or 'Conexoes' not in df.columns:
                raise ValueError("O CSV deve conter as colunas: 'Planeta', 'Conexoes'")
            
            G.clear()  # Limpar o grafo antes de adicionar novos dados
            
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
            update_missing_planets_dropdown()  # Atualizar a lista de planetas que não estão no grafo
            update_delete_planet_dropdown()   # Atualizar a lista de planetas para exclusão
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
    pos = {}
    central_planet = "Terra"  # Colocar a Terra no centro
    pos[central_planet] = np.array([0, 0])

    scale = 0.5  # Fator de escala para ajustar o espaçamento no gráfico
    angle_step = 2 * np.pi / (len(valid_planets) - 1)  # Dividir 360 graus entre os planetas
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
            angle += angle_step

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
    
    if planet in G.nodes():
        messagebox.showerror("Erro", "Planeta já existe no grafo!")
        return
    
    if planet:
        try:
            G.add_node(planet)  # Adicionar o planeta ao grafo
            for connection in valid_planets:  # Adicionar conexões predefinidas
                if connection in G.nodes() and (planet, connection) in distances:
                    G.add_edge(planet, connection, weight=distances[(planet, connection)])
                elif connection in G.nodes() and (connection, planet) in distances:
                    G.add_edge(planet, connection, weight=distances[(connection, planet)])

            update_graph()
            populate_planet_options()  # Atualizar as opções de planeta no menu
            update_missing_planets_dropdown()  # Atualizar a lista de planetas faltantes
            update_delete_planet_dropdown()   # Atualizar o menu de exclusão de planetas
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar planeta: {str(e)}")
    else:
        messagebox.showerror("Erro", "Selecione um planeta para adicionar.")

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

def show_shortest_path():
    origin = origin_var.get()
    destination = destination_var.get()
    stopover = stopover_var.get()
    
    if origin and destination:
        try:
            if stopover and stopover != "Nenhuma":
                # Calcular o caminho passando pela parada intermediária
                path1 = nx.shortest_path(G, source=origin, target=stopover, weight='weight')
                path2 = nx.shortest_path(G, source=stopover, target=destination, weight='weight')
                
                if path1 and path2:
                    # Unir os dois caminhos
                    full_path = path1[:-1] + path2
                    full_path_edges = list(zip(full_path, full_path[1:]))
                else:
                    messagebox.showerror("Erro", "Não há caminho entre os planetas especificados.")
                    return
            else:
                # Calcular o caminho direto
                full_path = nx.shortest_path(G, source=origin, target=destination, weight='weight')
                full_path_edges = list(zip(full_path, full_path[1:]))
            
            update_graph()  # Atualizar o grafo
            
            # Destacar o caminho mais curto
            pos = calculate_positions()  # Posições recalculadas
            nx.draw_networkx_edges(G, pos, edgelist=full_path_edges, edge_color='red', width=3, ax=fig.axes[0])
            canvas.draw()
        except nx.NetworkXNoPath:
            messagebox.showerror("Erro", f"Não há caminho entre {origin} e {destination}")

# Interface Tkinter
window = tk.Tk()
window.title("Planejamento de Rotas Interplanetárias")

# Configurar layout usando grid
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)

# Botão de upload de CSV
btn_upload = tk.Button(window, text="Carregar CSV", command=upload_csv)
btn_upload.grid(row=0, column=0, columnspan=4, padx=2, pady=2, sticky='ew')

# Seletor de planeta de origem e destino
origin_var = tk.StringVar(window)
destination_var = tk.StringVar(window)
stopover_var = tk.StringVar(window)

origin_label = tk.Label(window, text="Origem:")
origin_label.grid(row=1, column=0, padx=2, pady=2, sticky='e')

origin_menu = ttk.OptionMenu(window, origin_var, "", *valid_planets)
origin_menu.grid(row=1, column=1, padx=2, pady=2, sticky='w')

destination_label = tk.Label(window, text="Destino:")
destination_label.grid(row=1, column=2, padx=2, pady=2, sticky='e')

destination_menu = ttk.OptionMenu(window, destination_var, "", *valid_planets)
destination_menu.grid(row=1, column=3, padx=2, pady=2, sticky='w')

# Seletor para parada intermediária (opcional)
stopover_label = tk.Label(window, text="Parada (Opcional):")
stopover_label.grid(row=2, column=0, padx=2, pady=2, sticky='e')

stopover_menu = ttk.OptionMenu(window, stopover_var, "", *valid_planets)
stopover_menu.grid(row=2, column=1, padx=2, pady=2, sticky='w')

# Botão para mostrar o caminho mais curto
btn_shortest_path = tk.Button(window, text="Caminho Mais Curto", command=show_shortest_path)
btn_shortest_path.grid(row=2, column=2, columnspan=2, padx=2, pady=2, sticky='ew')

# Seletor para planetas faltantes (não no grafo)
missing_planet_label = tk.Label(window, text="Adicionar Planeta:")
missing_planet_label.grid(row=3, column=0, padx=2, pady=2, sticky='e')

missing_planet_var = tk.StringVar(window)
missing_planet_menu = ttk.OptionMenu(window, missing_planet_var, "")
missing_planet_menu.grid(row=3, column=1, padx=2, pady=2, sticky='w')

# Botão para adicionar planeta
btn_add_planet = tk.Button(window, text="Adicionar", command=add_planet)
btn_add_planet.grid(row=3, column=2, columnspan=2, padx=2, pady=2, sticky='ew')

# Seletor para excluir planetas no grafo
delete_planet_label = tk.Label(window, text="Excluir Planeta:")
delete_planet_label.grid(row=4, column=0, padx=2, pady=2, sticky='e')

delete_planet_var = tk.StringVar(window)
delete_planet_menu = ttk.OptionMenu(window, delete_planet_var, "")
delete_planet_menu.grid(row=4, column=1, padx=2, pady=2, sticky='w')

# Botão para excluir planeta
btn_delete_planet = tk.Button(window, text="Excluir", command=delete_planet)
btn_delete_planet.grid(row=4, column=2, columnspan=2, padx=2, pady=2, sticky='ew')

# Visualização do grafo
fig = plt.Figure(figsize=(7, 7))
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().grid(row=0, column=4, rowspan=5, padx=2, pady=2)

window.mainloop()

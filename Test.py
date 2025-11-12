import osmnx as ox
import networkx as nx

# Baixa o grafo de ruas de uma cidade
G = ox.graph_from_place("Barcelos, Portugal", network_type="drive")

# Mostra informações básicas
# print(nx.info(G))

# Visualiza o grafo

fig, ax = ox.plot_graph(G, show=False, save=True, filepath="map.png")
print("Mapa salvo como 'map.png'")

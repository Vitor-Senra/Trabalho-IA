import osmnx as ox
import json
import os
from noise import pnoise2

# Função Perlin
def perlin(x, y, scale=0.1, octaves=6):
    return pnoise2(
        x / scale,
        y / scale,
        octaves=octaves,
        persistence=0.5,
        lacunarity=2.0,
        repeatx=1024,
        repeaty=1024,
        base=0
    )

def gerar_json_rede_viaria(localizacao="Barcelos, Portugal", ficheiro_saida="src/data/cidade.json"):
    print(f"1. A baixar rede viária de '{localizacao}'...")
    
    # Baixar apenas ruas transitáveis por carros
    G = ox.graph_from_place(localizacao, network_type="drive")
    
    # Simplificar: remove nós intermédios em retas, mantém apenas cruzamentos
    G = ox.project_graph(G)
    
    print("2. A calcular tempos de viagem...")
    # Adicionar velocidades e tempos baseados no tipo de estrada
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    print("3. A converter para JSON (Apenas Zonas de Pickup)...")
    
    dados_projeto = {
        "direcional": True,
        "nos": {},
        "arestas": []
    }

    # Reverter projeção para ter Latitude/Longitude corretas
    G_proj = ox.project_graph(G, to_crs="EPSG:4326")
    
    # --- PROCESSAR NÓS ---
    for no_id, dados in G_proj.nodes(data=True):
        # SIMPLIFICAÇÃO: Todos os nós são apenas locais de passagem/recolha
        # Não criamos estações de recarga nem bombas de gasolina
        
        dados_projeto["nos"][str(no_id)] = {
            "tipo": "zona_pickup",  # <--- Forçamos este tipo para todos
            "coords": [dados['x'], dados['y']], # longitude, latitude
            "nome": f"Cruzamento {no_id}",
            "capacidade_recarga": 0 # Sem capacidade de recarga
        }

    # --- PROCESSAR ARESTAS ---
    for u, v, k, dados in G_proj.edges(keys=True, data=True):
        # Converter distância para Km
        dist_km = dados.get('length', 0) / 1000.0
        
        # Converter tempo para Minutos (se não existir, estima a 30km/h)
        tempo_min = dados.get('travel_time', 0) / 60.0
        if tempo_min == 0 and dist_km > 0:
            tempo_min = (dist_km / 30.0) * 60.0

        # Coordenadas dos nós
        ux = G_proj.nodes[u]['x']
        uy = G_proj.nodes[u]['y']
        vx = G_proj.nodes[v]['x']
        vy = G_proj.nodes[v]['y']

        fator = (
            (perlin(ux, uy, scale=0.005) +
            perlin(vx, vy, scale=0.005)) / 2
        ) * 0.7 + 1.5 


        dados_projeto["arestas"].append({
            "origem": str(u),
            "destino": str(v),
            "distancia": round(dist_km, 3),
            "tempo_base": round(tempo_min, 2),
            "fator_transito": round(fator, 3)  # Variação entre 0.7x a 1.3x
        })

    # --- GUARDAR ---
    os.makedirs(os.path.dirname(ficheiro_saida), exist_ok=True)
    
    with open(ficheiro_saida, 'w', encoding='utf-8') as f:
        json.dump(dados_projeto, f, indent=2, ensure_ascii=False)

    print(f"SUCESSO! Mapa guardado em '{ficheiro_saida}'")
    print(f"Total de Nós (Todos Pickup): {len(dados_projeto['nos'])}")
    print(f"Total de Arestas: {len(dados_projeto['arestas'])}")

if __name__ == "__main__":
    gerar_json_rede_viaria("Porto, Portugal")
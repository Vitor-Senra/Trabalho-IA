import math
from typing import Optional


def heuristica_distancia_euclidiana(grafo, no_atual: str, no_destino: str) -> float:

    if no_atual not in grafo.nos or no_destino not in grafo.nos:
        return float('inf')
    
    return grafo.distancia_euclidiana(no_atual, no_destino)


def heuristica_tempo_estimado(
    grafo,
    no_atual: str,
    no_destino: str,
    velocidade_media: float = 40.0
) -> float:

    distancia = heuristica_distancia_euclidiana(grafo, no_atual, no_destino)
    
    if distancia == float('inf'):
        return float('inf')
    
    # Converter para minutos: (distancia / velocidade) * 60
    return (distancia / velocidade_media) * 60.0


def heuristica_custo_estimado(
    grafo,
    no_atual: str,
    no_destino: str,
    custo_por_km: float = 0.20
) -> float:

    distancia = heuristica_distancia_euclidiana(grafo, no_atual, no_destino)
    
    if distancia == float('inf'):
        return float('inf')
    
    return distancia * custo_por_km


def heuristica_custo_veiculo(
    grafo,
    no_atual: str,
    no_destino: str,
    veiculo
) -> float:

    distancia = heuristica_distancia_euclidiana(grafo, no_atual, no_destino)
    
    if distancia == float('inf'):
        return float('inf')
    
    return distancia * veiculo.custo_por_km



def heuristica_com_autonomia(
    grafo,
    no_atual: str,
    no_destino: str,
    autonomia_disponivel: float,
    estacoes_recarga: list
) -> float:
    """
    Heurística que considera autonomia do veículo e localização de estações.
    
    Se a autonomia é insuficiente para chegar ao destino, considera a estação mais próxima.
    
    Args:
        grafo: Objeto Grafo
        no_atual: ID do nó atual
        no_destino: ID do nó destino
        autonomia_disponivel: Autonomia atual do veículo em km
        estacoes_recarga: Lista de IDs de estações de recarga
        
    Returns:
        float: Distância estimada considerando recargas
        
    """
    dist_direta = heuristica_distancia_euclidiana(grafo, no_atual, no_destino)
    
    if dist_direta == float('inf'):
        return float('inf')
    
    # Se tem autonomia suficiente, distância direta
    if autonomia_disponivel >= dist_direta:
        return dist_direta
    
    # Precisa de recarga - encontrar estação mais próxima
    if not estacoes_recarga:
        return float('inf')  # Sem estações disponíveis
    
    melhor_distancia = float('inf')
    
    for estacao in estacoes_recarga:
        # Distância até estação + distância da estação até destino
        dist_ate_estacao = heuristica_distancia_euclidiana(grafo, no_atual, estacao)
        dist_estacao_destino = heuristica_distancia_euclidiana(grafo, estacao, no_destino)
        
        dist_total = dist_ate_estacao + dist_estacao_destino
        
        if dist_total < melhor_distancia:
            melhor_distancia = dist_total
    
    return melhor_distancia


def criar_heuristica_ponderada(heuristica_base, peso: float = 1.5):
    """
    Cria uma versão ponderada de uma heurística.
    
        """
    def heuristica_ponderada(grafo, no_atual, no_destino):
        return peso * heuristica_base(grafo, no_atual, no_destino)
    
    return heuristica_ponderada


def selecionar_heuristica(metrica: str, **kwargs):
    """
    Função auxiliar para selecionar a heurística apropriada baseada na métrica.
    
    Args:
        metrica: 'distancia', 'tempo', 'custo', etc.
        **kwargs: Parâmetros adicionais (velocidade_media, custo_por_km, etc.)
        
    Returns:
        function: Função heurística apropriada
        
    Exemplo:
        h = selecionar_heuristica('tempo', velocidade_media=50)
        custo_h = h(grafo, 'A', 'B')
    """
    if metrica == 'distancia':
        return heuristica_distancia_euclidiana
    
    elif metrica == 'tempo':
        velocidade = kwargs.get('velocidade_media', 40.0)
        return lambda g, n1, n2: heuristica_tempo_estimado(g, n1, n2, velocidade)
    
    elif metrica == 'custo':
        custo_km = kwargs.get('custo_por_km', 0.20)
        return lambda g, n1, n2: heuristica_custo_estimado(g, n1, n2, custo_km)
        
    else:
        # Default: distância euclidiana
        return heuristica_distancia_euclidiana


# Dicionário de heurísticas disponíveis
HEURISTICAS_DISPONIVEIS = {
    'euclidiana': heuristica_distancia_euclidiana,
    'tempo': heuristica_tempo_estimado,
    'custo': heuristica_custo_estimado,
}


def comparar_heuristicas(grafo, no_atual: str, no_destino: str) -> dict:
    """
    Compara todas as heurísticas disponíveis para um par de nós.
        
    Args:
        grafo: Objeto Grafo
        no_atual: ID do nó atual
        no_destino: ID do nó destino
        
    Returns:
        dict: Dicionário com valores de cada heurística
    """
    resultados = {}
    
    for nome, funcao in HEURISTICAS_DISPONIVEIS.items():
        try:
            valor = funcao(grafo, no_atual, no_destino)
            resultados[nome] = round(valor, 2)
        except Exception as e:
            resultados[nome] = f"Erro: {str(e)}"
    
    return resultados
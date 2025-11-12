import heapq
from typing import List, Optional, Dict, Callable
from datetime import datetime
from .heuristicas import heuristica_distancia_euclidiana


class ResultadoAStar:
    """
    Classe para armazenar os resultados da procura A*.
    
    Attributes:
        caminho (List[str]): Lista de nós do caminho encontrado
        custo_total (float): Custo real g(n) - ÓTIMO se heurística admissível
        nos_expandidos (int): Número de nós expandidos
        tempo_execucao (float): Tempo de execução em segundos
        sucesso (bool): Se encontrou um caminho válido
        metrica (str): Métrica usada
        nos_visitados (int): Total de nós visitados
        heuristica_nome (str): Nome da heurística usada
    """
    
    def __init__(
        self,
        caminho: Optional[List[str]] = None,
        custo_total: float = float('inf'),
        nos_expandidos: int = 0,
        tempo_execucao: float = 0.0,
        sucesso: bool = False,
        metrica: str = 'distancia',
        nos_visitados: int = 0,
        heuristica_nome: str = 'euclidiana'
    ):
        self.caminho = caminho if caminho else []
        self.custo_total = custo_total
        self.nos_expandidos = nos_expandidos
        self.tempo_execucao = tempo_execucao
        self.sucesso = sucesso
        self.metrica = metrica
        self.nos_visitados = nos_visitados
        self.heuristica_nome = heuristica_nome
    
    def obter_resumo(self) -> Dict:
        """Retorna um resumo dos resultados"""
        return {
            'algoritmo': 'A*',
            'sucesso': self.sucesso,
            'caminho': self.caminho,
            'num_nos_caminho': len(self.caminho),
            'custo_total': round(self.custo_total, 2),
            'custo_otimo': True if self.sucesso else False,
            'metrica': self.metrica,
            'heuristica': self.heuristica_nome,
            'nos_expandidos': self.nos_expandidos,
            'nos_visitados': self.nos_visitados,
            'tempo_execucao_s': round(self.tempo_execucao, 4)
        }
    
    def __str__(self) -> str:
        if self.sucesso:
            return (
                f"A*: Caminho ÓTIMO com {len(self.caminho)} nós, "
                f"custo={self.custo_total:.2f}, "
                f"h={self.heuristica_nome}, "
                f"expandidos={self.nos_expandidos}"
            )
        return f"A*: Nenhum caminho encontrado (expandidos={self.nos_expandidos})"


def astar(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia',
    heuristica: Optional[Callable] = None
) -> ResultadoAStar:
    """
    Executa o algoritmo A* para encontrar o caminho de menor custo.
        
    Args:
        grafo: Objeto Grafo da cidade
        origem: ID do nó de origem
        destino: ID do nó de destino
        metrica: 'distancia' ou 'tempo' para cálculo de custo
        heuristica: Função heurística (padrão: distância euclidiana)
        
    Returns:
        ResultadoAStar: Objeto com o caminho ÓTIMO
        
    """
    inicio_execucao = datetime.now()
    
    # Usar heurística padrão se não fornecida
    if heuristica is None:
        heuristica = heuristica_distancia_euclidiana
        heuristica_nome = 'euclidiana'
    else:
        heuristica_nome = heuristica.__name__.replace('heuristica_', '')
    
    # Validações
    if origem not in grafo.nos:
        return ResultadoAStar(sucesso=False, metrica=metrica, heuristica_nome=heuristica_nome)
    
    if destino not in grafo.nos:
        return ResultadoAStar(sucesso=False, metrica=metrica, heuristica_nome=heuristica_nome)
    
    if origem == destino:
        return ResultadoAStar(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica,
            nos_visitados=1,
            heuristica_nome=heuristica_nome
        )
    
    # Estruturas de dados
    # Priority queue: (f(n), g(n), nó_atual)
    # f(n) = g(n) + h(n)
    h_inicial = heuristica(grafo, origem, destino)
    fila_prioridade = [(h_inicial, 0.0, origem)]
    
    # Dicionário de custos g(n) - custo real da origem até n
    custos_g = {origem: 0.0}
    
    # Dicionário de predecessores para reconstruir caminho
    predecessores = {origem: None}
    
    # Conjunto de nós já processados (fechados)
    visitados = set()
    
    nos_expandidos = 0
    
    # Algoritmo A*
    while fila_prioridade:
        f_atual, g_atual, no_atual = heapq.heappop(fila_prioridade)
        
        # Se já foi visitado (fechado), ignorar
        if no_atual in visitados:
            continue
        
        # Marcar como visitado
        visitados.add(no_atual)
        nos_expandidos += 1
        
        # Verificar se chegou ao destino
        if no_atual == destino:
            # Reconstruir caminho
            caminho = []
            no = destino
            while no is not None:
                caminho.append(no)
                no = predecessores[no]
            caminho.reverse()
            
            tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoAStar(
                caminho=caminho,
                custo_total=g_atual,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_execucao,
                sucesso=True,
                metrica=metrica,
                nos_visitados=len(visitados),
                heuristica_nome=heuristica_nome
            )
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho, aresta in vizinhos.items():
            # Se já foi fechado, ignorar
            if vizinho in visitados:
                continue
            
            # Calcular g(vizinho) = g(atual) + custo(atual -> vizinho)
            if metrica == 'distancia':
                custo_aresta = aresta.distancia
            else:  # tempo
                custo_aresta = aresta.tempo_atual()
            
            novo_g = g_atual + custo_aresta
            
            # Se encontrou um caminho melhor para o vizinho
            if vizinho not in custos_g or novo_g < custos_g[vizinho]:
                custos_g[vizinho] = novo_g
                predecessores[vizinho] = no_atual
                
                # Calcular f(vizinho) = g(vizinho) + h(vizinho)
                h_vizinho = heuristica(grafo, vizinho, destino)
                f_vizinho = novo_g + h_vizinho
                
                heapq.heappush(fila_prioridade, (f_vizinho, novo_g, vizinho))
    
    # Nenhum caminho encontrado
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoAStar(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_execucao,
        sucesso=False,
        metrica=metrica,
        nos_visitados=len(visitados),
        heuristica_nome=heuristica_nome
    )

import heapq
from typing import List, Optional, Dict, Callable
from datetime import datetime
from .heuristicas import heuristica_distancia_euclidiana


class ResultadoGreedy:
    """
    Classe para armazenar os resultados da procura Greedy.
    
    Attributes:
        caminho (List[str]): Lista de nós do caminho encontrado
        custo_total (float): Custo real do caminho (pode NÃO ser ótimo)
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
            'algoritmo': 'Greedy Best-First',
            'sucesso': self.sucesso,
            'caminho': self.caminho,
            'num_nos_caminho': len(self.caminho),
            'custo_total': round(self.custo_total, 2),
            'custo_otimo': False,  # Greedy NÃO garante ótimo
            'metrica': self.metrica,
            'heuristica': self.heuristica_nome,
            'nos_expandidos': self.nos_expandidos,
            'nos_visitados': self.nos_visitados,
            'tempo_execucao_s': round(self.tempo_execucao, 4)
        }
    
    def __str__(self) -> str:
        if self.sucesso:
            return (
                f"Greedy: Caminho com {len(self.caminho)} nós, "
                f"custo={self.custo_total:.2f}, "
                f"h={self.heuristica_nome}, "
                f"expandidos={self.nos_expandidos}"
            )
        return f"Greedy: Nenhum caminho encontrado (expandidos={self.nos_expandidos})"


def greedy(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia',
    heuristica: Optional[Callable] = None
) -> ResultadoGreedy:
    """
    Executa o algoritmo Greedy Best-First Search.
        
    Args:
        grafo: Objeto Grafo da cidade
        origem: ID do nó de origem
        destino: ID do nó de destino
        metrica: 'distancia' ou 'tempo' para cálculo de custo real
        heuristica: Função heurística (padrão: distância euclidiana)
        
    Returns:
        ResultadoGreedy: Objeto com o caminho encontrado (pode não ser ótimo)
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
        return ResultadoGreedy(sucesso=False, metrica=metrica, heuristica_nome=heuristica_nome)
    
    if destino not in grafo.nos:
        return ResultadoGreedy(sucesso=False, metrica=metrica, heuristica_nome=heuristica_nome)
    
    if origem == destino:
        return ResultadoGreedy(
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
    # Priority queue: (h(n), nó_atual, caminho, custo_g)
    # Ordena apenas por h(n) - ignora custo real g(n)
    h_inicial = heuristica(grafo, origem, destino)
    fila_prioridade = [(h_inicial, origem, [origem], 0.0)]
    
    # Conjunto de nós já visitados
    visitados = set()
    
    nos_expandidos = 0
    
    # Algoritmo Greedy
    while fila_prioridade:
        h_atual, no_atual, caminho_atual, g_atual = heapq.heappop(fila_prioridade)
        
        # Se já foi visitado, ignorar
        if no_atual in visitados:
            continue
        
        # Marcar como visitado
        visitados.add(no_atual)
        nos_expandidos += 1
        
        # Verificar se chegou ao destino
        if no_atual == destino:
            tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoGreedy(
                caminho=caminho_atual,
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
            # Se já foi visitado, ignorar
            if vizinho in visitados:
                continue
            
            # Calcular custo real até o vizinho (para estatísticas)
            if metrica == 'distancia':
                custo_aresta = aresta.distancia
            else:  # tempo
                custo_aresta = aresta.tempo_atual()
            
            novo_g = g_atual + custo_aresta
            
            # Calcular apenas h(vizinho) - ignora g!
            h_vizinho = heuristica(grafo, vizinho, destino)
            
            # Novo caminho
            novo_caminho = caminho_atual + [vizinho]
            
            # Adicionar à fila ordenado APENAS por h(n)
            heapq.heappush(fila_prioridade, (h_vizinho, vizinho, novo_caminho, novo_g))
    
    # Nenhum caminho encontrado
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoGreedy(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_execucao,
        sucesso=False,
        metrica=metrica,
        nos_visitados=len(visitados),
        heuristica_nome=heuristica_nome
    )

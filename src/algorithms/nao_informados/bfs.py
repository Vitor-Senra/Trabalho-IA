from collections import deque
from typing import List, Optional, Dict, Tuple
from datetime import datetime


class ResultadoBFS:
    """
    Classe para armazenar os resultados da procura BFS.
    
    Attributes:
        caminho (List[str]): Lista de nós do caminho encontrado
        custo_total (float): Custo total do caminho (distância ou tempo)
        nos_expandidos (int): Número de nós expandidos durante a procura
        tempo_execucao (float): Tempo de execução em segundos
        sucesso (bool): Se encontrou um caminho válido
        metrica (str): Métrica usada ('distancia' ou 'tempo')
    """
     
    def __init__(
        self,
        caminho: Optional[List[str]] = None,
        custo_total: float = float('inf'),
        nos_expandidos: int = 0,
        tempo_execucao: float = 0.0,
        sucesso: bool = False,
        metrica: str = 'distancia'
    ):
        self.caminho = caminho if caminho else []
        self.custo_total = custo_total
        self.nos_expandidos = nos_expandidos
        self.tempo_execucao = tempo_execucao
        self.sucesso = sucesso
        self.metrica = metrica
    
    def obter_resumo(self) -> Dict:
        """Retorna um resumo dos resultados"""
        return {
            'algoritmo': 'BFS',
            'sucesso': self.sucesso,
            'caminho': self.caminho,
            'num_nos_caminho': len(self.caminho),
            'custo_total': round(self.custo_total, 2),
            'metrica': self.metrica,
            'nos_expandidos': self.nos_expandidos,
            'tempo_execucao_s': round(self.tempo_execucao, 4)
        }
    
    def __str__(self) -> str:
        if self.sucesso:
            return (
                f"BFS: Caminho encontrado com {len(self.caminho)} nós, "
                f"custo={self.custo_total:.2f}, "
                f"expandidos={self.nos_expandidos}"
            )
        return f"BFS: Nenhum caminho encontrado (expandidos={self.nos_expandidos})"


def bfs(grafo, origem: str, destino: str, metrica: str = 'distancia') -> ResultadoBFS:
    """
    Executa o algoritmo BFS para encontrar um caminho entre origem e destino.
    
    BFS garante encontrar o caminho com menor número de arestas, mas não
    necessariamente o caminho de menor custo (distância ou tempo).
    
    Args:
        grafo: Objeto Grafo da cidade
        origem: ID do nó de origem
        destino: ID do nó de destino
        metrica: 'distancia' ou 'tempo' para cálculo de custo
        
    Returns:
        ResultadoBFS: Objeto com os resultados da procura
        
    Complexidade:
        Tempo: O(V + E) onde V = nós, E = arestas
        Espaço: O(V) para armazenar visitados e fila
    """
    inicio_execucao = datetime.now()
    
    # Validações
    if origem not in grafo.nos:
        return ResultadoBFS(sucesso=False, metrica=metrica)
    
    if destino not in grafo.nos:
        return ResultadoBFS(sucesso=False, metrica=metrica)
    
    if origem == destino:
        return ResultadoBFS(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica
        )
    
    # Estruturas de dados
    fila = deque([(origem, [origem])])  # (nó_atual, caminho_ate_aqui)
    visitados = {origem}
    nos_expandidos = 0
    
    # Procura BFS
    while fila:
        no_atual, caminho_atual = fila.popleft()
        nos_expandidos += 1
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho in vizinhos.keys():
            # Se já visitado, ignorar
            if vizinho in visitados:
                continue
            
            # Marcar como visitado
            visitados.add(vizinho)
            
            # Construir novo caminho
            novo_caminho = caminho_atual + [vizinho]
            
            # Verificar se chegou ao destino
            if vizinho == destino:
                # Calcular custo total do caminho
                custo_total = grafo.calcular_custo_caminho(novo_caminho, metrica)
                
                tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
                
                return ResultadoBFS(
                    caminho=novo_caminho,
                    custo_total=custo_total,
                    nos_expandidos=nos_expandidos,
                    tempo_execucao=tempo_execucao,
                    sucesso=True,
                    metrica=metrica
                )
            
            # Adicionar à fila
            fila.append((vizinho, novo_caminho))
    
    # Nenhum caminho encontrado
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoBFS(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_execucao,
        sucesso=False,
        metrica=metrica
    )


"""

FAZ SENTIDO MANTER ESTES ALGORITMOS?
OU SO O NORMAL, TEMOS DE DISCUTIR ISTO!!!!!

"""



def bfs_todos_caminhos(
    grafo,
    origem: str,
    max_distancia: float = float('inf'),
    metrica: str = 'distancia'
) -> Dict[str, Tuple[List[str], float]]:
    """
    Executa BFS para encontrar caminhos de origem para TODOS os nós alcançáveis.
    Útil para calcular distâncias de um veículo a todos os pedidos.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        max_distancia: Distância máxima a considerar (para autonomia)
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        Dict[str, Tuple[List[str], float]]: Dicionário {destino: (caminho, custo)}
    """
    if origem not in grafo.nos:
        return {}
    
    fila = deque([(origem, [origem], 0.0)])  # (nó, caminho, custo_acumulado)
    visitados = {origem}
    resultados = {origem: ([origem], 0.0)}
    
    while fila:
        no_atual, caminho_atual, custo_atual = fila.popleft()
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho, aresta in vizinhos.items():
            if vizinho in visitados:
                continue
            
            # Calcular custo até o vizinho
            if metrica == 'distancia':
                custo_aresta = aresta.distancia
            else:  # tempo
                custo_aresta = aresta.tempo_atual()
            
            novo_custo = custo_atual + custo_aresta
            
            # Verificar limite de distância (autonomia)
            if novo_custo > max_distancia:
                continue
            
            visitados.add(vizinho)
            novo_caminho = caminho_atual + [vizinho]
            
            resultados[vizinho] = (novo_caminho, novo_custo)
            fila.append((vizinho, novo_caminho, novo_custo))
    
    return resultados


def bfs_multiplos_destinos(
    grafo,
    origem: str,
    destinos: List[str],
    metrica: str = 'distancia'
) -> Dict[str, ResultadoBFS]:
    """
    Executa BFS para encontrar caminhos de origem para múltiplos destinos.
    Mais eficiente que executar BFS separadamente para cada destino.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destinos: Lista de nós de destino
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        Dict[str, ResultadoBFS]: Dicionário {destino: ResultadoBFS}
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos:
        return {dest: ResultadoBFS(sucesso=False) for dest in destinos}
    
    # Converter para conjunto para busca rápida
    destinos_set = set(destinos)
    destinos_encontrados = {}
    
    # BFS padrão
    fila = deque([(origem, [origem])])
    visitados = {origem}
    nos_expandidos = 0
    
    # Se origem é um dos destinos
    if origem in destinos_set:
        destinos_encontrados[origem] = ResultadoBFS(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica
        )
        destinos_set.remove(origem)
    
    while fila and destinos_set:
        no_atual, caminho_atual = fila.popleft()
        nos_expandidos += 1
        
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho in vizinhos.keys():
            if vizinho in visitados:
                continue
            
            visitados.add(vizinho)
            novo_caminho = caminho_atual + [vizinho]
            
            # Verificar se é um destino
            if vizinho in destinos_set:
                custo_total = grafo.calcular_custo_caminho(novo_caminho, metrica)
                tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
                
                destinos_encontrados[vizinho] = ResultadoBFS(
                    caminho=novo_caminho,
                    custo_total=custo_total,
                    nos_expandidos=nos_expandidos,
                    tempo_execucao=tempo_exec,
                    sucesso=True,
                    metrica=metrica
                )
                
                destinos_set.remove(vizinho)
            
            fila.append((vizinho, novo_caminho))
    
    # Adicionar destinos não encontrados
    tempo_final = (datetime.now() - inicio_execucao).total_seconds()
    for destino in destinos_set:
        destinos_encontrados[destino] = ResultadoBFS(
            nos_expandidos=nos_expandidos,
            tempo_execucao=tempo_final,
            sucesso=False,
            metrica=metrica
        )
    
    return destinos_encontrados


def bfs_com_restricao_autonomia(
    grafo,
    origem: str,
    destino: str,
    autonomia_disponivel: float,
    estacoes_recarga: List[str],
    metrica: str = 'distancia'
) -> ResultadoBFS:
    """
    BFS modificado que considera autonomia do veículo e localização de estações.
    Pode incluir paragens em estações de recarga no caminho.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino
        autonomia_disponivel: Autonomia atual do veículo em km
        estacoes_recarga: Lista de IDs de estações de recarga
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        ResultadoBFS: Resultado incluindo possíveis paragens em estações
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos or destino not in grafo.nos:
        return ResultadoBFS(sucesso=False, metrica=metrica)
    
    # Estado: (nó_atual, caminho, autonomia_restante)
    fila = deque([(origem, [origem], autonomia_disponivel)])
    visitados = {(origem, autonomia_disponivel)}  # (nó, autonomia) para permitir revisitar com mais autonomia
    nos_expandidos = 0
    
    while fila:
        no_atual, caminho_atual, autonomia_atual = fila.popleft()
        nos_expandidos += 1
        
        # Chegou ao destino?
        if no_atual == destino:
            custo_total = grafo.calcular_custo_caminho(caminho_atual, metrica)
            tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoBFS(
                caminho=caminho_atual,
                custo_total=custo_total,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_exec,
                sucesso=True,
                metrica=metrica
            )
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho, aresta in vizinhos.items():
            distancia = aresta.distancia
            
            # Verificar se tem autonomia suficiente
            if distancia > autonomia_atual:
                continue
            
            nova_autonomia = autonomia_atual - distancia
            
            # Se é estação de recarga, pode reabastecer
            if vizinho in estacoes_recarga:
                nova_autonomia = autonomia_disponivel  # Recarrega completamente
            
            estado = (vizinho, nova_autonomia)
            
            # Evitar revisitar com menos autonomia
            if any(v == vizinho and a >= nova_autonomia for v, a in visitados):
                continue
            
            visitados.add(estado)
            novo_caminho = caminho_atual + [vizinho]
            fila.append((vizinho, novo_caminho, nova_autonomia))
    
    tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
    return ResultadoBFS(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_exec,
        sucesso=False,
        metrica=metrica
    )

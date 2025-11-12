from typing import List, Optional, Dict, Set
from datetime import datetime


class ResultadoDFS:
    """
    Classe para armazenar os resultados da procura DFS.
    
    Attributes:
        caminho (List[str]): Lista de nós do caminho encontrado
        custo_total (float): Custo total do caminho
        nos_expandidos (int): Número de nós expandidos
        tempo_execucao (float): Tempo de execução em segundos
        sucesso (bool): Se encontrou um caminho válido
        metrica (str): Métrica usada
        profundidade_maxima (int): Profundidade máxima alcançada
    """
    
    def __init__(
        self,
        caminho: Optional[List[str]] = None,
        custo_total: float = float('inf'),
        nos_expandidos: int = 0,
        tempo_execucao: float = 0.0,
        sucesso: bool = False,
        metrica: str = 'distancia',
        profundidade_maxima: int = 0
    ):
        self.caminho = caminho if caminho else []
        self.custo_total = custo_total
        self.nos_expandidos = nos_expandidos
        self.tempo_execucao = tempo_execucao
        self.sucesso = sucesso
        self.metrica = metrica
        self.profundidade_maxima = profundidade_maxima
    
    def obter_resumo(self) -> Dict:
        """Retorna um resumo dos resultados"""
        return {
            'algoritmo': 'DFS',
            'sucesso': self.sucesso,
            'caminho': self.caminho,
            'num_nos_caminho': len(self.caminho),
            'custo_total': round(self.custo_total, 2),
            'metrica': self.metrica,
            'nos_expandidos': self.nos_expandidos,
            'profundidade_maxima': self.profundidade_maxima,
            'tempo_execucao_s': round(self.tempo_execucao, 4)
        }
    
    def __str__(self) -> str:
        if self.sucesso:
            return (
                f"DFS: Caminho encontrado com {len(self.caminho)} nós, "
                f"custo={self.custo_total:.2f}, "
                f"prof={self.profundidade_maxima}, "
                f"expandidos={self.nos_expandidos}"
            )
        return f"DFS: Nenhum caminho encontrado (expandidos={self.nos_expandidos})"


def dfs(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia',
    limite_profundidade: Optional[int] = None
) -> ResultadoDFS:
    """
    Executa o algoritmo DFS para encontrar um caminho entre origem e destino.
    
    DFS pode encontrar caminhos mais rapidamente que BFS em alguns casos,
    mas não garante o caminho mais curto.
    
    Args:
        grafo: Objeto Grafo da cidade
        origem: ID do nó de origem
        destino: ID do nó de destino
        metrica: 'distancia' ou 'tempo' para cálculo de custo
        limite_profundidade: Profundidade máxima permitida (None = ilimitada)
        
    Returns:
        ResultadoDFS: Objeto com os resultados da procura
        
    Complexidade:
        Tempo: O(V + E) onde V = nós, E = arestas
        Espaço: O(V) no pior caso (caminho mais longo)
    """
    inicio_execucao = datetime.now()
    
    # Validações
    if origem not in grafo.nos:
        return ResultadoDFS(sucesso=False, metrica=metrica)
    
    if destino not in grafo.nos:
        return ResultadoDFS(sucesso=False, metrica=metrica)
    
    if origem == destino:
        return ResultadoDFS(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica,
            profundidade_maxima=0
        )
    
    # Estruturas de dados
    pilha = [(origem, [origem], 0)]  # (nó_atual, caminho, profundidade)
    visitados = set()
    nos_expandidos = 0
    profundidade_max = 0
    
    # Procura DFS
    while pilha:
        no_atual, caminho_atual, profundidade = pilha.pop()
        
        # Verificar limite de profundidade
        if limite_profundidade is not None and profundidade > limite_profundidade:
            continue
        
        # Marcar como visitado
        if no_atual in visitados:
            continue
        
        visitados.add(no_atual)
        nos_expandidos += 1
        profundidade_max = max(profundidade_max, profundidade)
        
        # Verificar se chegou ao destino
        if no_atual == destino:
            custo_total = grafo.calcular_custo_caminho(caminho_atual, metrica)
            tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoDFS(
                caminho=caminho_atual,
                custo_total=custo_total,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_execucao,
                sucesso=True,
                metrica=metrica,
                profundidade_maxima=profundidade_max
            )
        
        # Expandir vizinhos (em ordem reversa para manter ordem na pilha)
        vizinhos = list(grafo.obter_vizinhos(no_atual).keys())
        for vizinho in reversed(vizinhos):
            if vizinho not in visitados:
                novo_caminho = caminho_atual + [vizinho]
                pilha.append((vizinho, novo_caminho, profundidade + 1))
    
    # Nenhum caminho encontrado
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoDFS(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_execucao,
        sucesso=False,
        metrica=metrica,
        profundidade_maxima=profundidade_max
    )



"""

FAZ SENTIDO MANTER ESTES ALGORITMOS?
OU SO O NORMAL, TEMOS DE DISCUTIR ISTO!!!!!

"""

def dfs_recursivo(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia'
) -> ResultadoDFS:
    """
    Implementação recursiva do DFS.
    Mais elegante mas pode causar stack overflow em grafos grandes.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        ResultadoDFS: Resultado da procura
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos or destino not in grafo.nos:
        return ResultadoDFS(sucesso=False, metrica=metrica)
    
    visitados = set()
    nos_expandidos = [0]  # Lista para permitir modificação em função interna
    profundidade_max = [0]
    
    def dfs_helper(no_atual: str, caminho: List[str], profundidade: int) -> Optional[List[str]]:
        """Função auxiliar recursiva"""
        visitados.add(no_atual)
        nos_expandidos[0] += 1
        profundidade_max[0] = max(profundidade_max[0], profundidade)
        
        # Chegou ao destino?
        if no_atual == destino:
            return caminho
        
        # Explorar vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        for vizinho in vizinhos.keys():
            if vizinho not in visitados:
                resultado = dfs_helper(vizinho, caminho + [vizinho], profundidade + 1)
                if resultado is not None:
                    return resultado
        
        return None
    
    # Executar DFS recursivo
    caminho_encontrado = dfs_helper(origem, [origem], 0)
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    if caminho_encontrado:
        custo_total = grafo.calcular_custo_caminho(caminho_encontrado, metrica)
        return ResultadoDFS(
            caminho=caminho_encontrado,
            custo_total=custo_total,
            nos_expandidos=nos_expandidos[0],
            tempo_execucao=tempo_execucao,
            sucesso=True,
            metrica=metrica,
            profundidade_maxima=profundidade_max[0]
        )
    
    return ResultadoDFS(
        nos_expandidos=nos_expandidos[0],
        tempo_execucao=tempo_execucao,
        sucesso=False,
        metrica=metrica,
        profundidade_maxima=profundidade_max[0]
    )


def dfs_iterative_deepening(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia',
    max_profundidade: int = 50
) -> ResultadoDFS:
    """
    DFS com aprofundamento iterativo (IDDFS).
    Combina vantagens de BFS (completude, otimalidade) com eficiência de memória do DFS.
    
    Executa DFS com limite de profundidade crescente até encontrar solução.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino
        metrica: 'distancia' ou 'tempo'
        max_profundidade: Profundidade máxima a tentar
        
    Returns:
        ResultadoDFS: Resultado da procura
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos or destino not in grafo.nos:
        return ResultadoDFS(sucesso=False, metrica=metrica)
    
    nos_expandidos_total = 0
    
    # Tentar profundidades crescentes
    for limite in range(max_profundidade + 1):
        resultado = dfs(grafo, origem, destino, metrica, limite_profundidade=limite)
        nos_expandidos_total += resultado.nos_expandidos
        
        if resultado.sucesso:
            tempo_total = (datetime.now() - inicio_execucao).total_seconds()
            resultado.nos_expandidos = nos_expandidos_total
            resultado.tempo_execucao = tempo_total
            return resultado
    
    # Não encontrou até profundidade máxima
    tempo_total = (datetime.now() - inicio_execucao).total_seconds()
    return ResultadoDFS(
        nos_expandidos=nos_expandidos_total,
        tempo_execucao=tempo_total,
        sucesso=False,
        metrica=metrica,
        profundidade_maxima=max_profundidade
    )


def dfs_todos_caminhos(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia',
    max_caminhos: int = 10
) -> List[ResultadoDFS]:
    """
    Encontra múltiplos caminhos entre origem e destino usando DFS.
    Útil para comparar alternativas de rota.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino
        metrica: 'distancia' ou 'tempo'
        max_caminhos: Número máximo de caminhos a encontrar
        
    Returns:
        List[ResultadoDFS]: Lista de caminhos encontrados, ordenados por custo
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos or destino not in grafo.nos:
        return [ResultadoDFS(sucesso=False, metrica=metrica)]
    
    caminhos_encontrados = []
    nos_expandidos = [0]
    
    def dfs_helper(no_atual: str, caminho: List[str], visitados: Set[str]):
        """Função auxiliar para encontrar todos os caminhos"""
        if len(caminhos_encontrados) >= max_caminhos:
            return
        
        nos_expandidos[0] += 1
        
        if no_atual == destino:
            custo = grafo.calcular_custo_caminho(caminho, metrica)
            tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
            
            caminhos_encontrados.append(ResultadoDFS(
                caminho=caminho.copy(),
                custo_total=custo,
                nos_expandidos=nos_expandidos[0],
                tempo_execucao=tempo_exec,
                sucesso=True,
                metrica=metrica,
                profundidade_maxima=len(caminho) - 1
            ))
            return
        
        vizinhos = grafo.obter_vizinhos(no_atual)
        for vizinho in vizinhos.keys():
            if vizinho not in visitados:
                visitados.add(vizinho)
                dfs_helper(vizinho, caminho + [vizinho], visitados)
                visitados.remove(vizinho)
    
    # Executar busca
    dfs_helper(origem, [origem], {origem})
    
    # Ordenar por custo
    caminhos_encontrados.sort(key=lambda r: r.custo_total)
    
    if not caminhos_encontrados:
        tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
        return [ResultadoDFS(
            nos_expandidos=nos_expandidos[0],
            tempo_execucao=tempo_exec,
            sucesso=False,
            metrica=metrica
        )]
    
    return caminhos_encontrados


def dfs_com_restricao_custo(
    grafo,
    origem: str,
    destino: str,
    custo_maximo: float,
    metrica: str = 'distancia'
) -> ResultadoDFS:
    """
    DFS que só explora caminhos até um custo máximo.
    Útil para considerar autonomia de veículos.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino
        custo_maximo: Custo máximo permitido
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        ResultadoDFS: Resultado da procura
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos or destino not in grafo.nos:
        return ResultadoDFS(sucesso=False, metrica=metrica)
    
    # Estado: (nó, caminho, custo_acumulado)
    pilha = [(origem, [origem], 0.0)]
    visitados = set()
    nos_expandidos = 0
    profundidade_max = 0
    
    while pilha:
        no_atual, caminho_atual, custo_atual = pilha.pop()
        
        # Verificar se excedeu custo
        if custo_atual > custo_maximo:
            continue
        
        if no_atual in visitados:
            continue
        
        visitados.add(no_atual)
        nos_expandidos += 1
        profundidade_max = max(profundidade_max, len(caminho_atual) - 1)
        
        # Chegou ao destino?
        if no_atual == destino:
            tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
            return ResultadoDFS(
                caminho=caminho_atual,
                custo_total=custo_atual,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_exec,
                sucesso=True,
                metrica=metrica,
                profundidade_maxima=profundidade_max
            )
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        for vizinho, aresta in vizinhos.items():
            if vizinho not in visitados:
                if metrica == 'distancia':
                    custo_aresta = aresta.distancia
                else:
                    custo_aresta = aresta.tempo_atual()
                
                novo_custo = custo_atual + custo_aresta
                
                if novo_custo <= custo_maximo:
                    novo_caminho = caminho_atual + [vizinho]
                    pilha.append((vizinho, novo_caminho, novo_custo))
    
    # Não encontrou
    tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
    return ResultadoDFS(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_exec,
        sucesso=False,
        metrica=metrica,
        profundidade_maxima=profundidade_max
    )
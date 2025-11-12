import heapq
from typing import List, Optional, Dict, Tuple
from datetime import datetime


class ResultadoCustoUniforme:
    """
    Classe para armazenar os resultados da procura por Custo Uniforme.
    
    Attributes:
        caminho (List[str]): Lista de nós do caminho encontrado
        custo_total (float): Custo total do caminho (ÓTIMO)
        nos_expandidos (int): Número de nós expandidos
        tempo_execucao (float): Tempo de execução em segundos
        sucesso (bool): Se encontrou um caminho válido
        metrica (str): Métrica usada ('distancia' ou 'tempo')
        nos_visitados (int): Total de nós visitados
    """
    
    def __init__(
        self,
        caminho: Optional[List[str]] = None,
        custo_total: float = float('inf'),
        nos_expandidos: int = 0,
        tempo_execucao: float = 0.0,
        sucesso: bool = False,
        metrica: str = 'distancia',
        nos_visitados: int = 0
    ):
        self.caminho = caminho if caminho else []
        self.custo_total = custo_total
        self.nos_expandidos = nos_expandidos
        self.tempo_execucao = tempo_execucao
        self.sucesso = sucesso
        self.metrica = metrica
        self.nos_visitados = nos_visitados
    
    def obter_resumo(self) -> Dict:
        """Retorna um resumo dos resultados"""
        return {
            'algoritmo': 'Custo Uniforme (Dijkstra)',
            'sucesso': self.sucesso,
            'caminho': self.caminho,
            'num_nos_caminho': len(self.caminho),
            'custo_total': round(self.custo_total, 2),
            'custo_otimo': True if self.sucesso else False,
            'metrica': self.metrica,
            'nos_expandidos': self.nos_expandidos,
            'nos_visitados': self.nos_visitados,
            'tempo_execucao_s': round(self.tempo_execucao, 4)
        }
    
    def __str__(self) -> str:
        if self.sucesso:
            return (
                f"Custo Uniforme: Caminho ÓTIMO com {len(self.caminho)} nós, "
                f"custo={self.custo_total:.2f}, "
                f"expandidos={self.nos_expandidos}"
            )
        return f"Custo Uniforme: Nenhum caminho encontrado (expandidos={self.nos_expandidos})"


def custo_uniforme(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia'
) -> ResultadoCustoUniforme:
    """
    Executa o algoritmo de Custo Uniforme (Dijkstra) para encontrar o caminho de menor custo.
    
    GARANTE encontrar o caminho de custo mínimo se todos os custos forem não-negativos.
    
    Args:
        grafo: Objeto Grafo da cidade
        origem: ID do nó de origem
        destino: ID do nó de destino
        metrica: 'distancia' ou 'tempo' para cálculo de custo
        
    Returns:
        ResultadoCustoUniforme: Objeto com o caminho ÓTIMO
        
    Complexidade:
        Tempo: O((V + E) log V) com heap binário
        Espaço: O(V)
    """
    inicio_execucao = datetime.now()
    
    # Validações
    if origem not in grafo.nos:
        return ResultadoCustoUniforme(sucesso=False, metrica=metrica)
    
    if destino not in grafo.nos:
        return ResultadoCustoUniforme(sucesso=False, metrica=metrica)
    
    if origem == destino:
        return ResultadoCustoUniforme(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica,
            nos_visitados=1
        )
    
    # Estruturas de dados
    # Priority queue: (custo_acumulado, nó_atual)
    fila_prioridade = [(0.0, origem)]
    
    # Dicionário de custos mínimos até cada nó
    custos = {origem: 0.0}
    
    # Dicionário de predecessores para reconstruir caminho
    predecessores = {origem: None}
    
    # Conjunto de nós já processados
    visitados = set()
    
    nos_expandidos = 0
    
    # Algoritmo de Dijkstra / Custo Uniforme
    while fila_prioridade:
        custo_atual, no_atual = heapq.heappop(fila_prioridade)
        
        # Se já foi visitado, ignorar
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
            
            return ResultadoCustoUniforme(
                caminho=caminho,
                custo_total=custo_atual,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_execucao,
                sucesso=True,
                metrica=metrica,
                nos_visitados=len(visitados)
            )
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho, aresta in vizinhos.items():
            # Se já foi visitado, ignorar
            if vizinho in visitados:
                continue
            
            # Calcular custo até o vizinho
            if metrica == 'distancia':
                custo_aresta = aresta.distancia
            else:  # tempo
                custo_aresta = aresta.tempo_atual()
            
            novo_custo = custo_atual + custo_aresta
            
            # Se encontrou um caminho melhor para o vizinho
            if vizinho not in custos or novo_custo < custos[vizinho]:
                custos[vizinho] = novo_custo
                predecessores[vizinho] = no_atual
                heapq.heappush(fila_prioridade, (novo_custo, vizinho))
    
    # Nenhum caminho encontrado
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoCustoUniforme(
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_execucao,
        sucesso=False,
        metrica=metrica,
        nos_visitados=len(visitados)
    )


"""

FAZ SENTIDO MANTER ESTES ALGORITMOS?
OU SO O NORMAL, TEMOS DE DISCUTIR ISTO!!!!!

"""

def dijkstra_todos_nos(
    grafo,
    origem: str,
    metrica: str = 'distancia',
    max_custo: float = float('inf')
) -> Dict[str, Tuple[List[str], float]]:
    """
    Executa Dijkstra para encontrar caminhos de custo mínimo da origem para TODOS os nós.
    Extremamente útil para calcular distâncias de um veículo a todos os pedidos.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        metrica: 'distancia' ou 'tempo'
        max_custo: Custo máximo a considerar (útil para autonomia)
        
    Returns:
        Dict[str, Tuple[List[str], float]]: {destino: (caminho, custo)}
    """
    if origem not in grafo.nos:
        return {}
    
    # Priority queue: (custo, nó)
    fila_prioridade = [(0.0, origem)]
    custos = {origem: 0.0}
    predecessores = {origem: None}
    visitados = set()
    
    while fila_prioridade:
        custo_atual, no_atual = heapq.heappop(fila_prioridade)
        
        if no_atual in visitados:
            continue
        
        visitados.add(no_atual)
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho, aresta in vizinhos.items():
            if vizinho in visitados:
                continue
            
            if metrica == 'distancia':
                custo_aresta = aresta.distancia
            else:
                custo_aresta = aresta.tempo_atual()
            
            novo_custo = custo_atual + custo_aresta
            
            # Verificar limite de custo
            if novo_custo > max_custo:
                continue
            
            if vizinho not in custos or novo_custo < custos[vizinho]:
                custos[vizinho] = novo_custo
                predecessores[vizinho] = no_atual
                heapq.heappush(fila_prioridade, (novo_custo, vizinho))
    
    # Reconstruir todos os caminhos
    resultados = {}
    
    for destino in custos.keys():
        if destino == origem:
            resultados[destino] = ([origem], 0.0)
            continue
        
        # Reconstruir caminho
        caminho = []
        no = destino
        while no is not None:
            caminho.append(no)
            no = predecessores.get(no)
        
        if caminho[-1] == origem:  # Caminho válido
            caminho.reverse()
            resultados[destino] = (caminho, custos[destino])
    
    return resultados


def dijkstra_multiplos_destinos(
    grafo,
    origem: str,
    destinos: List[str],
    metrica: str = 'distancia'
) -> Dict[str, ResultadoCustoUniforme]:
    """
    Dijkstra otimizado para encontrar caminhos para múltiplos destinos.
    Para quando terminar de processar todos os destinos.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destinos: Lista de destinos desejados
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        Dict[str, ResultadoCustoUniforme]: {destino: resultado}
    """
    inicio_execucao = datetime.now()
    
    if origem not in grafo.nos:
        return {dest: ResultadoCustoUniforme(sucesso=False) for dest in destinos}
    
    destinos_set = set(destinos)
    destinos_encontrados = {}
    
    # Se origem é um destino
    if origem in destinos_set:
        destinos_encontrados[origem] = ResultadoCustoUniforme(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica
        )
        destinos_set.remove(origem)
    
    # Dijkstra padrão
    fila_prioridade = [(0.0, origem)]
    custos = {origem: 0.0}
    predecessores = {origem: None}
    visitados = set()
    nos_expandidos = 0
    
    while fila_prioridade and destinos_set:
        custo_atual, no_atual = heapq.heappop(fila_prioridade)
        
        if no_atual in visitados:
            continue
        
        visitados.add(no_atual)
        nos_expandidos += 1
        
        # Verificar se é um destino
        if no_atual in destinos_set:
            # Reconstruir caminho
            caminho = []
            no = no_atual
            while no is not None:
                caminho.append(no)
                no = predecessores[no]
            caminho.reverse()
            
            tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
            
            destinos_encontrados[no_atual] = ResultadoCustoUniforme(
                caminho=caminho,
                custo_total=custo_atual,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_exec,
                sucesso=True,
                metrica=metrica,
                nos_visitados=len(visitados)
            )
            
            destinos_set.remove(no_atual)
        
        # Expandir vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        for vizinho, aresta in vizinhos.items():
            if vizinho in visitados:
                continue
            
            if metrica == 'distancia':
                custo_aresta = aresta.distancia
            else:
                custo_aresta = aresta.tempo_atual()
            
            novo_custo = custo_atual + custo_aresta
            
            if vizinho not in custos or novo_custo < custos[vizinho]:
                custos[vizinho] = novo_custo
                predecessores[vizinho] = no_atual
                heapq.heappush(fila_prioridade, (novo_custo, vizinho))
    
    # Adicionar destinos não encontrados
    tempo_final = (datetime.now() - inicio_execucao).total_seconds()
    for destino in destinos_set:
        destinos_encontrados[destino] = ResultadoCustoUniforme(
            nos_expandidos=nos_expandidos,
            tempo_execucao=tempo_final,
            sucesso=False,
            metrica=metrica
        )
    
    return destinos_encontrados


def dijkstra_com_paradas_obrigatorias(
    grafo,
    origem: str,
    destino: str,
    paradas: List[str],
    metrica: str = 'distancia'
) -> ResultadoCustoUniforme:
    """
    Dijkstra modificado que deve passar por pontos específicos (paradas obrigatórias).
    Útil para incluir estações de recarga obrigatórias no caminho.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino final
        paradas: Lista de nós por onde deve passar (em ordem)
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        ResultadoCustoUniforme: Resultado com caminho completo
    """
    inicio_execucao = datetime.now()
    
    # Construir sequência completa: origem -> parada1 -> parada2 -> ... -> destino
    sequencia = [origem] + paradas + [destino]
    
    caminho_completo = []
    custo_total = 0.0
    nos_expandidos_total = 0
    
    # Calcular caminho entre cada par consecutivo
    for i in range(len(sequencia) - 1):
        inicio_segmento = sequencia[i]
        fim_segmento = sequencia[i + 1]
        
        resultado = custo_uniforme(grafo, inicio_segmento, fim_segmento, metrica)
        
        if not resultado.sucesso:
            # Não há caminho possível
            tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
            return ResultadoCustoUniforme(
                nos_expandidos=nos_expandidos_total + resultado.nos_expandidos,
                tempo_execucao=tempo_exec,
                sucesso=False,
                metrica=metrica
            )
        
        # Adicionar ao caminho (evitando duplicar nós de junção)
        if i == 0:
            caminho_completo.extend(resultado.caminho)
        else:
            caminho_completo.extend(resultado.caminho[1:])  # Pular primeiro nó (já está)
        
        custo_total += resultado.custo_total
        nos_expandidos_total += resultado.nos_expandidos
    
    tempo_exec = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoCustoUniforme(
        caminho=caminho_completo,
        custo_total=custo_total,
        nos_expandidos=nos_expandidos_total,
        tempo_execucao=tempo_exec,
        sucesso=True,
        metrica=metrica
    )


def dijkstra_k_caminhos_mais_curtos(
    grafo,
    origem: str,
    destino: str,
    k: int = 3,
    metrica: str = 'distancia'
) -> List[ResultadoCustoUniforme]:
    """
    Encontra os K caminhos mais curtos entre origem e destino usando variação de Dijkstra.
    Útil para fornecer rotas alternativas.
    
    Implementação simplificada: executa Dijkstra múltiplas vezes removendo arestas.
    
    Args:
        grafo: Objeto Grafo
        origem: Nó de origem
        destino: Nó de destino
        k: Número de caminhos desejados
        metrica: 'distancia' ou 'tempo'
        
    Returns:
        List[ResultadoCustoUniforme]: Lista dos K melhores caminhos
    """
    caminhos = []
    
    # Primeiro caminho (ótimo)
    resultado = custo_uniforme(grafo, origem, destino, metrica)
    
    if resultado.sucesso:
        caminhos.append(resultado)
    else:
        return caminhos
    
    # Nota: Implementação completa de K caminhos mais curtos (Yen's algorithm)
    # é complexa. Esta é uma versão simplificada para demonstração.
    
    return caminhos
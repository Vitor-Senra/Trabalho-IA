from typing import List, Optional, Dict, Callable, Set
from datetime import datetime
from .heuristicas import heuristica_distancia_euclidiana
import random


class ResultadoHillClimbing:
    """
    Classe para armazenar os resultados do Hill Climbing.
    
    Attributes:
        caminho (List[str]): Lista de nós do caminho encontrado
        custo_total (float): Custo real do caminho
        nos_expandidos (int): Número de nós expandidos
        tempo_execucao (float): Tempo de execução em segundos
        sucesso (bool): Se encontrou o destino
        ficou_preso (bool): Se ficou preso em ótimo local
        metrica (str): Métrica usada
        heuristica_nome (str): Nome da heurística
    """
    
    def __init__(
        self,
        caminho: Optional[List[str]] = None,
        custo_total: float = float('inf'),
        nos_expandidos: int = 0,
        tempo_execucao: float = 0.0,
        sucesso: bool = False,
        ficou_preso: bool = False,
        metrica: str = 'distancia',
        heuristica_nome: str = 'euclidiana'
    ):
        self.caminho = caminho if caminho else []
        self.custo_total = custo_total
        self.nos_expandidos = nos_expandidos
        self.tempo_execucao = tempo_execucao
        self.sucesso = sucesso
        self.ficou_preso = ficou_preso
        self.metrica = metrica
        self.heuristica_nome = heuristica_nome
    
    def obter_resumo(self) -> Dict:
        """Retorna um resumo dos resultados"""
        return {
            'algoritmo': 'Hill Climbing',
            'sucesso': self.sucesso,
            'ficou_preso': self.ficou_preso,
            'caminho': self.caminho,
            'num_nos_caminho': len(self.caminho),
            'custo_total': round(self.custo_total, 2),
            'custo_otimo': False,
            'metrica': self.metrica,
            'heuristica': self.heuristica_nome,
            'nos_expandidos': self.nos_expandidos,
            'tempo_execucao_s': round(self.tempo_execucao, 4)
        }
    
    def __str__(self) -> str:
        if self.sucesso:
            return (
                f"Hill Climbing: Caminho com {len(self.caminho)} nós, "
                f"custo={self.custo_total:.2f}, "
                f"expandidos={self.nos_expandidos}"
            )
        elif self.ficou_preso:
            return f"Hill Climbing: Ficou preso em ótimo local após {self.nos_expandidos} nós"
        return f"Hill Climbing: Falhou (expandidos={self.nos_expandidos})"


def hill_climbing(
    grafo,
    origem: str,
    destino: str,
    metrica: str = 'distancia',
    heuristica: Optional[Callable] = None,
    max_iteracoes: int = 1000
) -> ResultadoHillClimbing:
    """
    Executa o algoritmo Hil Climbing.
        
    Args:
        grafo: Objeto Grafo
        origem: ID do nó de origem
        destino: ID do nó de destino
        metrica: 'distancia' ou 'tempo'
        heuristica: Função heurística
        max_iteracoes: Limite de iterações (evitar loops infinitos)
        
    Returns:
        ResultadoHillClimbing: Resultado da procura
        
    """
    inicio_execucao = datetime.now()
    
    if heuristica is None:
        heuristica = heuristica_distancia_euclidiana
        heuristica_nome = 'euclidiana'
    else:
        heuristica_nome = heuristica.__name__.replace('heuristica_', '')
    
    # Validações
    if origem not in grafo.nos or destino not in grafo.nos:
        return ResultadoHillClimbing(
            sucesso=False,
            metrica=metrica,
            heuristica_nome=heuristica_nome
        )
    
    if origem == destino:
        return ResultadoHillClimbing(
            caminho=[origem],
            custo_total=0.0,
            nos_expandidos=0,
            tempo_execucao=0.0,
            sucesso=True,
            metrica=metrica,
            heuristica_nome=heuristica_nome
        )
    
    # Inicialização
    no_atual = origem
    caminho = [origem]
    custo_acumulado = 0.0
    nos_expandidos = 0
    visitados = {origem}
    
    # Hill Climbing loop
    for iteracao in range(max_iteracoes):
        nos_expandidos += 1
        
        # Verificar se chegou ao destino
        if no_atual == destino:
            tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoHillClimbing(
                caminho=caminho,
                custo_total=custo_acumulado,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_execucao,
                sucesso=True,
                metrica=metrica,
                heuristica_nome=heuristica_nome
            )
        
        # Avaliar vizinhos
        vizinhos = grafo.obter_vizinhos(no_atual)
        
        melhor_vizinho = None
        melhor_h = float('inf')
        melhor_custo_aresta = 0
        
        for vizinho, aresta in vizinhos.items():
            # Evitar revisitar nós (prevenir ciclos)
            if vizinho in visitados:
                continue
            
            # Calcular heurística do vizinho
            h_vizinho = heuristica(grafo, vizinho, destino)
            
            # Manter o melhor (menor heurística)
            if h_vizinho < melhor_h:
                melhor_h = h_vizinho
                melhor_vizinho = vizinho
                
                if metrica == 'distancia':
                    melhor_custo_aresta = aresta.distancia
                else:
                    melhor_custo_aresta = aresta.tempo_atual()
        
        # Se nenhum vizinho é melhor, ficou preso
        if melhor_vizinho is None:
            tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoHillClimbing(
                caminho=caminho,
                custo_total=custo_acumulado,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_execucao,
                sucesso=False,
                ficou_preso=True,
                metrica=metrica,
                heuristica_nome=heuristica_nome
            )
        
        # Verificar se o melhor vizinho é realmente melhor que o atual
        h_atual = heuristica(grafo, no_atual, destino)
        
        if melhor_h >= h_atual:
            # Nenhum vizinho melhora - ótimo local
            tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
            
            return ResultadoHillClimbing(
                caminho=caminho,
                custo_total=custo_acumulado,
                nos_expandidos=nos_expandidos,
                tempo_execucao=tempo_execucao,
                sucesso=False,
                ficou_preso=True,
                metrica=metrica,
                heuristica_nome=heuristica_nome
            )
        
        # Mover para o melhor vizinho
        no_atual = melhor_vizinho
        caminho.append(no_atual)
        custo_acumulado += melhor_custo_aresta
        visitados.add(no_atual)
    
    # Atingiu limite de iterações
    tempo_execucao = (datetime.now() - inicio_execucao).total_seconds()
    
    return ResultadoHillClimbing(
        caminho=caminho,
        custo_total=custo_acumulado,
        nos_expandidos=nos_expandidos,
        tempo_execucao=tempo_execucao,
        sucesso=False,
        ficou_preso=True,
        metrica=metrica,
        heuristica_nome=heuristica_nome
    )


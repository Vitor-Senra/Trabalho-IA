import json
import math
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict


class TipoNo(str):
    """Tipos de nós no grafo"""
    ZONA_PICKUP = "zona_pickup"
    ESTACAO_RECARGA = "estacao_recarga"
    POSTO_ABASTECIMENTO = "posto_abastecimento"
    ZONA_MISTA = "zona_mista"  # Pode ser pickup e ter estação


class No:
    """
    Representa um nó no grafo da cidade
    
    Attributes:
        id (str): Identificador único do nó
        tipo (str): Tipo do nó (zona_pickup, estacao_recarga, etc.)
        coords (Tuple[float, float]): Coordenadas (x, y) do nó
        nome (str): Nome descritivo da localização
        capacidade_recarga (int): Capacidade de veículos em recarga (se aplicável)
        veiculos_em_recarga (int): Número atual de veículos em recarga
    """
    
    def __init__(
        self,
        id: str,
        tipo: str,
        coords: Tuple[float, float],
        nome: Optional[str] = None,
        capacidade_recarga: int = 0,
        zona: str = "periferia"
    ):
        self.id = id
        self.tipo = tipo
        self.coords = coords
        self.nome = nome if nome else id
        self.capacidade_recarga = capacidade_recarga
        self.zona = zona
        self.veiculos_em_recarga = 0
    
    def tem_recarga_disponivel(self) -> bool:
        """Verifica se há capacidade de recarga disponível"""
        if self.capacidade_recarga == 0:
            return False
        return self.veiculos_em_recarga < self.capacidade_recarga
    
    def pode_recarregar_eletrico(self) -> bool:
        """Verifica se o nó suporta recarga elétrica"""
        return self.tipo in [TipoNo.ESTACAO_RECARGA, TipoNo.ZONA_MISTA]
    
    def pode_abastecer_combustao(self) -> bool:
        """Verifica se o nó suporta abastecimento de combustão"""
        return self.tipo in [TipoNo.POSTO_ABASTECIMENTO, TipoNo.ZONA_MISTA]
    
    def eh_zona_centro(self) -> bool:
        return self.zona == "centro"
    
    def __str__(self) -> str:
        return f"No({self.id}, {self.tipo}, {self.coords})"
    
    def __repr__(self) -> str:
        return self.__str__()


class Aresta:
    """
    Representa uma aresta (conexão) entre dois nós
    
    Attributes:
        origem (str): ID do nó de origem
        destino (str): ID do nó de destino
        distancia (float): Distância em km
        tempo_base (float): Tempo base de viagem em minutos
        fator_transito (float): Fator de trânsito atual (1.0 = normal, >1.0 = lento)
    """
    
    def __init__(
        self,
        origem: str,
        destino: str,
        distancia: float,
        tempo_base: Optional[float] = None,
        fator_transito: float = 1.0
    ):
        self.origem = origem
        self.destino = destino
        self.distancia = distancia
        
        # Se tempo não fornecido, calcular baseado em velocidade média (40 km/h)
        self.tempo_base = tempo_base if tempo_base else (distancia / 40.0) * 60.0
        
        self.fator_transito = fator_transito
    
    def tempo_atual(self) -> float:
        """Calcula o tempo atual considerando o trânsito"""
        return self.tempo_base * self.fator_transito
    
    def __str__(self) -> str:
        return f"Aresta({self.origem}->{self.destino}, {self.distancia}km, {self.tempo_base:.1f}min)"


class Grafo:
    """
    Representa o grafo da cidade para o sistema TaxiGreen
    
    Attributes:
        nos (Dict[str, No]): Dicionário de nós indexados por ID
        arestas (Dict[str, Dict[str, Aresta]]): Arestas como grafo de adjacências
        direcional (bool): Se o grafo é direcional ou não
    """
    
    def __init__(self, direcional: bool = False):
        self.nos: Dict[str, No] = {}
        self.arestas: Dict[str, Dict[str, Aresta]] = defaultdict(dict)
        self.direcional = direcional
    
    def adicionar_no(
        self,
        id: str,
        tipo: str,
        coords: Tuple[float, float],
        nome: Optional[str] = None,
        capacidade_recarga: int = 0,
        zona: str = "periferia"
    ) -> No:
        """
        Adiciona um nó ao grafo
        
        Args:
            id: Identificador único do nó
            tipo: Tipo do nó
            coords: Coordenadas (x, y)
            nome: Nome descritivo
            capacidade_recarga: Capacidade de recarga
            
        Returns:
            No: O nó criado
        """
        no = No(id, tipo, coords, nome, capacidade_recarga, zona)
        self.nos[id] = no
        return no
    
    def adicionar_aresta(
        self,
        origem: str,
        destino: str,
        distancia: Optional[float] = None,
        tempo_base: Optional[float] = None,
        fator_transito: float = 1.0,
        bidirecional: bool = True
    ):
        """
        Adiciona uma aresta entre dois nós
        
        Args:
            origem: ID do nó de origem
            destino: ID do nó de destino
            distancia: Distância em km (calculada automaticamente se None)
            tempo_base: Tempo base em minutos
            fator_transito: Fator de trânsito
            bidirecional: Se deve criar aresta reversa também
        """
        if origem not in self.nos or destino not in self.nos:
            raise ValueError(f"Nós {origem} ou {destino} não existem no grafo")
        
        # Calcular distância euclidiana se não fornecida
        if distancia is None:
            x1, y1 = self.nos[origem].coords
            x2, y2 = self.nos[destino].coords
            distancia = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        aresta = Aresta(origem, destino, distancia, tempo_base, fator_transito)
        self.arestas[origem][destino] = aresta
        
        # Adicionar aresta reversa se não for direcional ou se bidirecional
        if not self.direcional or bidirecional:
            aresta_reversa = Aresta(destino, origem, distancia, tempo_base, fator_transito)
            self.arestas[destino][origem] = aresta_reversa
    
    def obter_vizinhos(self, no_id: str) -> Dict[str, Aresta]:
        """
        Obtém os vizinhos de um nó
        
        Args:
            no_id: ID do nó
            
        Returns:
            Dict[str, Aresta]: Dicionário de vizinhos e suas arestas
        """
        return self.arestas.get(no_id, {})
    
    def obter_distancia(self, origem: str, destino: str) -> Optional[float]:
        """
        Obtém a distância entre dois nós conectados
        
        Args:
            origem: ID do nó de origem
            destino: ID do nó de destino
            
        Returns:
            float: Distância em km, ou None se não conectados
        """
        if origem in self.arestas and destino in self.arestas[origem]:
            return self.arestas[origem][destino].distancia
        return None
    
    def obter_tempo(self, origem: str, destino: str) -> Optional[float]:
        """
        Obtém o tempo de viagem entre dois nós (considerando trânsito)
        
        Args:
            origem: ID do nó de origem
            destino: ID do nó de destino
            
        Returns:
            float: Tempo em minutos, ou None se não conectados
        """
        if origem in self.arestas and destino in self.arestas[origem]:
            return self.arestas[origem][destino].tempo_atual()
        return None
    
    def atualizar_transito(self, origem: str, destino: str, fator: float):
        """
        Atualiza o fator de trânsito de uma aresta
        
        Args:
            origem: ID do nó de origem
            destino: ID do nó de destino
            fator: Novo fator de trânsito (1.0 = normal)
        """
        if origem in self.arestas and destino in self.arestas[origem]:
            self.arestas[origem][destino].fator_transito = fator
    
    def distancia_euclidiana(self, no1: str, no2: str) -> float:
        """
        Calcula a distância euclidiana entre dois nós (heurística)
        
        Args:
            no1: ID do primeiro nó
            no2: ID do segundo nó
            
        Returns:
            float: Distância euclidiana
        """
        if no1 not in self.nos or no2 not in self.nos:
            return float('inf')
        
        x1, y1 = self.nos[no1].coords
        x2, y2 = self.nos[no2].coords
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def obter_estacoes_recarga(self) -> List[str]:
        """
        Retorna lista de IDs de nós com estações de recarga
        
        Returns:
            List[str]: IDs dos nós com recarga
        """
        return [
            no_id for no_id, no in self.nos.items()
            if no.pode_recarregar_eletrico()
        ]
    
    def obter_postos_abastecimento(self) -> List[str]:
        """
        Retorna lista de IDs de nós com postos de abastecimento
        
        Returns:
            List[str]: IDs dos nós com abastecimento
        """
        return [
            no_id for no_id, no in self.nos.items()
            if no.pode_abastecer_combustao()
        ]
    
    def obter_estacao_recarga_mais_proxima(self, no_id: str) -> Optional[str]:
        """
        Encontra a estação de recarga mais próxima (distância euclidiana)
        
        Args:
            no_id: ID do nó de referência
            
        Returns:
            str: ID da estação mais próxima, ou None se não houver
        """
        estacoes = self.obter_estacoes_recarga()
        if not estacoes:
            return None
        
        return min(estacoes, key=lambda e: self.distancia_euclidiana(no_id, e))
    
    def validar_caminho(self, caminho: List[str]) -> bool:
        """
        Valida se um caminho é válido no grafo
        
        Args:
            caminho: Lista de IDs de nós
            
        Returns:
            bool: True se o caminho é válido
        """
        if not caminho:
            return False
        
        for i in range(len(caminho) - 1):
            origem = caminho[i]
            destino = caminho[i + 1]
            
            if origem not in self.nos or destino not in self.nos:
                return False
            
            if destino not in self.arestas.get(origem, {}):
                return False
        
        return True
    
    def calcular_custo_caminho(self, caminho: List[str], metrica: str = 'distancia') -> float:
        """
        Calcula o custo total de um caminho
        
        Args:
            caminho: Lista de IDs de nós
            metrica: 'distancia' ou 'tempo'
            
        Returns:
            float: Custo total
        """
        if not self.validar_caminho(caminho):
            return float('inf')
        
        custo = 0.0
        for i in range(len(caminho) - 1):
            origem = caminho[i]
            destino = caminho[i + 1]
            
            if metrica == 'distancia':
                custo += self.arestas[origem][destino].distancia
            elif metrica == 'tempo':
                custo += self.arestas[origem][destino].tempo_atual()
        
        return custo
    
    def obter_nos_por_tipo(self, tipo: str) -> List[str]:
        """
        Retorna todos os nós de um determinado tipo
        
        Args:
            tipo: Tipo de nó
            
        Returns:
            List[str]: Lista de IDs
        """
        return [no_id for no_id, no in self.nos.items() if no.tipo == tipo]
    
    def existe_caminho(self, origem: str, destino: str) -> bool:
        """
        Verifica se existe algum caminho entre dois nós (BFS simples)
        
        Args:
            origem: ID do nó de origem
            destino: ID do nó de destino
            
        Returns:
            bool: True se existe caminho
        """
        if origem == destino:
            return True
        
        visitados = set()
        fila = [origem]
        
        while fila:
            atual = fila.pop(0)
            if atual == destino:
                return True
            
            visitados.add(atual)
            
            for vizinho in self.obter_vizinhos(atual).keys():
                if vizinho not in visitados:
                    fila.append(vizinho)
        
        return False
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas sobre o grafo
        
        Returns:
            Dict: Estatísticas do grafo
        """
        num_arestas = sum(len(vizinhos) for vizinhos in self.arestas.values())
        if not self.direcional:
            num_arestas //= 2
        
        distancia_total = sum(
            aresta.distancia
            for vizinhos in self.arestas.values()
            for aresta in vizinhos.values()
        )
        if not self.direcional:
            distancia_total /= 2
        
        return {
            'num_nos': len(self.nos),
            'num_arestas': num_arestas,
            'distancia_total_km': round(distancia_total, 2),
            'num_estacoes_recarga': len(self.obter_estacoes_recarga()),
            'num_postos_abastecimento': len(self.obter_postos_abastecimento()),
            'direcional': self.direcional
        }
    
    def salvar_json(self, filepath: str):
        """
        Salva o grafo em formato JSON
        
        Args:
            filepath: Caminho do arquivo
        """
        dados = {
            'direcional': self.direcional,
            'nos': {
                no_id: {
                    'tipo': no.tipo,
                    'coords': list(no.coords),
                    'nome': no.nome,
                    'capacidade_recarga': no.capacidade_recarga
                }
                for no_id, no in self.nos.items()
            },
            'arestas': [
                {
                    'origem': aresta.origem,
                    'destino': aresta.destino,
                    'distancia': aresta.distancia,
                    'tempo_base': aresta.tempo_base,
                    'fator_transito': aresta.fator_transito
                }
                for vizinhos in self.arestas.values()
                for aresta in vizinhos.values()
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def carregar_json(cls, filepath: str) -> 'Grafo':
        """
        Carrega um grafo de um arquivo JSON
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            Grafo: Instância do grafo carregado
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        grafo = cls(direcional=dados.get('direcional', False))
        
        # Adicionar nós
        for no_id, info in dados['nos'].items():
            grafo.adicionar_no(
                id=no_id,
                tipo=info['tipo'],
                coords=tuple(info['coords']),
                nome=info.get('nome'),
                capacidade_recarga=info.get('capacidade_recarga', 0),
                zona=info.get('zona', 'periferia')
            )
        
        # Adicionar arestas
        arestas_processadas = set()
        for aresta_info in dados['arestas']:
            origem = aresta_info['origem']
            destino = aresta_info['destino']
            
            # Evitar duplicatas em grafos não direcionais
            aresta_key = tuple(sorted([origem, destino]))
            if not grafo.direcional and aresta_key in arestas_processadas:
                continue
            
            grafo.adicionar_aresta(
                origem=origem,
                destino=destino,
                distancia=aresta_info['distancia'],
                tempo_base=aresta_info.get('tempo_base'),
                fator_transito=aresta_info.get('fator_transito', 1.0),
                bidirecional=not grafo.direcional
            )
            
            arestas_processadas.add(aresta_key)
        
        return grafo
    
    def __str__(self) -> str:
        return f"Grafo({len(self.nos)} nós, {sum(len(v) for v in self.arestas.values())} arestas)"
    
    def __repr__(self) -> str:
        return self.__str__()
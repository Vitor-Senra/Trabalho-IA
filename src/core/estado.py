from typing import List, Dict, Optional, Set
from datetime import datetime
from copy import deepcopy

from .pedido import PrioridadePedido


class Estado:
    """
    Representa o estado completo do sistema TaxiGreen num momento específico.
    Usado para algoritmos de procura e simulação.
    
    Attributes:
        timestamp (datetime): Momento do estado
        veiculos (Dict): Dicionário de veículos indexados por ID
        pedidos_pendentes (List): Lista de pedidos ainda não atendidos
        pedidos_ativos (List): Lista de pedidos em curso
        pedidos_concluidos (List): Lista de pedidos finalizados
        grafo: Referência ao grafo da cidade
    """
    
    def __init__(
        self,
        veiculos: Dict,
        pedidos_pendentes: List,
        grafo,
        timestamp: Optional[datetime] = None,
        pedidos_ativos: Optional[List] = None,
        pedidos_concluidos: Optional[List] = None
    ):
        self.timestamp = timestamp if timestamp else datetime.now()
        self.veiculos = veiculos  # Dict[str, Veiculo]
        self.pedidos_pendentes = pedidos_pendentes
        self.pedidos_ativos = pedidos_ativos if pedidos_ativos else []
        self.pedidos_concluidos = pedidos_concluidos if pedidos_concluidos else []
        self.grafo = grafo
        
        # Estatísticas do estado
        self._calcular_estatisticas()
    
    def _calcular_estatisticas(self):
        """Calcula estatísticas agregadas do estado atual"""
        self.num_veiculos_disponiveis = sum(
            1 for v in self.veiculos.values() if v.esta_disponivel()
        )
        
        self.num_veiculos_em_servico = sum(
            1 for v in self.veiculos.values() if not v.esta_disponivel()
        )
        
        self.num_veiculos_eletricos = sum(
            1 for v in self.veiculos.values() 
            if v.tipo_str == "eletrico"
        )
        
        self.num_veiculos_combustao = len(self.veiculos) - self.num_veiculos_eletricos
        
        # Autonomia média da frota
        autonomias = [v.autonomia_atual for v in self.veiculos.values()]
        self.autonomia_media = sum(autonomias) / len(autonomias) if autonomias else 0
    
    def obter_veiculos_disponiveis(self) -> List:
        """
        Retorna lista de veículos disponíveis
        
        Returns:
            List: Lista de objetos Veiculo disponíveis
        """
        return [v for v in self.veiculos.values() if v.esta_disponivel()]
    
    def obter_veiculos_necessitam_recarga(self, limiar: float = 0.2) -> List:
        """
        Retorna lista de veículos que necessitam recarga
        
        Args:
            limiar: Percentagem mínima de autonomia
            
        Returns:
            List: Lista de objetos Veiculo
        """
        return [v for v in self.veiculos.values() if v.necessita_recarga(limiar)]
    
    def tem_pedidos_pendentes(self) -> bool:
        """Verifica se há pedidos pendentes"""
        return len(self.pedidos_pendentes) > 0
    
    def todos_pedidos_atendidos(self) -> bool:
        """Verifica se todos os pedidos foram atendidos ou rejeitados"""
        return len(self.pedidos_pendentes) == 0 and len(self.pedidos_ativos) == 0
    
    def adicionar_pedido(self, pedido):
        """
        Adiciona um novo pedido ao estado
        Se o pedido for PREMIUM, insere no início da lista
        
        Args:
            pedido: Objeto Pedido
        """
        if pedido.prioridade == PrioridadePedido.PREMIUM:
            # Inserir no início da lista
            self.pedidos_pendentes.insert(0, pedido)
        else:
            self.pedidos_pendentes.append(pedido)
    
    def atribuir_pedido(self, pedido, veiculo) -> bool:
        """
        Atribui um pedido a um veículo
        
        Args:
            pedido: Objeto Pedido
            veiculo: Objeto Veiculo
            
        Returns:
            bool: True se atribuição bem-sucedida
        """
        if pedido not in self.pedidos_pendentes:
            return False
        
        if not veiculo.esta_disponivel():
            return False
        
        # Remover de pendentes e adicionar a ativos
        self.pedidos_pendentes.remove(pedido)
        self.pedidos_ativos.append(pedido)
        
        # Atribuir no pedido
        pedido.atribuir_veiculo(veiculo)
        
        # Atualizar estado do veículo
        veiculo.iniciar_viagem(pedido, pedido.destino)
        
        return True
    
    def concluir_pedido(self, pedido, distancia: float, custo: float):
        """
        Marca um pedido como concluído
        
        Args:
            pedido: Objeto Pedido
            distancia: Distância percorrida
            custo: Custo da viagem
        """
        if pedido in self.pedidos_ativos:
            self.pedidos_ativos.remove(pedido)
            self.pedidos_concluidos.append(pedido)
            
            pedido.concluir(distancia, custo)
            
            if pedido.veiculo_atribuido:
                pedido.veiculo_atribuido.finalizar_viagem(custo)
    
    def cancelar_pedido(self, pedido, motivo: str = ""):
        """
        Cancela um pedido
        
        Args:
            pedido: Objeto Pedido
            motivo: Motivo do cancelamento
        """
        if pedido in self.pedidos_pendentes:
            self.pedidos_pendentes.remove(pedido)
        elif pedido in self.pedidos_ativos:
            self.pedidos_ativos.remove(pedido)
        
        pedido.cancelar(motivo)
        
        # Liberar veículo se estava atribuído
        if pedido.veiculo_atribuido:
            pedido.veiculo_atribuido.finalizar_viagem()
    
    def rejeitar_pedido(self, pedido, motivo: str):
        """
        Rejeita um pedido
        
        Args:
            pedido: Objeto Pedido
            motivo: Motivo da rejeição
        """
        if pedido in self.pedidos_pendentes:
            self.pedidos_pendentes.remove(pedido)
        
        pedido.rejeitar(motivo)
        self.pedidos_concluidos.append(pedido)
    
    def verificar_pedidos_expirados(self):
        """Remove pedidos expirados da fila de pendentes"""
        expirados = [p for p in self.pedidos_pendentes if p.expirou()]
        
        for pedido in expirados:
            pedido.marcar_expirado()
            self.pedidos_pendentes.remove(pedido)
            self.pedidos_concluidos.append(pedido)
    
    def calcular_metricas_globais(self) -> Dict:
        """
        Calcula métricas globais do sistema
        
        Returns:
            Dict: Dicionário com métricas
        """
        pedidos_totais = (
            len(self.pedidos_pendentes) + 
            len(self.pedidos_ativos) + 
            len(self.pedidos_concluidos)
        )
        
        # Pedidos bem-sucedidos
        pedidos_bem_sucedidos = [
            p for p in self.pedidos_concluidos if p.foi_concluido()
        ]
        
        # Taxa de sucesso
        taxa_sucesso = (
            len(pedidos_bem_sucedidos) / pedidos_totais * 100 
            if pedidos_totais > 0 else 0
        )
        
        # Tempo médio de espera
        tempos_espera = [
            p.tempo_espera_real for p in pedidos_bem_sucedidos 
            if p.tempo_espera_real is not None
        ]
        tempo_medio_espera = (
            sum(tempos_espera) / len(tempos_espera) 
            if tempos_espera else 0
        )
        
        # Satisfação média
        satisfacoes = [
            p.satisfacao_cliente for p in pedidos_bem_sucedidos 
            if p.satisfacao_cliente is not None
        ]
        satisfacao_media = (
            sum(satisfacoes) / len(satisfacoes) 
            if satisfacoes else 0
        )
        
        # Custos e receitas
        custo_total = sum(v.custo_total for v in self.veiculos.values())
        receita_total = sum(v.receita_total for v in self.veiculos.values())
        lucro_total = receita_total - custo_total
        
        # Emissões
        emissoes_totais = sum(v.calcular_emissoes_totais() for v in self.veiculos.values())
        
        # Eficiência da frota (km com passageiros / km total)
        km_total = sum(v.km_total_percorridos for v in self.veiculos.values())
        km_com_passageiros = sum(v.km_com_passageiros for v in self.veiculos.values())
        eficiencia_frota = (
            km_com_passageiros / km_total * 100 
            if km_total > 0 else 0
        )
        
        # Taxa de ocupação da frota
        taxa_ocupacao = (
            self.num_veiculos_em_servico / len(self.veiculos) * 100 
            if len(self.veiculos) > 0 else 0
        )
        
        return {
            'timestamp': self.timestamp.isoformat(),
            'frota': {
                'num_veiculos_total': len(self.veiculos),
                'num_veiculos_disponiveis': self.num_veiculos_disponiveis,
                'num_veiculos_em_servico': self.num_veiculos_em_servico,
                'num_eletricos': self.num_veiculos_eletricos,
                'num_combustao': self.num_veiculos_combustao,
                'autonomia_media_km': round(self.autonomia_media, 2),
                'taxa_ocupacao_percent': round(taxa_ocupacao, 1)
            },
            'pedidos': {
                'total': pedidos_totais,
                'pendentes': len(self.pedidos_pendentes),
                'ativos': len(self.pedidos_ativos),
                'concluidos': len(self.pedidos_concluidos),
                'bem_sucedidos': len(pedidos_bem_sucedidos),
                'taxa_sucesso_percent': round(taxa_sucesso, 1)
            },
            'operacao': {
                'tempo_medio_espera_min': round(tempo_medio_espera, 2),
                'satisfacao_media': round(satisfacao_media, 1),
                'km_total': round(km_total, 2),
                'km_com_passageiros': round(km_com_passageiros, 2),
                'km_sem_passageiros': round(km_total - km_com_passageiros, 2),
                'eficiencia_frota_percent': round(eficiencia_frota, 1)
            },
            'financeiro': {
                'receita_total_euros': round(receita_total, 2),
                'custo_total_euros': round(custo_total, 2),
                'lucro_total_euros': round(lucro_total, 2)
            },
            'ambiental': {
                'emissoes_co2_kg': round(emissoes_totais, 2)
            }
        }
    
    def obter_estado_veiculo(self, veiculo_id: str) -> Optional[Dict]:
        """
        Obtém o estado de um veículo específico
        
        Args:
            veiculo_id: ID do veículo
            
        Returns:
            Dict: Estado do veículo ou None se não encontrado
        """
        if veiculo_id not in self.veiculos:
            return None
        
        return self.veiculos[veiculo_id].obter_estatisticas()
    
    def clonar(self) -> 'Estado':
        """
        Cria uma cópia profunda do estado (útil para simulações)
        
        Returns:
            Estado: Nova instância do estado
        """
        return Estado(
            veiculos=deepcopy(self.veiculos),
            pedidos_pendentes=deepcopy(self.pedidos_pendentes),
            grafo=self.grafo,  # Grafo não precisa deep copy
            timestamp=self.timestamp,
            pedidos_ativos=deepcopy(self.pedidos_ativos),
            pedidos_concluidos=deepcopy(self.pedidos_concluidos)
        )
    
    def eh_estado_objetivo(self) -> bool:
        """
        Verifica se este é um estado objetivo (todos pedidos atendidos)
        
        Returns:
            bool: True se é estado objetivo
        """
        return self.todos_pedidos_atendidos()
    
    def obter_acoes_possiveis(self) -> List[Dict]:
        """
        Retorna todas as ações possíveis a partir deste estado.
        Uma ação é atribuir um veículo disponível a um pedido pendente.
        
        Returns:
            List[Dict]: Lista de ações possíveis (pares veículo-pedido)
        """
        acoes = []
        veiculos_disp = self.obter_veiculos_disponiveis()
        
        VELOCIDADE_MEDIA_KMH = 40.0
        
        for pedido in self.pedidos_pendentes:
            tempo_decorrido = (self.timestamp - pedido.timestamp).total_seconds() / 60.0
            
            if tempo_decorrido > pedido.tempo_espera_maximo:
                continue

            for veiculo in veiculos_disp:
                # Estimar distância até à origem do pedido (onde está o cliente)
                dist_origem = self.grafo.distancia_euclidiana(
                    veiculo.localizacao, 
                    pedido.origem
                )
                
                tempo_ate_cliente = (dist_origem / VELOCIDADE_MEDIA_KMH) * 60.0
                
                if (tempo_decorrido + tempo_ate_cliente) > pedido.tempo_espera_maximo:
                    continue  # Este carro não serve, tenta o próximo

                # Estimar distância da viagem (do cliente ao destino)
                dist_viagem = self.grafo.distancia_euclidiana(
                    pedido.origem, 
                    pedido.destino
                )
                
                dist_total = dist_origem + dist_viagem
                
                # Verificar se veículo pode atender (autonomia e capacidade)
                if veiculo.pode_atender_pedido(pedido.num_passageiros, dist_total):
                    # Verificar preferências do cliente (ex: quer elétrico?)
                    if pedido.aceita_veiculo(veiculo):
                        acoes.append({
                            'tipo': 'atribuir',
                            'pedido': pedido,
                            'veiculo': veiculo,
                            'distancia_estimada': dist_total
                        })
        
        return acoes
    
    def aplicar_acao(self, acao: Dict) -> 'Estado':
        """
        Aplica uma ação e retorna um novo estado
        
        Args:
            acao: Dicionário com a ação
            
        Returns:
            Estado: Novo estado resultante
        """
        novo_estado = self.clonar()
        
        if acao['tipo'] == 'atribuir':
            pedido = acao['pedido']
            veiculo = acao['veiculo']
            
            # Encontrar objetos correspondentes no novo estado
            novo_pedido = next(p for p in novo_estado.pedidos_pendentes if p.id == pedido.id)
            novo_veiculo = novo_estado.veiculos[veiculo.id]
            
            # Atribuir
            novo_estado.atribuir_pedido(novo_pedido, novo_veiculo)
        
        return novo_estado
    
    def __str__(self) -> str:
        return (
            f"Estado({len(self.veiculos)} veículos, "
            f"{len(self.pedidos_pendentes)} pendentes, "
            f"{len(self.pedidos_ativos)} ativos)"
        )
    
    def __repr__(self) -> str:
        return self.__str__()
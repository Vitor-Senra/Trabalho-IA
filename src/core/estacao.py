from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime, timedelta


class TipoEstacao(Enum):
    """Tipos de estação"""
    RECARGA_ELETRICA = "recarga_eletrica"
    BOMBAS_GASOL = "bombas_gasol"


class EstadoEstacao(Enum):
    """Estado operacional da estação"""
    OPERACIONAL = "operacional"
    MANUTENCAO = "manutencao"
    FORA_SERVICO = "fora_servico"
    LOTADA = "lotada"


class Estacao:
    """
    Representa uma estação de recarga ou posto de abastecimento.
    
    Attributes:
        id (str): Identificador único da estação
        no_grafo (str): ID do nó no grafo onde está localizada
        tipo (TipoEstacao): Tipo de estação
        capacidade (int): Número máximo de veículos simultâneos
        velocidade_recarga (float): Velocidade de recarga em km/min de autonomia
        custo_por_kwh (float): Custo por kWh (para elétricas)
        custo_por_litro (float): Custo por litro (para combustão)
        estado (EstadoEstacao): Estado operacional
    """
    
    def __init__(
        self,
        id: str,
        no_grafo: str,
        tipo: TipoEstacao,
        capacidade: int = 4,
        velocidade_recarga: Optional[float] = None,
        custo_por_kwh: float = 0.30,
        custo_por_litro: float = 1.80
    ):
        self.id = id
        self.no_grafo = no_grafo
        self.tipo = tipo
        self.capacidade = capacidade
        self.estado = EstadoEstacao.OPERACIONAL
        
        # Velocidade de recarga (km de autonomia por minuto)
        # Elétrico: ~6.7 km/min (300km em ~45min)
        # Combustão: ~100 km/min (500km em ~5min)
        if velocidade_recarga is not None:
            self.velocidade_recarga = velocidade_recarga
        else:
            if tipo == TipoEstacao.RECARGA_ELETRICA:
                self.velocidade_recarga = 6.7
            elif tipo == TipoEstacao.BOMBAS_GASOL:
                self.velocidade_recarga = 100.0

        self.custo_por_kwh = custo_por_kwh
        self.custo_por_litro = custo_por_litro
        
        # Fila de veículos
        self.veiculos_em_atendimento: List[Dict] = []  # {veiculo, inicio, fim_estimado}
        self.fila_espera: List = []  # Lista de veículos aguardando
        
        # Estatísticas
        self.total_atendimentos = 0
        self.tempo_total_utilizacao = 0.0  # em minutos
        self.receita_total = 0.0
        
        # Falhas simuladas
        self.probabilidade_falha = 0.0  # 0.0 a 1.0
        self.tempo_ate_falha = None  # minutos até próxima falha
    
    def esta_disponivel(self) -> bool:
        """Verifica se a estação está disponível"""
        if self.estado != EstadoEstacao.OPERACIONAL:
            return False
        return len(self.veiculos_em_atendimento) < self.capacidade
    
    def esta_lotada(self) -> bool:
        """Verifica se a estação está na capacidade máxima"""
        return len(self.veiculos_em_atendimento) >= self.capacidade
    
    def pode_atender(self, veiculo) -> bool:
        """
        Verifica se a estação pode atender um veículo
        
        Args:
            veiculo: Objeto Veiculo
            
        Returns:
            bool: True se pode atender
        """
        if not self.esta_disponivel():
            return False
        
        from .veiculo import TipoVeiculo
        
        # Verificar compatibilidade de tipo
        if veiculo.tipo == TipoVeiculo.ELETRICO:
            return self.tipo in [TipoEstacao.RECARGA_ELETRICA]
        elif veiculo.tipo == TipoVeiculo.COMBUSTAO:
            return self.tipo in [TipoEstacao.BOMBAS_GASOL]
        
        return False
    
    def calcular_tempo_recarga(
        self, 
        veiculo, 
        percentagem_alvo: float = 1.0
    ) -> float:
        """
        Calcula o tempo necessário para recarga
        
        Args:
            veiculo: Objeto Veiculo
            percentagem_alvo: Percentagem desejada (0.0 a 1.0)
            
        Returns:
            float: Tempo em minutos
        """
        autonomia_necessaria = (
            percentagem_alvo * veiculo.autonomia_max - veiculo.autonomia_atual
        )
        
        if autonomia_necessaria <= 0:
            return 0.0
        
        from .veiculo import TipoVeiculo
        
        # Ajustar velocidade baseado no tipo de veículo
        velocidade = self.velocidade_recarga
        if veiculo.tipo == TipoVeiculo.COMBUSTAO and self.tipo != TipoEstacao.BOMBAS_GASOL:
            velocidade = 100.0  # Abastecimento sempre rápido
        
        return autonomia_necessaria / velocidade
    
    def calcular_custo_recarga(
        self, 
        veiculo, 
        percentagem_alvo: float = 1.0
    ) -> float:
        """
        Calcula o custo da recarga
        
        Args:
            veiculo: Objeto Veiculo
            percentagem_alvo: Percentagem desejada
            
        Returns:
            float: Custo em euros
        """
        autonomia_necessaria = (
            percentagem_alvo * veiculo.autonomia_max - veiculo.autonomia_atual
        )
        
        if autonomia_necessaria <= 0:
            return 0.0
        
        from .veiculo import TipoVeiculo
        
        if veiculo.tipo == TipoVeiculo.ELETRICO:
            # Assumindo ~0.2 kWh por km
            kwh_necessarios = autonomia_necessaria * 0.2
            return kwh_necessarios * self.custo_por_kwh
        else:  # Combustão
            # Assumindo ~0.08 litros por km
            litros_necessarios = autonomia_necessaria * 0.08
            return litros_necessarios * self.custo_por_litro
    
    def iniciar_atendimento(
        self, 
        veiculo, 
        percentagem_alvo: float = 1.0,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Inicia o atendimento de um veículo
        
        Args:
            veiculo: Objeto Veiculo
            percentagem_alvo: Percentagem de recarga desejada
            timestamp: Momento do início
            
        Returns:
            bool: True se iniciado com sucesso
        """
        if not self.pode_atender(veiculo):
            # Adicionar à fila de espera
            if veiculo not in self.fila_espera:
                self.fila_espera.append(veiculo)
            return False
        
        tempo_recarga = self.calcular_tempo_recarga(veiculo, percentagem_alvo)
        custo = self.calcular_custo_recarga(veiculo, percentagem_alvo)
        
        inicio = timestamp if timestamp else datetime.now()
        fim_estimado = inicio + timedelta(minutes=tempo_recarga)
        
        atendimento = {
            'veiculo': veiculo,
            'inicio': inicio,
            'fim_estimado': fim_estimado,
            'percentagem_alvo': percentagem_alvo,
            'custo': custo
        }
        
        self.veiculos_em_atendimento.append(atendimento)
        veiculo.iniciar_recarga()
        
        # Atualizar estado se lotada
        if self.esta_lotada():
            self.estado = EstadoEstacao.LOTADA
        
        return True
    
    def finalizar_atendimento(
        self, 
        veiculo, 
        timestamp: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Finaliza o atendimento de um veículo
        
        Args:
            veiculo: Objeto Veiculo
            timestamp: Momento da finalização
            
        Returns:
            float: Custo da recarga, ou None se não encontrado
        """
        # Encontrar atendimento
        atendimento = None
        for i, atend in enumerate(self.veiculos_em_atendimento):
            if atend['veiculo'].id == veiculo.id:
                atendimento = self.veiculos_em_atendimento.pop(i)
                break
        
        if not atendimento:
            return None
        
        # Calcular tempo real de utilização
        fim_real = timestamp if timestamp else datetime.now()
        tempo_utilizacao = (fim_real - atendimento['inicio']).total_seconds() / 60.0
        
        # Finalizar recarga no veículo
        veiculo.finalizar_recarga(atendimento['percentagem_alvo'])
        
        # Atualizar estatísticas
        self.total_atendimentos += 1
        self.tempo_total_utilizacao += tempo_utilizacao
        self.receita_total += atendimento['custo']
        
        # Atualizar estado
        if self.estado == EstadoEstacao.LOTADA:
            self.estado = EstadoEstacao.OPERACIONAL
        
        # Processar fila de espera
        if self.fila_espera and self.esta_disponivel():
            proximo_veiculo = self.fila_espera.pop(0)
            self.iniciar_atendimento(proximo_veiculo, timestamp=fim_real)
        
        return atendimento['custo']
    
    def atualizar_estado(self, timestamp: Optional[datetime] = None):
        """
        Atualiza o estado da estação (processa recargas concluídas)
        
        Args:
            timestamp: Momento atual
        """
        agora = timestamp if timestamp else datetime.now()
        
        # Verificar atendimentos concluídos
        concluidos = [
            atend for atend in self.veiculos_em_atendimento
            if agora >= atend['fim_estimado']
        ]
        
        for atendimento in concluidos:
            self.finalizar_atendimento(atendimento['veiculo'], timestamp=agora)
    
    def simular_falha(self, duracao_minutos: float = 30.0):
        """
        Simula uma falha na estação
        
        Args:
            duracao_minutos: Duração da falha em minutos
        """
        self.estado = EstadoEstacao.FORA_SERVICO
        self.tempo_ate_falha = duracao_minutos
    
    def reparar(self):
        """Repara a estação (volta ao estado operacional)"""
        self.estado = EstadoEstacao.OPERACIONAL
        self.tempo_ate_falha = None
    
    def calcular_taxa_utilizacao(self, tempo_total_operacao: float) -> float:
        """
        Calcula a taxa de utilização da estação
        
        Args:
            tempo_total_operacao: Tempo total de operação em minutos
            
        Returns:
            float: Taxa de utilização (0.0 a 1.0)
        """
        if tempo_total_operacao == 0:
            return 0.0
        
        tempo_max_possivel = self.capacidade * tempo_total_operacao
        return self.tempo_total_utilizacao / tempo_max_possivel
    
    def obter_tempo_espera_estimado(self) -> float:
        """
        Estima o tempo de espera para o próximo veículo na fila
        
        Returns:
            float: Tempo estimado em minutos
        """
        if self.esta_disponivel():
            return 0.0
        
        # Encontrar o atendimento que termina primeiro
        if not self.veiculos_em_atendimento:
            return 0.0
        
        agora = datetime.now()
        tempos_restantes = [
            (atend['fim_estimado'] - agora).total_seconds() / 60.0
            for atend in self.veiculos_em_atendimento
        ]
        
        return max(0, min(tempos_restantes))
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas da estação
        
        Returns:
            Dict: Estatísticas completas
        """
        return {
            'id': self.id,
            'no_grafo': self.no_grafo,
            'tipo': self.tipo.value,
            'estado': self.estado.value,
            'capacidade': self.capacidade,
            'veiculos_em_atendimento': len(self.veiculos_em_atendimento),
            'veiculos_na_fila': len(self.fila_espera),
            'esta_disponivel': self.esta_disponivel(),
            'total_atendimentos': self.total_atendimentos,
            'tempo_total_utilizacao_min': round(self.tempo_total_utilizacao, 2),
            'receita_total_euros': round(self.receita_total, 2),
            'tempo_espera_estimado_min': round(self.obter_tempo_espera_estimado(), 2)
        }
    
    def resetar_estatisticas(self):
        """Reseta as estatísticas da estação"""
        self.total_atendimentos = 0
        self.tempo_total_utilizacao = 0.0
        self.receita_total = 0.0
    
    def __str__(self) -> str:
        return (
            f"Estacao({self.id}, {self.tipo.value}, "
            f"{len(self.veiculos_em_atendimento)}/{self.capacidade})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()

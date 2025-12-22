from enum import Enum
from typing import Optional
from datetime import datetime, timedelta


class PrioridadePedido(Enum):
    """Níveis de prioridade dos pedidos"""
    NORMAL = 1
    PREMIUM = 2


class EstadoPedido(Enum):
    """Estados possíveis de um pedido"""
    PENDENTE = "pendente"
    ATRIBUIDO = "atribuido"
    EM_CURSO = "em_curso"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"
    REJEITADO = "rejeitado"
    EXPIRADO = "expirado"


class PreferenciaAmbiental(Enum):
    """Preferência ambiental do cliente"""
    INDIFERENTE = "indiferente"
    PREFERENCIA_ELETRICO = "preferencia_eletrico"
    APENAS_ELETRICO = "apenas_eletrico"


class Pedido:
    """
    Classe que representa um pedido de transporte.
    
    Attributes:
        id (str): Identificador único do pedido
        origem (str): Nó de origem no grafo
        destino (str): Nó de destino no grafo
        num_passageiros (int): Número de passageiros
        horario_pretendido (datetime): Horário desejado para a viagem
        prioridade (PrioridadePedido): Nível de prioridade
        preferencia_ambiental (PreferenciaAmbiental): Preferência por tipo de veículo
        tempo_espera_maximo (float): Tempo máximo de espera em minutos
        estado (EstadoPedido): Estado atual do pedido
    """
    
    # Contador para gerar IDs únicos
    _contador = 0
    
    def __init__(
        self,
        origem: str,
        destino: str,
        num_passageiros: int,
        timestamp: Optional[datetime] = None,
        horario_pretendido: Optional[datetime] = None,
        prioridade: PrioridadePedido = PrioridadePedido.NORMAL,
        preferencia_ambiental: PreferenciaAmbiental = PreferenciaAmbiental.INDIFERENTE,
        tempo_espera_maximo: Optional[float] = float('inf'),
        id: Optional[str] = None
    ):
        # Gerar ID único se não fornecido
        if id is None:
            Pedido._contador += 1
            self.id = f"P{Pedido._contador:04d}"
        else:
            self.id = id
        
        self.origem = origem
        self.destino = destino
        self.num_passageiros = num_passageiros
        self.timestamp = timestamp if timestamp else datetime.now()
        self.horario_pretendido = horario_pretendido if horario_pretendido else self.timestamp
        self.prioridade = prioridade
        self.preferencia_ambiental = preferencia_ambiental
        self.tempo_espera_maximo = tempo_espera_maximo
        self.estado = EstadoPedido.PENDENTE
        
        # Veículo atribuído (None se ainda não atribuído)
        self.veiculo_atribuido = None
        
        # Timestamps importantes
        self.timestamp_atribuicao = None
        self.timestamp_inicio_viagem = None
        self.timestamp_conclusao = None
        
        # Métricas do pedido
        self.tempo_espera_real = None  # em minutos
        self.distancia_percorrida = None  # em km
        self.custo_viagem = None  # em euros
        self.emissoes_co2 = None  # em gramas
        
        # Tentativas de atribuição (para diagnóstico)
        self.tentativas_atribuicao = 0
        self.motivos_rejeicao = []
        
        # Satisfação do cliente (calculada no final)
        self.satisfacao_cliente = None
    
    def esta_pendente(self) -> bool:
        """Verifica se o pedido está pendente"""
        return self.estado == EstadoPedido.PENDENTE
    
    def esta_ativo(self) -> bool:
        """Verifica se o pedido está ativo (atribuído ou em curso)"""
        return self.estado in [EstadoPedido.ATRIBUIDO, EstadoPedido.EM_CURSO]
    
    def foi_concluido(self) -> bool:
        """Verifica se o pedido foi concluído com sucesso"""
        return self.estado == EstadoPedido.CONCLUIDO
    
    def expirou(self) -> bool:
        """Verifica se o pedido expirou pelo tempo de espera"""
        if self.estado != EstadoPedido.PENDENTE:
            return False
        
        tempo_decorrido = (datetime.now() - self.timestamp).total_seconds() / 60.0
        return tempo_decorrido > self.tempo_espera_maximo
    
    def atribuir_veiculo(self, veiculo):
        """
        Atribui um veículo ao pedido
        
        Args:
            veiculo: Objeto Veiculo atribuído
        """
        self.veiculo_atribuido = veiculo
        self.estado = EstadoPedido.ATRIBUIDO
        self.timestamp_atribuicao = datetime.now()
        
        # Calcular tempo de espera até atribuição
        self.tempo_espera_real = (self.timestamp_atribuicao - self.timestamp).total_seconds() / 60.0
    
    def iniciar_viagem(self):
        """Marca o início da viagem"""
        self.estado = EstadoPedido.EM_CURSO
        self.timestamp_inicio_viagem = datetime.now()
    
    def concluir(self, distancia: float, custo: float):
        """
        Conclui o pedido
        
        Args:
            distancia: Distância total percorrida em km
            custo: Custo total da viagem em euros
        """
        self.estado = EstadoPedido.CONCLUIDO
        self.timestamp_conclusao = datetime.now()
        self.distancia_percorrida = distancia
        self.custo_viagem = custo
        
        # Calcular emissões se veículo atribuído
        if self.veiculo_atribuido:
            self.emissoes_co2 = distancia * self.veiculo_atribuido.emissao_co2_por_km
        
        # Calcular satisfação do cliente
        self._calcular_satisfacao()
    
    def cancelar(self, motivo: str = ""):
        """
        Cancela o pedido
        
        Args:
            motivo: Motivo do cancelamento
        """
        self.estado = EstadoPedido.CANCELADO
        if motivo:
            self.motivos_rejeicao.append(motivo)
    
    def rejeitar(self, motivo: str):
        """
        Rejeita o pedido
        
        Args:
            motivo: Motivo da rejeição
        """
        self.estado = EstadoPedido.REJEITADO
        self.motivos_rejeicao.append(motivo)
        self.tentativas_atribuicao += 1
    
    def marcar_expirado(self):
        """Marca o pedido como expirado"""
        self.estado = EstadoPedido.EXPIRADO
    
    def _calcular_satisfacao(self):
        """
        Calcula a satisfação do cliente (0-100)
        Baseado em tempo de espera, preferência ambiental, e prioridade
        """
        if not self.foi_concluido():
            return
        
        satisfacao = 100.0
        
        # Penalizar por tempo de espera excessivo
        if self.tempo_espera_real > self.tempo_espera_maximo * 0.5:
            penalizacao_tempo = min(30, (self.tempo_espera_real / self.tempo_espera_maximo) * 20)
            satisfacao -= penalizacao_tempo
        
        # Bonus por atender preferência ambiental
        if self.veiculo_atribuido:
            from .veiculo import TipoVeiculo
            
            if self.preferencia_ambiental == PreferenciaAmbiental.PREFERENCIA_ELETRICO:
                if self.veiculo_atribuido.tipo == TipoVeiculo.ELETRICO:
                    satisfacao += 10
            elif self.preferencia_ambiental == PreferenciaAmbiental.APENAS_ELETRICO:
                if self.veiculo_atribuido.tipo != TipoVeiculo.ELETRICO:
                    satisfacao -= 20
        
        # Ajustar por prioridade (clientes premium esperam mais)
        if self.prioridade == PrioridadePedido.PREMIUM:
            if self.tempo_espera_real > 5:
                satisfacao -= 15
        
        # Limitar entre 0 e 100
        self.satisfacao_cliente = max(0, min(100, satisfacao))
    
    def obter_valor_prioridade(self) -> int:
        """
        Retorna o valor numérico da prioridade para ordenação
        
        Returns:
            int: Valor da prioridade (maior = mais prioritário)
        """
        return self.prioridade.value
    
    def calcular_tempo_total(self) -> Optional[float]:
        """
        Calcula o tempo total desde criação até conclusão em minutos
        
        Returns:
            float: Tempo em minutos, ou None se não concluído
        """
        if not self.timestamp_conclusao:
            return None
        
        return (self.timestamp_conclusao - self.timestamp).total_seconds() / 60.0
    
    def calcular_tempo_viagem(self) -> Optional[float]:
        """
        Calcula o tempo da viagem em si (início até conclusão) em minutos
        
        Returns:
            float: Tempo em minutos, ou None se não concluído
        """
        if not self.timestamp_inicio_viagem or not self.timestamp_conclusao:
            return None
        
        return (self.timestamp_conclusao - self.timestamp_inicio_viagem).total_seconds() / 60.0
    
    def aceita_veiculo(self, veiculo) -> bool:
        """
        Verifica se o pedido aceita um determinado tipo de veículo
        
        Args:
            veiculo: Objeto Veiculo a verificar
            
        Returns:
            bool: True se aceita, False caso contrário
        """
        from .veiculo import TipoVeiculo
        
        if self.preferencia_ambiental == PreferenciaAmbiental.APENAS_ELETRICO:
            return veiculo.tipo == TipoVeiculo.ELETRICO
        
        return True
    
    def obter_estatisticas(self) -> dict:
        """
        Retorna um dicionário com as estatísticas do pedido
        
        Returns:
            dict: Estatísticas do pedido
        """
        stats = {
            'id': self.id,
            'origem': self.origem,
            'destino': self.destino,
            'num_passageiros': self.num_passageiros,
            'prioridade': self.prioridade.name,
            'preferencia_ambiental': self.preferencia_ambiental.value,
            'estado': self.estado.value,
            'tempo_espera_maximo': self.tempo_espera_maximo,
            'tempo_espera_real': round(self.tempo_espera_real, 2) if self.tempo_espera_real else None,
            'tentativas_atribuicao': self.tentativas_atribuicao
        }
        
        if self.veiculo_atribuido:
            stats['veiculo_id'] = self.veiculo_atribuido.id
            stats['tipo_veiculo'] = self.veiculo_atribuido.tipo.value
        
        if self.foi_concluido():
            stats['distancia_km'] = round(self.distancia_percorrida, 2)
            stats['custo_euros'] = round(self.custo_viagem, 2)
            stats['emissoes_co2_g'] = round(self.emissoes_co2, 2) if self.emissoes_co2 else 0
            stats['tempo_total_min'] = round(self.calcular_tempo_total(), 2)
            stats['tempo_viagem_min'] = round(self.calcular_tempo_viagem(), 2)
            stats['satisfacao_cliente'] = round(self.satisfacao_cliente, 1)
        
        if self.motivos_rejeicao:
            stats['motivos_rejeicao'] = self.motivos_rejeicao
        
        return stats
    
    def __str__(self) -> str:
        return f"Pedido({self.id}, {self.origem}->{self.destino}, {self.num_passageiros}pax, {self.estado.value})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __lt__(self, other):
        """Comparação para ordenação por prioridade (maior prioridade primeiro)"""
        if not isinstance(other, Pedido):
            return NotImplemented
        
        # Primeiro por prioridade (maior primeiro)
        if self.prioridade.value != other.prioridade.value:
            return self.prioridade.value > other.prioridade.value
        
        # Depois por timestamp (mais antigo primeiro)
        return self.timestamp < other.timestamp
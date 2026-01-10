from enum import Enum
from typing import Optional, Dict, List
from datetime import datetime
from abc import ABC, abstractmethod

# Removemos o Enum TipoVeiculo pois agora são classes
# Mantemos o EstadoVeiculo pois é partilhado
class EstadoVeiculo(Enum):
    DISPONIVEL = "disponivel"
    EM_SERVICO = "em_servico"
    A_CAMINHO = "a_caminho"
    EM_RECARGA = "em_recarga"          # Usado para elétricos
    EM_ABASTECIMENTO = "em_abastecimento" # Usado para combustão
    MANUTENCAO = "manutencao"
    FORA_SERVICO = "fora_servico"

class Veiculo(ABC):
    """
    Classe base abstrata para todos os veículos da frota TaxiGreen.
    """
    
    def __init__(
        self,
        id: str,
        autonomia_max: float,
        capacidade: int,
        custo_por_km: float,
        localizacao: str,
        autonomia_atual: Optional[float] = None
    ):
        self.id = id
        self.autonomia_max = autonomia_max
        self.autonomia_atual = autonomia_atual if autonomia_atual is not None else autonomia_max
        self.capacidade = capacidade
        self.custo_por_km = custo_por_km
        self.localizacao = localizacao
        self.estado = EstadoVeiculo.DISPONIVEL
        self.passageiros_atuais = 0
        
        # Estatísticas de operação
        self.km_total_percorridos = 0.0
        self.km_com_passageiros = 0.0
        self.km_sem_passageiros = 0.0
        self.numero_viagens = 0
        self.receita_total = 0.0
        self.custo_total = 0.0
        
        # Navegação
        self.pedido_atual = None
        self.destino_atual = None
        self.historico_localizacoes = [localizacao]
        self.ultimo_update = datetime.now()
        
        # Atributos de Rota (A*)
        self.rota_atual = []
        self.proximo_no_index = 0
        self.progresso_aresta = 0.0

        # Sistema de recarga/abastecimento
        self.tempo_em_recarga = 0  # Minutos acumulados na estação
        self.autonomia_ao_iniciar_recarga = 0  # Para calcular taxa de recarga

    @property
    @abstractmethod
    def emissao_co2_por_km(self) -> float:
        """Define a emissão de CO2 específica da subclasse"""
        pass

    @property
    @abstractmethod
    def tipo_str(self) -> str:
        """Retorna uma string representando o tipo ('eletrico' ou 'combustao')"""
        pass

    def esta_disponivel(self) -> bool:
        return self.estado == EstadoVeiculo.DISPONIVEL
    
    def pode_atender_pedido(self, num_passageiros: int, distancia_estimada: float) -> bool:
        if not self.esta_disponivel():
            return False
        if num_passageiros > self.capacidade:
            return False
        
        margem_seguranca = 1.2
        if self.autonomia_atual < distancia_estimada * margem_seguranca:
            return False
        return True
    
    def necessita_recarga(self, limiar: float = 0.2) -> bool:
        percentagem_autonomia = self.autonomia_atual / self.autonomia_max
        return percentagem_autonomia < limiar

    # Lógica de movimento comum a ambos
    def atualizar_posicao(self, grafo, passo_tempo_min: float = 1.0) -> bool:
        if not self.rota_atual:
            return False

        tempo_disponivel = passo_tempo_min
        chegou_ao_destino_final = False
        MAX_ITERACOES = 10
        iteracoes = 0

        while tempo_disponivel > 0 and iteracoes < MAX_ITERACOES:
            iteracoes += 1
            if self.proximo_no_index >= len(self.rota_atual):
                chegou_ao_destino_final = True
                break

            no_origem = self.rota_atual[self.proximo_no_index - 1]
            no_destino = self.rota_atual[self.proximo_no_index]

            tempo_total_aresta = max(0.01, grafo.obter_tempo(no_origem, no_destino))
            distancia_aresta = max(0.001, grafo.obter_distancia(no_origem, no_destino))

            tempo_restante_na_aresta = (1.0 - self.progresso_aresta) * tempo_total_aresta

            if tempo_disponivel >= tempo_restante_na_aresta:
                # Completa a aresta
                fracao = tempo_restante_na_aresta / tempo_total_aresta
                distancia_percorrida = fracao * distancia_aresta
                self._registrar_movimento(distancia_percorrida)
                
                tempo_disponivel -= tempo_restante_na_aresta
                self.localizacao = no_destino
                self.historico_localizacoes.append(self.localizacao)
                self.proximo_no_index += 1
                self.progresso_aresta = 0.0

                if self.proximo_no_index >= len(self.rota_atual):
                    self.rota_atual = []
                    chegou_ao_destino_final = True
                    break
            else:
                # Move parcialmente na aresta
                fracao = tempo_disponivel / tempo_total_aresta
                distancia_percorrida = fracao * distancia_aresta
                self._registrar_movimento(distancia_percorrida)
                
                self.progresso_aresta += fracao
                tempo_disponivel = 0

        self.autonomia_atual = max(0.0, self.autonomia_atual)
        self.ultimo_update = datetime.now()
        return chegou_ao_destino_final

    def _registrar_movimento(self, distancia: float):
        """Método auxiliar interno para atualizar estatísticas ao mover"""
        self.autonomia_atual -= distancia
        self.km_total_percorridos += distancia
        self.custo_total += distancia * self.custo_por_km
        
        if self.passageiros_atuais > 0:
            self.km_com_passageiros += distancia
        else:
            self.km_sem_passageiros += distancia

    def definir_rota(self, lista_nos_do_astar: List[str]):
        self.rota_atual = lista_nos_do_astar
        self.proximo_no_index = 1
        self.progresso_aresta = 0.0

    def iniciar_viagem(self, pedido, destino: str):
        self.estado = EstadoVeiculo.A_CAMINHO
        self.pedido_atual = pedido
        self.destino_atual = destino
        self.passageiros_atuais = pedido.num_passageiros
        self.numero_viagens += 1

    def finalizar_viagem(self, receita: float = 0.0):
        self.estado = EstadoVeiculo.DISPONIVEL
        self.pedido_atual = None
        self.destino_atual = None
        self.passageiros_atuais = 0
        self.receita_total += receita

    def finalizar_recarga(self, percentagem: float = 1.0):
        self.autonomia_atual = self.autonomia_max * percentagem
        self.estado = EstadoVeiculo.DISPONIVEL

    # Métodos Abstratos que as subclasses DEVEM implementar
    @abstractmethod
    def iniciar_recarga(self):
        pass

    @abstractmethod
    def tempo_recarga_estimado(self, percentagem_alvo: float = 1.0) -> float:
        pass

    def calcular_lucro(self) -> float:
        return self.receita_total - self.custo_total

    def calcular_emissoes_totais(self) -> float:
        return (self.km_total_percorridos * self.emissao_co2_por_km) / 1000.0

    def obter_estatisticas(self) -> Dict:
        return {
            'id': self.id,
            'tipo': self.tipo_str,
            'estado': self.estado.value,
            'localizacao': self.localizacao,
            'autonomia_atual': round(self.autonomia_atual, 2),
            'autonomia_max': self.autonomia_max,
            'percentagem_autonomia': round((self.autonomia_atual / self.autonomia_max) * 100, 1),
            'km_total': round(self.km_total_percorridos, 2),
            'lucro': round(self.calcular_lucro(), 2),
            'emissoes_co2_kg': round(self.calcular_emissoes_totais(), 2)
        }

    def __str__(self) -> str:
        return f"Veiculo({self.id}, {self.tipo_str}, {self.estado.value}, {self.localizacao})"


# --- Subclasses Especializadas ---

class VeiculoEletrico(Veiculo):
    """Veículo movido a eletricidade (zero emissões, recarga lenta)"""
    
    def __init__(self, id: str, autonomia_max: float, capacidade: int, custo_por_km: float, localizacao: str):
        super().__init__(id, autonomia_max, capacidade, custo_por_km, localizacao)

    @property
    def emissao_co2_por_km(self) -> float:
        return 0.0

    @property
    def tipo_str(self) -> str:
        return "eletrico"

    def iniciar_recarga(self):
        self.estado = EstadoVeiculo.EM_RECARGA

    def tempo_recarga_estimado(self, percentagem_alvo: float = 1.0) -> float:
        """Elétricos demoram ~10 mins para carga total"""
        autonomia_necessaria = (percentagem_alvo * self.autonomia_max) - self.autonomia_atual
        tempo_carga_completa = 10.0  # minutos (ajustado para visualização)
        return (autonomia_necessaria / self.autonomia_max) * tempo_carga_completa


class VeiculoCombustao(Veiculo):
    """Veículo a combustão (emissões altas, reabastecimento rápido)"""
    
    def __init__(self, id: str, autonomia_max: float, capacidade: int, custo_por_km: float, localizacao: str):
        super().__init__(id, autonomia_max, capacidade, custo_por_km, localizacao)

    @property
    def emissao_co2_por_km(self) -> float:
        return 120.0  # g/km

    @property
    def tipo_str(self) -> str:
        return "combustao"

    def iniciar_recarga(self):
        self.estado = EstadoVeiculo.EM_ABASTECIMENTO

    def tempo_recarga_estimado(self, percentagem_alvo: float = 1.0) -> float:
        """Combustão demora ~5 mins para tanque cheio"""
        autonomia_necessaria = (percentagem_alvo * self.autonomia_max) - self.autonomia_atual
        tempo_abastecimento_completo = 5.0 # minutos
        return (autonomia_necessaria / self.autonomia_max) * tempo_abastecimento_completo
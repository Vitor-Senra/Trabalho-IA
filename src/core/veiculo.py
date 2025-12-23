from enum import Enum
from typing import Optional, Dict
from datetime import datetime


class TipoVeiculo(Enum):
    """Tipos de motorização disponíveis"""
    ELETRICO = "eletrico"
    COMBUSTAO = "combustao"


class EstadoVeiculo(Enum):
    """Estados possíveis de um veículo"""
    DISPONIVEL = "disponivel"
    EM_SERVICO = "em_servico"
    A_CAMINHO = "a_caminho"
    EM_RECARGA = "em_recarga"
    EM_ABASTECIMENTO = "em_abastecimento"
    MANUTENCAO = "manutencao"
    FORA_SERVICO = "fora_servico"


class Veiculo:
    """
    Classe que representa um veículo da frota TaxiGreen.
    
    Attributes:
        id (str): Identificador único do veículo
        tipo (TipoVeiculo): Tipo de motorização
        autonomia_max (float): Autonomia máxima em km
        autonomia_atual (float): Autonomia atual em km
        capacidade (int): Número máximo de passageiros
        custo_por_km (float): Custo operacional por km em euros
        localizacao (str): Nó atual no grafo da cidade
        estado (EstadoVeiculo): Estado atual do veículo
        passageiros_atuais (int): Número de passageiros a bordo
        emissao_co2_por_km (float): Emissões de CO2 por km (g/km)
    """
    
    def __init__(
        self,
        id: str,
        tipo: TipoVeiculo,
        autonomia_max: float,
        capacidade: int,
        custo_por_km: float,
        localizacao: str,
        autonomia_atual: Optional[float] = None,
        emissao_co2_por_km: Optional[float] = None
    ):
        self.id = id
        self.tipo = tipo
        self.autonomia_max = autonomia_max
        self.autonomia_atual = autonomia_atual if autonomia_atual is not None else autonomia_max
        self.capacidade = capacidade
        self.custo_por_km = custo_por_km
        self.localizacao = localizacao
        self.estado = EstadoVeiculo.DISPONIVEL
        self.passageiros_atuais = 0
        
        # Emissões CO2 (0 para elétricos, ~120g/km para combustão)
        if emissao_co2_por_km is not None:
            self.emissao_co2_por_km = emissao_co2_por_km
        else:
            self.emissao_co2_por_km = 0.0 if tipo == TipoVeiculo.ELETRICO else 120.0
        
        # Estatísticas de operação
        self.km_total_percorridos = 0.0
        self.km_com_passageiros = 0.0
        self.km_sem_passageiros = 0.0
        self.numero_viagens = 0
        self.tempo_total_operacao = 0.0  # em minutos
        self.receita_total = 0.0
        self.custo_total = 0.0
        
        # Pedido atual (se em serviço)
        self.pedido_atual = None
        self.destino_atual = None
        
        # Histórico de localizações
        self.historico_localizacoes = [localizacao]
        
        # Timestamp da última atualização
        self.ultimo_update = datetime.now()
    
    def esta_disponivel(self) -> bool:
        """Verifica se o veículo está disponível para atender pedidos"""
        return self.estado == EstadoVeiculo.DISPONIVEL
    
    def pode_atender_pedido(self, num_passageiros: int, distancia_estimada: float) -> bool:
        """
        Verifica se o veículo pode atender um pedido específico
        
        Args:
            num_passageiros: Número de passageiros do pedido
            distancia_estimada: Distância estimada da viagem em km
            
        Returns:
            bool: True se pode atender, False caso contrário
        """
        # Verificar se está disponível
        if not self.esta_disponivel():
            return False
        
        # Verificar capacidade
        if num_passageiros > self.capacidade:
            return False
        
        # Verificar autonomia (com margem de segurança de 20%)
        margem_seguranca = 1.2
        if self.autonomia_atual < distancia_estimada * margem_seguranca:
            return False
        
        return True
    
    def necessita_recarga(self, limiar: float = 0.2) -> bool:
        """
        Verifica se o veículo precisa de recarga/reabastecimento
        
        Args:
            limiar: Percentagem mínima de autonomia (0.0 a 1.0)
            
        Returns:
            bool: True se precisa de recarga
        """
        percentagem_autonomia = self.autonomia_atual / self.autonomia_max
        return percentagem_autonomia < limiar
    
    def mover_para(self, nova_localizacao: str, distancia: float):
        """
        Move o veículo para uma nova localização
        
        Args:
            nova_localizacao: ID do nó de destino
            distancia: Distância percorrida em km
        """
        # Atualizar autonomia
        self.autonomia_atual -= distancia
        
        # Atualizar localização
        self.localizacao = nova_localizacao
        self.historico_localizacoes.append(nova_localizacao)
        
        # Atualizar estatísticas
        self.km_total_percorridos += distancia
        if self.passageiros_atuais > 0:
            self.km_com_passageiros += distancia
        else:
            self.km_sem_passageiros += distancia
        
        # Atualizar custos
        self.custo_total += distancia * self.custo_por_km
        
        # Atualizar timestamp
        self.ultimo_update = datetime.now()
    
    def iniciar_viagem(self, pedido, destino: str):
        """
        Inicia uma viagem com passageiros
        
        Args:
            pedido: Objeto Pedido associado
            destino: Nó de destino
        """
        self.estado = EstadoVeiculo.A_CAMINHO
        self.pedido_atual = pedido
        self.destino_atual = destino
        self.passageiros_atuais = pedido.num_passageiros
        self.numero_viagens += 1
    
    def finalizar_viagem(self, receita: float = 0.0):
        """
        Finaliza a viagem atual
        
        Args:
            receita: Receita gerada pela viagem em euros
        """
        self.estado = EstadoVeiculo.DISPONIVEL
        self.pedido_atual = None
        self.destino_atual = None
        self.passageiros_atuais = 0
        self.receita_total += receita
    
    def iniciar_recarga(self):
        """Inicia o processo de recarga/reabastecimento"""
        if self.tipo == TipoVeiculo.ELETRICO:
            self.estado = EstadoVeiculo.EM_RECARGA
        else:
            self.estado = EstadoVeiculo.EM_ABASTECIMENTO
    
    def finalizar_recarga(self, percentagem: float = 1.0):
        """
        Finaliza a recarga/reabastecimento
        
        Args:
            percentagem: Percentagem de recarga (0.0 a 1.0)
        """
        self.autonomia_atual = self.autonomia_max * percentagem
        self.estado = EstadoVeiculo.DISPONIVEL
    
    def tempo_recarga_estimado(self, percentagem_alvo: float = 1.0) -> float:
        """
        Calcula o tempo estimado de recarga em minutos
        
        Args:
            percentagem_alvo: Percentagem desejada (0.0 a 1.0)
            
        Returns:
            float: Tempo em minutos
        """
        autonomia_necessaria = (percentagem_alvo * self.autonomia_max) - self.autonomia_atual
        
        if self.tipo == TipoVeiculo.ELETRICO:
            # Elétrico: ~30-60 min para carga completa (dependendo do carregador)
            tempo_carga_completa = 45.0  # minutos
            return (autonomia_necessaria / self.autonomia_max) * tempo_carga_completa
        else:
            # Combustão: ~5 minutos para abastecimento completo
            tempo_abastecimento_completo = 5.0
            return (autonomia_necessaria / self.autonomia_max) * tempo_abastecimento_completo
    
    def calcular_eficiencia(self) -> float:
        """
        Calcula a eficiência operacional do veículo (km com passageiros / km total)
        
        Returns:
            float: Eficiência entre 0.0 e 1.0
        """
        if self.km_total_percorridos == 0:
            return 0.0
        return self.km_com_passageiros / self.km_total_percorridos
    
    def calcular_lucro(self) -> float:
        """
        Calcula o lucro líquido do veículo
        
        Returns:
            float: Lucro em euros
        """
        return self.receita_total - self.custo_total
    
    def calcular_emissoes_totais(self) -> float:
        """
        Calcula as emissões totais de CO2 em kg
        
        Returns:
            float: Emissões em kg
        """
        return (self.km_total_percorridos * self.emissao_co2_por_km) / 1000.0
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna um dicionário com todas as estatísticas do veículo
        
        Returns:
            Dict: Estatísticas completas
        """
        return {
            'id': self.id,
            'tipo': self.tipo.value,
            'estado': self.estado.value,
            'localizacao': self.localizacao,
            'autonomia_atual': round(self.autonomia_atual, 2),
            'autonomia_max': self.autonomia_max,
            'percentagem_autonomia': round((self.autonomia_atual / self.autonomia_max) * 100, 1),
            'km_total': round(self.km_total_percorridos, 2),
            'km_com_passageiros': round(self.km_com_passageiros, 2),
            'km_sem_passageiros': round(self.km_sem_passageiros, 2),
            'eficiencia': round(self.calcular_eficiencia() * 100, 1),
            'numero_viagens': self.numero_viagens,
            'receita_total': round(self.receita_total, 2),
            'custo_total': round(self.custo_total, 2),
            'lucro': round(self.calcular_lucro(), 2),
            'emissoes_co2_kg': round(self.calcular_emissoes_totais(), 2),
            'passageiros_atuais': self.passageiros_atuais
        }
    
    def resetar_estatisticas(self):
        """Reseta todas as estatísticas do veículo"""
        self.km_total_percorridos = 0.0
        self.km_com_passageiros = 0.0
        self.km_sem_passageiros = 0.0
        self.numero_viagens = 0
        self.tempo_total_operacao = 0.0
        self.receita_total = 0.0
        self.custo_total = 0.0
    
    def __str__(self) -> str:
        return f"Veiculo({self.id}, {self.tipo.value}, {self.estado.value}, {self.localizacao})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def definir_rota(self, lista_nos_do_astar):
        self.rota_atual = lista_nos_do_astar  # Ex: ['A', 'B', 'C']
        self.proximo_no_index = 1
        self.progresso_aresta = 0.0  # 0% a 100% entre o nó atual e o próximo

    def atualizar_posicao(self, grafo, passo_tempo_min: float = 1.0) -> bool:
        if not self.rota_atual:
            return False

        tempo_disponivel = passo_tempo_min
        chegou_ao_destino_final = False
        
        # Limitador de segurança: impede loop infinito se houver erro no mapa
        iteracoes_seguranca = 0 
        MAX_ITERACOES = 10 

        while tempo_disponivel > 0 and iteracoes_seguranca < MAX_ITERACOES:
            iteracoes_seguranca += 1
            
            no_origem = self.rota_atual[self.proximo_no_index - 1]
            no_destino = self.rota_atual[self.proximo_no_index]

            tempo_total_aresta = grafo.obter_tempo(no_origem, no_destino)
            
            if not tempo_total_aresta or tempo_total_aresta < 0.01:
                tempo_total_aresta = 0.01 

            tempo_restante_na_aresta = (1.0 - self.progresso_aresta) * tempo_total_aresta

            if tempo_disponivel >= tempo_restante_na_aresta:
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
                fracao_percorrida = tempo_disponivel / tempo_total_aresta
                self.progresso_aresta += fracao_percorrida
                tempo_disponivel = 0
        
        return chegou_ao_destino_final
import random
import heapq
from datetime import datetime, timedelta
from src.core.grafo import Grafo
from src.core.veiculo import (
    EstadoVeiculo, 
    TaxiEletrico, TaxiCombustao,
    taxiXLEletrica, taxiXLCombustao,
)
from src.core.pedido import Pedido, PrioridadePedido, PreferenciaAmbiental, EstadoPedido
from src.core.estado import Estado


class Simulador:
    def __init__(self, caminho_dados):
        print("-> A carregar mapa...")
        self.grafo = Grafo.carregar_json(caminho_dados)
        
        # Criar frota inicial diversificada
        nos_mapa = list(self.grafo.nos.keys())
        frota_temp = {}
        
        # 2 Táxis Elétricos (capacidade 4)
        frota_temp["T_E1"] = TaxiEletrico("T_E1", random.choice(nos_mapa))
        frota_temp["T_E2"] = TaxiEletrico("T_E2", random.choice(nos_mapa))
        
        # 2 Táxis Combustão (capacidade 4)
        frota_temp["T_C1"] = TaxiCombustao("T_C1", random.choice(nos_mapa))
        frota_temp["T_C2"] = TaxiCombustao("T_C2", random.choice(nos_mapa))
        
        # 1 TaxiXL Elétrica (capacidade 6)
        frota_temp["V_E1"] = taxiXLEletrica("V_E1", random.choice(nos_mapa))
        
        # 1 TaxiXL Combustão (capacidade 6)
        frota_temp["V_C1"] = taxiXLCombustao("V_C1", random.choice(nos_mapa))

        self.pedidos_pendentes = []
        self.tempo_atual = datetime.now()
        self.estado = Estado(frota_temp, self.pedidos_pendentes, self.grafo, self.tempo_atual)
        
        # Métricas de acompanhamento
        self.metricas = {
            'pedidos_expirados': 0,
            'pedidos_escalados': 0,
            'pedidos_concluidos': 0,
            'taxis_criados': 4,
            'taxixl_criadas': 2,
            'eventos_transito_total': 0
        }
        
        # Sistema de Algoritmos
        self.algoritmo_ativo = "A* (Ótimo)"
        
        print(f"✅ Frota inicial criada:")
        print(f"   - 2 Táxis Elétricos (4 passageiros)")
        print(f"   - 2 Táxis Combustão (4 passageiros)")
        print(f"   - 1 TaxiXL Elétrica (6 passageiros)")
        print(f"   - 1 TaxiXL Combustão (6 passageiros)")

    def definir_algoritmo(self, nome_algoritmo):
        """Define qual algoritmo de pathfinding usar."""
        self.algoritmo_ativo = nome_algoritmo
        print(f" [SISTEMA] Algoritmo de pathfinding alterado para: {nome_algoritmo}")
    
    def _obter_funcao_algoritmo(self):
        """
        Retorna a função do algoritmo baseada na escolha atual.
        Usa imports dinâmicos para permitir hot-swapping.
        """
        algoritmos = {
            "A* (Ótimo)": ("src.algorithms.informados.astar", "astar"),
            "Greedy (Rápido)": ("src.algorithms.informados.greedy", "greedy"),
            "Hill Climbing (Local)": ("src.algorithms.informados.hill_climbing", "hill_climbing"),
            "DFS (Profundidade)": ("src.algorithms.nao_informados.dfs", "dfs"),
            "BFS (Largura)": ("src.algorithms.nao_informados.bfs", "bfs"),
            "Uniforme (Custo)": ("src.algorithms.nao_informados.custo_uniforme", "custo_uniforme"),
        }
        
        if self.algoritmo_ativo in algoritmos:
            modulo_path, funcao_nome = algoritmos[self.algoritmo_ativo]
            try:
                modulo = __import__(modulo_path, fromlist=[funcao_nome])
                return getattr(modulo, funcao_nome)
            except (ImportError, AttributeError) as e:
                print(f"  {self.algoritmo_ativo} não disponível: {e}")
                print("    Usando A* como fallback")
                from src.algorithms.informados.astar import astar
                return astar
        else:
            print(f"  Algoritmo '{self.algoritmo_ativo}' desconhecido, usando A*")
            from src.algorithms.informados.astar import astar
            return astar

    def gerar_pedido_aleatorio(self):
        if random.random() < 0.3:  # 30% chance
            nos = list(self.grafo.nos.keys())
            origem = random.choice(nos)
            destinos = [n for n in nos if n != origem]
            
            if destinos:
                destino = random.choice(destinos)
                
                # Gerar número de passageiros (70% = 1-4, 30% = 5-6 para testar TaxiXL)
                if random.random() < 0.7:
                    num_passageiros = random.randint(1, 4)  # Táxi serve
                else:
                    num_passageiros = random.randint(5, 6)  # Só TaxiXL serve
                
                # 20% dos pedidos são PREMIUM
                if random.random() < 0.2:
                    prioridade = PrioridadePedido.PREMIUM
                    tempo_max = 30.0
                    tipo = "PREMIUM"
                else:
                    prioridade = PrioridadePedido.NORMAL
                    tempo_max = 60.0
                    tipo = "NORMAL"
                
                novo_pedido = Pedido(
                    origem, 
                    destino, 
                    num_passageiros,
                    prioridade=prioridade,
                    tempo_espera_maximo=tempo_max
                )
                
                self.estado.adicionar_pedido(novo_pedido)
                pax_info = f"{num_passageiros}pax"
                if num_passageiros > 4:
                    pax_info += " [TaxiXL]"
                print(f"[PEDIDO {tipo}] {origem} → {destino} ({pax_info}, Máx: {tempo_max:.0f}min)")

    def gerar_carro_aleatorio(self):
        """Gera veículo aleatório (TAXI ou TaxiXL, elétrico ou combustão)"""
        nos = list(self.grafo.nos.keys())
        local = random.choice(nos)
        
        # 70% TAXI, 30% TaxiXL
        if random.random() < 0.7:
            categoria = "TAXI"
            num_taxis = self.metricas['taxis_criados'] + 1
            self.metricas['taxis_criados'] = num_taxis
            
            # 50% elétrico, 50% combustão
            if random.random() < 0.5:
                vid = f"T_E{num_taxis}"
                novo_veiculo = TaxiEletrico(vid, local)
                tipo = "Táxi Elétrico"
            else:
                vid = f"T_C{num_taxis}"
                novo_veiculo = TaxiCombustao(vid, local)
                tipo = "Táxi Combustão"
        else:
            categoria = "TaxiXL"
            num_taxixl = self.metricas['taxixl_criadas'] + 1
            self.metricas['taxixl_criadas'] = num_taxixl
            
            if random.random() < 0.5:
                vid = f"V_E{num_taxixl}"
                novo_veiculo = taxiXLEletrica(vid, local)
                tipo = "TaxiXL Elétrica"
            else:
                vid = f"V_C{num_taxixl}"
                novo_veiculo = taxiXLCombustao(vid, local)
                tipo = "TaxiXL Combustão"
        
        self.estado.veiculos[vid] = novo_veiculo
        print(f"[VEÍCULO] {tipo} ({novo_veiculo.capacidade} lugares) adicionado em {local}")
        
    def criar_veiculo_manual(self, tipo_str, no_inicial, capacidade=None, autonomia=None):
        """
        Cria um veículo com parâmetros específicos.
        
        Args:
            tipo_str: "taxi_eletrico", "taxi_combustao", "taxixl_eletrica", "taxixl_combustao"
            no_inicial: Nó onde criar o veículo
            capacidade: Ignorado (cada tipo tem capacidade fixa)
            autonomia: Ignorado (cada tipo tem autonomia padrão)
        """
        tipo_str = tipo_str.lower().replace(" ", "_")
        
        if no_inicial not in self.grafo.nos:
            print(f"❌ Erro: Nó '{no_inicial}' não existe.")
            return

        # Criar veículo baseado no tipo
        if tipo_str in ["taxi_eletrico", "eletrico", "taxi"]:
            num_taxis = self.metricas['taxis_criados'] + 1
            self.metricas['taxis_criados'] = num_taxis
            vid = f"T_E{num_taxis}"
            novo_veiculo = TaxiEletrico(vid, no_inicial)
            tipo_nome = "Táxi Elétrico"
            
        elif tipo_str in ["taxi_combustao", "combustao"]:
            num_taxis = self.metricas['taxis_criados'] + 1
            self.metricas['taxis_criados'] = num_taxis
            vid = f"T_C{num_taxis}"
            novo_veiculo = TaxiCombustao(vid, no_inicial)
            tipo_nome = "Táxi Combustão"
            
        elif tipo_str in ["taxixl_eletrica", "taxixl_eletrico", "taxixl"]:
            num_taxixl = self.metricas['taxixl_criadas'] + 1
            self.metricas['taxixl_criadas'] = num_taxixl
            vid = f"V_E{num_taxixl}"
            novo_veiculo = taxiXLEletrica(vid, no_inicial)
            tipo_nome = "TaxiXL Elétrica"
            
        elif tipo_str in ["taxixl_combustao", "taxixl_combust"]:
            num_taxixl = self.metricas['taxixl_criadas'] + 1
            self.metricas['taxixl_criadas'] = num_taxixl
            vid = f"V_C{num_taxixl}"
            novo_veiculo = taxiXLCombustao(vid, no_inicial)
            tipo_nome = "TaxiXL Combustão"
        else:
            print(f"❌ Erro: Tipo '{tipo_str}' inválido.")
            print("   Tipos válidos: taxi_eletrico, taxi_combustao, taxixl_eletrica, taxixl_combustao")
            return
        
        self.estado.veiculos[vid] = novo_veiculo
        print(f"✅ {tipo_nome} criado em {no_inicial} (ID: {vid}, {novo_veiculo.capacidade} lugares)")

    def criar_pedido_manual(self, origem, destino, num_passageiros=1, premium=False):
        """Cria um pedido específico para testes controlados."""
        if origem not in self.grafo.nos:
            print(f"❌ [ERRO] A origem '{origem}' não existe no mapa.")
            return

        if destino not in self.grafo.nos:
            print(f"❌ [ERRO] O destino '{destino}' não existe no mapa.")
            return

        if premium:
            prioridade = PrioridadePedido.PREMIUM
            tempo_max = 30.0
            tipo = "PREMIUM"
        else:
            prioridade = PrioridadePedido.NORMAL
            tempo_max = 60.0
            tipo = "NORMAL"

        novo_pedido = Pedido(origem, destino, num_passageiros,
                            prioridade=prioridade,
                            tempo_espera_maximo=tempo_max)

        self.estado.adicionar_pedido(novo_pedido)
        
        # Indicar se precisa de TaxiXL
        pax_info = f"{num_passageiros} pax"
        if num_passageiros > 4:
            pax_info += " [REQUER TaxiXL]"
        
        print(f"✅ Pedido Manual {tipo} criado: {origem} -> {destino} ({pax_info}, {tempo_max}min)")

    # ✅ FIX 1: MOVER PARA DENTRO DA CLASSE
    def recarregar_veiculo(self, veiculo_id: str, forcado: bool = False) -> bool:
        """
        Envia um veículo para a estação de recarga/abastecimento mais próxima.
        """
        if veiculo_id not in self.estado.veiculos:
            print(f"❌ [ERRO] Veículo {veiculo_id} não encontrado")
            return False

        veiculo = self.estado.veiculos[veiculo_id]

        # Se não for forçado, verificar se está disponível
        if not forcado and veiculo.estado != EstadoVeiculo.DISPONIVEL:
            print(f"❌ [ERRO] Veículo {veiculo_id} não está disponível (Estado: {veiculo.estado.value})")
            return False

        # Identificar tipo de estação
        if veiculo.tipo_str == "eletrico":
            tipo_estacao = "estacao_recarga"
            nome_estacao = "RECARGA"
        else:
            tipo_estacao = "posto_abastecimento"
            nome_estacao = "ABASTECIMENTO"

        estacoes = [
            (no_id, no) for no_id, no in self.grafo.nos.items()
            if no.tipo == tipo_estacao
        ]

        if not estacoes:
            print(f"❌ [ERRO] Nenhuma estação de {nome_estacao} encontrada no mapa")
            return False

        estacao_mais_proxima = min(
            estacoes,
            key=lambda e: self.grafo.distancia_euclidiana(veiculo.localizacao, e[0])
        )

        no_estacao_id = estacao_mais_proxima[0]

        algoritmo = self._obter_funcao_algoritmo()
        resultado = algoritmo(
            self.grafo,
            veiculo.localizacao,
            no_estacao_id,
            metrica='tempo'
        )

        if not resultado.sucesso:
            print(f"❌ [ERRO] Não foi possível calcular rota para {no_estacao_id}")
            return False

        veiculo.definir_rota(resultado.caminho)
        veiculo.destino_atual = no_estacao_id

        # ✅ FIX PRINCIPAL: Marcar como missão de recarga
        veiculo.em_missao_recarga = True
        
        # ✅ FIX: Estado fica A_CAMINHO (não EM_RECARGA ainda)
        veiculo.estado = EstadoVeiculo.A_CAMINHO

        print(f"🔋 [{nome_estacao}] {veiculo_id} ({veiculo.categoria_veiculo}) enviado para {no_estacao_id} ({veiculo.autonomia_atual:.0f}km restantes)")
        return True

    def atualizar_prioridades_pedidos(self):
        """Verifica e atualiza prioridades de todos os pedidos pendentes."""
        pedidos_a_remover = []
        
        for pedido in self.estado.pedidos_pendentes:
            resultado = pedido.verificar_e_escalar_prioridade(self.tempo_atual)
            
            if resultado == "ESCALADO_CRITICO":
                tempo_restante = pedido.tempo_restante_minutos(self.tempo_atual)
                print(f"🚨 [CRÍTICO] Pedido {pedido.id} ({pedido.origem}→{pedido.destino}) escalado! Restam {tempo_restante:.1f}min")
                self.metricas['pedidos_escalados'] += 1
            
            elif resultado == "EXPIRAR":
                pedidos_a_remover.append(pedido)
                print(f"❌ [EXPIRADO] Pedido {pedido.id} cancelado após {pedido.tempo_espera_maximo:.0f}min")
                self.metricas['pedidos_expirados'] += 1
        
        for pedido in pedidos_a_remover:
            pedido.marcar_expirado()
            self.estado.pedidos_pendentes.remove(pedido)

    def _consumir_autonomia(self, veiculo, distancia):
        consumo = distancia * veiculo.consumo_por_km
        veiculo.autonomia_atual = max(0, veiculo.autonomia_atual - consumo)

    def _obter_distancia_estacao_mais_proxima(self, veiculo, localizacao_destino):
        """
        Calcula a distância até à estação de recarga mais próxima a partir de um destino.
        """
        tipo_estacao = "estacao_recarga" if veiculo.tipo_str == "eletrico" else "posto_abastecimento"

        estacoes = [
            (no_id, no) for no_id, no in self.grafo.nos.items()
            if no.tipo == tipo_estacao
        ]

        if not estacoes:
            return 50.0  # Fallback: assumir 50km se não houver estações

        estacao_mais_proxima = min(
            estacoes,
            key=lambda e: self.grafo.distancia_euclidiana(localizacao_destino, e[0])
        )

        return self.grafo.distancia_euclidiana(localizacao_destino, estacao_mais_proxima[0])

    def atualizar_movimento_veiculos(self):
        algoritmo = self._obter_funcao_algoritmo()

        for veiculo in self.estado.veiculos.values():

            # ===== RECARGA / ABASTECIMENTO =====
            if veiculo.estado in (EstadoVeiculo.EM_RECARGA, EstadoVeiculo.EM_ABASTECIMENTO):
                veiculo.tempo_em_recarga += 1
                progresso = veiculo.tempo_em_recarga / veiculo.tempo_recarga_estimado(1.0)

                veiculo.autonomia_atual = min(
                    veiculo.autonomia_max,
                    veiculo.autonomia_ao_iniciar_recarga +
                    progresso * (veiculo.autonomia_max - veiculo.autonomia_ao_iniciar_recarga)
                )

                if veiculo.autonomia_atual >= veiculo.autonomia_max * 0.999:
                    veiculo.autonomia_atual = veiculo.autonomia_max
                    veiculo.estado = EstadoVeiculo.DISPONIVEL
                    veiculo.tempo_em_recarga = 0
                    veiculo.destino_atual = None
                    print(f"✅ {veiculo.id} recarregado")

                continue

            # ===== VEÍCULO PARADO =====
            if veiculo.estado == EstadoVeiculo.DISPONIVEL:
                continue

            # ===== MOVIMENTO =====
            chegou = veiculo.atualizar_posicao(self.grafo, 0.4)

            if chegou:
                no_atual = self.grafo.nos.get(veiculo.localizacao)

                # ✅ FIX: SÓ TRATA ESTAÇÃO SE ESTIVER EM MISSÃO DE RECARGA
                if getattr(veiculo, "em_missao_recarga", False):
                    if no_atual and (
                        (veiculo.tipo_str == "eletrico" and no_atual.tipo == "estacao_recarga") or
                        (veiculo.tipo_str != "eletrico" and no_atual.tipo == "posto_abastecimento")
                    ):
                        veiculo.autonomia_ao_iniciar_recarga = veiculo.autonomia_atual
                        veiculo.tempo_em_recarga = 0
                        veiculo.estado = (
                            EstadoVeiculo.EM_RECARGA if veiculo.tipo_str == "eletrico"
                            else EstadoVeiculo.EM_ABASTECIMENTO
                        )
                        veiculo.em_missao_recarga = False
                        tipo_estacao = "RECARGA" if veiculo.tipo_str == "eletrico" else "ABASTECIMENTO"
                        print(f"🔌 {veiculo.id} chegou à estação de {tipo_estacao} - iniciando ({veiculo.autonomia_atual:.0f}km)")
                        continue
                    else:
                        # Chegou ao sítio errado durante missão de recarga
                        print(f"⚠️ ERRO: {veiculo.id} estava em missão de recarga mas chegou a {getattr(no_atual, 'tipo', 'desconhecido')}")
                        veiculo.em_missao_recarga = False
                        veiculo.estado = EstadoVeiculo.DISPONIVEL
                        veiculo.destino_atual = None
                        continue

                # Chegou ao pickup
                if veiculo.estado == EstadoVeiculo.A_CAMINHO:
                    veiculo.estado = EstadoVeiculo.EM_SERVICO
                    veiculo.pedido_atual.iniciar_viagem()

                    rota = algoritmo(
                        self.grafo,
                        veiculo.localizacao,
                        veiculo.pedido_atual.destino,
                        metrica="tempo"
                    )
                    if rota.sucesso:
                        veiculo.definir_rota(rota.caminho)
                    else:
                        veiculo.estado = EstadoVeiculo.DISPONIVEL
                        veiculo.pedido_atual = None

                # Chegou ao destino
                elif veiculo.estado == EstadoVeiculo.EM_SERVICO:
                    self.estado.concluir_pedido(veiculo.pedido_atual, 5, 10)
                    veiculo.estado = EstadoVeiculo.DISPONIVEL
                    veiculo.pedido_atual = None

    def correr_passo(self):
        """Avança 1 minuto na simulação."""
        self.tempo_atual += timedelta(minutes=1)
        
        self.atualizar_prioridades_pedidos()
        self.gerar_pedido_aleatorio()
        self.processar_atribuicoes_inteligente()
        self.atualizar_movimento_veiculos()
        self.verificar_e_recarregar_veiculos()

    def verificar_e_recarregar_veiculos(self, limiar=0.3, limiar_critico=0.15):
        """
        Verifica bateria dos veículos e envia para recarga quando necessário.
        """
        for v in self.estado.veiculos.values():
            percentagem_bateria = v.autonomia_atual / v.autonomia_max

            # CASO 1: Veículo disponível com bateria baixa
            if (
                v.estado == EstadoVeiculo.DISPONIVEL and
                percentagem_bateria < limiar
            ):
                self.recarregar_veiculo(v.id)

            # CASO 2: Veículo em serviço com bateria CRÍTICA - abortar viagem
            elif (
                v.estado in (EstadoVeiculo.A_CAMINHO, EstadoVeiculo.EM_SERVICO) and
                percentagem_bateria < limiar_critico
            ):
                print(f"⚠️  {v.id} com bateria crítica ({percentagem_bateria*100:.1f}%) - abortando viagem!")

                # Cancelar pedido atual se existir
                if v.pedido_atual:
                    # Devolver pedido para pendentes
                    if v.pedido_atual in self.estado.pedidos_ativos:
                        self.estado.pedidos_ativos.remove(v.pedido_atual)
                        v.pedido_atual.estado = EstadoPedido.PENDENTE
                        v.pedido_atual.veiculo_atribuido = None
                        self.estado.pedidos_pendentes.append(v.pedido_atual)
                        print(f"   Pedido {v.pedido_atual.id} devolvido à fila")

                    v.pedido_atual = None

                # Limpar rota e passageiros
                v.rota_atual = []
                v.proximo_no_index = 0
                v.progresso_aresta = 0.0
                v.passageiros_atuais = 0
                v.destino_atual = None

                # Marcar como disponível para poder ir recarregar
                v.estado = EstadoVeiculo.DISPONIVEL

                # Enviar para recarga imediatamente
                self.recarregar_veiculo(v.id)
                
    def processar_atribuicoes_inteligente(self):
        """
        Planeamento de Frota usando A* no Espaço de Estados.
        """
        if not self.estado.pedidos_pendentes or not self.estado.obter_veiculos_disponiveis():
            return

        print(f"[{self.tempo_atual.strftime('%H:%M')}] A planear atribuições (Smart)...")

        estado_inicial = self.estado.clonar()
        queue = []
        counter = 0
        
        h_inicial = self._heuristica_estado(estado_inicial)
        heapq.heappush(queue, (h_inicial, 0, counter, estado_inicial, []))
        
        melhor_caminho = []
        melhor_f = float('inf')
        iteracoes = 0
        MAX_ITERACOES = 50
        
        while queue and iteracoes < MAX_ITERACOES:
            f, g, _, estado_atual, caminho = heapq.heappop(queue)
            iteracoes += 1
            
            if not estado_atual.pedidos_pendentes:
                melhor_caminho = caminho
                break
            
            acoes_possiveis = estado_atual.obter_acoes_possiveis()
            
            if not acoes_possiveis:
                if f < melhor_f:
                    melhor_f = f
                    melhor_caminho = caminho
                continue

            for acao in acoes_possiveis:
                novo_estado = estado_atual.aplicar_acao(acao)
                custo_acao = acao['distancia_estimada']
                novo_g = g + custo_acao
                novo_h = self._heuristica_estado(novo_estado)
                novo_f = novo_g + novo_h
                
                counter += 1
                novo_caminho = caminho + [acao]
                heapq.heappush(queue, (novo_f, novo_g, counter, novo_estado, novo_caminho))

        if melhor_caminho:
            melhor_acao = melhor_caminho[0]
            pedido_clone = melhor_acao['pedido']
            veiculo_clone = melhor_acao['veiculo']
            
            # ✅ FIX 2: DEFINIR pedido_real e veiculo_real ANTES de usar
            pedido_real = next(p for p in self.estado.pedidos_pendentes if p.id == pedido_clone.id)
            veiculo_real = self.estado.veiculos[veiculo_clone.id]
            
            # ✅ Agora sim pode usar
            veiculo_real.em_missao_recarga = False
            veiculo_real.destino_atual = pedido_real.origem

            print(f"[INTELIGENTE] Decisão: Atribuir {veiculo_real.id} ({veiculo_real.categoria_veiculo}) ao pedido {pedido_real.id} ({pedido_real.num_passageiros}pax, {pedido_real.prioridade.name})")
            
            self.estado.atribuir_pedido(pedido_real, veiculo_real)
            veiculo_real.estado = EstadoVeiculo.A_CAMINHO
            
            algoritmo = self._obter_funcao_algoritmo()
            rota_pickup = algoritmo(
                self.grafo, 
                veiculo_real.localizacao, 
                pedido_real.origem, 
                metrica='tempo'
            )
            
            if rota_pickup.sucesso:
                veiculo_real.definir_rota(rota_pickup.caminho)
            else:
                print(f"❌ [ERRO] Falha ao calcular rota física para {veiculo_real.id}")

    def _heuristica_estado(self, estado):
        """Heurística Multiobjetivo com Sistema de Prioridades."""
        custo_estimado_total = 0
        veiculos_disponiveis = estado.obter_veiculos_disponiveis()
        
        if not veiculos_disponiveis and estado.pedidos_pendentes:
            return len(estado.pedidos_pendentes) * 10000.0
            
        agora = estado.timestamp
        total_frota = len(estado.veiculos)
        carros_centro = 0
        
        if total_frota > 0:
            for v in estado.veiculos.values():
                no = estado.grafo.nos.get(v.localizacao)
                if no and getattr(no, 'zona', 'periferia') == 'centro':
                    carros_centro += 1
            percent_centro = carros_centro / total_frota
        else:
            percent_centro = 0

        for pedido in estado.pedidos_pendentes:
            min_custo_para_este_pedido = float('inf')
            
            tempo_espera_min = (agora - pedido.timestamp).total_seconds() / 60.0
            fator_urgencia = 1.0 + (tempo_espera_min / 30.0)
            
            # Multiplicador de prioridade
            if pedido.prioridade == PrioridadePedido.CRITICO:
                fator_prioridade = 10.0
            elif pedido.prioridade == PrioridadePedido.PREMIUM:
                fator_prioridade = 3.0
            else:
                fator_prioridade = 1.0
            
            fator_urgencia *= fator_prioridade
                
            for veiculo in veiculos_disponiveis:
                # CRUCIAL: Verificar capacidade
                if veiculo.capacidade < pedido.num_passageiros:
                    continue

                dist_pickup = estado.grafo.distancia_euclidiana(veiculo.localizacao, pedido.origem)
                dist_viagem = estado.grafo.distancia_euclidiana(pedido.origem, pedido.destino)
                dist_total = dist_pickup + dist_viagem

                # Validação de autonomia
                dist_estacao = self._obter_distancia_estacao_mais_proxima(veiculo, pedido.destino)
                dist_total_com_margem = dist_total + dist_estacao

                autonomia_necessaria = dist_total_com_margem * 1.2
                if veiculo.autonomia_atual < autonomia_necessaria:
                    continue

                custo_base = dist_total * veiculo.custo_por_km

                penalizacao_pref = 0
                if pedido.preferencia_ambiental == PreferenciaAmbiental.APENAS_ELETRICO:
                    if veiculo.tipo_str != "eletrico":
                        penalizacao_pref = 1000.0
                elif pedido.preferencia_ambiental == PreferenciaAmbiental.PREFERENCIA_ELETRICO:
                    if veiculo.tipo_str != "eletrico":
                        penalizacao_pref = 100.0

                custo_zona = 0
                no_origem = estado.grafo.nos.get(veiculo.localizacao)
                no_destino = estado.grafo.nos.get(pedido.destino)
                
                if no_origem and no_destino:
                    zona_origem = getattr(no_origem, 'zona', 'periferia')
                    zona_destino = getattr(no_destino, 'zona', 'periferia')
                    saiu_do_centro = (zona_origem == "centro" and zona_destino == "periferia")
                    if saiu_do_centro and percent_centro < 0.5:
                        custo_zona = 200.0

                custo_opcao = (custo_base * fator_urgencia) + penalizacao_pref + custo_zona
                
                if custo_opcao < min_custo_para_este_pedido:
                    min_custo_para_este_pedido = custo_opcao

            custo_estimado_total += min_custo_para_este_pedido

        return custo_estimado_total
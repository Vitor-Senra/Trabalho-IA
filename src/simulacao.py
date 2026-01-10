import random
import heapq
from datetime import datetime, timedelta
from src.core.grafo import Grafo
from src.core.veiculo import EstadoVeiculo, VeiculoCombustao, VeiculoEletrico
from src.core.pedido import Pedido, PrioridadePedido, PreferenciaAmbiental
from src.core.estado import Estado


class Simulador:
    def __init__(self, caminho_dados):
        print("-> A carregar mapa...")
        self.grafo = Grafo.carregar_json(caminho_dados)
        
        # Criar 3 Veículos de teste em nós aleatórios do mapa
        nos_mapa = list(self.grafo.nos.keys())
        frota_temp = {} 
        for i in range(3):
            vid = f"V{i+1}"
            local = random.choice(nos_mapa)
            if i % 2 == 0:
                frota_temp[vid] = VeiculoCombustao(vid, 300, 4, 0.5, local)
            else:
                frota_temp[vid] = VeiculoEletrico(vid, 300, 4, 0.5, local)

        self.pedidos_pendentes = []
        self.tempo_atual = datetime.now()
        self.estado = Estado(frota_temp, self.pedidos_pendentes, self.grafo, self.tempo_atual)
        
        # Métricas de acompanhamento
        self.metricas = {
            'pedidos_expirados': 0,
            'pedidos_escalados': 0,
            'pedidos_concluidos': 0
        }
        
        # Sistema de Algoritmos
        self.algoritmo_ativo = "A* (Ótimo)"

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
                # Import dinâmico
                modulo = __import__(modulo_path, fromlist=[funcao_nome])
                return getattr(modulo, funcao_nome)
            except (ImportError, AttributeError) as e:
                print(f"  {self.algoritmo_ativo} não disponível: {e}")
                print("    Usando A* como fallback")
                # Fallback para A*
                from src.algorithms.informados.astar import astar
                return astar
        else:
            # Algoritmo desconhecido
            print(f"  Algoritmo '{self.algoritmo_ativo}' desconhecido, usando A*")
            from src.algorithms.informados.astar import astar
            return astar

    def gerar_pedido_aleatorio(self):
        if random.random() < 0.3: # 30% chance
            nos = list(self.grafo.nos.keys())
            origem = random.choice(nos)
            destinos = [n for n in nos if n != origem]
            
            if destinos:
                destino = random.choice(destinos)
                
                # 20% dos pedidos são PREMIUM
                if random.random() < 0.2:
                    prioridade = PrioridadePedido.PREMIUM
                    tempo_max = 30.0  # Premium: 30 min
                    tipo = "PREMIUM"
                else:
                    prioridade = PrioridadePedido.NORMAL
                    tempo_max = 60.0  # Normal: 60 min
                    tipo = "NORMAL"
                
                novo_pedido = Pedido(
                    origem, 
                    destino, 
                    random.randint(1, 4),
                    prioridade=prioridade,
                    tempo_espera_maximo=tempo_max
                )
                
                self.estado.adicionar_pedido(novo_pedido)
                print(f"[PEDIDO {tipo}] {origem} → {destino} (Máx: {tempo_max:.0f}min)")

    def gerar_carro_aleatorio(self):
        nos = list(self.grafo.nos.keys())
        vid = f"V_Rand_{len(self.estado.veiculos)+1}"
        tipo = random.choice(["eletrico", "combustao"])
        local = random.choice(nos)
        if tipo == "eletrico":
            novo_veiculo = VeiculoEletrico(vid, 300, 4, 0.5, local)
        else:
            novo_veiculo = VeiculoCombustao(vid, 300, 4, 1.0, local)       
        self.estado.veiculos[vid] = novo_veiculo
        print(f"[VEÍCULO] Novo veículo {vid} do tipo {tipo} adicionado em {local}")
        
    def criar_veiculo_manual(self, tipo_str, no_inicial, capacidade=4, autonomia=300):
        """Cria um veículo com parâmetros específicos"""
        # 1. Validar Tipo
        tipo_str = tipo_str.lower()
        
        if no_inicial not in self.grafo.nos:
            print(f"Erro: Nó '{no_inicial}' não existe.")
            return

        vid = f"V_Man_{len(self.estado.veiculos)+1}"
        
        if tipo_str == "eletrico":
            novo_veiculo = VeiculoEletrico(vid, autonomia, capacidade, 0.5, no_inicial)
        elif tipo_str == "combustao":
            novo_veiculo = VeiculoCombustao(vid, autonomia, capacidade, 1.0, no_inicial)
        else:
            print(f"Erro: Tipo '{tipo_str}' inválido.")
            return
        
        self.estado.veiculos[vid] = novo_veiculo
        print(f"[SUCESSO] Veículo {vid} ({tipo_str}) criado em {no_inicial}.")

    def criar_pedido_manual(self, origem, destino, num_passageiros=1, premium=False):
        """Cria um pedido específico para testes controlados."""
        if origem not in self.grafo.nos:
            print(f"[ERRO] A origem '{origem}' não existe no mapa.")
            return

        if destino not in self.grafo.nos:
            print(f"[ERRO] O destino '{destino}' não existe no mapa.")
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
        print(f"[TESTE] Pedido Manual {tipo} criado: {origem} -> {destino} ({num_passageiros} pax, {tempo_max}min)")

    def recarregar_veiculo(self, veiculo_id: str) -> bool:
        """
        Envia um veículo para a estação de recarga/abastecimento mais próxima.

        Args:
            veiculo_id: ID do veículo

        Returns:
            bool: True se conseguiu enviar, False caso contrário
        """
        # 1. Validar que o veículo existe
        if veiculo_id not in self.estado.veiculos:
            print(f"[ERRO] Veículo {veiculo_id} não encontrado")
            return False

        veiculo = self.estado.veiculos[veiculo_id]

        # 2. Verificar se está disponível
        if veiculo.estado != EstadoVeiculo.DISPONIVEL:
            print(f"[ERRO] Veículo {veiculo_id} não está disponível (Estado: {veiculo.estado.value})")
            return False

        # 3. Identificar tipo de estação necessária
        if isinstance(veiculo, VeiculoEletrico):
            tipo_estacao = "estacao_recarga"
            nome_estacao = "RECARGA"
        else:
            tipo_estacao = "posto_abastecimento"
            nome_estacao = "ABASTECIMENTO"

        # 4. Encontrar a estação mais próxima
        estacoes = [
            (no_id, no) for no_id, no in self.grafo.nos.items()
            if no.tipo == tipo_estacao
        ]

        if not estacoes:
            print(f"[ERRO] Nenhuma estação de {nome_estacao} encontrada no mapa")
            return False

        # Calcular distância euclidiana para cada estação
        estacao_mais_proxima = min(
            estacoes,
            key=lambda e: self.grafo.distancia_euclidiana(veiculo.localizacao, e[0])
        )

        no_estacao_id = estacao_mais_proxima[0]

        # 5. Calcular rota usando o algoritmo ativo
        algoritmo = self._obter_funcao_algoritmo()
        resultado = algoritmo(
            self.grafo,
            veiculo.localizacao,
            no_estacao_id,
            metrica='tempo'
        )

        if not resultado.sucesso:
            print(f"[ERRO] Não foi possível calcular rota para {no_estacao_id}")
            return False

        # 6. Definir rota e estado
        veiculo.definir_rota(resultado.caminho)
        veiculo.destino_atual = no_estacao_id

        if isinstance(veiculo, VeiculoEletrico):
            veiculo.estado = EstadoVeiculo.EM_RECARGA
        else:
            veiculo.estado = EstadoVeiculo.EM_ABASTECIMENTO

        print(f"🔋 [{nome_estacao}] {veiculo_id} enviado para {no_estacao_id} ({veiculo.autonomia_atual:.0f}km restantes)")
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
            
            elif resultado == "AVISO_70":
                tempo_restante = pedido.tempo_restante_minutos(self.tempo_atual)
                print(f"⚠️  [AVISO] Pedido {pedido.id} em 70% do tempo ({tempo_restante:.1f}min restantes)")
            
            elif resultado == "AVISO_50":
                tempo_restante = pedido.tempo_restante_minutos(self.tempo_atual)
                print(f"⏰ [AVISO] Pedido {pedido.id} em 50% do tempo ({tempo_restante:.1f}min restantes)")
            
            elif resultado == "EXPIRAR":
                pedidos_a_remover.append(pedido)
                print(f"❌ [EXPIRADO] Pedido {pedido.id} cancelado após {pedido.tempo_espera_maximo:.0f}min")
                self.metricas['pedidos_expirados'] += 1
        
        for pedido in pedidos_a_remover:
            pedido.marcar_expirado()
            self.estado.pedidos_pendentes.remove(pedido)

    def atualizar_movimento_veiculos(self):
        """Simula o movimento dos veículos usando o algoritmo selecionado."""
        # Obter função do algoritmo ATUAL
        algoritmo = self._obter_funcao_algoritmo()

        for veiculo in self.estado.veiculos.values():
            # PROCESSAR RECARGA/ABASTECIMENTO (independente de movimento)
            if veiculo.estado == EstadoVeiculo.EM_RECARGA or veiculo.estado == EstadoVeiculo.EM_ABASTECIMENTO:
                if not veiculo.rota_atual:
                    if veiculo.tempo_em_recarga == 0:
                        veiculo.autonomia_ao_iniciar_recarga = veiculo.autonomia_atual
                        tipo = "RECARGA" if isinstance(veiculo, VeiculoEletrico) else "ABASTECIMENTO"
                        tempo_necessario = veiculo.tempo_recarga_estimado(1.0)
                        print(f"🔌 [{tipo}] {veiculo.id} a carregar... ({veiculo.autonomia_atual:.0f}km → {veiculo.autonomia_max:.0f}km | {tempo_necessario:.1f}min)")

                    veiculo.tempo_em_recarga += 1

                    # Calcular quanto tempo falta para recarga completa
                    tempo_total_necessario = veiculo.tempo_recarga_estimado(1.0)

                    # Recarga gradual proporcional ao tempo
                    if veiculo.tempo_em_recarga >= tempo_total_necessario:
                        # Recarga completa
                        veiculo.autonomia_atual = veiculo.autonomia_max
                        veiculo.estado = EstadoVeiculo.DISPONIVEL
                        veiculo.destino_atual = None
                        veiculo.tempo_em_recarga = 0

                        tipo = "RECARGA" if isinstance(veiculo, VeiculoEletrico) else "ABASTECIMENTO"
                        print(f"[{tipo}] {veiculo.id} recarregado para {veiculo.autonomia_max:.0f}km")
                    else:
                        # Recarga parcial (proporcional ao tempo decorrido)
                        autonomia_faltante = veiculo.autonomia_max - veiculo.autonomia_ao_iniciar_recarga
                        progresso = veiculo.tempo_em_recarga / tempo_total_necessario
                        veiculo.autonomia_atual = veiculo.autonomia_ao_iniciar_recarga + (autonomia_faltante * progresso)

                        if veiculo.tempo_em_recarga % 2 == 0:
                            percentagem = progresso * 100
                            print(f"{veiculo.id}: {percentagem:.0f}% ({veiculo.autonomia_atual:.0f}km)")

                        # PROCESSAR MOVIMENTO (se não estiver disponível)
            if veiculo.estado == EstadoVeiculo.DISPONIVEL:
                continue

        
            chegou = veiculo.atualizar_posicao(self.grafo, 0.4)

            if chegou:
                if veiculo.estado == EstadoVeiculo.A_CAMINHO:
                    veiculo.estado = EstadoVeiculo.EM_SERVICO
                    veiculo.pedido_atual.iniciar_viagem()

                    resultado_viagem = algoritmo(
                        self.grafo,
                        veiculo.localizacao,
                        veiculo.pedido_atual.destino,
                        metrica='tempo'
                    )

                    if resultado_viagem.sucesso:
                        veiculo.definir_rota(resultado_viagem.caminho)
                    else:
                        print(f"[ERRO] Caminho bloqueado para destino {veiculo.pedido_atual.destino}")
                        veiculo.estado = EstadoVeiculo.DISPONIVEL
                        veiculo.pedido_atual = None

                elif veiculo.estado == EstadoVeiculo.EM_SERVICO:
                    self.estado.concluir_pedido(veiculo.pedido_atual, 5, 10)
                    self.metricas['pedidos_concluidos'] += 1
                    veiculo.estado = EstadoVeiculo.DISPONIVEL
                    veiculo.pedido_atual = None


    def correr_passo(self):
        """Avança 1 minuto na simulação."""
        self.tempo_atual += timedelta(minutes=1)

        self.atualizar_prioridades_pedidos()
        self.gerar_pedido_aleatorio()
        self.processar_atribuicoes_inteligente()
        self.atualizar_movimento_veiculos()
        self.verificar_e_recarregar_veiculos()  # Nova função automática

    def verificar_e_recarregar_veiculos(self, limiar=0.3):
        """
        Verifica se há veículos com bateria/combustível baixo e envia automaticamente para recarga.

        Args:
            limiar: Percentagem mínima de autonomia (padrão: 30%)
        """
        veiculos_baixa_autonomia = self.estado.obter_veiculos_necessitam_recarga(limiar)

        for veiculo in veiculos_baixa_autonomia:
            # Só recarrega se estiver DISPONIVEL (não ocupado)
            if veiculo.estado == EstadoVeiculo.DISPONIVEL:
                self.recarregar_veiculo(veiculo.id)

    def processar_atribuicoes_inteligente(self):
        """
        Planeamento de Frota usando A* no Espaço de Estados.
        NOTA: Este A* é para PLANEAMENTO, não para navegação no mapa.
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
            
            pedido_real = next(p for p in self.estado.pedidos_pendentes if p.id == pedido_clone.id)
            veiculo_real = self.estado.veiculos[veiculo_clone.id]
            
            print(f"[INTELIGENTE] Decisão: Atribuir {veiculo_real.id} ao pedido {pedido_real.id} ({pedido_real.prioridade.name})")
            
            self.estado.atribuir_pedido(pedido_real, veiculo_real)
            veiculo_real.estado = EstadoVeiculo.A_CAMINHO
            
            # Calcular rota de pickup com o algoritmo selecionado
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
                print(f"[ERRO] Falha ao calcular rota física para {veiculo_real.id}")

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
                if veiculo.capacidade < pedido.num_passageiros:
                    continue 
                
                dist_pickup = estado.grafo.distancia_euclidiana(veiculo.localizacao, pedido.origem)
                dist_viagem = estado.grafo.distancia_euclidiana(pedido.origem, pedido.destino)
                dist_total = dist_pickup + dist_viagem
                custo_base = dist_total * veiculo.custo_por_km

                penalizacao_pref = 0
                if pedido.preferencia_ambiental == PreferenciaAmbiental.APENAS_ELETRICO:
                    if not isinstance(veiculo, VeiculoEletrico):
                        penalizacao_pref = 1000.0
                elif pedido.preferencia_ambiental == PreferenciaAmbiental.PREFERENCIA_ELETRICO:
                    if not isinstance(veiculo, VeiculoEletrico):
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
    
    def obter_metricas(self):
        """Retorna métricas da simulação."""
        return {
            **self.metricas,
            'pedidos_pendentes': len(self.estado.pedidos_pendentes),
            'veiculos_disponiveis': len(self.estado.obter_veiculos_disponiveis()),
            'tempo_simulacao': self.tempo_atual.strftime('%H:%M:%S'),
            'algoritmo_ativo': self.algoritmo_ativo
        }
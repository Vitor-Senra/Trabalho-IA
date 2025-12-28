import time
import random
from datetime import datetime, timedelta
from src.core.grafo import Grafo
from src.core.veiculo import EstadoVeiculo, VeiculoCombustao, VeiculoEletrico
from src.core.pedido import Pedido
from src.core.estado import Estado
from src.algorithms.informados.astar import astar
from datetime import datetime
from src.core.pedido import PreferenciaAmbiental
import heapq

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

    def gerar_pedido_aleatorio(self):
        if random.random() < 0.3: # 30% chance
            nos = list(self.grafo.nos.keys())
            origem = random.choice(nos)
            destinos = [n for n in nos if n != origem]
            
            if destinos:
                destino = random.choice(destinos)
                novo_pedido = Pedido(origem, destino, random.randint(1,4))
                self.estado.adicionar_pedido(novo_pedido)
                print(f"[PEDIDO] Novo pedido de {origem} para {destino}")

    def gerar_carro_aleatorio(self):
        nos = list(self.grafo.nos.keys())
        vid = f"V_Rand_{len(self.estado.veiculos)+1}"
        tipo = random.choice(["eletrico", "combustao"])
        local = random.choice(nos)
        if tipo == "eletrico":
            novo_veiculo = VeiculoEletrico(vid, 300, 4, 0.5, local)
        elif tipo == "combustao":
            novo_veiculo = VeiculoCombustao(vid, 300, 4, 1.0, local)
        self.estado.veiculos[vid] = novo_veiculo
        print(f"[VEÍCULO] Novo veículo {vid} do tipo {tipo} adicionado em {local}")
    def criar_veiculo_manual(self, tipo_str, no_inicial, capacidade=4, autonomia=300):
        """Cria um veículo com parâmetros específicos"""
        # 1. Validar Tipo
        tipo_str = tipo_str.lower()
        custo_km = 0.5
        tipo_enum = None
        # 2. Validar Nó
        if no_inicial not in self.grafo.nos:
            print(f"Erro: Nó '{no_inicial}' não existe.")
            return

        # 3. Criar e Adicionar
        vid = f"V_Man_{len(self.estado.veiculos)+1}"
        
        if tipo_str == "eletrico":
            novo_veiculo = VeiculoEletrico(
                id=vid,
                autonomia_max=autonomia, 
                capacidade=capacidade, 
                custo_por_km=0.5, 
                localizacao=no_inicial
            )
        elif tipo_str == "combustao":
            novo_veiculo = VeiculoCombustao(
                id=vid,
                autonomia_max=autonomia, 
                capacidade=capacidade, 
                custo_por_km=1.0,
                localizacao=no_inicial
            )
        else:
            print(f"Erro: Tipo '{tipo_str}' inválido.")
            return
        
        self.estado.veiculos[vid] = novo_veiculo
        print(f"[SUCESSO] Veículo {vid} ({tipo_str}) criado em {no_inicial}.")

    # Em src/simulacao.py

    def criar_pedido_manual(self, origem, destino, num_passageiros=1):
        """
        Cria um pedido específico para testes controlados.
        """
        # 1. Validar se os locais existem no mapa
        if origem not in self.grafo.nos:
            print(f"[ERRO] A origem '{origem}' não existe no mapa.")
            return
        
        if destino not in self.grafo.nos:
            print(f"[ERRO] O destino '{destino}' não existe no mapa.")
            return

        # 2. Criar o pedido
        # Importar Pedido aqui dentro ou garantir que está no topo do ficheiro
        from src.core.pedido import Pedido 
        
        novo_pedido = Pedido(origem, destino, num_passageiros)
        
        # 3. Adicionar ao sistema
        self.estado.adicionar_pedido(novo_pedido)
        print(f"[TESTE] Pedido Manual criado: {origem} -> {destino} ({num_passageiros} pax)")

    def atualizar_movimento_veiculos(self):
        """
        Simula o movimento dos veículos e gere a transição Pickup -> Viagem -> Conclusão.
        """
        # Velocidade de simulação: % da aresta percorrida por passo.
        # 0.1 significa que demora 10 passos (10 segundos) a atravessar qualquer aresta.
        # Podes ajustar para basear-se no tamanho da aresta se quiseres mais realismo.


        for veiculo in self.estado.veiculos.values():
            if veiculo.estado is EstadoVeiculo.DISPONIVEL:
                continue

            chegou = veiculo.atualizar_posicao(self.grafo, 0.4)
            if chegou:
                if veiculo.estado == EstadoVeiculo.A_CAMINHO:
                    
                    veiculo.estado = EstadoVeiculo.EM_SERVICO
                    veiculo.pedido_atual.iniciar_viagem()
                    
                    # CALCULAR NOVA ROTA: Daqui (Origem Pedido) -> Destino Pedido
                    resultado_viagem = astar(
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
                    # TODO: Finalizar pedido
                    #distancia = veiculo.pedido_atual.calcular_distancia_percorrida(self.grafo)
                    #custo = distancia * veiculo.custo_por_km
                    # Libertar veículo e finalizar pedido
                    self.estado.concluir_pedido(veiculo.pedido_atual, 5, 10)
                    veiculo.estado = EstadoVeiculo.DISPONIVEL
                    veiculo.pedido_atual = None

    def correr_passo(self):
        """Avança 1 minuto na simulação"""
        self.tempo_atual += timedelta(minutes=1)
        
        # 1. Gerar novos pedidos aleatórios
        self.gerar_pedido_aleatorio()
        
        # 2. Processar a fila com a nova inteligência
        self.processar_atribuicoes_inteligente()
        
        # 3. (Opcional) Atualizar movimento físico dos carros
        self.atualizar_movimento_veiculos()

    def processar_atribuicoes_inteligente(self):
        """
        Planeamento de Frota usando A* no Espaço de Estados.
        Procura a melhor ação (atribuição) que leva a um estado com menor custo global.
        """
        
        # Se não há nada para gerir, sai
        if not self.estado.pedidos_pendentes or not self.estado.obter_veiculos_disponiveis():
            return

        print(f"[{self.tempo_atual.strftime('%H:%M')}] A planear atribuições (Smart)...")

        # 1. Configuração do A*
        estado_inicial = self.estado.clonar()
        
        # Fila de Prioridade: (f_score, g_score, contador_desempate, estado, caminho_de_acoes)
        # f_score = custo_acumulado (g) + heuristica (h)
        queue = []
        counter = 0 # Para desempatar na queue
        
        h_inicial = self._heuristica_estado(estado_inicial)
        heapq.heappush(queue, (h_inicial, 0, counter, estado_inicial, []))
        
        melhor_caminho = []
        melhor_f = float('inf')
        iteracoes = 0
        MAX_ITERACOES = 50
        
        # 2. Ciclo de Procura
        while queue and iteracoes < MAX_ITERACOES:
            f, g, _, estado_atual, caminho = heapq.heappop(queue)
            iteracoes += 1
            
            # Se encontrámos um estado onde todos os pedidos foram tratados (objetivo)
            if not estado_atual.pedidos_pendentes:
                melhor_caminho = caminho
                break
            
            # Gerar sucessores (Ações Possíveis: V1->P1, V1->P2, V2->P1...)
            acoes_possiveis = estado_atual.obter_acoes_possiveis()
            
            if not acoes_possiveis:
                # Se este caminho não tem saída mas é o melhor até agora (menos pendentes)
                if f < melhor_f:
                    melhor_f = f
                    melhor_caminho = caminho
                continue

            for acao in acoes_possiveis:
                # Simular o novo estado
                novo_estado = estado_atual.aplicar_acao(acao)
                
                # Custo g: Custo acumulado + Custo desta ação (distância da viagem)
                custo_acao = acao['distancia_estimada']
                novo_g = g + custo_acao
                
                # Heurística h: Estimativa do que falta fazer
                novo_h = self._heuristica_estado(novo_estado)
                novo_f = novo_g + novo_h
                
                # Adicionar à fila
                counter += 1
                novo_caminho = caminho + [acao]
                heapq.heappush(queue, (novo_f, novo_g, counter, novo_estado, novo_caminho))

        # 3. Execução da Decisão
        # Se o algoritmo encontrou um plano, executamos APENAS a primeira ação (passo seguinte)
        if melhor_caminho:
            melhor_acao = melhor_caminho[0]
            
            pedido_clone = melhor_acao['pedido']
            veiculo_clone = melhor_acao['veiculo']
            
            # Recuperar os objetos REAIS da simulação (não os clones)
            pedido_real = next(p for p in self.estado.pedidos_pendentes if p.id == pedido_clone.id)
            veiculo_real = self.estado.veiculos[veiculo_clone.id]
            
            print(f"[INTELIGENTE] Decisão: Atribuir {veiculo_real.id} ao pedido {pedido_real.id}")
            
            # --- Lógica de Atribuição (Cópia da lógica 'A Caminho') ---
            from src.core.veiculo import EstadoVeiculo
            
            # Definir estado e atribuir
            self.estado.atribuir_pedido(pedido_real, veiculo_real)
            veiculo_real.estado = EstadoVeiculo.A_CAMINHO
            
            # Calcular rota física no mapa (Pickup)
            rota_pickup = astar(
                self.grafo, 
                veiculo_real.localizacao, 
                pedido_real.origem, 
                metrica='tempo'
            )
            
            if rota_pickup.sucesso:
                veiculo_real.definir_rota(rota_pickup.caminho)
            else:
                print(f"[ERRO] Falha ao calcular rota física para {veiculo_real.id}")
        else:
            # Fallback: Se o planeamento falhar, não faz nada neste turno
            pass


    def _heuristica_estado(self, estado):
        """
        Heurística Multiobjetivo Completa.
        """
        custo_estimado_total = 0
        veiculos_disponiveis = estado.obter_veiculos_disponiveis()
        
        # Se há pedidos mas não há carros, penalização máxima
        if not veiculos_disponiveis and estado.pedidos_pendentes:
            return len(estado.pedidos_pendentes) * 10000.0
            
        agora = estado.timestamp

        total_frota = len(estado.veiculos)
        carros_centro = 0
        
        if total_frota > 0:
            for v in estado.veiculos.values():
                # Proteção com getattr caso o mapa não tenha zonas definidas
                no = estado.grafo.nos.get(v.localizacao)
                if no and getattr(no, 'zona', 'periferia') == 'centro':
                    carros_centro += 1
            
            percent_centro = carros_centro / total_frota
        else:
            percent_centro = 0

        for pedido in estado.pedidos_pendentes:
            min_custo_para_este_pedido = float('inf')
            
            # Quanto mais tempo passou, maior o multiplicador de custo
            tempo_espera_min = (agora - pedido.timestamp).total_seconds() / 60.0
            fator_urgencia = 1.0 + (tempo_espera_min / 30.0) 
                
            for veiculo in veiculos_disponiveis:
                # 1. Filtro de Capacidade
                if veiculo.capacidade < pedido.num_passageiros:
                    continue 
                
                # 2. Distâncias
                dist_pickup = estado.grafo.distancia_euclidiana(veiculo.localizacao, pedido.origem)
                dist_viagem = estado.grafo.distancia_euclidiana(pedido.origem, pedido.destino)
                dist_total = dist_pickup + dist_viagem
                
                # 3. Custo Operacional Base
                custo_base = dist_total * veiculo.custo_por_km
                
                # 4. (Autonomia - comentado no original)

                # 5. Preferências
                penalizacao_pref = 0
                if pedido.preferencia_ambiental == PreferenciaAmbiental.APENAS_ELETRICO and not isinstance(veiculo, VeiculoEletrico):
                    penalizacao_pref = 1000.0
                elif pedido.preferencia_ambiental == PreferenciaAmbiental.PREFERENCIA_ELETRICO and not isinstance(veiculo, VeiculoEletrico) :
                    penalizacao_pref = 100.0

                # 6. Restrições de Zona
                custo_zona = 0

                # Obter nós com segurança
                no_origem = estado.grafo.nos.get(veiculo.localizacao)
                no_destino = estado.grafo.nos.get(pedido.destino)
                
                if no_origem and no_destino:
                    zona_origem = getattr(no_origem, 'zona', 'periferia')
                    zona_destino = getattr(no_destino, 'zona', 'periferia')

                    saiu_do_centro = (zona_origem == "centro" and zona_destino == "periferia")

                    if saiu_do_centro and percent_centro < 0.5:
                        custo_zona = 200.0

                # Soma Final
                custo_opcao = (custo_base * fator_urgencia) + penalizacao_pref + custo_zona
                
                if custo_opcao < min_custo_para_este_pedido:
                    min_custo_para_este_pedido = custo_opcao

            custo_estimado_total += min_custo_para_este_pedido

        return custo_estimado_total
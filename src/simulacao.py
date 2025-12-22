import time
import random
from datetime import datetime, timedelta
from src.core.grafo import Grafo
from src.core.veiculo import EstadoVeiculo, Veiculo, TipoVeiculo
from src.core.pedido import Pedido
from src.core.estado import Estado
from src.algorithms.informados.astar import astar

class Simulador:
    def __init__(self, caminho_dados):
        print("-> A carregar mapa...")
        self.grafo = Grafo.carregar_json(caminho_dados)
        
        # Criar 3 Veículos de teste em nós aleatórios do mapa
        nos_mapa = list(self.grafo.nos.keys())
        self.frota = {}
        
        for i in range(3):
            vid = f"V{i+1}"
            tipo = TipoVeiculo.ELETRICO if i % 2 == 0 else TipoVeiculo.COMBUSTAO
            local = random.choice(nos_mapa)
            self.frota[vid] = Veiculo(vid, tipo, 300, 4, 0.5, local)

        self.pedidos_pendentes = []
        self.tempo_atual = datetime.now()
        self.estado = Estado(self.frota, self.pedidos_pendentes, self.grafo, self.tempo_atual)

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

    def processar_atribuicoes(self):
        """
        Algoritmo Inteligente de Gestão de Frota:
        1. Analisa cada pedido pendente.
        2. Simula o tempo de viagem para TODOS os carros disponíveis.
        3. Escolhe o que chega mais rápido (se cumprir o tempo máximo de espera).
        """
        # Iterar sobre uma cópia da lista para podermos remover pedidos se necessário
        for pedido in list(self.estado.pedidos_pendentes):
            
            melhor_veiculo = None
            menor_tempo_chegada = float('inf')
            
            # --- FASE DE PROCURA ---
            for veiculo in self.estado.veiculos.values():
                if not veiculo.esta_disponivel():
                    continue

                # 1. Calcular rota do Veículo -> Cliente (Pickup)
                # Usamos metrica='tempo' para o A* otimizar por rapidez e não distância
                resultado_pickup = astar(
                    self.grafo, 
                    veiculo.localizacao, 
                    pedido.origem, 
                    metrica='tempo'
                )

                if not resultado_pickup.sucesso:
                    continue # Não há caminho possível

                tempo_ate_cliente = resultado_pickup.custo_total

                # 2. Verificar Restrição: O cliente espera este tempo?
                # O 'tempo_espera_maximo' está definido no pedido.py (ex: 15 min)
                if tempo_ate_cliente > pedido.tempo_espera_maximo:
                    continue # Este carro demora muito, o cliente desistiria

                # 3. Escolher o Melhor (Greedy na escolha do veículo)
                # Se este carro chega mais rápido que o anterior melhor, escolhemos este
                if tempo_ate_cliente < menor_tempo_chegada:
                    menor_tempo_chegada = tempo_ate_cliente
                    melhor_veiculo = veiculo
                    veiculo.definir_rota(resultado_pickup.caminho)  

            # --- FASE DE ATRIBUIÇÃO ---
            if melhor_veiculo:
                print(f"[SUCESSO] Pedido {pedido.id}: Atribuído ao {melhor_veiculo.id} (Chega em {menor_tempo_chegada:.1f} min)")
                self.estado.atribuir_pedido(pedido, melhor_veiculo)
            else:
                # Nenhum carro consegue chegar a tempo ou estão todos ocupados
                # Opção A: O pedido continua pendente para a próxima iteração (pode libertar-se um carro)
                # Opção B: O pedido é rejeitado/cancelado (se quiseres ser rigoroso)
                print(f"[FALHA] Pedido {pedido.id}: Nenhum veículo consegue chegar em {pedido.tempo_espera_maximo} min.")
                
                # Se quiseres cancelar o pedido após falhar:
                # self.estado.cancelar_pedido(pedido, motivo="Tempo de espera excessivo")


    def atualizar_movimento_veiculos(self):
        """
        Simula o movimento dos veículos e gere a transição Pickup -> Viagem -> Conclusão.
        """
        # Velocidade de simulação: % da aresta percorrida por passo.
        # 0.1 significa que demora 10 passos (10 segundos) a atravessar qualquer aresta.
        # Podes ajustar para basear-se no tamanho da aresta se quiseres mais realismo.


        for veiculo in self.estado.veiculos.values():
            if veiculo.estado is EstadoVeiculo.EM_SERVICO:
                veiculo.atualizar_posicao(10)


    def correr_passo(self):
        """Avança 1 minuto na simulação"""
        self.tempo_atual += timedelta(minutes=1)
        
        # 1. Gerar novos pedidos aleatórios
        self.gerar_pedido_aleatorio()
        
        # 2. Processar a fila com a nova inteligência
        self.processar_atribuicoes()
        
        # 3. (Opcional) Atualizar movimento físico dos carros
        self.atualizar_movimento_veiculos()
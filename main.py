import sys
import os
import time

# Configurar caminhos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.simulacao import Simulador
from gui import Gui

def get_dados_visuais(self):
        # 1. Dados dos Veículos
        dados_veiculos = []
        for v in self.estado.veiculos.values():
            ocupado = v.estado.value != "disponivel"
            
            # --- NOVO: Tenta obter a rota atual, se existir ---
            rota = getattr(v, 'rota_atual', []) 
            
            dados_veiculos.append({
                'id': v.id,
                'pos': v.localizacao,
                'bateria': v.autonomia_atual / v.autonomia_max,
                'ocupado': ocupado,
                'estado_texto': v.estado.value.upper(), 
                'passageiros': v.passageiros_atuais,
                'rota': rota  # <--- Enviamos a lista de nós do caminho
            })
        
        # 2. Dados dos Pedidos Pendentes
        dados_pedidos = []
        for p in self.estado.pedidos_pendentes:
            tempo_espera = (self.tempo_atual - p.timestamp).total_seconds() / 60.0
            dados_pedidos.append({
                'id': p.id,
                'origem': p.origem,
                'destino': p.destino,
                'espera': f"{tempo_espera:.1f}m"
            })
            
        return {
            'tempo': self.tempo_atual.strftime("%H:%M"),
            'veiculos': dados_veiculos,
            'pedidos': dados_pedidos
        }

def main():
    caminho_dados = "src/data/cidade.json"
    
    # 1. Inicia
    sim = Simulador(caminho_dados)
    gui = Gui(caminho_dados)
    
    print("A iniciar simulação gráfica...")

    while gui.running:
        # A. Atualiza Lógica
        sim.correr_passo() # ou sim.atualizar_movimento()
        
        # B. Obtém dados
        dados = get_dados_visuais(sim)
        
        # C. Desenha e RECEBE AÇÕES DO UTILIZADOR
        acoes = gui.desenhar(dados)
        
        # D. Processar Ações da GUI
        for acao, tipo in acoes:
            print(f"Ação Recebida: {acao} -> {tipo}")
            
            # --- ADICIONAR VEÍCULO ---
            if acao == "add_carro":
                if tipo == "random":
                    # Cria um veículo aleatório (truque: usa a lógica do init ou cria função random)
                    import random
                    from src.core.veiculo import TipoVeiculo, Veiculo
                    nos = list(sim.grafo.nos.keys())
                    vid = f"V_Rand_{len(sim.frota)+1}"
                    sim.frota[vid] = Veiculo(vid, TipoVeiculo.ELETRICO, 300, 4, 0.5, random.choice(nos))
                    sim.estado.veiculos[vid] = sim.frota[vid]
                    print("Carro Aleatório Adicionado!")
                
                elif tipo == "custom":
                    print("\n--- NOVO VEÍCULO (CONSOLA) ---")
                    try:
                        t = input("Tipo (eletrico/combustao): ").strip().lower()
                        loc = input("ID do Nó Inicial: ").strip()
                        sim.criar_veiculo_manual(t, loc)
                    except Exception as e:
                        print(f"Erro ao criar: {e}")
                    print("------------------------------\n")

            # --- ADICIONAR PEDIDO ---
            elif acao == "add_pedido":
                if tipo == "random":
                    sim.gerar_pedido_aleatorio() # Já tens esta função
                    print("Pedido Aleatório Gerado!")
                
                elif tipo == "custom":
                    print("\n--- NOVO PEDIDO (CONSOLA) ---")
                    try:
                        orig = input("ID Origem: ").strip()
                        dest = input("ID Destino: ").strip()
                        sim.criar_pedido_manual(orig, dest)
                    except Exception as e:
                        print(f"Erro ao criar: {e}")
                    print("-----------------------------\n")

        # Pausa
        time.sleep(1) 

if __name__ == "__main__":
    main()
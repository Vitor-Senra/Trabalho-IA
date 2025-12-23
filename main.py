import sys
import os
import time

# Configurar caminhos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.simulacao import Simulador
from gui import Gui

def get_dados_visuais(sim):
        # 1. Dados dos Veículos
        dados_veiculos = []
        for v in sim.estado.veiculos.values():
            ocupado = v.estado.value != "disponivel"
            
            # Tenta obter a rota atual, se existir
            rota = getattr(v, 'rota_atual', []) 
            
            dados_veiculos.append({
                'id': v.id,
                'pos': v.localizacao,
                'bateria': v.autonomia_atual / v.autonomia_max,
                'ocupado': ocupado,
                'estado_texto': v.estado.value.upper(), 
                'passageiros': v.passageiros_atuais,
                'rota': rota
            })
        
        # 2. Dados dos Pedidos Pendentes
        dados_pedidos = []
        for p in sim.estado.pedidos_pendentes:
            tempo_espera = (sim.tempo_atual - p.timestamp).total_seconds() / 60.0
            dados_pedidos.append({
                'id': p.id,
                'origem': p.origem,
                'destino': p.destino,
                'espera': f"{tempo_espera:.1f}m"
            })
            
        return {
            'tempo': sim.tempo_atual.strftime("%H:%M"),
            'veiculos': dados_veiculos,
            'pedidos': dados_pedidos
        }

def main():
    caminho_dados = "src/data/cidade.json"
    
    # 1. Inicia
    sim = Simulador(caminho_dados)
    gui = Gui(caminho_dados)
    
    print("A iniciar simulação gráfica...")
    
    # --- CONTROLO DE TEMPO OTIMIZADO ---
    ultimo_passo_simulacao = time.time()
    INTERVALO_SIMULACAO = 1  # 1 segundos entre movimentos dos carros
    
    # Gera dados iniciais
    dados = get_dados_visuais(sim)

    while gui.running:
        agora = time.time()
        
        if agora - ultimo_passo_simulacao >= INTERVALO_SIMULACAO:
            sim.correr_passo()
            dados = get_dados_visuais(sim)
            ultimo_passo_simulacao = agora
            
        acoes = gui.desenhar(dados)
        
        
        # C. Processar Ações da GUI
        for acao, parametros in acoes:
            print(f"Ação Recebida: {acao} -> {parametros}")
            
            # --- 1. CRIAR VEÍCULO MANUALMENTE ---
            if acao == "criar_carro_manual":
                t = parametros['tipo']  
                n = parametros['no']
                try:
                    sim.criar_veiculo_manual(t, n)
                    dados = get_dados_visuais(sim) # Atualiza visual imediatamente
                except AttributeError:
                    print("ERRO: O método 'criar_veiculo_manual' não existe no Simulador.")
                except Exception as e:
                    print(f"ERRO ao criar veículo: {e}")

            # --- 2. CRIAR PEDIDO MANUALMENTE ---
            elif acao == "criar_pedido_manual":
                orig = parametros['origem']
                dest = parametros['destino']
                try:
                    sim.criar_pedido_manual(orig, dest)
                    dados = get_dados_visuais(sim)
                except AttributeError:
                    print("ERRO: O método 'criar_pedido_manual' não existe no Simulador.")
                except Exception as e:
                    print(f"ERRO ao criar pedido: {e}")

            # --- 3. BOTÕES RÁPIDOS (Aleatório) ---
            elif acao == "add_carro":
                if parametros == "random":
                    import random
                    from src.core.veiculo import TipoVeiculo, Veiculo
                    
                    if not sim.grafo.nos:
                        print("Erro: Grafo vazio.")
                        continue
                        
                    nos = list(sim.grafo.nos.keys())
                    vid = f"V_Rand_{len(sim.estado.veiculos)+1}"
                    tipo_v = TipoVeiculo.ELETRICO if random.random() > 0.5 else TipoVeiculo.COMBUSTAO
                    
                    novo_veiculo = Veiculo(vid, tipo_v, 300, 4, 0.5, random.choice(nos))
                    sim.estado.veiculos[vid] = novo_veiculo
                    print(f"Carro Aleatório {vid} Adicionado!")
                    dados = get_dados_visuais(sim)

            elif acao == "add_pedido":
                if parametros == "random":
                    sim.gerar_pedido_aleatorio()
                    print("Pedido Aleatório Gerado!")
                    dados = get_dados_visuais(sim)


if __name__ == "__main__":
    main()
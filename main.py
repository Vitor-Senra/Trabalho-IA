import sys
import os
import time

# Configurar caminhos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.simulacao import Simulador
from gui import Gui

def get_dados_visuais(sim):
    """Extrai dados visuais da simulação para a GUI"""
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
    
    # 2. Dados dos Pedidos Pendentes (COM PRIORIDADE E TEMPO RESTANTE)
    dados_pedidos = []
    for p in sim.estado.pedidos_pendentes:
        # Calcular tempo de espera
        tempo_espera = (sim.tempo_atual - p.timestamp).total_seconds() / 60.0
        
        # Calcular tempo restante até expirar
        tempo_restante = p.tempo_espera_maximo - tempo_espera
        tempo_restante = max(0, tempo_restante) 
        
        dados_pedidos.append({
            'id': p.id,
            'origem': p.origem,
            'destino': p.destino,
            'espera': f"{tempo_espera:.1f}m",
            'restante': f"{tempo_restante:.1f}m",
            'prioridade': p.prioridade.name,  # NORMAL/PREMIUM/CRITICO
        })
        
    return {
        'tempo': sim.tempo_atual.strftime("%H:%M"),
        'veiculos': dados_veiculos,
        'pedidos': dados_pedidos
    }

def main():
    caminho_dados = "src/data/cidade.json"
    
    # 1. Inicializar
    sim = Simulador(caminho_dados)
    gui = Gui(caminho_dados)
    
    print("=" * 60)
    print(" TAXIGREEN - SISTEMA DE GESTÃO INTELIGENTE DE FROTA")
    print("=" * 60)
    print(f"Algoritmo inicial: {sim.algoritmo_ativo}")
    print("A iniciar simulação gráfica...")
    print()

    # ========== TESTE: FORÇAR BATERIA BAIXA ==========
    print("\n[TESTE] Forçando bateria baixa nos veículos para teste de recarga...")
    for v in sim.estado.veiculos.values():
        v.autonomia_atual = 50  # 50km (menos de 30% de 300km)
        tipo = "ELÉTRICO" if hasattr(v, 'taxa_recarga') else "COMBUSTÃO"
        print(f"  {v.id} ({tipo}): {v.autonomia_atual:.0f}km ({v.autonomia_atual/v.autonomia_max*100:.0f}%)")
    print("==================================================\n")
    # ==================================================

    # --- CONTROLO DE TEMPO OTIMIZADO ---
    ultimo_passo_simulacao = time.time()
    INTERVALO_SIMULACAO = 1  # 1 segundo entre passos da simulação
    
    # Gera dados iniciais
    dados = get_dados_visuais(sim)

    while gui.running:
        agora = time.time()
        
        # Avançar simulação a cada INTERVALO_SIMULACAO
        if agora - ultimo_passo_simulacao >= INTERVALO_SIMULACAO:
            sim.correr_passo()
            dados = get_dados_visuais(sim)
            ultimo_passo_simulacao = agora
            
        # Desenhar GUI e obter ações do utilizador
        acoes = gui.desenhar(dados)
        
        # Processar Ações da GUI
        for acao, parametros in acoes:
            print(f"[GUI] Ação Recebida: {acao} -> {parametros}")
            
            # --- 1. CRIAR VEÍCULO MANUALMENTE ---
            if acao == "criar_carro_manual":
                t = parametros['tipo']  
                n = parametros['no']
                try:
                    sim.criar_veiculo_manual(t, n)
                    dados = get_dados_visuais(sim)  # Atualiza visual imediatamente
                    print(f" Veículo {t} criado no nó {n}")
                except AttributeError:
                    print("ERRO: O método 'criar_veiculo_manual' não existe no Simulador.")
                except Exception as e:
                    print(f"ERRO ao criar veículo: {e}")

            # --- 2. CRIAR PEDIDO MANUALMENTE ---
            elif acao == "criar_pedido_manual":
                orig = parametros['origem']
                dest = parametros['destino']
                premium = parametros.get('premium', False)  # Ler flag premium
                try:
                    sim.criar_pedido_manual(orig, dest, premium=premium)
                    dados = get_dados_visuais(sim)
                    tipo = "PREMIUM" if premium else "NORMAL"
                    print(f"Pedido {tipo} criado: {orig} → {dest}")
                except AttributeError:
                    print("ERRO: O método 'criar_pedido_manual' não existe no Simulador.")
                except Exception as e:
                    print(f"ERRO ao criar pedido: {e}")

            # --- 3. BOTÕES RÁPIDOS (Aleatório) ---
            elif acao == "add_carro":
                if parametros == "random":
                    if not sim.grafo.nos:
                        print("Erro: Grafo vazio.")
                        continue
                    sim.gerar_carro_aleatorio()
                    dados = get_dados_visuais(sim)
                    print("Veículo aleatório adicionado")
                    
            elif acao == "add_pedido":
                if parametros == "random":
                    sim.gerar_pedido_aleatorio()
                    dados = get_dados_visuais(sim)
                    print("Pedido aleatório adicionado")
            
            # --- 4. MUDAR ALGORITMO ---
            elif acao == "mudar_algoritmo":
                sim.definir_algoritmo(parametros)
                dados = get_dados_visuais(sim)
                print(f"Algoritmo alterado para: {parametros}")

if __name__ == "__main__":
    main()
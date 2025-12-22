import sys
import os
import pygame

# Configurar caminhos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.simulacao import Simulador
from gui import Gui

def extrair_dados_para_gui(sim):
    """
    Traduz o estado da simulação (Classes do core) para o formato que a GUI desenha.
    """
    dados_veiculos = []
    dados_pedidos = []

    # 1. Extrair Veículos
    # Na tua classe Estado, 'veiculos' é um Dicionário {id: Veiculo}
    # Por isso usamos .values() para obter a lista de objetos
    frota = sim.estado.veiculos.values()
    
    for v in frota:
        # Calcular percentagem de bateria
        # Atributos confirmados em veiculo.py: autonomia_atual, autonomia_max
        bateria_pct = 0
        if v.autonomia_max > 0:
            bateria_pct = v.autonomia_atual / v.autonomia_max

        # Obter rota com segurança
        # Em veiculo.py, 'rota_atual' só é criado no método definir_rota.
        # Se o carro acabou de nascer, ele não tem esse atributo. Usamos getattr com default [].
        rota = getattr(v, 'rota_atual', [])

        dados_veiculos.append({
            'id': v.id,
            'pos': v.localizacao, # É uma string (ID do nodo), a GUI converte
            'bateria': bateria_pct,
            'rota': rota,
            'estado': v.estado.value # Para debug visual (opcional)
        })

    # 2. Extrair Pedidos Pendentes
    # Na classe Estado: pedidos_pendentes é uma List
    for p in sim.estado.pedidos_pendentes:
        dados_pedidos.append({
            'id': p.id,
            'pos': p.origem # É uma string (ID do nodo)
        })

    return {
        'tempo': sim.tempo_atual.strftime('%H:%M'),
        'veiculos': dados_veiculos,
        'pedidos': dados_pedidos
    }

def main():
    arquivo_mapa = "src/data/cidade.json"
    
    if not os.path.exists(arquivo_mapa):
        print("ERRO: Mapa não encontrado em src/data/cidade.json")
        return

    # Inicialização
    sim = Simulador(arquivo_mapa)
    gui = Gui(arquivo_mapa)
    
    print("\n--- SIMULAÇÃO VISUAL A CORRER ---")
    print("Legenda: Verde=Táxi | Azul=Rota | Laranja=Cliente")

    # Controlo de tempo
    ultimo_passo = pygame.time.get_ticks()
    intervalo_ms = 1000  # 1 segundo por passo de simulação

    try:
        while gui.running:
            agora = pygame.time.get_ticks()
            
            # Lógica da Simulação (avança a cada 1 seg)
            if agora - ultimo_passo >= intervalo_ms:
                print(f"[{sim.tempo_atual.strftime('%H:%M')}] Passo de simulação...")
                sim.correr_passo()
                ultimo_passo = agora
            
            # Atualização Visual (avança a 60fps)
            dados = extrair_dados_para_gui(sim)
            gui.desenhar(dados)

    except KeyboardInterrupt:
        print("\nInterrompido pelo utilizador.")
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
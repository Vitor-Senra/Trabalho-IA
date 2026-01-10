"""
TESTE VISUAL (LENTO): Recarga e Abastecimento

Objetivo:
- Criar 4 veículos com bateria/combustível BAIXO
- Enviar para a estação certa
- Ver no GUI o movimento e a bateria a subir DEVAGAR

Controlos:
  ESPAÇO  -> pausa/retoma
  ESC     -> sair
  +       -> mais rápido (menos intervalo)
  -       -> mais lento (mais intervalo)
"""

import pygame
from src.simulacao import Simulador
from gui import Gui
from src.core.veiculo import EstadoVeiculo

def main():
    print("=" * 70)
    print("TESTE VISUAL (LENTO): RECARGA / ABASTECIMENTO")
    print("=" * 70)

    # --- Configs ---
    LIMIAR = 0.30
    LIMIAR_CRITICO = 0.15
    PERCENT_INICIAL = 0.15

    # Intervalo entre updates da simulação (em segundos)
    # 1.0 = 1 update por segundo (bem visível)
    intervalo_update = 1.0

    sim = Simulador("src/data/cidade.json")
    gui = Gui("src/data/cidade.json")

    # Limpar frota e criar 4 veículos fixos
    sim.estado.veiculos.clear()
    nos = list(sim.grafo.nos.keys())

    sim.criar_veiculo_manual("taxi_eletrico", nos[0])
    sim.criar_veiculo_manual("taxi_combustao", nos[5])
    sim.criar_veiculo_manual("taxixl_eletrica", nos[10])
    sim.criar_veiculo_manual("taxixl_combustao", nos[15])

    ids = list(sim.estado.veiculos.keys())

    # Forçar bateria baixa
    print("\n[SETUP] Bateria/combustível inicial:")
    for vid in ids:
        v = sim.estado.veiculos[vid]
        v.autonomia_atual = v.autonomia_max * PERCENT_INICIAL
        print(f"  {vid}: {v.autonomia_atual:.0f}/{v.autonomia_max:.0f}km ({PERCENT_INICIAL*100:.0f}%)")

    print("\n[AÇÃO] Enviando todos para recarga/abastecimento...")
    sim.verificar_e_recarregar_veiculos(limiar=LIMIAR, limiar_critico=LIMIAR_CRITICO)

    print("\n[DESTINOS]")
    for vid in ids:
        v = sim.estado.veiculos[vid]
        print(f"  {vid}: estado={v.estado.value}, destino={v.destino_atual}")

    # --- Loop Pygame ---
    clock = pygame.time.Clock()
    running = True
    paused = False

    frame = 0
    acumulador = 0.0  # acumula tempo real (segundos)

    print("\nDica: '+' acelera, '-' abranda.")
    print(f"Intervalo inicial: {intervalo_update:.2f}s por update de simulação")

    while running:
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    print("⏸️  PAUSA" if paused else "▶️  A CORRER")

                # + => mais rápido (menor intervalo)
                elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    intervalo_update = max(0.05, intervalo_update - 0.1)
                    print(f"⚡ intervalo_update = {intervalo_update:.2f}s")

                # - => mais lento (maior intervalo)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    intervalo_update = min(5.0, intervalo_update + 0.1)
                    print(f"🐢 intervalo_update = {intervalo_update:.2f}s")

        # Tempo real passado desde o último frame
        dt = clock.get_time() / 1000.0
        if not paused:
            acumulador += dt

        # Atualizar simulação apenas quando passar o intervalo
        if not paused and acumulador >= intervalo_update:
            sim.atualizar_movimento_veiculos()
            acumulador = 0.0

        # Montar dados para GUI
        dados_gui = {
            "tempo": sim.tempo_atual.strftime("%H:%M"),
            "veiculos": [],
            "pedidos": []
        }

        for v in sim.estado.veiculos.values():
            dados_gui["veiculos"].append({
                "id": v.id,
                "pos": v.localizacao,
                "ocupado": v.estado != EstadoVeiculo.DISPONIVEL,
                "estado_texto": v.estado.value.upper(),
                "rota": v.rota_atual if v.rota_atual else [],
                "bateria": v.autonomia_atual / v.autonomia_max,
                "tipo_str": v.tipo_str,
                "categoria": getattr(v, "categoria_veiculo", "N/A"),
                "capacidade": v.capacidade
            })

        gui.desenhar(dados_gui)

        # Log a cada ~2s (60 frames a 30 FPS)
        if frame % 60 == 0:
            print("\n[STATUS]")
            for vid in ids:
                v = sim.estado.veiculos[vid]
                pct = (v.autonomia_atual / v.autonomia_max) * 100
                print(f"  {vid}: {v.estado.value:16s} | loc={v.localizacao} | rota={len(v.rota_atual):2d} | bat={pct:5.1f}%")

            if all(sim.estado.veiculos[vid].estado == EstadoVeiculo.DISPONIVEL for vid in ids):
                print("\n✅ Todos recarregados/abastecidos. (PAUSADO) — ESC para sair.")
                paused = True

        clock.tick(30)  # 30 FPS

    pygame.quit()

if __name__ == "__main__":
    main()

from src.simulacao import Simulador
from src.core.veiculo import EstadoVeiculo
import time

print("=" * 60)
print("TESTE SIMPLES: MOVIMENTO + RECARGA")
print("=" * 60)

sim = Simulador("src/data/cidade.json")

# Limpar frota inicial
sim.estado.veiculos.clear()

nos = list(sim.grafo.nos.keys())

# Criar veículos com bateria baixa
sim.criar_veiculo_manual("taxi_eletrico", nos[0])
sim.criar_veiculo_manual("taxi_combustao", nos[5])
sim.criar_veiculo_manual("taxixl_eletrica", nos[10])
sim.criar_veiculo_manual("taxixl_combustao", nos[15])

ids = list(sim.estado.veiculos.keys())

# Forçar baterias baixas
for vid in ids:
    v = sim.estado.veiculos[vid]
    v.autonomia_atual = v.autonomia_max * 0.15
    print(f"{vid} criado em {v.localizacao} com {v.autonomia_atual:.0f}km")

print("\n[AÇÃO] Enviando para recarga/abastecimento...\n")
sim.verificar_e_recarregar_veiculos(limiar=0.3, limiar_critico=0.15)

print("\n[ESTADO INICIAL]")
for vid in ids:
    v = sim.estado.veiculos[vid]
    print(f"{vid}: estado={v.estado.value}, destino={v.destino_atual}")

print("\n[SIMULAÇÃO]\n")

# Simular 50 passos
for passo in range(1, 51):
    print(f"\n--- PASSO {passo} ---")
    sim.atualizar_movimento_veiculos()

    for vid in ids:
        v = sim.estado.veiculos[vid]
        percent = (v.autonomia_atual / v.autonomia_max) * 100
        print(
            f"{vid:5s} | {v.estado.value:15s} | "
            f"loc={v.localizacao} | "
            f"rota_len={len(v.rota_atual)} | "
            f"bat={percent:5.1f}%"
        )

    time.sleep(0.2)  # só para conseguires ler na consola

print("\n" + "=" * 60)
print("FIM DO TESTE")
print("=" * 60)

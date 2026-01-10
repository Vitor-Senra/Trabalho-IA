"""
Script de Teste: Sistema de Recarga e Abastecimento
====================================================
Testa se:
1. Veículos elétricos vão para estações de recarga
2. Veículos a combustão vão para postos de abastecimento
3. A autonomia sobe corretamente durante o processo
"""

from src.simulacao import Simulador
from src.core.veiculo import EstadoVeiculo
import time

def testar_recarga_abastecimento():
    print("=" * 70)
    print("TESTE: Sistema de Recarga e Abastecimento")
    print("=" * 70)

    # Criar simulador
    sim = Simulador('src/data/cidade.json')

    # Obter lista de nós disponíveis
    nos_disponiveis = list(sim.grafo.nos.keys())

    # Criar 4 veículos de teste (um de cada tipo) com bateria baixa
    print("\n[1] CRIANDO VEÍCULOS DE TESTE COM BATERIA BAIXA...")
    print("-" * 70)

    # Táxi Elétrico com 20% bateria
    sim.criar_veiculo_manual("taxi_eletrico", nos_disponiveis[0])
    taxi_eletrico_id = f"T_E{sim.metricas['taxis_criados']}"
    sim.estado.veiculos[taxi_eletrico_id].autonomia_atual = 50.0  # 20% de 250km

    # Táxi Combustão com 15% bateria
    sim.criar_veiculo_manual("taxi_combustao", nos_disponiveis[1])
    taxi_combustao_id = f"T_C{sim.metricas['taxis_criados']}"
    sim.estado.veiculos[taxi_combustao_id].autonomia_atual = 60.0  # 15% de 400km

    # TaxiXL Elétrica com 25% bateria
    sim.criar_veiculo_manual("taxixl_eletrica", nos_disponiveis[2])
    taxixl_eletrica_id = f"V_E{sim.metricas['taxixl_criadas']}"
    sim.estado.veiculos[taxixl_eletrica_id].autonomia_atual = 50.0  # 25% de 200km

    # TaxiXL Combustão com 10% bateria
    sim.criar_veiculo_manual("taxixl_combustao", nos_disponiveis[3])
    taxixl_combustao_id = f"V_C{sim.metricas['taxixl_criadas']}"
    sim.estado.veiculos[taxixl_combustao_id].autonomia_atual = 35.0  # 10% de 350km

    # Mostrar estado inicial
    print("\n[2] ESTADO INICIAL DOS VEÍCULOS:")
    print("-" * 70)
    for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]:
        v = sim.estado.veiculos[vid]
        percentagem = (v.autonomia_atual / v.autonomia_max) * 100
        print(f"  {vid:12s} | {v.tipo_str:10s} | {v.categoria_veiculo:6s} | "
              f"Bateria: {v.autonomia_atual:6.1f}km / {v.autonomia_max:6.1f}km ({percentagem:5.1f}%)")

    # Forçar verificação de recarga
    print("\n[3] FORÇANDO VERIFICAÇÃO DE RECARGA (limiar 30%)...")
    print("-" * 70)
    sim.verificar_e_recarregar_veiculos(limiar=0.3, limiar_critico=0.15)

    # Verificar para onde foram enviados
    print("\n[4] VERIFICANDO DESTINOS DE RECARGA:")
    print("-" * 70)
    for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]:
        v = sim.estado.veiculos[vid]
        destino_no = sim.grafo.nos.get(v.destino_atual)

        if destino_no:
            tipo_correto = "✅ CORRETO" if (
                (v.tipo_str == "eletrico" and destino_no.tipo == "estacao_recarga") or
                (v.tipo_str == "combustao" and destino_no.tipo == "posto_abastecimento")
            ) else "❌ ERRO"

            print(f"  {vid:12s} | Motor: {v.tipo_str:10s} | "
                  f"Vai para: {v.destino_atual:8s} ({destino_no.tipo:20s}) | {tipo_correto}")
        else:
            print(f"  {vid:12s} | ❌ SEM DESTINO DEFINIDO")

    # Simular chegada e processo de recarga
    print("\n[5] SIMULANDO MOVIMENTO ATÉ À ESTAÇÃO...")
    print("-" * 70)

    # Simular 20 passos (suficiente para a maioria dos veículos chegarem)
    max_passos = 20
    for passo in range(max_passos):
        todos_chegaram = True
        for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]:
            v = sim.estado.veiculos[vid]
            if v.rota_atual and v.estado not in (EstadoVeiculo.EM_RECARGA, EstadoVeiculo.EM_ABASTECIMENTO):
                todos_chegaram = False

        if todos_chegaram:
            print(f"  Todos os veículos chegaram às estações após {passo} passos!")
            break

        sim.atualizar_movimento_veiculos()

    # Verificar se chegaram e iniciaram recarga
    print("\n[6] ESTADO APÓS CHEGADA À ESTAÇÃO:")
    print("-" * 70)
    for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]:
        v = sim.estado.veiculos[vid]
        estado_correto = "✅ RECARREGANDO" if v.estado in (
            EstadoVeiculo.EM_RECARGA, EstadoVeiculo.EM_ABASTECIMENTO
        ) else f"⚠️  {v.estado.value}"

        percentagem = (v.autonomia_atual / v.autonomia_max) * 100
        print(f"  {vid:12s} | Estado: {estado_correto:20s} | "
              f"Bateria: {v.autonomia_atual:6.1f}km ({percentagem:5.1f}%)")

    # Registar autonomias iniciais de recarga
    autonomias_inicio = {
        vid: sim.estado.veiculos[vid].autonomia_atual
        for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]
    }

    # Simular processo de recarga (vários passos)
    print("\n[7] SIMULANDO PROCESSO DE RECARGA...")
    print("-" * 70)
    print("  Passo | Táxi Elét | Táxi Comb | TaxiXL El | TaxiXL Cb")
    print("-" * 70)

    passos_recarga = 30
    for passo in range(0, passos_recarga, 5):
        # Executar 5 passos
        for _ in range(5):
            sim.atualizar_movimento_veiculos()

        # Mostrar progresso
        valores = []
        for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]:
            v = sim.estado.veiculos[vid]
            percentagem = (v.autonomia_atual / v.autonomia_max) * 100
            valores.append(f"{percentagem:5.1f}%")

        print(f"  {passo+5:5d} | {valores[0]:9s} | {valores[1]:9s} | {valores[2]:9s} | {valores[3]:9s}")

    # Verificar resultado final
    print("\n[8] RESULTADO FINAL:")
    print("-" * 70)

    todos_recarregados = True
    for vid in [taxi_eletrico_id, taxi_combustao_id, taxixl_eletrica_id, taxixl_combustao_id]:
        v = sim.estado.veiculos[vid]
        autonomia_inicial = autonomias_inicio[vid]
        autonomia_final = v.autonomia_atual
        ganho = autonomia_final - autonomia_inicial
        percentagem_final = (v.autonomia_atual / v.autonomia_max) * 100

        # Verificar se a bateria subiu
        if ganho > 0:
            resultado = "✅ SUBIU"
        else:
            resultado = "❌ NÃO SUBIU"
            todos_recarregados = False

        # Verificar se está disponível novamente (se chegou a 100%)
        estado_final = "DISPONÍVEL" if v.estado == EstadoVeiculo.DISPONIVEL else v.estado.value

        print(f"  {vid:12s} | Inicial: {autonomia_inicial:6.1f}km | "
              f"Final: {autonomia_final:6.1f}km ({percentagem_final:5.1f}%) | "
              f"Ganho: +{ganho:6.1f}km | {resultado}")
        print(f"                Estado final: {estado_final}")

    # Resumo
    print("\n" + "=" * 70)
    if todos_recarregados:
        print("✅ TESTE PASSOU: Todos os veículos recarregaram corretamente!")
    else:
        print("❌ TESTE FALHOU: Alguns veículos não recarregaram!")
    print("=" * 70)

    # Verificação de tipos de estação
    print("\n[9] VERIFICAÇÃO DE TIPOS DE ESTAÇÃO NO MAPA:")
    print("-" * 70)
    estacoes_recarga = [no_id for no_id, no in sim.grafo.nos.items() if no.tipo == "estacao_recarga"]
    postos_abast = [no_id for no_id, no in sim.grafo.nos.items() if no.tipo == "posto_abastecimento"]

    print(f"  Estações de Recarga (Elétrico): {len(estacoes_recarga)}")
    if len(estacoes_recarga) > 0:
        print(f"    Exemplos: {', '.join(estacoes_recarga[:5])}")

    print(f"  Postos de Abastecimento (Combustão): {len(postos_abast)}")
    if len(postos_abast) > 0:
        print(f"    Exemplos: {', '.join(postos_abast[:5])}")

    if len(estacoes_recarga) == 0 or len(postos_abast) == 0:
        print("\n  ⚠️  AVISO: Faltam estações no mapa! Isto pode causar problemas.")

if __name__ == "__main__":
    testar_recarga_abastecimento()

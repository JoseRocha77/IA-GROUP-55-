import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
import osmnx as ox
import numpy as np
import random

from cidade_osm import CidadeOSM
from modelos import Veiculo, Pedido
from problema import Estado
import algoritmos
from simulador import Simulador


# =============================================================================
# 1. VISUALIZAÇÃO (Replay e Demo)
# =============================================================================
def animar_mapa_osmnx(cidade_osm, caminho_estados, titulo_alg):
    if not caminho_estados:
        print("❌ Sem caminho para visualizar.")
        return

    print(f"🎬 A preparar visualização ({len(caminho_estados)} frames)...")

    # Desenhar mapa base
    fig, ax = ox.plot_graph(cidade_osm.G, show=False, close=False,
                            node_size=0, edge_color='#cccccc', edge_linewidth=0.8,
                            bgcolor='white', figsize=(10, 10))

    # --- LOCAIS ---
    gx, gy = cidade_osm.nodes[cidade_osm.garagem]['coords']
    ax.scatter(gx, gy, c='black', marker='s', s=150, zorder=5, label='Garagem')

    bx, by = [], []
    for b in cidade_osm.bombas:
        c = cidade_osm.nodes[b]['coords']
        bx.append(c[0]);
        by.append(c[1])
    ax.scatter(bx, by, c='orange', marker='^', s=100, zorder=4, edgecolors='black')

    cx, cy = [], []
    for c in cidade_osm.carregadores:
        c = cidade_osm.nodes[c]['coords']
        cx.append(c[0]);
        cy.append(c[1])
    ax.scatter(cx, cy, c='blue', marker='P', s=100, zorder=4, edgecolors='white')

    # --- AGENTES ---
    taxi_scatters = [ax.scatter([], [], zorder=10, edgecolors='black', s=200) for _ in range(10)]
    origem_scatter = ax.scatter([], [], c='#FFD700', marker='*', s=350, zorder=6, edgecolors='black')
    destino_scatter = ax.scatter([], [], c='#9C27B0', marker='X', s=250, zorder=5, edgecolors='white', linewidth=1.5)

    titulo_obj = ax.set_title(f"{titulo_alg}", fontsize=14, fontweight='bold')

    # --- LEGENDA ---
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#32CD32', markersize=10, label='Táxi Livre'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF4500', markersize=10, label='Táxi Ocupado'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#00FFFF', markersize=10, label='A Carregar/Abastecer'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFD700', markersize=10, label='Bateria Fraca'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#FFD700', markersize=12, label='Cliente (Origem)'),
        Line2D([0], [0], marker='X', color='w', markerfacecolor='#9C27B0', markersize=10, label='Destino'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='black', markersize=8, label='Garagem'),
        Line2D([0], [0], marker='P', color='w', markerfacecolor='blue', markersize=8, label='Carregador'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='orange', markersize=8, label='Combustível')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8, framealpha=0.9)

    def update(frame):
        estado = caminho_estados[frame]
        ox_list, oy_list, dx_list, dy_list = [], [], [], []

        for p in estado.pedidos_pendentes:
            if p.origem in cidade_osm.nodes:
                ocoords = cidade_osm.nodes[p.origem]['coords']
                dcoords = cidade_osm.nodes[p.destino]['coords']
                ox_list.append(ocoords[0]);
                oy_list.append(ocoords[1])
                dx_list.append(dcoords[0]);
                dy_list.append(dcoords[1])

        for v in estado.veiculos:
            if v.ocupado and v.passageiros_a_bordo:
                for p in v.passageiros_a_bordo:
                    dcoords = cidade_osm.nodes[p.destino]['coords']
                    dx_list.append(dcoords[0]);
                    dy_list.append(dcoords[1])

        origem_scatter.set_offsets(np.c_[ox_list, oy_list] if ox_list else np.empty((0, 2)))
        destino_scatter.set_offsets(np.c_[dx_list, dy_list] if dx_list else np.empty((0, 2)))

        for sc in taxi_scatters: sc.set_offsets(np.empty((0, 2)))

        acao_atual = getattr(estado, 'acao_geradora', '') or ''

        for i, v in enumerate(estado.veiculos):
            if i < len(taxi_scatters):
                x, y = cidade_osm.nodes[v.local]['coords']
                cor = '#32CD32'
                tag_veiculo = f"[{v.id}]"
                if tag_veiculo in acao_atual and ("Recarregou" in acao_atual or "Abasteceu" in acao_atual):
                    cor = '#00FFFF'
                elif v.ocupado:
                    cor = '#FF4500'
                else:
                    if v.tipo == "eletrico" and v.autonomia_atual < 20:
                        cor = '#FFD700'
                    elif v.tipo == "combustao" and v.autonomia_atual < 100:
                        cor = '#FFD700'

                taxi_scatters[i].set_offsets([[x, y]])
                taxi_scatters[i].set_facecolor(cor)

        custo = estado.custo_acumulado
        titulo_obj.set_text(f"{titulo_alg} | Passo {frame} | {acao_atual}")

    # Intervalo mais rápido (100ms) se for replay longo
    intervalo = 200 if len(caminho_estados) > 100 else 500
    ani = animation.FuncAnimation(fig, update, frames=len(caminho_estados), interval=intervalo, repeat=False)
    plt.show()


# =============================================================================
# 2. GERAR CENÁRIOS
# =============================================================================
def gerar_cenario_demo(cidade):
    frota = []
    frota.append(Veiculo(1, "eletrico", cidade.garagem, 50, 4))
    frota.append(Veiculo(2, "combustao", cidade.get_local_aleatorio(), 600, 4))
    pedidos = []
    for i in range(2):
        origem = cidade.get_local_aleatorio()
        destino = cidade.get_local_aleatorio()
        while destino == origem: destino = cidade.get_local_aleatorio()
        pedidos.append(Pedido(100 + i, origem, destino, 1, 60))
    return Estado(frota, pedidos)


def gerar_cenario_simulacao(cidade):
    frota = []
    frota.append(Veiculo(1, "eletrico", cidade.garagem, 200, 4))
    frota.append(Veiculo(2, "combustao", cidade.get_local_aleatorio(), 600, 4))
    return frota


# =============================================================================
# 3. MENU PRINCIPAL
# =============================================================================
def main():
    print("🌍 A carregar OSMnx (Braga)... Por favor aguarde.")
    try:
        cidade = CidadeOSM()
    except Exception as e:
        print(f"Erro ao carregar mapa: {e}")
        return

    estado_demo = gerar_cenario_demo(cidade)

    while True:
        print("\n" + "=" * 50)
        print(" 🚖 TAXIGREEN - SISTEMA INTELIGENTE DE TRANSPORTE")
        print("=" * 50)
        print("--- DEMONSTRAÇÃO VISUAL (Estática) ---")
        print("1. Visualizar A*")
        print("2. Visualizar Greedy")
        print("3. Visualizar BFS")
        print("4. Visualizar DFS")
        print("5. 🎲 Gerar Novo Cenário Demo")
        print("-" * 30)
        print("--- SIMULAÇÃO REAL (Dinâmica) ---")
        print("6. ⏱️  Executar Simulação")
        print("-" * 30)
        print("0. Sair")

        opcao = input("👉 Escolha uma opção: ")

        if opcao == "0": break

        # --- OPÇÕES VISUAIS ---
        alg_map = {
            "1": ("A*", algoritmos.a_star, algoritmos.heuristica_taxi),
            "2": ("Greedy", algoritmos.greedy, algoritmos.heuristica_taxi),
            "3": ("BFS", algoritmos.bfs, None),
            "4": ("DFS", algoritmos.dfs, None),
        }

        if opcao in alg_map:
            nome, func, extra = alg_map[opcao]
            print(f"\n🧠 A calcular rota com {nome}...")
            args = (estado_demo, cidade, extra) if extra else (estado_demo, cidade)
            res = func(*args)
            if res:
                animar_mapa_osmnx(cidade, res[0], nome)
            else:
                print("❌ Sem solução.")

        elif opcao == "5":
            estado_demo = gerar_cenario_demo(cidade)
            print("✅ Novo cenário gerado.")

        # --- SIMULAÇÃO DINÂMICA ---
        elif opcao == "6":
            print("\n🚀 Configuração da Simulação:")

            # 1. Escolha do Algoritmo
            print("   [1] A* (Recomendado)")
            print("   [2] Greedy (Rápido)")
            print("   [3] BFS (Lento)")
            alg_esc = input("   Escolha o algoritmo [Default: Greedy]: ")

            algoritmo_func = algoritmos.greedy
            nome_alg = "Greedy"

            if alg_esc == "1":
                algoritmo_func = algoritmos.a_star
                nome_alg = "A*"
            elif alg_esc == "3":
                algoritmo_func = algoritmos.bfs
                nome_alg = "BFS"

            # 2. Duração
            try:
                tempo = int(input("   Duração (minutos) [Default: 200]: ") or "200")
            except:
                tempo = 200

            frota_sim = gerar_cenario_simulacao(cidade)
            sim = Simulador(cidade, frota_sim, algoritmo_escolhido=algoritmo_func)

            # Executa e guarda a cassete
            historico = sim.executar_simulacao(tempo_maximo=tempo, probabilidade_pedido=0.1)

            # 3. Visualizar Replay?
            ver_replay = input("\n🎬 Queres visualizar o REPLAY da simulação? (s/n): ")
            if ver_replay.lower() == 's':
                animar_mapa_osmnx(cidade, historico, f"Replay Simulação ({nome_alg})")

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
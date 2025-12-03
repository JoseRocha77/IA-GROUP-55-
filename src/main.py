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

# =============================================================================
# 1. VISUALIZAÇÃO (COM CORES E LEGENDAS CORRETAS)
# =============================================================================
def animar_mapa_osmnx(cidade_osm, caminho_estados, titulo_alg):
    if not caminho_estados:
        print("❌ Sem caminho.")
        return

    print(f"🎬 A gerar animação ({titulo_alg})...")

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
        bx.append(c[0]); by.append(c[1])
    ax.scatter(bx, by, c='orange', marker='^', s=100, zorder=4, edgecolors='black')

    cx, cy = [], []
    for c in cidade_osm.carregadores:
        c = cidade_osm.nodes[c]['coords']
        cx.append(c[0]); cy.append(c[1])
    ax.scatter(cx, cy, c='blue', marker='P', s=100, zorder=4, edgecolors='white')

    # --- AGENTES ---
    taxi_scatters = [ax.scatter([], [], zorder=10, edgecolors='black', s=200) for _ in range(10)]
    origem_scatter = ax.scatter([], [], c='#FFD700', marker='*', s=350, zorder=6, edgecolors='black')
    destino_scatter = ax.scatter([], [], c='#9C27B0', marker='X', s=250, zorder=5, edgecolors='white', linewidth=1.5)

    titulo_obj = ax.set_title(f"{titulo_alg}", fontsize=14, fontweight='bold')

    # --- LEGENDA COMPLETA ---
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#32CD32', markersize=10, label='Táxi Livre'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF4500', markersize=10, label='Táxi Ocupado'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#00FFFF', markersize=10, label='A Carregar/Abastecer'), # NOVA
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFD700', markersize=10, label='Bateria Fraca'),       # NOVA
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#FFD700', markersize=12, label='Cliente (Origem)'),
        Line2D([0], [0], marker='X', color='w', markerfacecolor='#9C27B0', markersize=10, label='Destino'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='black', markersize=8, label='Garagem'),
        Line2D([0], [0], marker='P', color='w', markerfacecolor='blue', markersize=8, label='Carregador'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='orange', markersize=8, label='Combustível')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8, framealpha=0.9)
    
    def update(frame):
        estado = caminho_estados[frame]
        
        ox_list, oy_list = [], [] 
        dx_list, dy_list = [], [] 
        
        # 1. Pedidos PENDENTES
        for p in estado.pedidos_pendentes:
            if p.origem in cidade_osm.nodes and p.destino in cidade_osm.nodes:
                ocoords = cidade_osm.nodes[p.origem]['coords']
                dcoords = cidade_osm.nodes[p.destino]['coords']
                
                ox_list.append(ocoords[0]); oy_list.append(ocoords[1])
                dx_list.append(dcoords[0]); dy_list.append(dcoords[1])

        # 2. Pedidos A BORDO
        for v in estado.veiculos:
            if v.ocupado and v.passageiros_a_bordo:
                for p in v.passageiros_a_bordo:
                    if p.destino in cidade_osm.nodes:
                        dcoords = cidade_osm.nodes[p.destino]['coords']
                        dx_list.append(dcoords[0])
                        dy_list.append(dcoords[1])
        
        # Atualizar scatters
        origem_scatter.set_offsets(np.c_[ox_list, oy_list] if ox_list else np.empty((0, 2)))
        destino_scatter.set_offsets(np.c_[dx_list, dy_list] if dx_list else np.empty((0, 2)))

        # 3. Táxis (COM LÓGICA DE CORES SEGURA)
        for sc in taxi_scatters: sc.set_offsets(np.empty((0, 2)))

        # Obter a string da ação de forma segura (evita erro no estado inicial)
        acao_atual = getattr(estado, 'acao_geradora', '')
        if acao_atual is None: acao_atual = ''

        for i, v in enumerate(estado.veiculos):
            if i < len(taxi_scatters):
                x, y = cidade_osm.nodes[v.local]['coords']
                
                # Cor base: Verde (Livre)
                cor = '#32CD32' 

                # Verificar se ESTE veículo específico está a carregar/abastecer AGORA
                # A string de ação é tipo "[1] Recarregou..."
                tag_veiculo = f"[{v.id}]"
                
                if tag_veiculo in acao_atual and ("Recarregou" in acao_atual or "Abasteceu" in acao_atual):
                    cor = '#00FFFF'  # CIANO (A carregar!)
                elif v.ocupado: 
                    cor = '#FF4500'  # Vermelho (Ocupado)
                else:
                    # Se não estiver a carregar nem ocupado, ver se tem bateria fraca
                    if v.tipo == "eletrico" and v.autonomia_atual < 15:
                        cor = '#FFD700' # Amarelo
                    elif v.tipo == "combustao" and v.autonomia_atual < 100:
                        cor = '#FFD700' # Amarelo
                
                taxi_scatters[i].set_offsets([[x, y]])
                taxi_scatters[i].set_facecolor(cor)
                
        custo = estado.custo_acumulado
        titulo_obj.set_text(f"{titulo_alg} | Passo {frame} | Custo: {custo:.1f}\n{acao_atual}")

    ani = animation.FuncAnimation(fig, update, frames=len(caminho_estados), interval=500, repeat=False) # Intervalo aumentado para veres melhor
    plt.show()

# =============================================================================
# 2. GERAR CENÁRIO (2 CARROS)
# =============================================================================
def gerar_cenario_original(cidade):
    frota = []
    # 1. Elétrico "quase a morrer" (15km) para testares o carregamento AZUL
    frota.append(Veiculo(1, "eletrico", cidade.garagem, 10, 4))
    
    # 2. Combustão normal
    loc2 = cidade.get_local_aleatorio()
    frota.append(Veiculo(2, "combustao", loc2, 600, 4))

    pedidos = []
    for i in range(2): 
        origem = cidade.get_local_aleatorio()
        destino = cidade.get_local_aleatorio()
        while destino == origem:
            destino = cidade.get_local_aleatorio()
        pedidos.append(Pedido(100+i, origem, destino, 1, 60))
        
    return Estado(frota, pedidos)

# =============================================================================
# 3. MENU
# =============================================================================
def main():
    print("🌍 A carregar OSMnx (1km)...")
    try:
        cidade = CidadeOSM()
    except Exception as e:
        print(f"Erro: {e}")
        return

    estado_inicial = gerar_cenario_original(cidade)
    
    while True:
        print("\n" + "="*45)
        print(" 🚖 TAXIGREEN - 2 Carros | 2 Pedidos")
        print("="*45)
        print("1. Ver A* (Inteligente)")
        print("2. Ver Greedy (Rápido)")
        print("3. Ver BFS (Lento)")
        print("4. Ver DFS (Profundidade)")
        print("5. 🎲 Novo Cenário")
        print("0. Sair")
        
        opcao = input("👉 Opção: ")
        
        if opcao == "0": break
        
        if opcao == "5": 
            estado_inicial = gerar_cenario_original(cidade)
            print("✅ Novo cenário gerado!")
            continue

        alg_map = {
            "1": ("A*", algoritmos.a_star, algoritmos.heuristica_taxi),
            "2": ("Greedy", algoritmos.greedy, algoritmos.heuristica_taxi),
            "3": ("BFS", algoritmos.bfs, None),
            "4": ("DFS", algoritmos.dfs, None),
        }
        
        if opcao in alg_map:
            nome, func, extra = alg_map[opcao]
            print(f"🧠 A processar {nome}...")
            
            start = time.time()
            args = (estado_inicial, cidade, extra) if extra else (estado_inicial, cidade)
            res = func(*args)
            
            if res:
                print(f"✅ Solução em {time.time() - start:.2f}s! A abrir mapa...")
                animar_mapa_osmnx(cidade, res[0], nome)
            else:
                print("❌ Sem solução ou tempo excedido.")
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
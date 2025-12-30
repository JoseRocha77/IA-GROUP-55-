import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider
from matplotlib.lines import Line2D
import osmnx as ox
import numpy as np
import random

# Importações dos teus módulos
from cidade_osm import CidadeOSM
from modelos import Veiculo, Pedido
from problema import Estado
import algoritmos
from simulador import Simulador

COR_FUNDO_JANELA = '#F7F7F7'
COR_FUNDO_MAPA = '#FFFFFF'
COR_TEXTO = '#666666'
COR_BOTOES = '#EFEFEF'


def imprimir_relatorio_estatico(estado_final, nome_algoritmo, tempo_execucao):
    print("\n" + "=" * 50)
    print(f"📊 RELATÓRIO DA SOLUÇÃO ({nome_algoritmo})")
    print("=" * 50)
    print(f"🧠 Tempo de Cálculo (CPU): {tempo_execucao:.4f} segundos")
    print("-" * 50)
    print(f"💰 Custo da Função Objetivo: {estado_final.custo_acumulado:.2f}")
    print(f"⏱️  Tempo Total da Operação:  {estado_final.tempo_atual:.1f} minutos")
    print(f"💵 Custo Monetário Real:     {estado_final.total_dinheiro:.2f} €")
    print(f"🌍 Emissões Totais de CO2:   {estado_final.total_co2:.1f} g")
    print("=" * 50 + "\n")


class VisualizadorInterativo:
    def __init__(self, cidade_osm, caminho_estados, titulo_alg):
        self.cidade_osm = cidade_osm
        self.caminho_estados = caminho_estados
        self.total_frames = len(caminho_estados)
        self.titulo_alg = titulo_alg
        self.is_playing = True
        self.textos_taxis = []

        self.fig, self.ax = ox.plot_graph(cidade_osm.G, show=False, close=False,
                                          node_size=0, edge_color='#e0e0e0', edge_linewidth=0.8,
                                          bgcolor=COR_FUNDO_MAPA, figsize=(12, 8))
        self.fig.patch.set_facecolor(COR_FUNDO_JANELA)
        plt.subplots_adjust(bottom=0.15, right=0.80, top=0.90, left=0.05)
        self.ax.axis('off')

        self.titulo_obj = self.ax.set_title(f"{titulo_alg} | A carregar...", fontsize=14, fontweight='bold', pad=20,
                                            color=COR_TEXTO)
        self._desenhar_estaticos()
        self.origem_scatter = self.ax.scatter([], [], c='#FFD700', marker='*', s=300, zorder=6, edgecolors='gray',
                                              linewidth=0.5)
        self.destino_scatter = self.ax.scatter([], [], c='#9C27B0', marker='X', s=200, zorder=5, edgecolors='white')
        self._configurar_legenda()
        self._configurar_widgets()
        self.ani = animation.FuncAnimation(self.fig, self.update, frames=self.total_frames, interval=200, repeat=True,
                                           blit=False)
        plt.show()

    def _desenhar_estaticos(self):
        gx, gy = self.cidade_osm.nodes[self.cidade_osm.garagem]['coords']
        self.ax.text(gx, gy, 'G', fontsize=10, ha='center', va='center', zorder=4, weight='bold', color='white',
                     bbox=dict(boxstyle="square,pad=0.3", fc="#555555", ec="none", alpha=0.8))
        for b in self.cidade_osm.bombas:
            x, y = self.cidade_osm.nodes[b]['coords']
            self.ax.text(x, y, 'B', fontsize=8, ha='center', va='center', zorder=4, weight='bold', color='#444',
                         bbox=dict(boxstyle="square,pad=0.3", fc="#FFD180", ec="none", alpha=0.8))
        for c in self.cidade_osm.carregadores:
            x, y = self.cidade_osm.nodes[c]['coords']
            self.ax.text(x, y, 'C', fontsize=8, ha='center', va='center', zorder=4, weight='bold', color='white',
                         bbox=dict(boxstyle="square,pad=0.3", fc="#64B5F6", ec="none", alpha=0.8))

    def _configurar_legenda(self):
        legend_elements = [
            Line2D([0], [0], marker='s', color='w', markerfacecolor='#555555', label='[G] Garagem', markersize=8),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='#FFD180', label='[B] Bombas', markersize=8),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='#64B5F6', label='[C] Carregador', markersize=8),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#66BB6A', label='(E) Elétrico', markersize=8),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#42A5F5', label='(C) Combustão', markersize=8),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#EF5350', label='(Ocupado)', markersize=8),
            Line2D([0], [0], marker='*', color='w', markerfacecolor='#FFD700', label='Origem', markersize=10),
            Line2D([0], [0], marker='X', color='w', markerfacecolor='#9C27B0', label='Destino', markersize=8),
        ]
        leg = self.ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.0, 1), borderaxespad=0.,
                             frameon=False, fontsize=9)
        leg.set_title("LEGENDA", prop={'weight': 'bold', 'size': 10});
        leg.get_title().set_color(COR_TEXTO)
        for text in leg.get_texts(): text.set_color(COR_TEXTO)

    def _configurar_widgets(self):
        ax_slider = plt.axes([0.20, 0.05, 0.60, 0.03], facecolor='white')
        self.slider = Slider(ax_slider, 'Tempo  ', 0, self.total_frames - 1, valinit=0, valstep=1, color='#B0BEC5')
        self.slider.label.set_color(COR_TEXTO);
        self.slider.valtext.set_color(COR_TEXTO)
        self.slider.on_changed(self.on_slider_change)
        ax_button = plt.axes([0.05, 0.05, 0.10, 0.04])
        self.btn = Button(ax_button, 'Pause', color=COR_BOTOES, hovercolor='white')
        self.btn.label.set_color(COR_TEXTO);
        self.btn.on_clicked(self.toggle_play)
        for spine in ax_slider.spines.values(): spine.set_edgecolor('#DDDDDD')
        for spine in ax_button.spines.values(): spine.set_edgecolor('#DDDDDD')

    def toggle_play(self, event):
        if self.is_playing:
            self.ani.event_source.stop(); self.btn.label.set_text('Play')
        else:
            self.ani.event_source.start(); self.btn.label.set_text('Pause')
        self.is_playing = not self.is_playing;
        self.fig.canvas.draw_idle()

    def on_slider_change(self, val):
        if self.is_playing: self.ani.event_source.stop(); self.is_playing = False; self.btn.label.set_text('Play')
        self.update(int(val));
        self.fig.canvas.draw_idle()

    def update(self, frame):
        self.slider.eventson = False;
        self.slider.set_val(frame);
        self.slider.eventson = True
        estado = self.caminho_estados[frame]
        ox_list, oy_list, dx_list, dy_list = [], [], [], []
        for p in estado.pedidos_pendentes:
            if p.origem in self.cidade_osm.nodes:
                ocoords = self.cidade_osm.nodes[p.origem]['coords'];
                dcoords = self.cidade_osm.nodes[p.destino]['coords']
                ox_list.append(ocoords[0]);
                oy_list.append(ocoords[1]);
                dx_list.append(dcoords[0]);
                dy_list.append(dcoords[1])
        for v in estado.veiculos:
            if v.ocupado and v.passageiros_a_bordo:
                for p in v.passageiros_a_bordo:
                    dcoords = self.cidade_osm.nodes[p.destino]['coords']
                    dx_list.append(dcoords[0]);
                    dy_list.append(dcoords[1])
        self.origem_scatter.set_offsets(np.c_[ox_list, oy_list] if ox_list else np.empty((0, 2)))
        self.destino_scatter.set_offsets(np.c_[dx_list, dy_list] if dx_list else np.empty((0, 2)))
        for txt in self.textos_taxis: txt.remove()
        self.textos_taxis.clear()
        for v in estado.veiculos:
            x, y = self.cidade_osm.nodes[v.local]['coords']
            letra = 'E' if v.tipo == 'eletrico' else 'C'
            cor_fundo = '#66BB6A'
            if v.tipo == 'combustao': cor_fundo = '#42A5F5'
            if v.ocupado:
                cor_fundo = '#EF5350'
            elif v.autonomia_atual < 20:
                cor_fundo = '#FFA726'
            txt = self.ax.text(x, y, letra, fontsize=9, ha='center', va='center', color='white', weight='bold',
                               zorder=10, bbox=dict(boxstyle="circle,pad=0.2", fc=cor_fundo, ec="white", lw=1.5))
            self.textos_taxis.append(txt)
            txt_id = self.ax.text(x + 60, y + 60, f"T{v.id}", fontsize=8, color=COR_TEXTO, weight='bold', zorder=11,
                                  bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.6))
            self.textos_taxis.append(txt_id)
        acao_atual = getattr(estado, 'acao_geradora', '') or ''
        self.titulo_obj.set_text(f"{self.titulo_alg}\nSim: {frame}m / {self.total_frames}m | {acao_atual}")


_visualizacao_atual = None


def animar_mapa_osmnx(cidade_osm, caminho_estados, titulo_alg):
    global _visualizacao_atual
    _visualizacao_atual = VisualizadorInterativo(cidade_osm, caminho_estados, titulo_alg)


def gerar_cenario_demo(cidade):
    frota = [Veiculo(1, "eletrico", cidade.garagem, 50, 4),
             Veiculo(2, "combustao", cidade.get_local_aleatorio(), 600, 4)]
    pedidos = []
    for i in range(2):
        origem = cidade.get_local_aleatorio();
        destino = cidade.get_local_aleatorio()
        while destino == origem: destino = cidade.get_local_aleatorio()
        pedidos.append(Pedido(100 + i, origem, destino, 1, 60))
    return Estado(frota, pedidos)


def gerar_frota_simulacao(cidade, num_veiculos):
    frota = []
    for i in range(1, num_veiculos + 1):
        if i == 1:
            tipo = "eletrico"; local = cidade.garagem; autonomia = 200
        else:
            tipo = "eletrico" if i % 2 != 0 else "combustao"
            local = cidade.get_local_aleatorio()
            autonomia = 200 if tipo == "eletrico" else 600
        frota.append(Veiculo(i, tipo, local, autonomia, 4))
    return frota


def main():
    print("🌍 A carregar OSMnx (Braga)... Por favor aguarde.")
    try:
        cidade = CidadeOSM()
    except Exception as e:
        print(f"Erro ao carregar mapa: {e}"); return
    estado_demo = gerar_cenario_demo(cidade)
    print("\n✅ Cenário de demonstração inicial gerado!")

    while True:
        print("\n" + "=" * 55)
        print(" 🚖 TAXIGREEN - SISTEMA INTELIGENTE DE TRANSPORTE")
        print("=" * 55)
        print("--- DEMONSTRAÇÃO VISUAL (Estática) ---")
        print("1. Visualizar A*")
        print("2. Visualizar Greedy")
        print("3. Visualizar BFS")
        print("4. Visualizar DFS")
        print("5. 🎲 Gerar Novo Cenário Demo")
        print("-" * 35)
        print("--- SIMULAÇÃO DE PERFORMANCE (Tempo Fixo) ---")
        print("6. ⏱️  Executar Benchmark (Limite: Segundos Reais)")
        print("-" * 35)
        print("0. Sair")
        opcao = input("👉 Escolha uma opção: ")

        if opcao == "0": break

        alg_map = {
            "1": ("A*", algoritmos.a_star, algoritmos.heuristica_taxi),
            "2": ("Greedy", algoritmos.greedy, algoritmos.heuristica_taxi),
            "3": ("BFS", algoritmos.bfs, None),
            "4": ("DFS", algoritmos.dfs, None),
        }

        if opcao in alg_map:
            nome, func, extra = alg_map[opcao]
            print(f"\n🧠 A calcular rota com {nome} (no cenário atual)...")
            start_time = time.time()
            args = (estado_demo, cidade, extra) if extra else (estado_demo, cidade)
            res = func(*args)
            end_time = time.time()
            if res:
                caminho, custo_final = res
                imprimir_relatorio_estatico(caminho[-1], nome, end_time - start_time)
                input("⚠️  ENTER para abrir gráfico (Feche a janela para voltar)...")
                animar_mapa_osmnx(cidade, caminho, nome)
            else:
                print("❌ Sem solução.")

        elif opcao == "5":
            estado_demo = gerar_cenario_demo(cidade); print("\n✅ NOVO CENÁRIO GERADO!")

        elif opcao == "6":
            print("\n🚀 Configuração do Benchmark:")
            print("   [1] A* (Recomendado)")
            print("   [2] Greedy (Recomendado)")
            print("   [3] BFS (⚠️ LENTO)")
            print("   [4] DFS (⚠️ LENTO)")

            alg_input = input("   Escolha o algoritmo [Default: Greedy]: ")
            algoritmo_func = algoritmos.greedy;
            nome_alg = "Greedy"
            if alg_input == "1":
                algoritmo_func = algoritmos.a_star; nome_alg = "A*"
            elif alg_input == "3":
                algoritmo_func = algoritmos.bfs; nome_alg = "BFS"
            elif alg_input == "4":
                algoritmo_func = algoritmos.dfs; nome_alg = "DFS"

            # --- HARDCODED: Sempre 2 carros ---
            num_veiculos = 2

            # --- MUDANÇA: Tempo default 60s ---
            try:
                segundos = int(input("   ⏱️  Tempo Limite (Segundos Reais) [Default: 60]: ") or "60")
            except:
                segundos = 60

            PROB_PEDIDO_FIXA = 0.025
            frota_sim = gerar_frota_simulacao(cidade, num_veiculos)
            sim = Simulador(cidade, frota_sim, algoritmo_escolhido=algoritmo_func)

            print(f"\n⚡ A iniciar Benchmark: {segundos}s reais | {num_veiculos} táxis | {nome_alg}...")
            historico = sim.executar_simulacao(segundos_reais_limite=segundos, probabilidade_pedido=PROB_PEDIDO_FIXA)

            if input("\n🎬 Visualizar Replay? (s/n): ").lower() == 's':
                print("⚠️  ENTER para abrir gráfico...")
                animar_mapa_osmnx(cidade, historico, f"Replay ({nome_alg} - {segundos}s)")

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
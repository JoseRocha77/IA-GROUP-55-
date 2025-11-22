import time
from cidade import Cidade
from modelos import Veiculo, Pedido
from problema import Estado
import algoritmos 

def imprimir_resultado(nome_algoritmo, resultado, tempo_execucao):
    """Função auxiliar para mostrar os resultados de forma bonita no terminal"""
    print(f"\n{'='*10} {nome_algoritmo} {'='*10}")
    
    if resultado is None:
        print("❌ Não foi encontrada solução.")
        return

    caminho, custo_total = resultado
    print(f"✅ Solução encontrada em {tempo_execucao:.4f} segundos.")
    print(f"💰 Custo Total: {custo_total}")
    print(f"👣 Passos ({len(caminho)} estados):")
    
    for i, estado in enumerate(caminho):
        # Se for o estado inicial
        if i == 0:
            print(f"  [Início] {estado.veiculos}")
        else:
            # Tenta mostrar a ação que levou a este estado
            acao = getattr(estado, 'acao_geradora', 'Movimento')
            print(f"  {i}. {acao} -> {estado.veiculos}")

def main():
    print("🚖 --- INÍCIO DA SIMULAÇÃO TAXIGREEN --- 🚖")

    # ---------------------------------------------------------
    # 1. CONFIGURAÇÃO DA CIDADE (O GRAFO)
    # ---------------------------------------------------------
    #mini cidade para teste rápido
    cidade = Cidade()

    # (Nós): ID, X, Y, Tipo
    # As coordenadas X,Y são importantes para a heurística do A*
    cidade.add_node("Garagem", 0, 0, "garagem")
    cidade.add_node("A", 0, 10, "cliente")        # Zona Norte
    cidade.add_node("B", 10, 0, "cliente")        # Zona Este
    cidade.add_node("Posto", 5, 5, "recarga")     # Ponto central

    # (Arestas): Origem, Destino, Distancia, Tempo
    # Estamos a criar estradas de ida e volta
    cidade.add_edge("Garagem", "A", 10, 15)
    cidade.add_edge("A", "Garagem", 10, 15)

    cidade.add_edge("Garagem", "B", 10, 15)
    cidade.add_edge("B", "Garagem", 10, 15)

    cidade.add_edge("A", "Posto", 6, 8)
    cidade.add_edge("Posto", "A", 6, 8)

    cidade.add_edge("B", "Posto", 6, 8)
    cidade.add_edge("Posto", "B", 6, 8)
    
    # Estrada direta longa entre clientes
    cidade.add_edge("A", "B", 15, 20) 
    cidade.add_edge("B", "A", 15, 20)

    print(f"🏙️ Cidade criada com {len(cidade.nodes)} locais.")

    # ---------------------------------------------------------
    # 2. CRIAR FROTA E PEDIDOS
    # ---------------------------------------------------------
    # Veículo Elétrico com pouca bateria (para forçar talvez uma recarga ou gestão cuidada)
    t1 = Veiculo(id_v=1, tipo="eletrico", local="Garagem", autonomia=40, cap_passageiros=4)
    
    # Pedido: Cliente quer ir de A para B
    p1 = Pedido(id_pedido=101, origem="A", destino="B", passageiros=1, prazo=50)

    frota = [t1]
    pedidos = [p1]

    # ---------------------------------------------------------
    # 3. ESTADO INICIAL
    # ---------------------------------------------------------
    estado_inicial = Estado(frota, pedidos)
    print(f"📍 Estado Inicial: Táxi em {t1.local}, Cliente em {p1.origem} quer ir para {p1.destino}")

    # ---------------------------------------------------------
    # 4. EXECUTAR ALGORITMOS
    # ---------------------------------------------------------
    
    # --- TESTE 1: BFS (Largura) ---
    start_time = time.time()
    res_bfs = algoritmos.bfs(estado_inicial, cidade)
    end_time = time.time()
    imprimir_resultado("BFS (Largura)", res_bfs, end_time - start_time)

    # --- TESTE 2: DFS (Profundidade) ---
    
    start_time = time.time()
    res_dfs = algoritmos.dfs(estado_inicial, cidade)
    end_time = time.time()
    imprimir_resultado("DFS (Profundidade)", res_dfs, end_time - start_time)

    # --- TESTE 3: A* (A-Star) ---
    
    start_time = time.time()
    res_astar = algoritmos.a_star(estado_inicial, cidade, algoritmos.heuristica_taxi)
    end_time = time.time()
    imprimir_resultado("A* (A-Star)", res_astar, end_time - start_time)

if __name__ == "__main__":
    main()
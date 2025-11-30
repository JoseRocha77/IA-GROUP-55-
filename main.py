import time
from cidade import Cidade
from modelos import Veiculo, Pedido
from problema import Estado
import algoritmos 

def imprimir_resultado(nome_algoritmo, resultado, tempo_execucao):
    """Função auxiliar para mostrar os resultados de forma bonita no terminal"""
    print(f"\n{'='*10} {nome_algoritmo} {'='*10}")
    
    if resultado is None:
        print("❌ Não foi encontrada solução (ou o algoritmo atingiu o limite).")
        return

    caminho, custo_total = resultado
    print(f"✅ Solução encontrada em {tempo_execucao:.4f} segundos.")
    print(f"💰 Custo Total: {custo_total:.2f}")
    print(f"👣 Passos ({len(caminho)} estados):")
    
    for i, estado in enumerate(caminho):
        # Se for o estado inicial
        if i == 0:
            print(f"  [Início] {estado.veiculos}")
        else:
            # Mostra a ação E o estado da frota nesse momento
            acao = getattr(estado, 'acao_geradora', 'Movimento')
            print(f"  {i}. {acao} -> {estado.veiculos}")

def main():
    print("🚖 --- INICIALIZANDO SIMULAÇÃO TAXIGREEN --- 🚖")
    
    # 1. Grelha 4x4
    cidade = Cidade()
    for x in range(4):
        for y in range(4):
            nome_no = f"Rua_{x}_{y}" 
            tipo = "cliente"
            if x == 0 and y == 0: tipo = "garagem"       
            elif x == 2 and y == 2: tipo = "recarga"     
            elif x == 3 and y == 0: tipo = "combustivel" 
            cidade.add_node(nome_no, x*4, y*4, tipo)

    for x in range(4):
        for y in range(4):
            origem = f"Rua_{x}_{y}"
            if x < 3:
                destino = f"Rua_{x+1}_{y}"
                cidade.add_edge(origem, destino, 4, 6)
                cidade.add_edge(destino, origem, 4, 6)
            if y < 3:
                destino = f"Rua_{x}_{y+1}"
                cidade.add_edge(origem, destino, 4, 6)
                cidade.add_edge(destino, origem, 4, 6)

    # 2. Frota Mista
    t1 = Veiculo(id_v=1, tipo="eletrico", local="Rua_0_0", autonomia=20, cap_passageiros=4)
    t2 = Veiculo(id_v=2, tipo="combustao", local="Rua_3_3", autonomia=500, cap_passageiros=4)
    p1 = Pedido(id_pedido=101, origem="Rua_0_3", destino="Rua_3_0", passageiros=1, prazo=60)
    p2 = Pedido(id_pedido=102, origem="Rua_3_2", destino="Rua_3_1", passageiros=2, prazo=30)

    frota = [t1, t2]
    pedidos = [p1, p2]
    estado_inicial = Estado(frota, pedidos)
    print(f"📍 Cenário Pronto: {len(frota)} Táxis e {len(pedidos)} Pedidos.")

    while True:
        print("\n" + "="*40)
        print("       🚖 MENU DE ALGORITMOS 🚖")
        print("="*40)
        print("1. Executar BFS (Largura)")
        print("2. Executar DFS (Profundidade)")
        print("3. Executar A* (A-Star)")
        print("4. Executar Greedy (Guloso)")
        print("0. Sair")
        
        opcao = input("👉 Opção: ")

        if opcao == "1":
            start = time.time()
            res = algoritmos.bfs(estado_inicial, cidade)
            imprimir_resultado("BFS", res, time.time() - start)
        elif opcao == "2":
            start = time.time()
            res = algoritmos.dfs(estado_inicial, cidade)
            imprimir_resultado("DFS", res, time.time() - start)
        elif opcao == "3":
            start = time.time()
            res = algoritmos.a_star(estado_inicial, cidade, algoritmos.heuristica_taxi)
            imprimir_resultado("A*", res, time.time() - start)
        elif opcao == "4":
            start = time.time()
            # O Greedy usa a mesma heurística que o A*
            res = algoritmos.greedy(estado_inicial, cidade, algoritmos.heuristica_taxi)
            imprimir_resultado("Greedy", res, time.time() - start)
        elif opcao == "0":
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    main()
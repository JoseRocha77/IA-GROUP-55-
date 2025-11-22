from queue import Queue

def heuristica_taxi(estado, cidade):
    """
    Estima o custo restante até ao objetivo.
    Lógica:
    1. Para cada passageiro não entregue, temos de percorrer pelo menos 
       a distância da sua origem ao destino.
    2. Se o passageiro ainda não foi apanhado, somar distância do táxi mais perto até ele.
    """
    custo_estimado = 0
    
    # 1. Pedidos que ainda estão à espera (na rua)
    for pedido in estado.pedidos_pendentes:
        # Distância mínima da viagem (Origem -> Destino)
        dist_viagem = cidade.get_heuristic(pedido.origem, pedido.destino)
        custo_estimado += dist_viagem
        
        # Distância do táxi mais próximo até à origem do pedido
        min_dist_taxi = float('inf')
        for v in estado.veiculos:
            if not v.ocupado: # Só conta táxis livres
                d = cidade.get_heuristic(v.local, pedido.origem)
                if d < min_dist_taxi:
                    min_dist_taxi = d
        
        if min_dist_taxi != float('inf'):
            custo_estimado += min_dist_taxi

    # 2. Pedidos que já estão no carro (a meio da viagem)
    for v in estado.veiculos:
        if v.ocupado and v.passageiros_a_bordo:
            pedido = v.passageiros_a_bordo[0]
            # Falta percorrer: Local Atual do Carro -> Destino do Cliente
            dist_restante = cidade.get_heuristic(v.local, pedido.destino)
            custo_estimado += dist_restante

    return custo_estimado



def reconstruir_caminho(estado_final):
    """
    Percorre os 'pais' de trás para a frente para reconstruir a história.
    Igual ao 'reconst_path' do teu código original.
    """
    caminho = []
    atual = estado_final
    while atual is not None:
        caminho.append(atual)
        atual = atual.pai
    return list(reversed(caminho))

# =============================================================================
# 1. PESQUISA EM LARGURA (BFS) 
# =============================================================================
def bfs(estado_inicial, cidade):
    # No teu código original: visited = set() e fila = Queue()
    visited = set()
    fila = Queue()

    fila.put(estado_inicial)
    visited.add(estado_inicial)

    while not fila.empty():
        estado_atual = fila.get()

        # Teste Objetivo
        if estado_atual.is_objetivo():
            return reconstruir_caminho(estado_atual), estado_atual.custo_acumulado

        # Gerar sucessores
        sucessores = estado_atual.gera_sucessores(cidade)
        
        for filho in sucessores:
            filho.pai = estado_atual
            if filho not in visited:
                fila.put(filho)
                visited.add(filho)
                # O 'pai' já foi definido dentro do gera_sucessores/Estado, 
                # por isso não precisamos do dicionário 'parent' aqui.

    return None

# =============================================================================
# 2. ALGORITMO A* (A-Star)
# =============================================================================
def a_star(estado_inicial, cidade, funcao_heuristica):
    # open_list e closed_list como no teu código
    open_list = {estado_inicial}
    closed_list = set()


    while len(open_list) > 0:
        
        # --- Encontrar n com o menor f(n) ---
        n = None
        min_f = float('inf')

        for v in open_list:
            # f(n) = g(n) + h(n)
            h = funcao_heuristica(v, cidade)
            g = v.custo_acumulado
            f = g + h
            
            if f < min_f:
                min_f = f
                n = v
        # -------------------------------------------

        if n is None:
            print('Caminho não encontrado!')
            return None

        # Se encontrou a solução
        if n.is_objetivo():
            return reconstruir_caminho(n), n.custo_acumulado

        # Remover n da open e passar para closed
        open_list.remove(n)
        closed_list.add(n)

        # Gerar sucessores de n
        sucessores = n.gera_sucessores(cidade)

        for filho in sucessores:
            filho.pai = n
            # Se já visitámos este estado exato com um custo menor ou igual, ignoramos
            if filho in closed_list:
                continue

            # Se o filho não está na open_list, adicionamos 
            if filho not in open_list:
                open_list.add(filho)
                # O pai já vem definido do 'gera_sucessores'

    return None

# =============================================================================
# 3. PESQUISA EM PROFUNDIDADE (DFS) 
# =============================================================================
def dfs(estado, cidade, path=None, visited=None):
    """
    Implementação recursiva igual à do Graph.py, mas para Estados.
    """
    if path is None:
        path = []
    if visited is None:
        visited = set()

    # Adicionar estado atual ao caminho e aos visitados
    path.append(estado)
    visited.add(estado)

    # Teste de Objetivo
    if estado.is_objetivo():
        return path, estado.custo_acumulado

    # Gerar filhos
    sucessores = estado.gera_sucessores(cidade)
    
    for filho in sucessores:
        if filho not in visited:
            resultado = dfs(filho, cidade, path, visited)
            if resultado is not None:
                return resultado

    # Backtracking: Se não encontrou nada por aqui, remove do caminho
    path.pop()
    return None


import heapq
from queue import Queue


def heuristica_taxi(estado, cidade):
    """
    Estima o custo restante até ao objetivo.
    1. Soma distância de cada passageiro pendente (Origem -> Destino).
    2. Soma distância do táxi livre mais próximo até ao passageiro.
    """
    custo_estimado = 0
    
    # 1. Pedidos pendentes
    for pedido in estado.pedidos_pendentes:
        dist_viagem = cidade.get_heuristic(pedido.origem, pedido.destino)
        custo_estimado += dist_viagem
        
        min_dist_taxi = float('inf')
        for v in estado.veiculos:
            if not v.ocupado:
                d = cidade.get_heuristic(v.local, pedido.origem)
                if d < min_dist_taxi:
                    min_dist_taxi = d
        
        if min_dist_taxi != float('inf'):
            custo_estimado += min_dist_taxi

    # 2. Pedidos a bordo
    for v in estado.veiculos:
        if v.ocupado and v.passageiros_a_bordo:
            pedido = v.passageiros_a_bordo[0]
            dist_restante = cidade.get_heuristic(v.local, pedido.destino)
            custo_estimado += dist_restante

    return custo_estimado

def reconstruir_caminho(estado_final):
    """Percorre os 'pais' de trás para a frente."""
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
    # BFS usa Queue (FIFO), não precisa de Heap
    visited = set()
    fila = Queue()

    fila.put(estado_inicial)
    visited.add(estado_inicial)

    while not fila.empty():
        estado_atual = fila.get()

        if estado_atual.is_objetivo():
            return reconstruir_caminho(estado_atual), estado_atual.custo_acumulado

        for filho in estado_atual.gera_sucessores(cidade):
            filho.pai = estado_atual
            if filho not in visited:
                fila.put(filho)
                visited.add(filho)

    return None

# =============================================================================
# 2. PESQUISA EM PROFUNDIDADE (DFS)
# =============================================================================
def dfs(estado_inicial, cidade):
    """
    Versão iterativa do DFS usando uma pilha (LIFO).
    Evita o RecursionError do Python em mapas grandes.
    """
    visitados = set()
    # Em Python, uma lista funciona como uma pilha se usarmos append() e pop()
    pilha = [] 
    
    pilha.append(estado_inicial)
    
    # Dicionário para acesso rápido aos visitados para evitar ciclos
    # Guardamos o hash para poupar memória, ou o próprio objeto se o __eq__ for robusto
    visitados.add(estado_inicial)

    while pilha:
        # Pop do último elemento (LIFO - Last In, First Out)
        estado_atual = pilha.pop()

        if estado_atual.is_objetivo():
            return reconstruir_caminho(estado_atual), estado_atual.custo_acumulado

        # Gerar sucessores
        sucessores = estado_atual.gera_sucessores(cidade)
        
        for filho in sucessores:
            # Verificação de ciclo básica
            if filho not in visitados:
                filho.pai = estado_atual
                visitados.add(filho)
                pilha.append(filho)

    return None

# =============================================================================
# 3. ALGORITMO A* (A-Star) - OTIMIZADO COM HEAPQ
# =============================================================================
def a_star(estado_inicial, cidade, funcao_heuristica):
    # A PriorityQueue (heap) ordena automaticamente pelo primeiro elemento do tuple
    # Guardamos: (f, contador, estado)
    # O 'contador' serve apenas para desempatar se f for igual, evitando erro de comparação
    
    count = 0
    open_list = [] # A nossa Heap
    
    # Calcular f inicial
    h = funcao_heuristica(estado_inicial, cidade)
    g = estado_inicial.custo_acumulado
    f = g + h
    
    # Push inicial: (f, count, estado)
    heapq.heappush(open_list, (f, count, estado_inicial))
    
    # Dicionários para acesso rápido (O(1))
    open_set_hashes = {estado_inicial} 
    closed_list = set()
    
    # Dicionário para guardar o melhor g encontrado até agora para cada estado
    # Isto é CRUCIAL para a performance do A*
    g_score = {estado_inicial: g}

    while open_list:
        # Pop do estado com MENOR f (Instantâneo O(1))
        f_atual, _, n = heapq.heappop(open_list)
        open_set_hashes.remove(n)

        if n.is_objetivo():
            return reconstruir_caminho(n), n.custo_acumulado

        closed_list.add(n)

        for filho in n.gera_sucessores(cidade):
            filho.pai = n
            
            # Se já fechámos este nó, ignorar
            if filho in closed_list:
                continue

            # Calcular novo g
            new_g = filho.custo_acumulado
            
            # Se já vimos este estado e o caminho novo não é melhor, ignorar
            if filho in g_score and new_g >= g_score[filho]:
                continue
            
            # Se é um caminho melhor (ou novo), registamos
            g_score[filho] = new_g
            h = funcao_heuristica(filho, cidade)
            f = new_g + h
            
            # Adicionar à Heap se não estiver lá
            if filho not in open_set_hashes:
                count += 1
                heapq.heappush(open_list, (f, count, filho))
                open_set_hashes.add(filho)

    return None

# =============================================================================
# 4. ALGORITMO GREEDY (GULOSO) - OTIMIZADO COM HEAPQ
# =============================================================================
def greedy(estado_inicial, cidade, funcao_heuristica):
    """
    Versão Otimizada com Heap.
    Ordena apenas pelo h(n).
    """
    count = 0
    open_list = []
    
    # Calcular h inicial
    h = funcao_heuristica(estado_inicial, cidade)
    heapq.heappush(open_list, (h, count, estado_inicial))
    
    open_set_hashes = {estado_inicial}
    closed_list = set()

    while open_list:
        # Pop do menor h
        h_atual, _, n = heapq.heappop(open_list)
        open_set_hashes.remove(n)

        if n.is_objetivo():
            return reconstruir_caminho(n), n.custo_acumulado

        closed_list.add(n)

        for filho in n.gera_sucessores(cidade):
            filho.pai = n
            
            if filho in closed_list:
                continue
            
            if filho not in open_set_hashes:
                # Calcular h para ordenar
                h = funcao_heuristica(filho, cidade)
                count += 1
                heapq.heappush(open_list, (h, count, filho))
                open_set_hashes.add(filho)
                
    return None


import math

class Cidade:
    def __init__(self):
        # Dicionário para guardar os nós: {id_no: {dados}}
        self.nodes = {}
        # Dicionário para guardar as arestas: {origem: {destino: {dados_aresta}}}
        self.graph = {}

    def add_node(self, node_id, x, y, node_type="rua"):
        """
        Adiciona um local à cidade.
        :param node_id: Nome ou ID do local (ex: 'A', 'Hospital')
        :param x, y: Coordenadas para cálculo de heurísticas (distância linha reta)
        :param node_type: 'rua', 'recarga', 'combustivel', 'cliente'
        """
        self.nodes[node_id] = {
            'coords': (x, y),
            'type': node_type
        }
        if node_id not in self.graph:
            self.graph[node_id] = {}

    def add_edge(self, u, v, distance, time):
        """
        Cria uma ligação (estrada) entre dois locais.
        :param distance: Distância em km (custo para bateria/combustivel)
        :param time: Tempo em minutos (custo para o cliente)
        """
        # Adiciona aresta de ida
        self.graph[u][v] = {'dist': distance, 'time': time}
        
        # Se a estrada for de duplo sentido, descomenta a linha abaixo:
        # self.graph[v][u] = {'dist': distance, 'time': time}

    def get_heuristic(self, start_id, goal_id):
        """
        Calcula a distância Euclidiana (linha reta) para o algoritmo A*.
        """
        x1, y1 = self.nodes[start_id]['coords']
        x2, y2 = self.nodes[goal_id]['coords']
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def get_neighbors(self, node_id):
        """Retorna os vizinhos de um nó"""
        return self.graph.get(node_id, {}).keys()
    
    def get_distance(self, u, v):
        """Retorna a distância (custo) da aresta entre u e v."""
        # Se existir uma estrada direta
        if u in self.graph and v in self.graph[u]:
            return self.graph[u][v]['dist']
        # Se for o mesmo local, distância é 0
        if u == v:
            return 0
        # Se não houver ligação direta, retorna infinito
        return float('inf')



cidade = Cidade()

# 1. ZONA CENTRAL (Coordenadas próximas, muito ligadas)
cidade.add_node("Central_Taxi", 10, 10, node_type="garagem")
cidade.add_node("Baixa", 12, 12, node_type="cliente")
cidade.add_node("Estacao_Comboio", 15, 10, node_type="cliente")

# 2. PONTOS CRÍTICOS (Recarga e Combustível) 
cidade.add_node("Posto_Galp", 8, 8, node_type="combustivel")
cidade.add_node("Super_Charger", 14, 14, node_type="recarga")

# 3. ZONA PERIFÉRICA (Longe, coordenadas distantes) [cite: 28]
cidade.add_node("Aeroporto", 50, 50, node_type="cliente")

# 4. LIGAR OS PONTOS (Criar estradas)
# (Origem, Destino, Km, Minutos)
cidade.add_edge("Central_Taxi", "Baixa", 2, 5)
cidade.add_edge("Baixa", "Super_Charger", 3, 6)
cidade.add_edge("Baixa", "Estacao_Comboio", 4, 8)
cidade.add_edge("Estacao_Comboio", "Aeroporto", 40, 30) # Via rápida: muitos km, tempo razoável
cidade.add_edge("Aeroporto", "Super_Charger", 35, 25) 

print("Vizinhos da Baixa:", list(cidade.get_neighbors("Baixa")))
print("Heurística (linha reta) Baixa -> Aeroporto:", cidade.get_heuristic("Baixa", "Aeroporto"))
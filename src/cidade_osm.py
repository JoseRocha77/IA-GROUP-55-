import osmnx as ox
import networkx as nx
import random
import math
from cidade import Cidade

class CidadeOSM(Cidade):
    def __init__(self):
        super().__init__()
        RAIO_MAPA = 700
        print(f" A descarregar o Centro de Braga (Raio {RAIO_MAPA}m)...")

        point = (41.55032, -8.42005)
        self.G = ox.graph_from_point(point, dist=RAIO_MAPA, network_type="drive")

        print(" A limpar nós isolados do mapa...")
        try:
            self.G = ox.truncate.largest_component(self.G, strongly=True)
        except AttributeError:
            try:
                self.G = ox.utils_graph.get_largest_component(self.G, strongly=True)
            except AttributeError:
                largest = max(nx.strongly_connected_components(self.G), key=len)
                self.G = self.G.subgraph(largest).copy()

        self.G = ox.project_graph(self.G)
        print(f" Mapa carregado e limpo: {len(self.G.nodes)} nós.")

        self._converter_mapa()
        self._definir_pois()
        
        self.pesos_originais = {}

    def _converter_mapa(self):
        for node_id, data in self.G.nodes(data=True):
            self.add_node(node_id, data['x'], data['y'], "rua")

        for u, v, data in self.G.edges(data=True):
            dist_m = data.get('length', 50)
            dist_km = dist_m / 1000.0
            tempo_min = (dist_km / 40) * 60
            self.add_edge(u, v, dist_km, tempo_min)

    def _definir_pois(self):
        todos_nos = list(self.nodes.keys())
        self.garagem = random.choice(todos_nos)
        self.nodes[self.garagem]['type'] = 'garagem'
        
        self.bombas = random.sample(todos_nos, 4)
        for b in self.bombas: self.nodes[b]['type'] = 'combustivel'
        self.carregadores = random.sample(todos_nos, 4)
        for c in self.carregadores: self.nodes[c]['type'] = 'recarga'
        self.locais_livres = [n for n in todos_nos if self.nodes[n]['type'] == 'rua']

    def get_local_aleatorio(self):
        return random.choice(self.locais_livres)

    def get_heuristic(self, start_id, goal_id):
        if start_id not in self.nodes or goal_id not in self.nodes: return float('inf')
        x1, y1 = self.nodes[start_id]['coords']
        x2, y2 = self.nodes[goal_id]['coords']
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) / 1000.0

    def simular_transito_dinamico(self):
        # 1. Cache inicial dos pesos (se não existir)
        if not self.pesos_originais:
             for u, v in self.G.edges():
                 if self.G.has_edge(u, v):
                     data = self.G.get_edge_data(u, v)
                     d = data[0] if 0 in data else data
                     self.pesos_originais[(u,v)] = d.get('time', 1)

        # 2. LIMPAR: Restaurar o trânsito normal em TODAS as ruas primeiro
        # Isto evita que a cidade fique toda vermelha acumulada
        for u, v in self.G.edges():
            if not self.G.has_edge(u, v): continue
            data = self.G.get_edge_data(u, v)
            d = data[0] if 0 in data else data
            original = self.pesos_originais.get((u,v), 1)
            d['time'] = original

        # 3. NOVO TRÂNSITO: Escolher apenas 5 a 10 ruas para engarrafar
        arestas = list(self.G.edges())
        # Engarrafa apenas 8 ruas aleatórias (para ser bem visível mas limpo)
        amostra = random.sample(arestas, min(len(arestas), 8)) 

        for u, v in amostra:
            if not self.G.has_edge(u, v): continue
            data = self.G.get_edge_data(u, v)
            d = data[0] if 0 in data else data
            
            original = self.pesos_originais.get((u,v), 1)
            # Torna a rua 5x mais lenta
            d['time'] = original * 5

    def get_arestas_engarrafadas(self):
        engarrafadas = []
        if not self.pesos_originais: return []
        
        for u, v in self.G.edges():
            if not self.G.has_edge(u, v): continue
            data = self.G.get_edge_data(u, v)
            d = data[0] if 0 in data else data
            
            original = self.pesos_originais.get((u,v), 0)
            # Se for significativamente mais lento que o original, está engarrafada
            if original > 0 and d.get('time', 0) > original * 1.5:
                engarrafadas.append((u, v))
        return engarrafadas
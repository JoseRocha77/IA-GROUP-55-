import osmnx as ox
import networkx as nx
import random
import math
from cidade import Cidade

class CidadeOSM(Cidade):
    def __init__(self):
        super().__init__()
        print("🌍 A descarregar o Centro de Braga (Raio 1km)...")
        
        point = (41.55032, -8.42005) # Sé de Braga
        self.G = ox.graph_from_point(point, dist=1000, network_type="drive")
        
        # --- CORREÇÃO DE SEGURANÇA (Versão OSMnx 2.0+) ---
        # Mantém apenas o maior conjunto de ruas ligadas (remove ilhas isoladas)
        print("🔧 A limpar nós isolados do mapa...")
        
        # Tenta usar a nova API (OSMnx 2.0+), se falhar usa a antiga
        try:
            # Nova sintaxe para OSMnx >= 2.0
            self.G = ox.truncate.largest_component(self.G, strongly=True)
        except AttributeError:
            try:
                # Sintaxe intermédia/antiga
                self.G = ox.utils_graph.get_largest_component(self.G, strongly=True)
            except AttributeError:
                # Fallback para NetworkX direto se tudo falhar
                print("⚠️ Aviso: A usar NetworkX para limpar ilhas.")
                # Para grafos direcionados (strongly connected)
                largest = max(nx.strongly_connected_components(self.G), key=len)
                self.G = self.G.subgraph(largest).copy()

        self.G = ox.project_graph(self.G) # Projeta para metros (UTM)
        
        print(f"✅ Mapa carregado e limpo: {len(self.G.nodes)} nós.")
        
        self._converter_mapa()
        self._definir_pois()

    def _converter_mapa(self):
        for node_id, data in self.G.nodes(data=True):
            # Guardamos X,Y em Metros
            self.add_node(node_id, data['x'], data['y'], "rua")

        for u, v, data in self.G.edges(data=True):
            dist_m = data.get('length', 50)
            dist_km = dist_m / 1000.0
            
            # 40km/h média na cidade
            tempo_min = (dist_km / 40) * 60
            
            # Adiciona aresta
            self.add_edge(u, v, dist_km, tempo_min)

    def _definir_pois(self):
        todos_nos = list(self.nodes.keys())
        
        self.garagem = random.choice(todos_nos)
        self.nodes[self.garagem]['type'] = 'garagem'
        
        # Garante que os pontos escolhidos existem mesmo no grafo limpo
        self.bombas = random.sample(todos_nos, 4)
        for b in self.bombas: self.nodes[b]['type'] = 'combustivel'
            
        self.carregadores = random.sample(todos_nos, 4)
        for c in self.carregadores: self.nodes[c]['type'] = 'recarga'
        
        self.locais_livres = [n for n in todos_nos if self.nodes[n]['type'] == 'rua']

    def get_local_aleatorio(self):
        return random.choice(self.locais_livres)

    def get_heuristic(self, start_id, goal_id):
        if start_id not in self.nodes or goal_id not in self.nodes:
            return float('inf')
            
        x1, y1 = self.nodes[start_id]['coords']
        x2, y2 = self.nodes[goal_id]['coords']
        
        dist_metros = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        return dist_metros / 1000.0
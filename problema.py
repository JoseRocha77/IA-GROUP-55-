import copy
from modelos import Veiculo, Pedido

class Estado:
    def __init__(self, veiculos, pedidos_pendentes, tempo_atual=0, custo_acumulado=0):
        self.veiculos = veiculos # Lista de objetos Veiculo
        self.pedidos_pendentes = pedidos_pendentes # Lista de Pedidos à espera
        self.tempo_atual = tempo_atual
        self.custo_acumulado = custo_acumulado # Custo g(n)
        
        # Para o algoritmo saber de onde veio (reconstrução do caminho)
        self.pai = None 
        self.acao_geradora = None

    def is_objetivo(self):
        # O objetivo é não ter pedidos pendentes nem passageiros nos carros
        carros_vazios = all(not v.ocupado for v in self.veiculos)
        return len(self.pedidos_pendentes) == 0 and carros_vazios

    # Métodos obrigatórios para o algoritmo de procura gerir conjuntos (set) e filas
    def __lt__(self, other):
        return self.custo_acumulado < other.custo_acumulado

    def __hash__(self):
        # Simplificação: criar uma string única que represente o estado
        v_str = "".join([str(v) for v in self.veiculos])
        p_str = "".join([str(p.id) for p in self.pedidos_pendentes])
        return hash(v_str + p_str)
    
    def __eq__(self, other):
        return hash(self) == hash(other)
    
    def gera_sucessores(self, grafo_cidade):
        sucessores = []
        
        # Iterar sobre cada veículo da frota
        for i, veiculo in enumerate(self.veiculos):
            
            # --- AÇÃO 1: RECOLHER PASSAGEIRO (Pickup) ---
            # Se o táxi está no mesmo local que um pedido pendente e está livre
            if not veiculo.ocupado:
                for pedido in self.pedidos_pendentes:
                    if veiculo.local == pedido.origem:
                        novo_estado = self.copiar_estado()
                        v_novo = novo_estado.veiculos[i]
                        
                        # Ação: Apanhar passageiro
                        v_novo.ocupado = True
                        v_novo.passageiros_a_bordo.append(pedido)
                        
                        # Remover dos pendentes
                        novo_estado.pedidos_pendentes = [p for p in novo_estado.pedidos_pendentes if p.id != pedido.id]
                        
                        novo_estado.acao_geradora = f"Veiculo {v_novo.id} recolheu pedido {pedido.id} em {veiculo.local}"
                        sucessores.append(novo_estado)
            
            # --- AÇÃO 2: ENTREGAR PASSAGEIRO (Dropoff) ---
            # Se tem passageiros e está no destino deles
            if veiculo.ocupado and veiculo.passageiros_a_bordo:
                pedido = veiculo.passageiros_a_bordo[0] # Vamos assumir 1 pedido de cada vez por simplicidade
                if veiculo.local == pedido.destino:
                    novo_estado = self.copiar_estado()
                    v_novo = novo_estado.veiculos[i]
                    
                    # Ação: Deixar passageiro
                    v_novo.ocupado = False
                    v_novo.passageiros_a_bordo = []
                    
                    # Ganho pelo serviço (opcional, mas reduz o custo para incentivar a entrega)
                    novo_estado.custo_acumulado -= 10 
                    
                    novo_estado.acao_geradora = f"Veiculo {v_novo.id} entregou pedido {pedido.id} em {veiculo.local}"
                    sucessores.append(novo_estado)

            # --- AÇÃO 3: RECARREGAR (Charge) ---
            # Se está numa estação de recarga e não está cheio
            dados_local = grafo_cidade.nodes[veiculo.local]
            if dados_local['type'] == 'recarga' and veiculo.autonomia_atual < veiculo.autonomia_max:
                novo_estado = self.copiar_estado()
                v_novo = novo_estado.veiculos[i]
                
                v_novo.autonomia_atual = veiculo.autonomia_max
                # Recarregar custa tempo/dinheiro
                novo_estado.custo_acumulado += 5 
                
                novo_estado.acao_geradora = f"Veiculo {v_novo.id} recarregou em {veiculo.local}"
                sucessores.append(novo_estado)

            # --- AÇÃO 4: MOVER PARA VIZINHO (Move) ---
            # O táxi pode sempre mover-se para uma rua adjacente
            vizinhos = grafo_cidade.get_neighbors(veiculo.local)
            for vizinho in vizinhos:
                distancia = grafo_cidade.get_distance(veiculo.local, vizinho)
                
                # Só move se tiver bateria
                if veiculo.autonomia_atual >= distancia:
                    novo_estado = self.copiar_estado()
                    v_novo = novo_estado.veiculos[i]
                    
                    # Atualizar posição e bateria
                    v_novo.local = vizinho
                    v_novo.autonomia_atual -= distancia
                    
                    # Custo do movimento
                    custo_movimento = distancia
                    if veiculo.tipo == "combustao":
                        custo_movimento = distancia * 1.5 # Penalização combustão
                        
                    novo_estado.custo_acumulado += custo_movimento
                    novo_estado.acao_geradora = f"Veiculo {v_novo.id} moveu-se {veiculo.local}->{vizinho}"
                    sucessores.append(novo_estado)
                    
        return sucessores

    def copiar_estado(self):
        """Cria uma cópia profunda (Deep Copy) para não alterar o estado atual"""
        return copy.deepcopy(self)
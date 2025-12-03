import math
from modelos import Veiculo, Pedido

# --- CONFIGURAÇÃO DE CUSTOS E PESOS ---
ALPHA = 0.4  # Peso do Dinheiro
BETA = 0.4   # Peso do Tempo
GAMMA = 0.2  # Peso do CO2

# Custos Unitários
CUSTO_KM_ELETRICO = 0.05
CUSTO_KM_COMBUSTAO = 0.15
CUSTO_MINUTO = 0.50
EMISSAO_CO2_KM_ICE = 120
EMISSAO_CO2_KM_EV = 0

class Estado:
    def __init__(self, veiculos, pedidos_pendentes, tempo_atual=0, custo_acumulado=0):
        self.veiculos = veiculos
        self.pedidos_pendentes = pedidos_pendentes
        self.tempo_atual = tempo_atual
        self.custo_acumulado = custo_acumulado
        
        self.pai = None
        self.acao_geradora = None

        self.total_co2 = 0.0       
        self.total_dinheiro = 0.0  

    def is_objetivo(self):
        # O objetivo é não haver pedidos pendentes e nenhum carro ter passageiros a bordo
        return len(self.pedidos_pendentes) == 0 and all(not v.ocupado for v in self.veiculos)

    def calcular_custo_acao(self, veiculo, distancia_km, tempo_min):
        custo_operacional = distancia_km * (CUSTO_KM_ELETRICO if veiculo.tipo == "eletrico" else CUSTO_KM_COMBUSTAO)
        custo_tempo = tempo_min * CUSTO_MINUTO # Assumindo custo por minuto
        custo_ambiental = distancia_km * EMISSAO_CO2_KM_ICE if veiculo.tipo == "combustao" else 0

        total = (ALPHA * custo_operacional) + (BETA * custo_tempo) + (GAMMA * custo_ambiental)
        return total, custo_operacional, custo_ambiental

    def copia_segura(self):
        # Clonar veiculos
        novos_veiculos = [v.clone() for v in self.veiculos]
        # Clonar lista de pedidos
        novos_pedidos = list(self.pedidos_pendentes)
        
        novo = Estado(novos_veiculos, novos_pedidos, self.tempo_atual, self.custo_acumulado)
        novo.total_co2 = self.total_co2
        novo.total_dinheiro = self.total_dinheiro
        novo.pai = None
        return novo

    def gera_sucessores(self, cidade):
        sucessores = []

        for i, veiculo in enumerate(self.veiculos):
            # --- 1. RECOLHER ---
            if not veiculo.ocupado:
                for pedido in self.pedidos_pendentes:
                    if veiculo.local == pedido.origem:
                        ns = self.copia_segura()
                        v_novo = ns.veiculos[i]
                        
                        v_novo.ocupado = True
                        v_novo.passageiros_a_bordo.append(pedido)
                        # Remove da lista global
                        ns.pedidos_pendentes = [p for p in ns.pedidos_pendentes if p.id != pedido.id]
                        
                        # Custo fixo de recolha (ex: 2 min)
                        t_op = 2
                        custo, eur, co2 = self.calcular_custo_acao(veiculo, 0, t_op)
                        
                        ns.custo_acumulado += custo
                        ns.tempo_atual += t_op
                        ns.total_dinheiro += eur
                        ns.total_co2 += co2
                        ns.acao_geradora = f"[{v_novo.id}] Recolheu passageiro em {v_novo.local}"
                        sucessores.append(ns)

            # --- 2. ENTREGAR ---
            if veiculo.ocupado and veiculo.passageiros_a_bordo:
                # Assume 1 passageiro de cada vez
                pedido = veiculo.passageiros_a_bordo[0]
                if veiculo.local == pedido.destino:
                    ns = self.copia_segura()
                    v_novo = ns.veiculos[i]
                    
                    v_novo.ocupado = False
                    v_novo.passageiros_a_bordo = []
                    
                    t_op = 2
                    custo, eur, co2 = self.calcular_custo_acao(veiculo, 0, t_op)
                    
                    ns.custo_acumulado += custo
                    ns.tempo_atual += t_op
                    ns.total_dinheiro += eur
                    ns.total_co2 += co2
                    ns.acao_geradora = f"[{v_novo.id}] Entregou passageiro em {v_novo.local}"
                    sucessores.append(ns)

            # --- 3. RECARREGAR ---
            tipo_loc = cidade.nodes[veiculo.local]['type']
            # Lógica simplificada: Só recarrega se não estiver cheio
            pode_rec = (veiculo.tipo == "eletrico" and tipo_loc == "recarga") or \
                       (veiculo.tipo == "combustao" and tipo_loc == "combustivel")
            
            if pode_rec and veiculo.autonomia_atual < veiculo.autonomia_max:
                ns = self.copia_segura()
                v_novo = ns.veiculos[i]
                
                recuperado = veiculo.autonomia_max - veiculo.autonomia_atual
                v_novo.autonomia_atual = veiculo.autonomia_max
                
                t_op = math.ceil(recuperado / 5) # 5km por min
                custo, eur, co2 = self.calcular_custo_acao(veiculo, 0, t_op)
                # Custo extra do combustivel/eletricidade
                eur += (recuperado * 0.1) 
                
                ns.custo_acumulado += custo
                ns.tempo_atual += t_op
                ns.total_dinheiro += eur
                
                acao_nome = "Recarregou" if veiculo.tipo == "eletrico" else "Abasteceu"
                ns.acao_geradora = f"[{v_novo.id}] {acao_nome} em {v_novo.local}"
                sucessores.append(ns)

            # --- 4. MOVER ---
            # Só se move se tiver autonomia
            vizinhos = cidade.get_neighbors(veiculo.local)
            for vizinho in vizinhos:
                dados = cidade.graph[veiculo.local][vizinho]
                dist = dados['dist']
                tempo = dados['time']

                if veiculo.autonomia_atual >= dist:
                    ns = self.copia_segura()
                    v_novo = ns.veiculos[i]
                    
                    v_novo.local = vizinho
                    v_novo.autonomia_atual -= dist
                    
                    custo, eur, co2 = self.calcular_custo_acao(veiculo, dist, tempo)
                    
                    ns.custo_acumulado += custo
                    ns.tempo_atual += tempo
                    ns.total_dinheiro += eur
                    ns.total_co2 += co2
                    ns.acao_geradora = f"[{v_novo.id}] Moveu: {veiculo.local} -> {vizinho}"
                    sucessores.append(ns)

        return sucessores

    # --- MÉTODOS PARA ALGORITMOS (HASHING CORRIGIDO) ---
    def __lt__(self, other):
        return self.custo_acumulado < other.custo_acumulado

    def __hash__(self):
        # ULTRA SEGURO: Removemos a autonomia do hash.
        # Se dois estados têm os carros nos mesmos sítios, com os mesmos passageiros
        # e os mesmos pedidos pendentes, consideramos IGUAIS.
        # Isto impede que o algoritmo ande em círculos a gastar gasolina infinitamente.
        
        # Tuple de veiculos: (ID, Local, Ocupado)
        v_info = tuple((v.id, v.local, v.ocupado) for v in self.veiculos)
        
        # Tuple de passageiros a bordo (importante para distinguir quem leva quem)
        # Assumindo que cada carro leva 1 lista de passageiros
        p_bordo = tuple(tuple(p.id for p in v.passageiros_a_bordo) for v in self.veiculos)

        # Tuple de pedidos pendentes
        p_pend = tuple(p.id for p in self.pedidos_pendentes)
        
        return hash((v_info, p_bordo, p_pend))

    def __eq__(self, other):
        return hash(self) == hash(other)
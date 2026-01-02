import math
from modelos import Veiculo, Pedido

# --- CONFIGURAÇÃO DE CUSTOS E PESOS ---
ALPHA = 0.1  # Peso do Dinheiro
BETA = 0.9  # Peso do Tempo
GAMMA = 0.05  # Peso do CO2

# Custos Unitários
CUSTO_KM_ELETRICO = 0.05
CUSTO_KM_COMBUSTAO = 0.15
CUSTO_MINUTO = 0.50
EMISSAO_CO2_KM_ICE = 120
EMISSAO_CO2_KM_EV = 0

PENALIDADE_CLIENTE_INSATISFEITO = 10.0


class Estado:
    def __init__(self, veiculos, pedidos_pendentes, tempo_atual=0, custo_acumulado=0, alerta=None,
                 arestas_transito=None):
        self.veiculos = veiculos
        self.pedidos_pendentes = pedidos_pendentes
        self.tempo_atual = tempo_atual
        self.custo_acumulado = custo_acumulado

        self.pai = None
        self.acao_geradora = None

        self.alerta = alerta
        self.arestas_transito = arestas_transito or []

        self.total_co2 = 0.0
        self.total_dinheiro = 0.0

    def is_objetivo(self):
        return len(self.pedidos_pendentes) == 0 and all(not v.ocupado for v in self.veiculos)

    def calcular_custo_acao(self, veiculo, distancia_km, tempo_min):
        custo_operacional = distancia_km * (CUSTO_KM_ELETRICO if veiculo.tipo == "eletrico" else CUSTO_KM_COMBUSTAO)
        custo_tempo = tempo_min * CUSTO_MINUTO
        custo_ambiental = distancia_km * EMISSAO_CO2_KM_ICE if veiculo.tipo == "combustao" else 0

        total = (ALPHA * custo_operacional) + (BETA * custo_tempo) + (GAMMA * custo_ambiental)
        return total, custo_operacional, custo_ambiental

    def copia_segura(self):
        novos_veiculos = [v.clone() for v in self.veiculos]
        novos_pedidos = list(self.pedidos_pendentes)
        novo = Estado(novos_veiculos, novos_pedidos, self.tempo_atual, self.custo_acumulado, self.alerta)
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
                        # Verificação de Prazo
                        if self.tempo_atual > pedido.prazo:
                            continue

                        # Calcula dist direta
                        dist_estimada = cidade.get_heuristic(pedido.origem, pedido.destino)
                        # Se não tiver bateria para a viagem + 10%, não aceita
                        if veiculo.autonomia_atual < dist_estimada * 1.1:
                            continue 
                       
                        ns = self.copia_segura()
                        
                        ns.alerta = None
                        v_novo = ns.veiculos[i]

                        v_novo.ocupado = True
                        v_novo.passageiros_a_bordo.append(pedido)
                        ns.pedidos_pendentes = [p for p in ns.pedidos_pendentes if p.id != pedido.id]

                        t_op = 2
                        custo, eur, co2 = self.calcular_custo_acao(veiculo, 0, t_op)

                        if pedido.prefere_eletrico and veiculo.tipo == "combustao":
                            custo += PENALIDADE_CLIENTE_INSATISFEITO

                        ns.custo_acumulado += custo
                        ns.tempo_atual += t_op
                        ns.total_dinheiro += eur
                        ns.total_co2 += co2
                        ns.acao_geradora = f"[{v_novo.id}] Recolheu passageiro em {v_novo.local}"
                        sucessores.append(ns)

            # 2. ENTREGAR
            if veiculo.ocupado and veiculo.passageiros_a_bordo:
                pedido = veiculo.passageiros_a_bordo[0]
                if veiculo.local == pedido.destino:
                    ns = self.copia_segura()
                    ns.alerta = None
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

            # 3. RECARREGAR
            tipo_loc = cidade.nodes[veiculo.local]['type']
            pode_rec = (veiculo.tipo == "eletrico" and tipo_loc == "recarga") or \
                       (veiculo.tipo == "combustao" and tipo_loc == "combustivel")

            if pode_rec and veiculo.autonomia_atual < veiculo.autonomia_max:
                ns = self.copia_segura()
                ns.alerta = None
                v_novo = ns.veiculos[i]
                recuperado = veiculo.autonomia_max - veiculo.autonomia_atual
                v_novo.autonomia_atual = veiculo.autonomia_max

                t_op = math.ceil(recuperado / 5)
                custo, eur, co2 = self.calcular_custo_acao(veiculo, 0, t_op)
                eur += (recuperado * 0.1)

                ns.custo_acumulado += custo
                ns.tempo_atual += t_op
                ns.total_dinheiro += eur

                acao_nome = "Recarregou" if veiculo.tipo == "eletrico" else "Abasteceu"
                ns.acao_geradora = f"[{v_novo.id}] {acao_nome} em {v_novo.local}"
                sucessores.append(ns)

            # 4. MOVER
            vizinhos = cidade.get_neighbors(veiculo.local)
            for vizinho in vizinhos:
                dados = cidade.graph[veiculo.local][vizinho]
                dist = dados['dist']
                tempo = dados['time']

                if veiculo.autonomia_atual >= dist:
                    ns = self.copia_segura()
                    ns.alerta = None
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

    def __lt__(self, other):
        return self.custo_acumulado < other.custo_acumulado

    # =========================================================================
    # --- CORREÇÃO PARA DFS: DISCRETIZAÇÃO DA BATERIA ---
    # =========================================================================
    def _assinatura_veiculo(self, v):
        """
        Cria uma assinatura simplificada do veículo usando DEGRAUS.
        """
        # Agrupa a bateria em blocos de 10km.
        # Ex: 99km -> 9, 91km -> 9. (Considera igual)
        # Ex: 89km -> 8. (Considera diferente, permite revisitar se tiver mais carga)
        nivel_bateria = int(v.autonomia_atual // 10)

        passageiros_ids = tuple(p.id for p in v.passageiros_a_bordo)

        return (v.id, v.local, v.ocupado, nivel_bateria, passageiros_ids)

    def __hash__(self):
        # Hash baseado na assinatura simplificada
        v_info = tuple(self._assinatura_veiculo(v) for v in self.veiculos)
        p_pend = tuple(p.id for p in self.pedidos_pendentes)
        return hash((v_info, p_pend))

    def __eq__(self, other):
        # Igualdade baseada na assinatura simplificada
        if not isinstance(other, Estado): return False

        minha_sig = tuple(self._assinatura_veiculo(v) for v in self.veiculos)
        outra_sig = tuple(other._assinatura_veiculo(v) for v in other.veiculos)

        meus_pends = tuple(p.id for p in self.pedidos_pendentes)
        outros_pends = tuple(p.id for p in other.pedidos_pendentes)

        return minha_sig == outra_sig and meus_pends == outros_pends
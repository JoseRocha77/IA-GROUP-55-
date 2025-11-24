import copy
import math

from modelos import Veiculo, Pedido

# --- CONFIGURAÇÃO DE CUSTOS E PESOS (Ajustar conforme relatório) ---
# A soma dos pesos (ALPHA, BETA, GAMMA) deve ser preferencialmente 1.0
ALPHA = 0.4  # Peso do Custo Monetário (Dinheiro)
BETA = 0.4  # Peso do Tempo (Rapidez)
GAMMA = 0.2  # Peso do Ambiente (CO2)

# Custos Unitários
CUSTO_KM_ELETRICO = 0.05  # €/km
CUSTO_KM_COMBUSTAO = 0.15  # €/km
CUSTO_MINUTO = 0.50  # €/min (Valor do tempo)
EMISSAO_CO2_KM_ICE = 120  # gramas CO2/km
EMISSAO_CO2_KM_EV = 0  # gramas CO2/km


class Estado:
    def __init__(self, veiculos, pedidos_pendentes, tempo_atual=0, custo_acumulado=0):
        self.veiculos = veiculos  # Lista de objetos Veiculo
        self.pedidos_pendentes = pedidos_pendentes  # Lista de Pedidos à espera
        self.tempo_atual = tempo_atual
        self.custo_acumulado = custo_acumulado  # g(n) - Custo real desde o início

        # Variáveis para reconstrução do caminho
        self.pai = None
        self.acao_geradora = None

        # Métricas para relatório (opcional, mas bom para análise)
        self.total_co2 = 0
        self.total_dinheiro = 0

    def is_objetivo(self):
        """
        O objetivo é atingido quando não há pedidos na lista de pendentes
        E não há passageiros dentro dos carros (todos entregues).
        """
        carros_vazios = all(not v.ocupado for v in self.veiculos)
        return len(self.pedidos_pendentes) == 0 and carros_vazios

    def calcular_custo_acao(self, veiculo, distancia_km, tempo_min):
        """
        Calcula o custo ponderado de uma transição (ação).
        Fórmula: Custo = (α * €) + (β * Tempo) + (γ * CO2)
        """
        # 1. Custo Monetário
        custo_operacional = 0
        if veiculo.tipo == "eletrico":
            custo_operacional = distancia_km * CUSTO_KM_ELETRICO
        else:
            custo_operacional = distancia_km * CUSTO_KM_COMBUSTAO

        # Custo do tempo "monetizado" (opcional, ou usar apenas o valor bruto do tempo)
        custo_operacional += (tempo_min * CUSTO_MINUTO)

        # 2. Custo Temporal (Direto)
        custo_tempo = tempo_min

        # 3. Custo Ambiental
        custo_ambiental = 0
        if veiculo.tipo == "combustao":
            custo_ambiental = distancia_km * EMISSAO_CO2_KM_ICE

        # Custo Final Ponderado
        total = (ALPHA * custo_operacional) + (BETA * custo_tempo) + (GAMMA * custo_ambiental)

        return total, custo_operacional, custo_ambiental

    def gera_sucessores(self, cidade):
        sucessores = []

        # O agente (sistema) decide uma ação para cada veículo disponível
        for i, veiculo in enumerate(self.veiculos):

            # ===============================================================
            # AÇÃO 1: RECOLHER PASSAGEIRO (PICKUP)
            # Pré-condição: Veículo livre E no mesmo local do pedido
            # ===============================================================
            if not veiculo.ocupado:
                for pedido in self.pedidos_pendentes:
                    if veiculo.local == pedido.origem:
                        novo_estado = self.copiar_estado()
                        v_novo = novo_estado.veiculos[i]

                        # Efeitos
                        v_novo.ocupado = True
                        v_novo.passageiros_a_bordo.append(pedido)

                        # Remove da lista de pendentes no novo estado
                        # (Filtra a lista mantendo todos MENOS o pedido atual)
                        novo_estado.pedidos_pendentes = [p for p in novo_estado.pedidos_pendentes if p.id != pedido.id]

                        # Custo: Tempo fixo de embarque (ex: 2 min)
                        tempo_embarque = 2
                        custo_passo, custo_monetario, co2 = self.calcular_custo_acao(veiculo, 0, tempo_embarque)

                        novo_estado.custo_acumulado += custo_passo
                        novo_estado.tempo_atual += tempo_embarque
                        novo_estado.acao_geradora = f"[{v_novo.id}] Recolheu passageiro em {v_novo.local}"

                        sucessores.append(novo_estado)

            # ===============================================================
            # AÇÃO 2: ENTREGAR PASSAGEIRO (DROPOFF)
            # Pré-condição: Veículo ocupado E no local de destino do passageiro
            # ===============================================================
            if veiculo.ocupado and veiculo.passageiros_a_bordo:
                pedido = veiculo.passageiros_a_bordo[0]  # Assume 1 passageiro

                if veiculo.local == pedido.destino:
                    novo_estado = self.copiar_estado()
                    v_novo = novo_estado.veiculos[i]

                    # Efeitos
                    v_novo.ocupado = False
                    v_novo.passageiros_a_bordo = []

                    # Custo: Tempo fixo de desembarque (ex: 2 min)
                    # NOTA: Não subtraímos valor! O custo só aumenta.
                    # O ganho é chegar ao estado objetivo.
                    tempo_desembarque = 2
                    custo_passo, custo_monetario, co2 = self.calcular_custo_acao(veiculo, 0, tempo_desembarque)

                    novo_estado.custo_acumulado += custo_passo
                    novo_estado.tempo_atual += tempo_desembarque
                    novo_estado.acao_geradora = f"[{v_novo.id}] Entregou passageiro em {v_novo.local}"

                    sucessores.append(novo_estado)

            # ===============================================================
            # AÇÃO 3: RECARREGAR / REABASTECER
            # Pré-condição: Estar numa estação/posto E não estar cheio
            # ===============================================================
            tipo_local = cidade.nodes[veiculo.local]['type']

            pode_recarregar = (veiculo.tipo == "eletrico" and tipo_local == "recarga")
            pode_abastecer = (veiculo.tipo == "combustao" and tipo_local == "combustivel")

            if (pode_recarregar or pode_abastecer) and veiculo.autonomia_atual < veiculo.autonomia_max:
                novo_estado = self.copiar_estado()
                v_novo = novo_estado.veiculos[i]

                # Efeitos
                energia_recuperada = veiculo.autonomia_max - veiculo.autonomia_atual
                v_novo.autonomia_atual = veiculo.autonomia_max

                # Custo: Tempo de recarga (ex: 1 min por cada 10km)
                tempo_recarga = math.ceil(energia_recuperada / 10)
                # Custo financeiro da energia (ex: 0.5€ fixo + energia)
                custo_energia = 0.5 + (energia_recuperada * 0.05)

                # Atualizar custo acumulado (aqui fazemos manual pois não é movimento)
                custo_ponderado = (ALPHA * custo_energia) + (BETA * tempo_recarga)

                novo_estado.custo_acumulado += custo_ponderado
                novo_estado.tempo_atual += tempo_recarga
                novo_estado.acao_geradora = f"[{v_novo.id}] Recarregou {energia_recuperada}km em {v_novo.local}"

                sucessores.append(novo_estado)

            # ===============================================================
            # AÇÃO 4: MOVER PARA LOCAL VIZINHO
            # Pré-condição: Ter autonomia suficiente para a aresta
            # ===============================================================
            vizinhos = cidade.get_neighbors(veiculo.local)

            for vizinho in vizinhos:
                # Obter dados da aresta no grafo
                # Nota: O teu cidade.py precisa garantir que isto retorna dados validos
                # Se usares o codigo anterior, graph[u][v] devolve dict {'dist': x, 'time': y}
                dados_aresta = cidade.graph[veiculo.local][vizinho]
                distancia = dados_aresta['dist']
                tempo_viagem = dados_aresta['time']

                # Só move se tiver autonomia
                if veiculo.autonomia_atual >= distancia:
                    # HEURÍSTICA DE PODA (Opcional mas recomendada):
                    # Se o carro está vazio, não o movas para longe dos pedidos pendentes
                    # Se o carro está ocupado, não o movas para longe do destino
                    # (Isto evita que o BFS/DFS explore movimentos estúpidos)

                    novo_estado = self.copiar_estado()
                    v_novo = novo_estado.veiculos[i]

                    # Efeitos
                    v_novo.local = vizinho
                    v_novo.autonomia_atual -= distancia

                    # Custo Multicritério
                    custo_passo, custo_monetario, co2 = self.calcular_custo_acao(veiculo, distancia, tempo_viagem)

                    novo_estado.custo_acumulado += custo_passo
                    novo_estado.tempo_atual += tempo_viagem

                    # Se tiver passageiro, o custo é mais alto? (Opcional)
                    # Pode-se adicionar penalidade extra por tempo com cliente a bordo

                    novo_estado.acao_geradora = f"[{v_novo.id}] Moveu: {veiculo.local} -> {vizinho}"

                    sucessores.append(novo_estado)

        return sucessores

    def copiar_estado(self):
        """Cria uma cópia profunda para garantir imutabilidade dos pais"""
        return copy.deepcopy(self)

    # --- MÉTODOS PARA O PYTHON GERIR O ESTADO EM SETS E FILAS ---
    def __lt__(self, other):
        # Necessário para a PriorityQueue do A* (desempate pelo custo)
        return self.custo_acumulado < other.custo_acumulado

    def __hash__(self):
        # Cria uma assinatura única do estado
        # Baseada na posição dos veículos, autonomia e lista de pedidos
        v_info = tuple((v.id, v.local, int(v.autonomia_atual), v.ocupado) for v in self.veiculos)
        p_info = tuple(p.id for p in self.pedidos_pendentes)
        return hash((v_info, p_info))

    def __eq__(self, other):
        return hash(self) == hash(other)
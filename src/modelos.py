class Pedido:
    def __init__(self, id_pedido, origem, destino, passageiros, prazo, tempo_criacao=0, prefere_eletrico=False):
        self.id = id_pedido
        self.origem = origem
        self.destino = destino
        self.passageiros = passageiros
        self.prazo = prazo
        self.prefere_eletrico = prefere_eletrico # [NOVO] Preferência do cliente

        # Estatísticas
        self.tempo_criacao = tempo_criacao
        self.tempo_conclusao = None

    def get_tempo_espera(self):
        if self.tempo_conclusao is None:
            return 0
        return self.tempo_conclusao - self.tempo_criacao

    def __repr__(self):
        tipo = "Eco" if self.prefere_eletrico else "Norm"
        return f"P{self.id}[{tipo}]"


class Veiculo:
    def __init__(self, id_v, tipo, local, autonomia, cap_passageiros):
        self.id = id_v
        self.tipo = tipo
        self.local = local
        self.autonomia_atual = autonomia
        self.autonomia_max = autonomia
        self.capacidade = cap_passageiros
        self.ocupado = False
        self.passageiros_a_bordo = []

        # Memória para o Simulador
        self.rota_planeada = []
        self.ocupado_ate = 0

    def clone(self):
        v_novo = Veiculo(self.id, self.tipo, self.local, self.autonomia_max, self.capacidade)
        v_novo.autonomia_atual = self.autonomia_atual
        v_novo.ocupado = self.ocupado
        v_novo.passageiros_a_bordo = list(self.passageiros_a_bordo)
        return v_novo

    def __repr__(self):
        return f"T{self.id}[{self.tipo}|{self.local}|{self.autonomia_atual:.0f}km]"
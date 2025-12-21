class Pedido:
    def __init__(self, id_pedido, origem, destino, passageiros, prazo, tempo_criacao=0):
        self.id = id_pedido
        self.origem = origem
        self.destino = destino
        self.passageiros = passageiros
        self.prazo = prazo

        # --- NOVOS CAMPOS PARA ESTATÍSTICAS ---
        self.tempo_criacao = tempo_criacao  # Minuto em que o pedido nasceu
        self.tempo_conclusao = None  # Minuto em que foi entregue (None se ainda não foi)

    def get_tempo_espera(self):
        """Calcula quanto tempo o cliente esperou até ser entregue."""
        if self.tempo_conclusao is None:
            return 0
        return self.tempo_conclusao - self.tempo_criacao

    def __repr__(self):
        return f"P{self.id}"


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

        # Memória para o Simulador (Cache de Rotas)
        self.rota_planeada = []
        self.ocupado_ate = 0

    def clone(self):
        """Cria uma cópia independente deste veículo."""
        v_novo = Veiculo(self.id, self.tipo, self.local, self.autonomia_max, self.capacidade)
        v_novo.autonomia_atual = self.autonomia_atual
        v_novo.ocupado = self.ocupado
        v_novo.passageiros_a_bordo = list(self.passageiros_a_bordo)
        return v_novo

    def __repr__(self):
        estado = "Ocupado" if self.ocupado else "Livre"
        return f"T{self.id}[{self.tipo}|{self.local}|{self.autonomia_atual:.0f}km]"
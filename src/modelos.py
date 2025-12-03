class Pedido:
    def __init__(self, id_pedido, origem, destino, passageiros, prazo):
        self.id = id_pedido
        self.origem = origem
        self.destino = destino
        self.passageiros = passageiros
        self.prazo = prazo
        
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

    def clone(self):
        """Cria uma cópia independente deste veículo (Substitui o deepcopy)"""
        # 1. Criar novo objeto com dados base
        v_novo = Veiculo(self.id, self.tipo, self.local, self.autonomia_max, self.capacidade)
        
        # 2. Copiar estado dinâmico
        v_novo.autonomia_atual = self.autonomia_atual
        v_novo.ocupado = self.ocupado
        
        # 3. Copiar lista de passageiros (cópia rasa da lista chega)
        v_novo.passageiros_a_bordo = list(self.passageiros_a_bordo)
        
        return v_novo

    def __repr__(self):
        estado = "Ocupado" if self.ocupado else "Livre"
        return f"T{self.id}[{self.tipo}|{self.local}|{self.autonomia_atual}km|{estado}]"
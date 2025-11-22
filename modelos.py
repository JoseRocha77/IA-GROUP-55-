import copy

class Pedido:
    def __init__(self, id_pedido, origem, destino, passageiros, prazo):
        self.id = id_pedido
        self.origem = origem
        self.destino = destino
        self.passageiros = passageiros
        self.prazo = prazo # Hora limite
        
    def __repr__(self):
        return f"Pedido({self.origem} -> {self.destino})"

class Veiculo:
    def __init__(self, id_v, tipo, local, autonomia, cap_passageiros):
        self.id = id_v
        self.tipo = tipo # "eletrico" ou "combustao" [cite: 11]
        self.local = local
        self.autonomia_atual = autonomia # km restantes
        self.autonomia_max = autonomia
        self.capacidade = cap_passageiros
        self.ocupado = False
        self.passageiros_a_bordo = [] # Lista de pedidos a bordo

    def __repr__(self):
        estado = "Ocupado" if self.ocupado else "Livre"
        return f"T{self.id}[{self.tipo}|{self.local}|{self.autonomia_atual}km|{estado}]"

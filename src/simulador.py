import time
import random
from modelos import Pedido
from problema import Estado
import algoritmos


class Simulador:
    def __init__(self, cidade, frota_inicial, algoritmo_escolhido=None):
        self.cidade = cidade
        self.frota = frota_inicial
        self.algoritmo = algoritmo_escolhido

        self.tempo_atual = 0
        self.pedidos_pendentes = []
        self.pedidos_ativos = []
        self.pedidos_concluidos = []
        self.id_counter = 100

        # Memória dos táxis
        for v in self.frota:
            v.rota_planeada = []
            v.ocupado_ate = 0

        # [NOVO] Fita de gravação para o Replay visual
        self.historico_estados = []

    def executar_simulacao(self, tempo_maximo, probabilidade_pedido=0.3):
        print(f"INICIAR SIMULAÇÃO ({tempo_maximo} min)...")

        # Gravar estado inicial (Minuto 0)
        self._gravar_snapshot()

        while self.tempo_atual < tempo_maximo:
            self.tempo_atual += 1

            self._gerar_novos_eventos(probabilidade_pedido)
            self._atualizar_frota()

            if self._precisa_de_intervencao():
                self._atribuir_tarefas_com_ia()

            # [NOVO] A cada minuto, tiramos uma foto da frota para ver depois
            self._gravar_snapshot()

        print("\nFIM DA SIMULAÇÃO.")
        self._imprimir_estatisticas()

        # Retornamos a cassete para o main.py poder passar no cinema
        return self.historico_estados

    def _gravar_snapshot(self):
        """Cria uma cópia segura do estado atual para visualização."""
        # Clonar veículos para garantir que guardamos a posição DESTE momento
        frota_copia = [v.clone() for v in self.frota]

        # Criar estado snapshot
        snapshot = Estado(frota_copia, list(self.pedidos_pendentes), self.tempo_atual)

        # Adicionar uma legenda para o gráfico
        snapshot.acao_geradora = f"Minuto {self.tempo_atual}"
        if len(self.pedidos_pendentes) > 0:
            snapshot.acao_geradora += f" | {len(self.pedidos_pendentes)} Pendentes"

        self.historico_estados.append(snapshot)

    def _gerar_novos_eventos(self, probabilidade):
        if random.random() < probabilidade:
            self.id_counter += 1
            origem = self.cidade.get_local_aleatorio()
            destino = self.cidade.get_local_aleatorio()

            while destino == origem:
                destino = self.cidade.get_local_aleatorio()

            novo_pedido = Pedido(
                self.id_counter,
                origem,
                destino,
                random.randint(1, 4),
                prazo=self.tempo_atual + 60,
                tempo_criacao=self.tempo_atual
            )

            self.pedidos_pendentes.append(novo_pedido)
            print(f"[{self.tempo_atual}m] 🆕 PEDIDO {novo_pedido} (Origem: {origem})")

    def _atualizar_frota(self):
        for i, v in enumerate(self.frota):
            if v.ocupado_ate > self.tempo_atual:
                continue

            if v.rota_planeada:
                proximo_estado = v.rota_planeada.pop(0)
                self._aplicar_transicao_veiculo(v, proximo_estado.veiculos[i], proximo_estado)

    def _precisa_de_intervencao(self):
        veiculos_sem_plano = [v for v in self.frota if not v.rota_planeada and v.ocupado_ate <= self.tempo_atual]
        return len(self.pedidos_pendentes) > 0 and len(veiculos_sem_plano) > 0

    def _atribuir_tarefas_com_ia(self):
        estado_atual = Estado(self.frota, self.pedidos_pendentes, tempo_atual=self.tempo_atual)

        # Usa o algoritmo escolhido no __init__
        if self.algoritmo is None:
            resultado = algoritmos.greedy(estado_atual, self.cidade, algoritmos.heuristica_taxi)
        elif self.algoritmo in [algoritmos.bfs, algoritmos.dfs]:
            resultado = self.algoritmo(estado_atual, self.cidade)
        else:
            resultado = self.algoritmo(estado_atual, self.cidade, algoritmos.heuristica_taxi)

        if not resultado:
            return

        caminho_completo, _ = resultado

        # Limpar planos antigos
        for v in self.frota:
            v.rota_planeada = []

        # Guardar novo plano
        for k in range(1, len(caminho_completo)):
            estado_futuro = caminho_completo[k]
            for i, v_real in enumerate(self.frota):
                v_sim = estado_futuro.veiculos[i]
                v_anterior = caminho_completo[k - 1].veiculos[i]

                if str(v_sim) != str(v_anterior) or (
                        v_real.rota_planeada and v_real.rota_planeada[-1] != estado_futuro):
                    v_real.rota_planeada.append(estado_futuro)

        print(
            f"[{self.tempo_atual}m] 🧠 IA redefiniu rotas (T1: {len(self.frota[0].rota_planeada)} passos, T2: {len(self.frota[1].rota_planeada)} passos)")

    def _aplicar_transicao_veiculo(self, v_real, v_simulado, estado_novo):
        duracao = max(1, int(estado_novo.tempo_atual - self.tempo_atual))
        v_real.ocupado_ate = self.tempo_atual + duracao

        v_real.local = v_simulado.local
        v_real.autonomia_atual = v_simulado.autonomia_atual

        # PICKUP
        if v_simulado.passageiros_a_bordo and not v_real.passageiros_a_bordo:
            pedido_sim = v_simulado.passageiros_a_bordo[0]
            pedido_real = next((p for p in self.pedidos_pendentes if p.id == pedido_sim.id), None)

            if pedido_real:
                v_real.ocupado = True
                v_real.passageiros_a_bordo.append(pedido_real)
                self.pedidos_pendentes.remove(pedido_real)
                self.pedidos_ativos.append(pedido_real)
                print(f"   -> 🚕 T{v_real.id} RECOLHEU {pedido_real}")

        # DROPOFF
        elif not v_simulado.passageiros_a_bordo and v_real.passageiros_a_bordo:
            pedido_real = v_real.passageiros_a_bordo[0]
            v_real.ocupado = False
            v_real.passageiros_a_bordo = []

            if pedido_real in self.pedidos_ativos:
                self.pedidos_ativos.remove(pedido_real)

            pedido_real.tempo_conclusao = self.tempo_atual
            self.pedidos_concluidos.append(pedido_real)

            print(f"   -> ✅ T{v_real.id} ENTREGOU {pedido_real} (Tempo Total: {pedido_real.get_tempo_espera()} min)")

        else:
            print(f"      T{v_real.id} moveu-se para {v_real.local}")

    def _imprimir_estatisticas(self):
        # (Mantém este método igual ao anterior, apenas certifica-te que está lá)
        # ... código das estatísticas ...
        total_pedidos = len(self.pedidos_concluidos) + len(self.pedidos_pendentes) + len(self.pedidos_ativos)
        if total_pedidos == 0:
            print("Nenhum pedido gerado.")
            return

        print("\n" + "=" * 50)
        print("📊 RELATÓRIO FINAL DA SIMULAÇÃO (TaxiGreen)")
        print("=" * 50)

        taxa_sucesso = (len(self.pedidos_concluidos) / total_pedidos) * 100
        print(f"⏱️  Tempo Simulado:     {self.tempo_atual} minutos")
        print(f"📦 Pedidos Totais:     {total_pedidos}")
        print(f"✅ Concluídos:         {len(self.pedidos_concluidos)} ({taxa_sucesso:.1f}%)")
        print(f"⏳ Pendentes/Ativos:   {len(self.pedidos_pendentes) + len(self.pedidos_ativos)}")

        if self.pedidos_concluidos:
            tempos = [p.get_tempo_espera() for p in self.pedidos_concluidos]
            medio = sum(tempos) / len(tempos)
            maximo = max(tempos)
            minimo = min(tempos)
            print("-" * 50)
            print(f"🕒 TEMPO DE RESPOSTA (Do pedido à entrega)")
            print(f"   - Média:   {medio:.1f} min")
            print(f"   - Mínimo:  {minimo} min")
            print(f"   - Máximo:  {maximo} min")

        print("-" * 50)
        print("🚗 FROTA E AMBIENTE")
        total_co2 = 0

        for v in self.frota:
            tipo_icon = "⚡" if v.tipo == "eletrico" else "⛽"
            co2_carro = 0
            if v.tipo == "combustao":
                km_andados = v.autonomia_max - v.autonomia_atual
                if km_andados > 0:
                    co2_carro = km_andados * 120

            total_co2 += co2_carro
            print(
                f"   > T{v.id} {tipo_icon} ({v.tipo}): {v.autonomia_atual:.0f}km bateria restante | CO2: {co2_carro:.0f}g")

        print("-" * 50)
        print(f"🌍 EMISSÕES TOTAIS: {total_co2 / 1000:.2f} kg CO2")
        print("=" * 50)
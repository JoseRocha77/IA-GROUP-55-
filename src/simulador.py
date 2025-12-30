import time
import random
from modelos import Pedido
from problema import Estado

# Importar constantes de custo do problema para manter consistência
from problema import CUSTO_KM_ELETRICO, CUSTO_KM_COMBUSTAO, CUSTO_MINUTO
import algoritmos


class Simulador:
    def __init__(self, cidade, frota_inicial, algoritmo_escolhido=None):
        self.cidade = cidade
        self.frota = frota_inicial
        self.algoritmo = algoritmo_escolhido

        self.tempo_atual = 0  # Minutos simulados
        self.pedidos_pendentes = []
        self.pedidos_ativos = []
        self.pedidos_concluidos = []
        self.id_counter = 100

        # Inicializar memória dos veículos
        for v in self.frota:
            v.rota_planeada = []
            v.ocupado_ate = 0

        # Estatísticas
        self.historico_estados = []
        self.total_dinheiro_gasto = 0.0
        self.tempo_cpu_total = 0.0

    def executar_simulacao(self, segundos_reais_limite, probabilidade_pedido=0.1):
        """
        Executa a simulação até que o tempo REAL (do relógio de parede) se esgote.
        """
        print(f"⏱️  INICIAR SIMULAÇÃO (Limite: {segundos_reais_limite} segundos reais)...")
        print("    (A tentar processar o máximo de minutos simulados possível...)")

        start_real_global = time.time()
        self._gravar_snapshot()

        # LOOP PRINCIPAL: Corre enquanto não passar o tempo limite
        while (time.time() - start_real_global) < segundos_reais_limite:
            self.tempo_atual += 1  # Avança 1 minuto no "mundo do jogo"

            self._gerar_novos_eventos(probabilidade_pedido)
            self._atualizar_frota()

            if self._precisa_de_intervencao():
                self._atribuir_tarefas_com_ia()

            self._gravar_snapshot()

        tempo_total_corrido = time.time() - start_real_global
        print(f"\n🛑 FIM DO TEMPO (Passaram {tempo_total_corrido:.2f}s).")

        self._imprimir_estatisticas(tempo_total_corrido)
        return self.historico_estados

    def _gravar_snapshot(self):
        """Guarda o estado atual para ver no gráfico depois."""
        frota_copia = [v.clone() for v in self.frota]
        snapshot = Estado(frota_copia, list(self.pedidos_pendentes), self.tempo_atual)

        # Guardar totais para o gráfico ler
        snapshot.total_dinheiro = self.total_dinheiro_gasto
        # O CO2 é calculado na hora, mas podíamos guardar aqui também

        snapshot.acao_geradora = f"Minuto Simulado: {self.tempo_atual}"
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
                self.id_counter, origem, destino,
                random.randint(1, 4),
                prazo=self.tempo_atual + 60,
                tempo_criacao=self.tempo_atual
            )
            self.pedidos_pendentes.append(novo_pedido)
            # print(f"[{self.tempo_atual}m] 🆕 PEDIDO {novo_pedido}")

    def _atualizar_frota(self):
        for i, v in enumerate(self.frota):
            # Custo fixo por minuto (salário/manutenção)
            self.total_dinheiro_gasto += CUSTO_MINUTO

            if v.ocupado_ate > self.tempo_atual:
                continue

            if v.rota_planeada:
                proximo_estado = v.rota_planeada.pop(0)
                self._aplicar_transicao_veiculo(v, proximo_estado.veiculos[i], proximo_estado)

    def _precisa_de_intervencao(self):
        veiculos_livres = [v for v in self.frota if not v.rota_planeada and v.ocupado_ate <= self.tempo_atual]
        return len(self.pedidos_pendentes) > 0 and len(veiculos_livres) > 0

    def _atribuir_tarefas_com_ia(self):
        estado_atual = Estado(self.frota, self.pedidos_pendentes, tempo_atual=self.tempo_atual)

        t_start = time.time()

        # Chama o algoritmo configurado
        if self.algoritmo is None:
            # Fallback para Greedy se nada for escolhido
            resultado = algoritmos.greedy(estado_atual, self.cidade, algoritmos.heuristica_taxi)
        elif self.algoritmo in [algoritmos.bfs, algoritmos.dfs]:
            # BFS/DFS não usam heurística nos argumentos
            resultado = self.algoritmo(estado_atual, self.cidade)
        else:
            # A* e Greedy usam heurística
            resultado = self.algoritmo(estado_atual, self.cidade, algoritmos.heuristica_taxi)

        t_end = time.time()
        self.tempo_cpu_total += (t_end - t_start)

        if not resultado:
            return

        caminho_completo, _ = resultado

        # Limpar rotas antigas
        for v in self.frota:
            v.rota_planeada = []

        # Atribuir novas rotas
        for k in range(1, len(caminho_completo)):
            estado_futuro = caminho_completo[k]
            for i, v_real in enumerate(self.frota):
                v_sim = estado_futuro.veiculos[i]
                v_anterior = caminho_completo[k - 1].veiculos[i]

                # Se o carro mudou de estado ou local, adiciona ao plano
                if str(v_sim) != str(v_anterior) or (
                        v_real.rota_planeada and v_real.rota_planeada[-1] != estado_futuro):
                    v_real.rota_planeada.append(estado_futuro)

        # print(f"[{self.tempo_atual}m] 🧠 IA Recalculou (CPU: {t_end - t_start:.4f}s)")

    def _aplicar_transicao_veiculo(self, v_real, v_simulado, estado_novo):
        duracao = max(1, int(estado_novo.tempo_atual - self.tempo_atual))
        v_real.ocupado_ate = self.tempo_atual + duracao

        # Calcular custos baseados na diferença de autonomia
        diff_autonomia = v_real.autonomia_atual - v_simulado.autonomia_atual

        if diff_autonomia > 0:
            # Gastou combustível
            km = diff_autonomia
            preco = CUSTO_KM_ELETRICO if v_real.tipo == "eletrico" else CUSTO_KM_COMBUSTAO
            self.total_dinheiro_gasto += km * preco
        elif diff_autonomia < 0:
            # Carregou (recuperou autonomia)
            recuperado = abs(diff_autonomia)
            self.total_dinheiro_gasto += recuperado * 0.10  # Custo recarga

        # Atualizar estado físico
        v_real.local = v_simulado.local
        v_real.autonomia_atual = v_simulado.autonomia_atual

        # PICKUP (Recolha)
        if v_simulado.passageiros_a_bordo and not v_real.passageiros_a_bordo:
            pedido_sim = v_simulado.passageiros_a_bordo[0]
            # Encontrar o objeto pedido real correspondente
            pedido_real = next((p for p in self.pedidos_pendentes if p.id == pedido_sim.id), None)

            if pedido_real:
                v_real.ocupado = True
                v_real.passageiros_a_bordo.append(pedido_real)
                self.pedidos_pendentes.remove(pedido_real)
                self.pedidos_ativos.append(pedido_real)
                self.total_dinheiro_gasto += 0.50  # Taxa de recolha

        # DROPOFF (Entrega)
        elif not v_simulado.passageiros_a_bordo and v_real.passageiros_a_bordo:
            pedido_real = v_real.passageiros_a_bordo[0]
            v_real.ocupado = False
            v_real.passageiros_a_bordo = []

            if pedido_real in self.pedidos_ativos:
                self.pedidos_ativos.remove(pedido_real)

            pedido_real.tempo_conclusao = self.tempo_atual
            self.pedidos_concluidos.append(pedido_real)

    def _imprimir_estatisticas(self, tempo_real_execucao):
        total_pedidos = len(self.pedidos_concluidos) + len(self.pedidos_pendentes) + len(self.pedidos_ativos)
        if total_pedidos == 0:
            print("Nenhum pedido gerado.")
            return

        print("\n" + "=" * 50)
        print("📊 RELATÓRIO DE PERFORMANCE (Tempo Real)")
        print("=" * 50)

        # Métricas de Velocidade
        mins_por_segundo = self.tempo_atual / (tempo_real_execucao + 0.001)

        print(f"⏱️  Tempo Limite Definido:  ~{int(tempo_real_execucao)}s")
        print(f"🔄 Minutos Simulados:      {self.tempo_atual} min")
        print(f"🚀 Velocidade da IA:       {mins_por_segundo:.2f} min/segundo")
        print(f"🧠 Tempo Total CPU (IA):   {self.tempo_cpu_total:.4f} s")
        print("-" * 50)

        # Métricas Financeiras
        print(f"💵 Custo Total Operação:   {self.total_dinheiro_gasto:.2f} €")

        # Métricas de Serviço
        taxa = (len(self.pedidos_concluidos) / total_pedidos) * 100
        print(f"📦 Pedidos Gerados:        {total_pedidos}")
        print(f"✅ Pedidos Concluídos:     {len(self.pedidos_concluidos)} ({taxa:.1f}%)")

        if self.pedidos_concluidos:
            tempos = [p.get_tempo_espera() for p in self.pedidos_concluidos]
            print(f"🕒 Tempo Espera Médio:     {sum(tempos) / len(tempos):.1f} min")

        print("=" * 50)
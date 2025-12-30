import time
import random
import threading  # <--- IMPORTANTE: Importar a biblioteca de threads
from modelos import Pedido
from problema import Estado

# Importar constantes de custo
from problema import CUSTO_KM_ELETRICO, CUSTO_KM_COMBUSTAO, CUSTO_MINUTO
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

        for v in self.frota:
            v.rota_planeada = []
            v.ocupado_ate = 0

        self.historico_estados = []
        self.total_dinheiro_gasto = 0.0
        self.tempo_cpu_total = 0.0

    def executar_simulacao(self, segundos_reais_limite, probabilidade_pedido=0.1):
        print(f"⏱️  INICIAR SIMULAÇÃO (Limite: {segundos_reais_limite}s)...")
        print("    (A usar THREADS para controlar o tempo rigorosamente)")

        start_real_global = time.time()
        # Calculamos o momento exato em que a simulação TEM de acabar
        deadline = start_real_global + segundos_reais_limite

        self._gravar_snapshot()

        # O loop verifica se ainda temos tempo antes do deadline
        while time.time() < deadline:
            self.tempo_atual += 1

            self._gerar_novos_eventos(probabilidade_pedido)
            self._atualizar_frota()

            if self._precisa_de_intervencao():
                # Passamos o tempo restante para a função saber quanto tempo tem
                tempo_restante = deadline - time.time()
                # Só chama a IA se houver pelo menos 0.1s de tempo útil
                if tempo_restante > 0.1:
                    self._atribuir_tarefas_com_ia_threaded(tempo_restante)

            self._gravar_snapshot()

        tempo_total_corrido = time.time() - start_real_global
        print(f"\n🛑 FIM DO TEMPO (Passaram {tempo_total_corrido:.2f}s).")

        self._imprimir_estatisticas(tempo_total_corrido)
        return self.historico_estados

    def _gravar_snapshot(self):
        frota_copia = [v.clone() for v in self.frota]
        snapshot = Estado(frota_copia, list(self.pedidos_pendentes), self.tempo_atual)
        snapshot.total_dinheiro = self.total_dinheiro_gasto
        snapshot.acao_geradora = f"Min: {self.tempo_atual}"
        if len(self.pedidos_pendentes) > 0:
            snapshot.acao_geradora += f" | {len(self.pedidos_pendentes)} Pend"
        self.historico_estados.append(snapshot)

    def _gerar_novos_eventos(self, probabilidade):
        if random.random() < probabilidade:
            self.id_counter += 1
            o = self.cidade.get_local_aleatorio()
            d = self.cidade.get_local_aleatorio()
            while d == o: d = self.cidade.get_local_aleatorio()
            self.pedidos_pendentes.append(Pedido(self.id_counter, o, d, 1, self.tempo_atual + 60, self.tempo_atual))

    def _atualizar_frota(self):
        for i, v in enumerate(self.frota):
            self.total_dinheiro_gasto += CUSTO_MINUTO
            if v.ocupado_ate > self.tempo_atual: continue
            if v.rota_planeada:
                prox = v.rota_planeada.pop(0)
                self._aplicar_transicao_veiculo(v, prox.veiculos[i], prox)

    def _precisa_de_intervencao(self):
        livres = [v for v in self.frota if not v.rota_planeada and v.ocupado_ate <= self.tempo_atual]
        return len(self.pedidos_pendentes) > 0 and len(livres) > 0

    # --- LÓGICA DE THREADING ---
    def _atribuir_tarefas_com_ia_threaded(self, tempo_limite_thread):
        """
        Executa a IA numa thread separada.
        Se a thread demorar mais que 'tempo_limite_thread', o simulador avança sem esperar.
        """
        estado_atual = Estado(self.frota, self.pedidos_pendentes, tempo_atual=self.tempo_atual)

        # Recipiente para guardar o resultado (lista é mutável, funciona como ponteiro)
        resultado_container = [None]

        def target_ia():
            """Função interna que corre na Thread"""
            t0 = time.time()
            if self.algoritmo in [algoritmos.bfs, algoritmos.dfs]:
                res = self.algoritmo(estado_atual, self.cidade)
            else:
                res = self.algoritmo(estado_atual, self.cidade, algoritmos.heuristica_taxi)
            self.tempo_cpu_total += (time.time() - t0)
            resultado_container[0] = res

        # 1. Criar a Thread
        thread_ia = threading.Thread(target=target_ia)

        # 2. Iniciar a Thread (começa a processar em paralelo)
        thread_ia.start()

        # 3. Esperar pela Thread, mas SÓ até o tempo limite acabar
        # Se tempo_limite_thread for 2s e a IA demorar 10s, o join solta aos 2s.
        thread_ia.join(timeout=tempo_limite_thread)

        if thread_ia.is_alive():
            # Se a thread ainda está viva, significa que o tempo acabou!
            # Ignoramos o resultado desta vez para cumprir o prazo.
            return

        # Se chegou aqui, a IA terminou a tempo
        resultado = resultado_container[0]
        if not resultado: return

        caminho_completo, _ = resultado
        for v in self.frota: v.rota_planeada = []

        for k in range(1, len(caminho_completo)):
            est_futuro = caminho_completo[k]
            for i, v_real in enumerate(self.frota):
                v_sim = est_futuro.veiculos[i]
                v_ant = caminho_completo[k - 1].veiculos[i]
                if str(v_sim) != str(v_ant) or (v_real.rota_planeada and v_real.rota_planeada[-1] != est_futuro):
                    v_real.rota_planeada.append(est_futuro)

    def _aplicar_transicao_veiculo(self, v_real, v_sim, est_novo):
        duracao = max(1, int(est_novo.tempo_atual - self.tempo_atual))
        v_real.ocupado_ate = self.tempo_atual + duracao

        diff = v_real.autonomia_atual - v_sim.autonomia_atual
        if diff > 0:
            custo = diff * (CUSTO_KM_ELETRICO if v_real.tipo == "eletrico" else CUSTO_KM_COMBUSTAO)
            self.total_dinheiro_gasto += custo
        elif diff < 0:
            self.total_dinheiro_gasto += abs(diff) * 0.10

        v_real.local = v_sim.local
        v_real.autonomia_atual = v_sim.autonomia_atual

        if v_sim.passageiros_a_bordo and not v_real.passageiros_a_bordo:
            pid = v_sim.passageiros_a_bordo[0].id
            preal = next((p for p in self.pedidos_pendentes if p.id == pid), None)
            if preal:
                v_real.ocupado = True;
                v_real.passageiros_a_bordo.append(preal)
                self.pedidos_pendentes.remove(preal);
                self.pedidos_ativos.append(preal)
                self.total_dinheiro_gasto += 0.50
        elif not v_sim.passageiros_a_bordo and v_real.passageiros_a_bordo:
            preal = v_real.passageiros_a_bordo[0]
            v_real.ocupado = False;
            v_real.passageiros_a_bordo = []
            if preal in self.pedidos_ativos: self.pedidos_ativos.remove(preal)
            preal.tempo_conclusao = self.tempo_atual;
            self.pedidos_concluidos.append(preal)

    def _imprimir_estatisticas(self, tempo_real_execucao):
        total = len(self.pedidos_concluidos) + len(self.pedidos_pendentes) + len(self.pedidos_ativos)
        if total == 0: print("Sem dados."); return

        sim_speed = self.tempo_atual / (tempo_real_execucao + 0.001)
        print(f"📊 RESULTADOS (Threaded Benchmark)")
        print(f"⏱️  Tempo Decorrido:    {tempo_real_execucao:.2f}s")
        print(f"⚡ Minutos Simulados:  {self.tempo_atual} min")
        print(f"🚀 Velocidade:         {sim_speed:.1f} min/s")
        print(f"💵 Custo Total:        {self.total_dinheiro_gasto:.2f} €")
        print(f"📦 Pedidos: {total} | Concluídos: {len(self.pedidos_concluidos)}")
        if self.pedidos_concluidos:
            tempos = [p.get_tempo_espera() for p in self.pedidos_concluidos]
            print(f"🕒 Tempo Espera Médio: {sum(tempos) / len(tempos):.1f} min")
        print("=" * 50)
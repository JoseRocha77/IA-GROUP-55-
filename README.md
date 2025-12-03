# 🚖 TaxiGreen - Otimização de Frota com IA

Este projeto implementa agentes inteligentes para a gestão de uma frota mista de táxis (elétricos e combustão) na cidade de **Braga**. O sistema utiliza dados reais do **OpenStreetMap (OSMnx)** e algoritmos de procura para otimizar recolhas, entregas e carregamentos.

## 📋 Funcionalidades

* **Mapa Real:** Centro de Braga (Raio 1km), com limpeza automática de ruas isoladas.
* **Algoritmos:**
    * **A* (A-Star):** Otimizado com heurística para encontrar o caminho mais barato/rápido.
    * **Greedy:** Procura gulosa (rápida, mas nem sempre ótima).
    * **BFS / DFS:** Algoritmos de procura cega (para comparação).
* **Simulação:**
    * Gestão de bateria/combustível.
    * Passageiros com Origem e Destino reais.
    * Recarregamento automático quando a autonomia é crítica.
* **Visualização:** Animação em tempo real com matplotlib.

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
Certifica-te que tens o **Python 3.9+** instalado.

### 2. Configurar o Ambiente Virtual (Recomendado)
Para não misturar bibliotecas, cria um ambiente virtual (`venv`):

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install osmnx matplotlib networkx numpy scipy requests
cd src
python main.py

Na primeira execução: O programa vai descarregar o mapa de Braga. Isto pode demorar 10-20 segundos. Nas vezes seguintes é instantâneo (cache).

Guia da Interface

Ao iniciar, verás um menu no terminal:

    *Opção 1 (A):** A melhor escolha. Encontra a solução ótima e é rápido.

    Opção 2 (Greedy): Muito rápido, mas pode tomar decisões sub-ótimas.

    Opção 3/4 (BFS/DFS): Algoritmos de força bruta. Cuidado: Podem ser lentos em cenários complexos.

    Opção 6 (Novo Cenário): Gera uma nova situação aleatória (posições dos táxis e clientes).

🎨 Legenda da Simulação (Mapa)

    🟢 Bola Verde: Táxi Livre.

    🔴 Bola Vermelha: Táxi Ocupado (com cliente).

    🔵 Bola Ciano (Azul Claro): Táxi a Carregar/Abastecer.

    🟡 Bola Amarela: Táxi com Bateria Fraca (< 15km).

    ⭐ Estrela Amarela: Cliente à espera (Origem).

    ❌ X Roxo: Destino do cliente.
    
Estrutura do Projeto

    src/main.py: Ponto de entrada. Gere o menu e a animação visual.

    src/algoritmos.py: Implementação do A*, Greedy, BFS e DFS (com controlo de ciclos).

    src/problema.py: Definição do Estado, funções de transição e cálculo de custos.

    src/cidade_osm.py: Integração com o OpenStreetMap e limpeza do grafo.

    src/modelos.py: Classes básicas (Veiculo, Pedido).

⚠️ Resolução de Problemas Comuns

Erro AttributeError: module 'osmnx' ... Se tiveres este erro, é porque tens uma versão muito recente ou muito antiga do OSMnx. O código já tem uma correção automática para detetar a versão e usar a função correta (largest_component). Basta correr o main.py novamente.

Erro Git RPC failed ao fazer push Se o push falhar, corre este comando no terminal: git config --global http.postBuffer 524288000
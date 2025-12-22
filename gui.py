import pygame
import sys
from src.core.grafo import Grafo

# Configurações de Cores e Ecrã
LARGURA, ALTURA = 1200, 800
COR_FUNDO = (30, 30, 30)
COR_NOS = (80, 80, 80)
COR_ARESTAS = (50, 50, 50)
COR_VEICULO = (0, 255, 0)      # Verde
COR_TEXTO = (255, 255, 255)
COR_ROTA = (0, 200, 255)       # Azul Ciano (caminho futuro)
COR_PEDIDO = (255, 165, 0)     # Laranja (cliente à espera)

class Gui:
    def __init__(self, json_path):
        pygame.init()
        pygame.display.set_caption("TaxiGreen - Visualização Completa")
        self.screen = pygame.display.set_mode((LARGURA, ALTURA))
        self.font = pygame.font.SysFont("Arial", 12)
        self.clock = pygame.time.Clock()
        
        # Carregar grafo (necessário para converter IDs de nós em coordenadas)
        self.grafo = Grafo.carregar_json(json_path) if hasattr(Grafo, 'carregar_json') else Grafo()
        
        self.calcular_escala()
        self.running = True

    def calcular_escala(self):
        self.min_lat, self.max_lat = float('inf'), float('-inf')
        self.min_lon, self.max_lon = float('inf'), float('-inf')
        
        if not self.grafo.nos: return

        for no in self.grafo.nos.values():
            lon, lat = no.coords
            if lat < self.min_lat: self.min_lat = lat
            if lat > self.max_lat: self.max_lat = lat
            if lon < self.min_lon: self.min_lon = lon
            if lon > self.max_lon: self.max_lon = lon
        self.padding = 50

    def to_screen(self, item):
        """ Converte coordenadas (lon, lat) ou ID de nodo para (x, y) no ecrã """
        lon, lat = 0, 0
        
        # Se for string, assume que é ID do nodo e busca no grafo
        if isinstance(item, str):
            if item in self.grafo.nos:
                lon, lat = self.grafo.nos[item].coords
            else:
                return (0, 0) # Nodo não encontrado
        # Se for tuplo/lista, assume coordenadas diretas
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            lon, lat = item
        else:
            return (0,0)

        if self.max_lon == self.min_lon: return LARGURA//2, ALTURA//2
        
        norm_x = (lon - self.min_lon) / (self.max_lon - self.min_lon)
        norm_y = (lat - self.min_lat) / (self.max_lat - self.min_lat)
        
        sx = self.padding + norm_x * (LARGURA - 2 * self.padding)
        sy = (ALTURA - self.padding) - norm_y * (ALTURA - 2 * self.padding)
        return int(sx), int(sy)

    def processar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()

    def desenhar(self, dados):
        """
        Estrutura esperada de 'dados':
        {
            'tempo': "12:00",
            'veiculos': [{'pos': 'n1', 'rota': ['n2', 'n3'], 'bateria': 0.8}, ...],
            'pedidos': [{'pos': 'n10', 'id': 5}, ...]
        }
        """
        if not self.running: return
        self.processar_eventos()
        self.screen.fill(COR_FUNDO)

        # 1. Desenhar Mapa (Fundo estático)
        for id_origem, arestas in self.grafo.arestas.items():
            p1 = self.to_screen(id_origem)
            for id_dest in arestas:
                p2 = self.to_screen(id_dest)
                pygame.draw.line(self.screen, COR_ARESTAS, p1, p2, 1)
        
        for id_no in self.grafo.nos:
            pygame.draw.circle(self.screen, COR_NOS, self.to_screen(id_no), 2)

        # 2. Desenhar Pedidos (Clientes à espera) - Quadrados Laranja
        for p in dados.get('pedidos', []):
            pos = self.to_screen(p['pos'])
            # Desenha um quadrado centrado
            rect = pygame.Rect(pos[0]-4, pos[1]-4, 8, 8)
            pygame.draw.rect(self.screen, COR_PEDIDO, rect)

        # 3. Desenhar Veículos e Rotas
        for v in dados.get('veiculos', []):
            pos_atual = self.to_screen(v['pos'])

            # A. Desenhar Rota Futura (Linhas Azuis)
            rota = v.get('rota', [])
            if rota and len(rota) > 0:
                pontos_rota = [pos_atual] + [self.to_screen(node_id) for node_id in rota]
                if len(pontos_rota) > 1:
                    pygame.draw.lines(self.screen, COR_ROTA, False, pontos_rota, 2)

            # B. Desenhar Carro (Círculo Verde)
            pygame.draw.circle(self.screen, COR_VEICULO, pos_atual, 8)
            
            # C. Info Bateria
            bat_texto = f"{v['bateria']*100:.0f}%"
            txt = self.font.render(bat_texto, True, COR_TEXTO)
            self.screen.blit(txt, (pos_atual[0]+10, pos_atual[1]-10))

        # 4. Info Texto
        tempo = dados.get('tempo', "--:--")
        n_pedidos = len(dados.get('pedidos', []))
        info_str = f"Hora: {tempo} | Pedidos em espera: {n_pedidos}"
        info = self.font.render(info_str, True, COR_TEXTO)
        self.screen.blit(info, (10, 10))

        pygame.display.flip()
        self.clock.tick(60)
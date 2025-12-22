import pygame
import sys
from src.core.grafo import Grafo

# --- CONFIGURAÇÕES ---
LARGURA_MAPA = 1000
LARGURA_BARRA = 350
LARGURA_TOTAL = LARGURA_MAPA + LARGURA_BARRA
ALTURA = 800

# Cores Gerais
COR_FUNDO_MAPA = (30, 30, 30)
COR_FUNDO_BARRA = (50, 50, 60)
COR_ARESTAS = (60, 60, 60)
COR_NOS = (100, 100, 100)

# Cores Entidades
COR_VEICULO_LIVRE = (0, 255, 0)
COR_VEICULO_OCUPADO = (255, 50, 50)
COR_PEDIDO = (0, 200, 255)
COR_ROTA = (0, 200, 255)

# Cores UI
COR_TEXTO = (255, 255, 255)
COR_TEXTO_SECUNDARIO = (200, 200, 200)
COR_SEPARADOR = (100, 100, 120)
COR_BTN_ATIVO = (0, 180, 0)
COR_BTN_INATIVO = (80, 80, 80)
COR_BTN_ACAO = (0, 120, 200) # Azul para botões de ação

class Gui:
    def __init__(self, caminho_json):
        pygame.init()
        pygame.display.set_caption("TaxiGreen - Painel de Controlo")
        self.screen = pygame.display.set_mode((LARGURA_TOTAL, ALTURA))
        
        self.font_titulo = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_texto = pygame.font.SysFont("Consolas", 12)
        self.clock = pygame.time.Clock()
        
        self.grafo = Grafo.carregar_json(caminho_json)
        self.calcular_escala()
        self.running = True

        # Estados de Filtro
        self.filtros = {'veiculos': True, 'pedidos': True, 'transito': True, 'tempo': True}
        
        # --- DEFINIÇÃO DE BOTÕES ---
        x_base = LARGURA_MAPA + 20
        
        # Botões de Filtro (Topo)
        self.botoes_filtro = {
            'veiculos': pygame.Rect(x_base, 60, 140, 30),
            'pedidos': pygame.Rect(x_base + 150, 60, 140, 30),
            'transito': pygame.Rect(x_base, 100, 140, 30),
            'tempo': pygame.Rect(x_base + 150, 100, 140, 30)
        }

        # Botões de Ação (Fundo)
        y_acao = ALTURA - 80
        self.btn_novo_carro = pygame.Rect(x_base, y_acao, 140, 50)
        self.btn_novo_pedido = pygame.Rect(x_base + 150, y_acao, 140, 50)

        # Estado do Popup (None, 'carro', 'pedido')
        self.popup_ativo = None 
        
        # Botões do Popup (Calculados dinamicamente ao desenhar)
        self.rect_popup_random = None
        self.rect_popup_custom = None

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

    def to_screen(self, coords):
        lon, lat = coords
        if self.max_lon == self.min_lon: return LARGURA_MAPA//2, ALTURA//2
        norm_x = (lon - self.min_lon) / (self.max_lon - self.min_lon)
        norm_y = (lat - self.min_lat) / (self.max_lat - self.min_lat)
        sx = self.padding + norm_x * (LARGURA_MAPA - 2 * self.padding)
        sy = (ALTURA - self.padding) - norm_y * (ALTURA - 2 * self.padding)
        return int(sx), int(sy)

    def processar_eventos(self):
        """Retorna uma lista de ações para o main.py executar"""
        acoes = []
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clique Esquerdo
                    mx, my = event.pos
                    
                    # 1. Se o Popup estiver aberto, só processa cliques nele
                    if self.popup_ativo:
                        if self.rect_popup_random and self.rect_popup_random.collidepoint(mx, my):
                            acoes.append((f"add_{self.popup_ativo}", "random"))
                            self.popup_ativo = None # Fecha popup
                        elif self.rect_popup_custom and self.rect_popup_custom.collidepoint(mx, my):
                            acoes.append((f"add_{self.popup_ativo}", "custom"))
                            self.popup_ativo = None # Fecha popup
                        else:
                            # Clicar fora fecha o popup
                            self.popup_ativo = None
                        continue # Não processa outros botões

                    # 2. Botões de Filtro
                    for chave, rect in self.botoes_filtro.items():
                        if rect.collidepoint(mx, my):
                            self.filtros[chave] = not self.filtros[chave]

                    # 3. Botões de Ação (Fundo)
                    if self.btn_novo_carro.collidepoint(mx, my):
                        self.popup_ativo = 'carro'
                    elif self.btn_novo_pedido.collidepoint(mx, my):
                        self.popup_ativo = 'pedido'

        return acoes

    def desenhar_botao(self, rect, texto, cor_base, texto_cor=COR_TEXTO):
        mx, my = pygame.mouse.get_pos()
        cor = cor_base
        if rect.collidepoint(mx, my): # Hover
            cor = (min(cor[0]+30, 255), min(cor[1]+30, 255), min(cor[2]+30, 255))
        
        pygame.draw.rect(self.screen, cor, rect, border_radius=5)
        pygame.draw.rect(self.screen, (200,200,200), rect, 1, border_radius=5)
        
        surf = self.font_titulo.render(texto, True, texto_cor)
        rect_txt = surf.get_rect(center=rect.center)
        self.screen.blit(surf, rect_txt)

    def desenhar_popup(self):
        """Desenha uma janela sobreposta para escolher Aleatório vs Manual"""
        if not self.popup_ativo: return

        # Fundo semi-transparente
        s = pygame.Surface((LARGURA_TOTAL, ALTURA))
        s.set_alpha(128)
        s.fill((0,0,0))
        self.screen.blit(s, (0,0))

        # Janela do Popup
        w, h = 400, 200
        cx, cy = LARGURA_TOTAL//2 - w//2, ALTURA//2 - h//2
        rect_janela = pygame.Rect(cx, cy, w, h)
        pygame.draw.rect(self.screen, (70, 70, 80), rect_janela, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), rect_janela, 2, border_radius=10)

        # Título
        titulo = "Adicionar Veículo" if self.popup_ativo == 'carro' else "Adicionar Pedido"
        txt = self.font_titulo.render(titulo, True, COR_TEXTO)
        self.screen.blit(txt, (cx + 20, cy + 20))

        # Botões de Escolha
        self.rect_popup_random = pygame.Rect(cx + 50, cy + 80, 140, 60)
        self.rect_popup_custom = pygame.Rect(cx + 210, cy + 80, 140, 60)

        self.desenhar_botao(self.rect_popup_random, "ALEATÓRIO", (0, 150, 0))
        self.desenhar_botao(self.rect_popup_custom, "PERSONALIZADO", (200, 100, 0))
        
        # Dica
        dica = self.font_texto.render("(Personalizado abre o terminal)", True, COR_TEXTO_SECUNDARIO)
        self.screen.blit(dica, (cx + 120, cy + 160))

    def desenhar_barra_lateral(self, dados):
        # Fundo e Linha
        pygame.draw.rect(self.screen, COR_FUNDO_BARRA, (LARGURA_MAPA, 0, LARGURA_BARRA, ALTURA))
        pygame.draw.line(self.screen, COR_SEPARADOR, (LARGURA_MAPA, 0), (LARGURA_MAPA, ALTURA), 2)

        x = LARGURA_MAPA + 20
        y = 15
        
        # Cabeçalho e Filtros
        self.screen.blit(self.font_titulo.render("CONTROLO E FILTROS", True, COR_TEXTO), (x, y))
        
        nomes_filtro = {'veiculos': "CARROS", 'pedidos': "PEDIDOS", 'transito': "ROTAS", 'tempo': "TEMPO"}
        for k, r in self.botoes_filtro.items():
            cor = COR_BTN_ATIVO if self.filtros[k] else COR_BTN_INATIVO
            self.desenhar_botao(r, nomes_filtro[k], cor)

        y = 150
        pygame.draw.line(self.screen, COR_SEPARADOR, (x, y), (LARGURA_TOTAL-20, y), 1)
        y += 20

        # --- LISTAS (Ocupam o meio do ecrã) ---
        area_listas = ALTURA - 100 - y # Espaço disponível
        
        if self.filtros['tempo']:
            self.screen.blit(self.font_titulo.render(f"HORA: {dados.get('tempo')}", True, COR_TEXTO), (x, y))
            y += 30

        if self.filtros['veiculos']:
            self.screen.blit(self.font_titulo.render("FROTA", True, (0, 200, 255)), (x, y))
            y += 25
            for v in dados.get('veiculos', []):
                if y > ALTURA - 120: break
                cor = COR_VEICULO_OCUPADO if v['ocupado'] else COR_VEICULO_LIVRE
                self.screen.blit(self.font_texto.render(f"{v['id']} | {v['estado_texto']}", True, cor), (x, y))
                y += 15
                self.screen.blit(self.font_texto.render(f"   Bat: {v['bateria']*100:.0f}%", True, COR_TEXTO_SECUNDARIO), (x, y))
                y += 20

        if self.filtros['pedidos'] and y < ALTURA - 120:
            y += 10
            self.screen.blit(self.font_titulo.render(f"PEDIDOS ({len(dados.get('pedidos',[]))})", True, (255, 200, 0)), (x, y))
            y += 25
            for p in dados.get('pedidos', []):
                if y > ALTURA - 120: break
                self.screen.blit(self.font_texto.render(f"{p['id']}: {p['origem']}->{p['destino']}", True, COR_TEXTO), (x, y))
                y += 15

        # --- BOTÕES DE AÇÃO (Fundo fixo) ---
        self.desenhar_botao(self.btn_novo_carro, "+ CARRO", COR_BTN_ACAO)
        self.desenhar_botao(self.btn_novo_pedido, "+ PEDIDO", COR_BTN_ACAO)

    def desenhar(self, dados):
        if not self.running: return

        acoes = self.processar_eventos()
        
        self.screen.fill(COR_FUNDO_MAPA)
        
        # 1. Mapa e Entidades
        # (Mapa)
        for o, a in self.grafo.arestas.items():
            if o in self.grafo.nos:
                p1 = self.to_screen(self.grafo.nos[o].coords)
                for d in a:
                    if d in self.grafo.nos:
                        pygame.draw.line(self.screen, COR_ARESTAS, p1, self.to_screen(self.grafo.nos[d].coords), 1)
        
        # (Rotas)
        if self.filtros['transito']:
            for v in dados.get('veiculos', []):
                rota = v.get('rota', [])
                if len(rota) > 1:
                    pts = [self.to_screen(self.grafo.nos[n].coords) for n in rota if n in self.grafo.nos]
                    if len(pts) > 1: pygame.draw.lines(self.screen, COR_ROTA, False, pts, 3)

        # (Pedidos)
        if self.filtros['pedidos']:
            for p in dados.get('pedidos', []):
                if p['origem'] in self.grafo.nos:
                    pos = self.to_screen(self.grafo.nos[p['origem']].coords)
                    pygame.draw.circle(self.screen, COR_PEDIDO, pos, 6)
                    pygame.draw.circle(self.screen, (255,255,255), pos, 6, 1)

        # (Carros)
        if self.filtros['veiculos']:
            for v in dados.get('veiculos', []):
                if v['pos'] in self.grafo.nos:
                    pos = self.to_screen(self.grafo.nos[v['pos']].coords)
                    cor = COR_VEICULO_OCUPADO if v['ocupado'] else COR_VEICULO_LIVRE
                    pygame.draw.circle(self.screen, cor, pos, 8)

        # 2. Interface
        self.desenhar_barra_lateral(dados)
        self.desenhar_popup() # Desenha o popup por cima de tudo se estiver ativo

        pygame.display.flip()
        self.clock.tick(30)
        
        return acoes
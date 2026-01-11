import pygame
import sys
import math
from src.core.grafo import Grafo

# --- CONFIGURAÇÕES ---
LARGURA_MAPA = 1000
LARGURA_BARRA = 400
LARGURA_TOTAL = LARGURA_MAPA + LARGURA_BARRA
ALTURA = 800

# Cores Gerais
COR_FUNDO_MAPA = (30, 30, 30)
COR_FUNDO_BARRA = (50, 50, 60)
COR_ARESTAS = (60, 60, 60)
COR_NOS = (100, 100, 100)

# Cores Trânsito
COR_TRANSITO_NORMAL = (60, 60, 60)
COR_TRANSITO_MEDIO = (255, 200, 0)
COR_TRANSITO_ALTO = (255, 50, 50)

# Cores Tipos de Nós
COR_ESTACAO_ELETRICA = (0, 200, 255)
COR_POSTO_COMBUSTIVEL = (255, 140, 0)
COR_NOS_PADRAO = (100, 100, 100)

# Cores Veículos
COR_TAXI_LIVRE = (0, 255, 0)
COR_TAXI_OCUPADO = (255, 50, 50)
COR_TAXIXL_LIVRE = (100, 255, 100)
COR_TAXIXL_OCUPADO = (255, 100, 100)

# Cores Pedidos
COR_PEDIDO_NORMAL = (255, 255, 255)
COR_PEDIDO_PREMIUM = (255, 215, 0)
COR_PEDIDO_CRITICO = (255, 0, 0)
COR_PEDIDO_TAXIXL = (138, 43, 226)

# Cores Rotas
COR_ROTA_RECOLHA = (255, 0, 255)
COR_ROTA_ENTREGA = (0, 255, 127)

# Cores UI
COR_TEXTO = (255, 255, 255)
COR_TEXTO_SECUNDARIO = (200, 200, 200)
COR_SEPARADOR = (100, 100, 120)
COR_BTN_ATIVO = (0, 180, 0)
COR_BTN_INATIVO = (80, 80, 80)
COR_BTN_ACAO = (0, 120, 200)
COR_BTN_SELECIONAR = (100, 100, 150)
COR_BTN_ALGORITMO = (120, 0, 200)

class Gui:
    def __init__(self, caminho_json):
        pygame.init()
        pygame.display.set_caption("TaxiGreen - Sistema Multi-Capacidade")
        self.screen = pygame.display.set_mode((LARGURA_TOTAL, ALTURA))
        
        self.font_titulo = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_texto = pygame.font.SysFont("Consolas", 12)
        self.font_pequena = pygame.font.SysFont("Consolas", 10)
        self.clock = pygame.time.Clock()
        
        self.grafo = Grafo.carregar_json(caminho_json)
        self.calcular_escala()
        self.running = True

        # Variáveis de estado dos formulários
        self.input_carro_no = ""
        self.input_pedido_origem = ""
        self.input_pedido_destino = ""
        self.input_pedido_passageiros = "1"
        self.campo_focado = None
        
        self.input_tipo_carro = "taxi_eletrico"
        self.input_pedido_premium = False
        self.modo_selecao = None

        # Estados de Filtro
        self.filtros = {
            'veiculos': True,
            'pedidos': True,
            'rotas': True,
            'tempo': True,
            'transito': True
        }
        
        # Seletor de Algoritmo
        self.algoritmos_disponiveis = [
            "A* (Ótimo)",
            "Greedy (Rápido)",
            "Hill Climbing (Local)",
            "DFS (Profundidade)",
            "BFS (Largura)",
            "Uniforme (Custo)"
        ]
        self.algoritmo_selecionado = 0
        self.dropdown_algoritmo_aberto = False
        
        # Cache do mapa (otimização)
        self.cache_mapa_surface = None
        self.ultimo_estado_transito = None
        
        # Definição de botões
        x_base = LARGURA_MAPA + 20
        self.botoes_filtro = {
            'veiculos': pygame.Rect(x_base, 60, 140, 30),
            'pedidos': pygame.Rect(x_base + 150, 60, 140, 30),
            'rotas': pygame.Rect(x_base, 100, 140, 30),
            'tempo': pygame.Rect(x_base + 150, 100, 140, 30),
            'transito': pygame.Rect(x_base, 140, 290, 30)
        }
        
        self.btn_algoritmo = pygame.Rect(x_base, 180, 290, 35)

        y_acao = ALTURA - 80
        self.btn_novo_carro = pygame.Rect(x_base, y_acao, 140, 50)
        self.btn_novo_pedido = pygame.Rect(x_base + 150, y_acao, 140, 50)

        self.popup_ativo = None
        self.rect_popup_random = None
        self.rect_popup_custom = None
        
        self.ui_rects = {}

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

    def obter_no_sob_mouse(self, pos):
        mx, my = pos
        limite_dist = 15
        melhor_no = None
        menor_dist = float('inf')

        for nid, no in self.grafo.nos.items():
            nx, ny = self.to_screen(no.coords)
            dist = math.sqrt((mx - nx)**2 + (my - ny)**2)
            if dist < limite_dist and dist < menor_dist:
                menor_dist = dist
                melhor_no = nid
        return melhor_no

    def _gerar_cache_mapa(self):
        """Desenha o mapa estático numa superfície para reutilização"""
        self.cache_mapa_surface = pygame.Surface((LARGURA_MAPA, ALTURA))
        self.cache_mapa_surface.fill(COR_FUNDO_MAPA)
        
        for o, vizinhos in self.grafo.arestas.items():
            if o in self.grafo.nos:
                p1 = self.to_screen(self.grafo.nos[o].coords)

                for d, aresta in vizinhos.items():
                    if d in self.grafo.nos:
                        p2 = self.to_screen(self.grafo.nos[d].coords)
                        cor = COR_ARESTAS
                        espessura = 1

                        if self.filtros.get('transito'):
                            fator = getattr(aresta, 'fator_transito', 1.0)
                            if fator >= 2.0:
                                cor = COR_TRANSITO_ALTO
                                espessura = 2
                            elif fator > 1.3:
                                cor = COR_TRANSITO_MEDIO
                                espessura = 2
                            else:
                                cor = COR_TRANSITO_NORMAL
                                
                        pygame.draw.line(self.cache_mapa_surface, cor, p1, p2, espessura)
        
        for no_id, no in self.grafo.nos.items():
            pos = self.to_screen(no.coords)
            raio = 3
            
            if no.tipo == "estacao_recarga":
                cor_no = COR_ESTACAO_ELETRICA
            elif no.tipo == "posto_abastecimento":
                cor_no = COR_POSTO_COMBUSTIVEL
            else:
                cor_no = COR_NOS_PADRAO
            
            pygame.draw.circle(self.cache_mapa_surface, cor_no, pos, raio)

    def processar_eventos(self):
        acoes = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit(); sys.exit()
            
            # Input de texto
            if event.type == pygame.KEYDOWN and self.campo_focado:
                texto_atual = ""
                if self.campo_focado == 'carro_no':
                    texto_atual = self.input_carro_no
                elif self.campo_focado == 'pedido_origem':
                    texto_atual = self.input_pedido_origem
                elif self.campo_focado == 'pedido_destino':
                    texto_atual = self.input_pedido_destino
                elif self.campo_focado == 'pedido_passageiros':
                    texto_atual = self.input_pedido_passageiros

                if event.key == pygame.K_BACKSPACE:
                    texto_atual = texto_atual[:-1]
                else:
                    if self.campo_focado == 'pedido_passageiros':
                        if event.unicode.isdigit() and len(texto_atual) < 1:
                            texto_atual += event.unicode
                    else:
                        if len(texto_atual) < 10 and event.unicode.isalnum():
                            texto_atual += event.unicode
                
                if self.campo_focado == 'carro_no':
                    self.input_carro_no = texto_atual
                elif self.campo_focado == 'pedido_origem':
                    self.input_pedido_origem = texto_atual
                elif self.campo_focado == 'pedido_destino':
                    self.input_pedido_destino = texto_atual
                elif self.campo_focado == 'pedido_passageiros':
                    self.input_pedido_passageiros = texto_atual
                
                return acoes

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    
                    # Dropdown de algoritmo
                    if self.dropdown_algoritmo_aberto:
                        y_dropdown = self.btn_algoritmo.bottom
                        for i, alg in enumerate(self.algoritmos_disponiveis):
                            rect_opcao = pygame.Rect(
                                self.btn_algoritmo.x,
                                y_dropdown + i * 30,
                                self.btn_algoritmo.width,
                                30
                            )
                            if rect_opcao.collidepoint(mx, my):
                                self.algoritmo_selecionado = i
                                acoes.append(("mudar_algoritmo", self.algoritmos_disponiveis[i]))
                                self.dropdown_algoritmo_aberto = False
                                return acoes
                        self.dropdown_algoritmo_aberto = False
                        return acoes
                    
                    if self.btn_algoritmo.collidepoint(mx, my):
                        self.dropdown_algoritmo_aberto = not self.dropdown_algoritmo_aberto
                        return acoes
                    
                    # Modo de seleção no mapa
                    if self.modo_selecao:
                        no_selecionado = self.obter_no_sob_mouse((mx, my))
                        if no_selecionado:
                            if self.modo_selecao == 'selecionar_carro':
                                self.input_carro_no = no_selecionado
                                self.popup_ativo = 'form_carro'
                            elif self.modo_selecao == 'selecionar_origem':
                                self.input_pedido_origem = no_selecionado
                                self.popup_ativo = 'form_pedido'
                            elif self.modo_selecao == 'selecionar_destino':
                                self.input_pedido_destino = no_selecionado
                                self.popup_ativo = 'form_pedido'
                            self.modo_selecao = None
                        continue

                    # Formulário carro
                    if self.popup_ativo == 'form_carro':
                        if self.ui_rects.get('input_carro_no', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.campo_focado = 'carro_no'
                        else:
                            self.campo_focado = None
                        
                        if self.ui_rects.get('btn_sel_carro', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.modo_selecao = 'selecionar_carro'
                            self.popup_ativo = None
                        
                        elif self.ui_rects.get('btn_taxi_eletrico', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.input_tipo_carro = "taxi_eletrico"
                        elif self.ui_rects.get('btn_taxi_combustao', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.input_tipo_carro = "taxi_combustao"
                        elif self.ui_rects.get('btn_taxixl_eletrica', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.input_tipo_carro = "taxixl_eletrica"
                        elif self.ui_rects.get('btn_taxixl_combustao', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.input_tipo_carro = "taxixl_combustao"
                        
                        elif self.ui_rects.get('btn_confirmar_carro', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            if self.input_carro_no:
                                acoes.append(("criar_carro_manual", {
                                    "tipo": self.input_tipo_carro,
                                    "no": self.input_carro_no
                                }))
                                self.popup_ativo = None
                        elif self.ui_rects.get('btn_cancelar', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.popup_ativo = None
                        continue

                    # Formulário pedido
                    if self.popup_ativo == 'form_pedido':
                        if self.ui_rects.get('input_origem', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.campo_focado = 'pedido_origem'
                        elif self.ui_rects.get('input_destino', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.campo_focado = 'pedido_destino'
                        elif self.ui_rects.get('input_passageiros', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.campo_focado = 'pedido_passageiros'
                        else:
                            self.campo_focado = None
                        
                        if self.ui_rects.get('checkbox_premium', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.input_pedido_premium = not self.input_pedido_premium
                        
                        if self.ui_rects.get('btn_sel_origem', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.modo_selecao = 'selecionar_origem'
                            self.popup_ativo = None
                        elif self.ui_rects.get('btn_sel_destino', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.modo_selecao = 'selecionar_destino'
                            self.popup_ativo = None
                        
                        elif self.ui_rects.get('btn_menos_pax', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            num = max(1, int(self.input_pedido_passageiros or 1) - 1)
                            self.input_pedido_passageiros = str(num)
                        elif self.ui_rects.get('btn_mais_pax', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            num = min(6, int(self.input_pedido_passageiros or 1) + 1)
                            self.input_pedido_passageiros = str(num)
                        
                        elif self.ui_rects.get('btn_confirmar_pedido', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            if self.input_pedido_origem and self.input_pedido_destino:
                                acoes.append(("criar_pedido_manual", {
                                    "origem": self.input_pedido_origem,
                                    "destino": self.input_pedido_destino,
                                    "num_passageiros": int(self.input_pedido_passageiros or 1),
                                    "premium": self.input_pedido_premium
                                }))
                                self.popup_ativo = None
                        elif self.ui_rects.get('btn_cancelar', pygame.Rect(0,0,0,0)).collidepoint(mx, my):
                            self.popup_ativo = None
                        continue

                    # Popup inicial
                    if self.popup_ativo in ['carro', 'pedido']:
                        if self.rect_popup_random and self.rect_popup_random.collidepoint(mx, my):
                            acoes.append((f"add_{self.popup_ativo}", "random"))
                            self.popup_ativo = None
                        elif self.rect_popup_custom and self.rect_popup_custom.collidepoint(mx, my):
                            if self.popup_ativo == 'carro':
                                self.popup_ativo = 'form_carro'
                                self.input_carro_no = ""
                            else:
                                self.popup_ativo = 'form_pedido'
                                self.input_pedido_origem = ""
                                self.input_pedido_destino = ""
                                self.input_pedido_passageiros = "1"
                                self.input_pedido_premium = False
                        else:
                            self.popup_ativo = None
                        continue

                    # Botões da interface
                    for chave, rect in self.botoes_filtro.items():
                        if rect.collidepoint(mx, my):
                            self.filtros[chave] = not self.filtros[chave]

                    if self.btn_novo_carro.collidepoint(mx, my):
                        self.popup_ativo = 'carro'
                    elif self.btn_novo_pedido.collidepoint(mx, my):
                        self.popup_ativo = 'pedido'

        return acoes

    def desenhar_botao(self, rect, texto, cor_base, texto_cor=COR_TEXTO, pequena_fonte=False):
        if not rect: return
        mx, my = pygame.mouse.get_pos()
        cor = cor_base
        if rect.collidepoint(mx, my):
            cor = (min(cor[0]+30, 255), min(cor[1]+30, 255), min(cor[2]+30, 255))
        
        pygame.draw.rect(self.screen, cor, rect, border_radius=5)
        pygame.draw.rect(self.screen, (200,200,200), rect, 1, border_radius=5)
        
        fonte = self.font_texto if pequena_fonte else self.font_titulo
        surf = fonte.render(texto, True, texto_cor)
        rect_txt = surf.get_rect(center=rect.center)
        self.screen.blit(surf, rect_txt)

    def desenhar_dropdown_algoritmo(self):
        """Desenha o dropdown de seleção de algoritmo"""
        if not self.dropdown_algoritmo_aberto:
            return
        
        y_dropdown = self.btn_algoritmo.bottom
        
        for i, alg in enumerate(self.algoritmos_disponiveis):
            rect_opcao = pygame.Rect(
                self.btn_algoritmo.x,
                y_dropdown + i * 30,
                self.btn_algoritmo.width,
                30
            )
            
            mx, my = pygame.mouse.get_pos()
            cor = (80, 80, 100) if rect_opcao.collidepoint(mx, my) else (60, 60, 70)
            
            pygame.draw.rect(self.screen, cor, rect_opcao)
            pygame.draw.rect(self.screen, (200, 200, 200), rect_opcao, 1)
            
            surf = self.font_texto.render(alg, True, COR_TEXTO)
            self.screen.blit(surf, (rect_opcao.x + 10, rect_opcao.y + 8))

    def desenhar_popup_inicial(self):
        if not self.popup_ativo or self.popup_ativo.startswith('form'): return
        self._desenhar_fundo_modal()
        w, h = 400, 200
        cx, cy = LARGURA_TOTAL//2 - w//2, ALTURA//2 - h//2
        rect_janela = pygame.Rect(cx, cy, w, h)
        self._desenhar_janela(rect_janela)
        titulo = "Adicionar Veículo" if self.popup_ativo == 'carro' else "Adicionar Pedido"
        self.screen.blit(self.font_titulo.render(titulo, True, COR_TEXTO), (cx + 20, cy + 20))
        self.rect_popup_random = pygame.Rect(cx + 50, cy + 80, 140, 60)
        self.rect_popup_custom = pygame.Rect(cx + 210, cy + 80, 140, 60)
        self.desenhar_botao(self.rect_popup_random, "ALEATÓRIO", (0, 150, 0))
        self.desenhar_botao(self.rect_popup_custom, "PERSONALIZADO", (200, 100, 0))
        
    def desenhar_form_carro(self):
        self._desenhar_fundo_modal()
        w, h = 420, 420
        cx, cy = LARGURA_TOTAL//2 - w//2, ALTURA//2 - h//2
        rect_janela = pygame.Rect(cx, cy, w, h)
        self._desenhar_janela(rect_janela)
        self.screen.blit(self.font_titulo.render("NOVO VEÍCULO", True, COR_TEXTO), (cx + 40, cy + 20))
        
        # Nó inicial
        self.screen.blit(self.font_texto.render("ID do Nó Inicial:", True, COR_TEXTO), (cx + 50, cy + 70))
        self.ui_rects['input_carro_no'] = pygame.Rect(cx + 50, cy + 90, 220, 35)
        self.ui_rects['btn_sel_carro'] = pygame.Rect(cx + 280, cy + 90, 90, 35)
        self._desenhar_input(self.ui_rects['input_carro_no'], self.input_carro_no, self.campo_focado == 'carro_no')
        self.desenhar_botao(self.ui_rects['btn_sel_carro'], "Mapa", COR_BTN_SELECIONAR, pequena_fonte=True)
        
        # 4 tipos de veículo
        self.screen.blit(self.font_titulo.render("TIPO DE VEÍCULO:", True, COR_TEXTO), (cx + 50, cy + 140))
        
        # Linha 1: TAXIs
        self.ui_rects['btn_taxi_eletrico'] = pygame.Rect(cx + 50, cy + 170, 160, 50)
        self.ui_rects['btn_taxi_combustao'] = pygame.Rect(cx + 220, cy + 170, 160, 50)
        
        cor_te = (0, 200, 100) if self.input_tipo_carro == "taxi_eletrico" else (60, 60, 60)
        cor_tc = (200, 100, 50) if self.input_tipo_carro == "taxi_combustao" else (60, 60, 60)
        
        self.desenhar_botao(self.ui_rects['btn_taxi_eletrico'], "TAXI Eletrico\n(4 pax)", cor_te, pequena_fonte=True)
        self.desenhar_botao(self.ui_rects['btn_taxi_combustao'], "TAXI Combustao\n(4 pax)", cor_tc, pequena_fonte=True)
        
        # Linha 2: TaxiXLs
        self.ui_rects['btn_taxixl_eletrica'] = pygame.Rect(cx + 50, cy + 230, 160, 50)
        self.ui_rects['btn_taxixl_combustao'] = pygame.Rect(cx + 220, cy + 230, 160, 50)
        
        cor_ve = (0, 180, 200) if self.input_tipo_carro == "taxixl_eletrica" else (60, 60, 60)
        cor_vc = (200, 120, 0) if self.input_tipo_carro == "taxixl_combustao" else (60, 60, 60)
        
        self.desenhar_botao(self.ui_rects['btn_taxixl_eletrica'], "TaxiXL Eletrica\n(6 pax)", cor_ve, pequena_fonte=True)
        self.desenhar_botao(self.ui_rects['btn_taxixl_combustao'], "TaxiXL Combustao\n(6 pax)", cor_vc, pequena_fonte=True)
        
        # Botões de ação
        self.ui_rects['btn_confirmar_carro'] = pygame.Rect(cx + 50, cy + 330, 160, 50)
        self.ui_rects['btn_cancelar'] = pygame.Rect(cx + 220, cy + 330, 160, 50)
        self.desenhar_botao(self.ui_rects['btn_confirmar_carro'], "CRIAR", COR_BTN_ACAO)
        self.desenhar_botao(self.ui_rects['btn_cancelar'], "CANCELAR", (100, 100, 100))

    def desenhar_form_pedido(self):
        self._desenhar_fundo_modal()
        w, h = 520, 480
        cx, cy = LARGURA_TOTAL//2 - w//2, ALTURA//2 - h//2
        rect_janela = pygame.Rect(cx, cy, w, h)
        self._desenhar_janela(rect_janela)
        self.screen.blit(self.font_titulo.render("NOVO PEDIDO", True, COR_TEXTO), (cx + 40, cy + 20))
        
        # Origem
        self.screen.blit(self.font_texto.render("Nó de Origem:", True, COR_TEXTO), (cx + 50, cy + 70))
        self.ui_rects['input_origem'] = pygame.Rect(cx + 50, cy + 90, 220, 35)
        self.ui_rects['btn_sel_origem'] = pygame.Rect(cx + 280, cy + 90, 90, 35)
        self._desenhar_input(self.ui_rects['input_origem'], self.input_pedido_origem, self.campo_focado == 'pedido_origem')
        self.desenhar_botao(self.ui_rects['btn_sel_origem'], "Mapa", COR_BTN_SELECIONAR, pequena_fonte=True)
        
        # Destino
        self.screen.blit(self.font_texto.render("Nó de Destino:", True, COR_TEXTO), (cx + 50, cy + 140))
        self.ui_rects['input_destino'] = pygame.Rect(cx + 50, cy + 160, 220, 35)
        self.ui_rects['btn_sel_destino'] = pygame.Rect(cx + 280, cy + 160, 90, 35)
        self._desenhar_input(self.ui_rects['input_destino'], self.input_pedido_destino, self.campo_focado == 'pedido_destino')
        self.desenhar_botao(self.ui_rects['btn_sel_destino'], "Mapa", COR_BTN_SELECIONAR, pequena_fonte=True)
        
        # Número de Passageiros
        self.screen.blit(self.font_texto.render("Passageiros:", True, COR_TEXTO), (cx + 50, cy + 210))
        
        self.ui_rects['btn_menos_pax'] = pygame.Rect(cx + 50, cy + 235, 40, 35)
        self.ui_rects['input_passageiros'] = pygame.Rect(cx + 100, cy + 235, 60, 35)
        self.ui_rects['btn_mais_pax'] = pygame.Rect(cx + 170, cy + 235, 40, 35)
        
        self.desenhar_botao(self.ui_rects['btn_menos_pax'], "-", (100, 100, 100), pequena_fonte=True)
        self._desenhar_input(self.ui_rects['input_passageiros'], self.input_pedido_passageiros, self.campo_focado == 'pedido_passageiros')
        self.desenhar_botao(self.ui_rects['btn_mais_pax'], "+", (100, 100, 100), pequena_fonte=True)
        
        # Info sobre TaxiXL
        num_pax = int(self.input_pedido_passageiros or 1)
        if num_pax > 4:
            info_text = "Requer TaxiXL (5-6 passageiros)"
            self.screen.blit(self.font_pequena.render(info_text, True, COR_PEDIDO_TAXIXL), (cx + 50, cy + 280))
        
        # Checkbox Premium
        self.ui_rects['checkbox_premium'] = pygame.Rect(cx + 50, cy + 315, 20, 20)
        cor_check = (255, 215, 0) if self.input_pedido_premium else (100, 100, 100)
        pygame.draw.rect(self.screen, cor_check, self.ui_rects['checkbox_premium'], border_radius=3)
        if self.input_pedido_premium:
            pygame.draw.line(self.screen, (0,0,0), (cx+52, cy+325), (cx+60, cy+332), 2)
            pygame.draw.line(self.screen, (0,0,0), (cx+60, cy+332), (cx+68, cy+318), 2)
        self.screen.blit(self.font_texto.render("Cliente Premium (30min)", True, COR_TEXTO), (cx + 80, cy + 315))
        
        # Botões de ação
        self.ui_rects['btn_confirmar_pedido'] = pygame.Rect(cx + 50, cy + 380, 160, 50)
        self.ui_rects['btn_cancelar'] = pygame.Rect(cx + 220, cy + 380, 160, 50)
        self.desenhar_botao(self.ui_rects['btn_confirmar_pedido'], "CRIAR", COR_BTN_ACAO)
        self.desenhar_botao(self.ui_rects['btn_cancelar'], "CANCELAR", (100, 100, 100))

        # Botões de ação
        self.ui_rects['btn_confirmar_pedido'] = pygame.Rect(cx + 50, cy + 380, 160, 50)
        self.ui_rects['btn_cancelar'] = pygame.Rect(cx + 220, cy + 380, 160, 50)
        self.desenhar_botao(self.ui_rects['btn_confirmar_pedido'], "CRIAR", COR_BTN_ACAO)
        self.desenhar_botao(self.ui_rects['btn_cancelar'], "CANCELAR", (100, 100, 100))

    def _desenhar_fundo_modal(self):
        s = pygame.Surface((LARGURA_TOTAL, ALTURA))
        s.set_alpha(180)
        s.fill((0,0,0))
        self.screen.blit(s, (0,0))

    def _desenhar_janela(self, rect):
        pygame.draw.rect(self.screen, (60, 60, 70), rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=10)

    def _desenhar_input(self, rect, texto, focado):
        cor_box = (255, 255, 255) if focado else (200, 200, 200)
        pygame.draw.rect(self.screen, cor_box, rect, border_radius=5)
        txt_surf = self.font_titulo.render(texto, True, (0,0,0))
        self.screen.blit(txt_surf, (rect.x + 5, rect.y + 5))

    def desenhar_barra_lateral(self, dados):
        pygame.draw.rect(self.screen, COR_FUNDO_BARRA, (LARGURA_MAPA, 0, LARGURA_BARRA, ALTURA))
        pygame.draw.line(self.screen, COR_SEPARADOR, (LARGURA_MAPA, 0), (LARGURA_MAPA, ALTURA), 2)

        x = LARGURA_MAPA + 20
        y = 15
        
        self.screen.blit(self.font_titulo.render("CONTROLO E FILTROS", True, COR_TEXTO), (x, y))
        
        nomes_filtro = {
            'veiculos': "CARROS", 'pedidos': "PEDIDOS", 'rotas': "ROTAS",
            'tempo': "TEMPO", 'transito': "VER TRANSITO"
        }
        for k, r in self.botoes_filtro.items():
            cor = COR_BTN_ATIVO if self.filtros[k] else COR_BTN_INATIVO
            self.desenhar_botao(r, nomes_filtro[k], cor)

        # Botão do Algoritmo
        texto_alg = self.algoritmos_disponiveis[self.algoritmo_selecionado]
        self.desenhar_botao(self.btn_algoritmo, f"Algoritmo: {texto_alg}", COR_BTN_ALGORITMO)
        
        # Seta do dropdown
        cx, cy = self.btn_algoritmo.right - 15, self.btn_algoritmo.centery
        seta = [(cx-5, cy-3), (cx+5, cy-3), (cx, cy+3)]
        pygame.draw.polygon(self.screen, (255,255,255), seta)
        
        y = 230
        pygame.draw.line(self.screen, COR_SEPARADOR, (x, y), (LARGURA_TOTAL-20, y), 1)
        y += 20

        # Tempo
        if self.filtros['tempo']:
            self.screen.blit(self.font_titulo.render(f"HORA: {dados.get('tempo')}", True, COR_TEXTO), (x, y))
            y += 30

        # Veículos Detalhados
        if self.filtros['veiculos']:
            self.screen.blit(self.font_titulo.render("VEICULOS", True, (0, 255, 127)), (x, y))
            y += 25
            for v in dados.get('veiculos', []):
                if y > ALTURA - 140: break
                
                categoria = v.get('categoria', 'TAXI')
                if categoria == 'TaxiXL':
                    cor = (138, 43, 226) if v['ocupado'] else (100, 255, 100)
                    icone = "TAXIXL"
                else:
                    cor = COR_TAXI_OCUPADO if v['ocupado'] else COR_TAXI_LIVRE
                    icone = "CAR"
                
                tipo_motor = "E" if v.get('tipo_str') == "eletrico" else "C"
                
                self.screen.blit(self.font_texto.render(
                    f"[{icone}][{tipo_motor}] {v['id']} | {v['estado_texto']}",
                    True, cor
                ), (x, y))
                y += 15
                
                cap = v.get('capacidade', 4)
                self.screen.blit(self.font_pequena.render(
                    f"   Cap: {cap} | Bat: {v['bateria']*100:.0f}%",
                    True, COR_TEXTO_SECUNDARIO
                ), (x, y))
                y += 20

        # Pedidos
        if self.filtros['pedidos'] and y < ALTURA - 120:
            y += 10
            self.screen.blit(self.font_titulo.render(
                f"PEDIDOS ({len(dados.get('pedidos',[]))})",
                True, (255, 200, 0)
            ), (x, y))
            y += 25
            
            for p in dados.get('pedidos', []):
                if y > ALTURA - 120: break
                
                prioridade = p.get('prioridade', 'NORMAL')
                if prioridade == 'CRITICO':
                    cor_prior = COR_PEDIDO_CRITICO
                    icone = "[!]"
                elif prioridade == 'PREMIUM':
                    cor_prior = COR_PEDIDO_PREMIUM
                    icone = "[*]"
                else:
                    cor_prior = COR_PEDIDO_NORMAL
                    icone = "[-]"
                
                num_pax = p.get('num_passageiros', 1)
                pax_info = f"{num_pax}pax"
                if num_pax > 4:
                    pax_info += " [XL]"
                    cor_prior = COR_PEDIDO_TAXIXL
                
                self.screen.blit(self.font_texto.render(
                    f"{icone} {p['id']}: {p['origem']}->{p['destino']} ({pax_info})",
                    True, cor_prior
                ), (x, y))
                y += 15
                
                if 'restante' in p:
                    self.screen.blit(self.font_pequena.render(
                        f"   Restam: {p['restante']}",
                        True, COR_TEXTO_SECUNDARIO
                    ), (x, y))
                    y += 15

        # Botões de Ação
        self.desenhar_botao(self.btn_novo_carro, "+ CARRO", COR_BTN_ACAO)
        self.desenhar_botao(self.btn_novo_pedido, "+ PEDIDO", COR_BTN_ACAO)

    def desenhar(self, dados):
        if not self.running: return []

        acoes = self.processar_eventos()
        
        # Desenhar o Mapa (com cache)
        estado_atual_transito = self.filtros.get('transito')
        
        if self.cache_mapa_surface is None or self.ultimo_estado_transito != estado_atual_transito:
            self._gerar_cache_mapa()
            self.ultimo_estado_transito = estado_atual_transito
            
        self.screen.blit(self.cache_mapa_surface, (0, 0))
        
        # Rotas
        if self.filtros['rotas']:
            for v in dados.get('veiculos', []):
                rota = v.get('rota', [])
                
                if len(rota) > 1:
                    pts = [self.to_screen(self.grafo.nos[n].coords) for n in rota if n in self.grafo.nos]
                    
                    if len(pts) > 1:
                        estado = v.get('estado_texto', '')
                        
                        if estado == "A_CAMINHO":
                            cor_atual = COR_ROTA_RECOLHA
                        elif estado == "EM_SERVICO":
                            cor_atual = COR_ROTA_ENTREGA
                        else:
                            cor_atual = (100, 100, 100)
                            
                        pygame.draw.lines(self.screen, cor_atual, False, pts, 3)

        # Pedidos
        if self.filtros['pedidos']:
            for p in dados.get('pedidos', []):
                if p['origem'] in self.grafo.nos:
                    pos = self.to_screen(self.grafo.nos[p['origem']].coords)
                    
                    prioridade = p.get('prioridade', 'NORMAL')
                    num_pax = p.get('num_passageiros', 1)
                    
                    if num_pax > 4:
                        cor = COR_PEDIDO_TAXIXL
                        raio = 9
                    elif prioridade == 'CRITICO':
                        cor = COR_PEDIDO_CRITICO
                        raio = 8
                    elif prioridade == 'PREMIUM':
                        cor = COR_PEDIDO_PREMIUM
                        raio = 7
                    else:
                        cor = COR_PEDIDO_NORMAL
                        raio = 6
                    
                    pygame.draw.circle(self.screen, cor, pos, raio)
                    pygame.draw.circle(self.screen, (255,255,255), pos, raio, 1)
                    
                    if num_pax > 1:
                        txt_pax = self.font_pequena.render(str(num_pax), True, (255, 255, 255))
                        self.screen.blit(txt_pax, (pos[0] + 12, pos[1] - 8))

        # Veículos
        if self.filtros['veiculos']:
            for v in dados.get('veiculos', []):
                if v['pos'] in self.grafo.nos:
                    pos = self.to_screen(self.grafo.nos[v['pos']].coords)
                    
                    categoria = v.get('categoria', 'TAXI')
                    if categoria == 'TaxiXL':
                        cor = COR_TAXIXL_OCUPADO if v['ocupado'] else COR_TAXIXL_LIVRE
                        raio = 10
                    else:
                        cor = COR_TAXI_OCUPADO if v['ocupado'] else COR_TAXI_LIVRE
                        raio = 8
                    
                    pygame.draw.circle(self.screen, cor, pos, raio)
                    
                    tipo_motor = v.get('tipo_str', 'combustao')
                    if tipo_motor == 'eletrico':
                        pygame.draw.circle(self.screen, (0, 200, 255), pos, raio//2)
        
        # Modo de Seleção
        if self.modo_selecao:
            texto_aviso = "SELECIONE UM PONTO NO MAPA"
            aviso_surf = self.font_titulo.render(texto_aviso, True, (255, 255, 0))
            self.screen.blit(aviso_surf, (LARGURA_MAPA // 2 - 100, 20))

        # Interface
        self.desenhar_barra_lateral(dados)
        
        # Popups e Formulários
        if self.popup_ativo == 'form_carro':
            self.desenhar_form_carro()
        elif self.popup_ativo == 'form_pedido':
            self.desenhar_form_pedido()
        else:
            self.desenhar_popup_inicial()

        # Dropdown por cima de tudo
        if self.dropdown_algoritmo_aberto:
            self.desenhar_dropdown_algoritmo()

        pygame.display.flip()
        self.clock.tick(30)
        
        return acoes
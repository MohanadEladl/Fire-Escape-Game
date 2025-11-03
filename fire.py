import pygame
import sys
import random
import time
import heapq
from collections import deque

WINDOW_WIDTH, WINDOW_HEIGHT = 900, 800
GRID_SIZE = 20
CELL_SIZE = 32
TOP_BAR = 80
PLAY_AREA_WIDTH = GRID_SIZE * CELL_SIZE
PLAY_AREA_HEIGHT = GRID_SIZE * CELL_SIZE
MARGIN_LEFT = (WINDOW_WIDTH - PLAY_AREA_WIDTH) // 2
MARGIN_TOP = TOP_BAR

FPS = 30
FIRE_SPREAD_INTERVAL = 1.2
FIRE_SPREAD_PROB = 0.22

AUTO_MOVE_DELAY = 0.20

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BRICK = (205, 92, 92)
GRAY = (180, 180, 180)
BLUE = (0, 0, 200)
GREEN = (0, 200, 0)
FIRE_COLOR = (255, 100, 0)
BUTTON_BG = (230, 230, 230)
BUTTON_BORDER = (100, 100, 100)
GOLD = (212, 175, 55)

PLAYER_IMG = "Player.png"
BACK_BTN_IMG = "BackButton.jpeg"
FIRE_IMG = "fire.png"

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

class EscapeTheFire:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Escape the Fire")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 42)

        self.player_img = self.load_and_scale(PLAYER_IMG, (CELL_SIZE, CELL_SIZE))
        self.back_img = self.load_and_scale(BACK_BTN_IMG, (36, 36))
        self.fire_img = self.load_and_scale(FIRE_IMG, (CELL_SIZE, CELL_SIZE))

        self.mode = "menu"
        self.reset_map()
        self.buttons = {}
        self.algo_start_time = None
        self.last_fire_spread = time.time()

    def load_and_scale(self, fname, size):
        try:
            img = pygame.image.load(fname).convert_alpha()
            return pygame.transform.scale(img, size)
        except Exception:
            return None

    def reset_map(self):
        self.player_pos = (0, 0)
        self.goal_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self.obstacles = set()
        self.fires = set()
        self.generate_solvable_map()
        self.initial_state = (self.player_pos, self.goal_pos, set(self.fires), set(self.obstacles))
        self.steps = 0
        self.start_time = None
        self.movement_started = False
        self.selected_solver = None
        self.auto_path = []
        self.auto_step_index = 0
        self.stats = {}
        self.algo_start_time = None
        self.last_fire_spread = time.time()
        self.auto_move_delay = AUTO_MOVE_DELAY
        self.last_auto_move_time = time.time() - self.auto_move_delay
        self.parents_cache = {}

    def generate_random_map(self):
        self.obstacles.clear()
        self.fires.clear()
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if (x, y) in [(0, 0), (GRID_SIZE - 1, GRID_SIZE - 1)]:
                    continue
                if random.random() < 0.18:
                    self.obstacles.add((x, y))
        for i in range(GRID_SIZE):
            if (i, i) in self.obstacles:
                self.obstacles.remove((i, i))
        for _ in range(int(GRID_SIZE * GRID_SIZE * 0.03)):
            rx = random.randrange(GRID_SIZE)
            ry = random.randrange(GRID_SIZE)
            if (rx, ry) not in self.obstacles and (rx, ry) not in [(0,0), self.goal_pos]:
                self.fires.add((rx, ry))

    def generate_solvable_map(self):
        attempts = 0
        while True:
            attempts += 1
            self.generate_random_map()
            if self.bfs_check_path_exists((0,0), self.goal_pos):
                return
            if attempts > 200:
                self.obstacles.clear()
                self.fires.clear()
                for i in range(GRID_SIZE):
                    if (i, i) in self.obstacles:
                        self.obstacles.remove((i, i))
                return

    def bfs_check_path_exists(self, start, goal):
        queue = deque([start])
        visited = {start}
        while queue:
            cur = queue.popleft()
            if cur == goal:
                return True
            for nx, ny in self.get_neighbors(cur):
                if (nx, ny) not in visited and (nx, ny) not in self.obstacles and (nx, ny) not in self.fires:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return False

    def draw_ui_top(self):
        pygame.draw.rect(self.screen, BUTTON_BG, (0, 0, WINDOW_WIDTH, TOP_BAR))
        title_surf = self.big_font.render("Escape the Fire", True, BLACK)
        self.screen.blit(title_surf, (20, 12))
        labels = ["A*", "Greedy", "BFS", "Restart", "Menu"]
        btn_w = 96
        btn_h = 34
        gap = 18
        start_x = 20
        y = 44
        self.buttons = {}
        for i, label in enumerate(labels):
            bx = start_x + i * (btn_w + gap)
            rect = pygame.Rect(bx, y, btn_w, btn_h)
            pygame.draw.rect(self.screen, BUTTON_BG, rect, border_radius=6)
            pygame.draw.rect(self.screen, BUTTON_BORDER, rect, 2, border_radius=6)
            txt = self.font.render(label, True, BLACK)
            self.screen.blit(txt, (bx + 12, y + 8))
            self.buttons[label] = rect
        if self.selected_solver and self.selected_solver in self.buttons:
            r = self.buttons[self.selected_solver]
            pygame.draw.rect(self.screen, GOLD, r, 3, border_radius=6)

    def draw_grid(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                gx = MARGIN_LEFT + x * CELL_SIZE
                gy = MARGIN_TOP + y * CELL_SIZE
                rect = pygame.Rect(gx, gy, CELL_SIZE, CELL_SIZE)
                color = WHITE
                if (x, y) in self.obstacles:
                    color = BRICK
                pygame.draw.rect(self.screen, color, rect)
                if (x, y) in self.fires:
                    if self.fire_img:
                        self.screen.blit(self.fire_img, (gx, gy))
                    else:
                        pygame.draw.rect(self.screen, FIRE_COLOR, rect)
                if (x, y) == self.goal_pos:
                    pygame.draw.rect(self.screen, GREEN, rect.inflate(-6, -6))
                if (x, y) == self.player_pos:
                    if self.player_img:
                        self.screen.blit(self.player_img, (gx, gy))
                    else:
                        pygame.draw.rect(self.screen, BLUE, rect.inflate(-6, -6))
                pygame.draw.rect(self.screen, BLACK, rect, 1)
        self.draw_path_arrows()

    def get_neighbors(self, pos):
        x, y = pos
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                yield (nx, ny)

    def bfs_search_with_parent(self, start):
        t0 = time.time()
        queue = deque([start])
        visited = {start}
        parent = {}
        nodes = 0
        while queue:
            nodes += 1
            cur = queue.popleft()
            if cur == self.goal_pos:
                length = 0
                p = cur
                while p in parent:
                    p = parent[p]
                    length += 1
                comp_time = time.time() - t0
                return nodes, True, length, parent, comp_time
            for nb in self.get_neighbors(cur):
                if nb not in visited and nb not in self.obstacles and nb not in self.fires:
                    visited.add(nb)
                    parent[nb] = cur
                    queue.append(nb)
        comp_time = time.time() - t0
        return nodes, False, 0, parent, comp_time

    def greedy_with_parent(self, start):
        t0 = time.time()
        pq = []
        heapq.heappush(pq, (manhattan(start, self.goal_pos), start))
        visited = {start}
        parent = {}
        nodes = 0
        while pq:
            nodes += 1
            _, cur = heapq.heappop(pq)
            if cur == self.goal_pos:
                length = 0
                p = cur
                while p in parent:
                    p = parent[p]
                    length += 1
                comp_time = time.time() - t0
                return nodes, True, length, parent, comp_time
            for nb in self.get_neighbors(cur):
                if nb not in visited and nb not in self.obstacles and nb not in self.fires:
                    visited.add(nb)
                    parent[nb] = cur
                    heapq.heappush(pq, (manhattan(nb, self.goal_pos), nb))
        comp_time = time.time() - t0
        return nodes, False, 0, parent, comp_time

    def a_star_with_parent(self, start):
        start_time = time.time()
        open_set = []
        g_score = {start: 0}
        heapq.heappush(open_set, (manhattan(start, self.goal_pos), start))
        parent = {}
        nodes = 0
        closed = set()
        while open_set:
            nodes += 1
            _, cur = heapq.heappop(open_set)
            if cur in closed:
                continue
            if cur == self.goal_pos:
                length = 0
                p = cur
                while p in parent:
                    p = parent[p]
                    length += 1
                comp_time = time.time() - start_time
                return nodes, True, length, parent, comp_time
            closed.add(cur)
            for nb in self.get_neighbors(cur):
                if nb in self.obstacles or nb in self.fires:
                    continue
                tentative_g = g_score[cur] + 1
                if nb not in g_score or tentative_g < g_score[nb]:
                    g_score[nb] = tentative_g
                    parent[nb] = cur
                    heapq.heappush(open_set, (tentative_g + manhattan(nb, self.goal_pos), nb))
        comp_time = time.time() - start_time
        return nodes, False, 0, parent, comp_time

    def reconstruct_path_from_parent(self, parent, start_override=None):
        cur = self.goal_pos
        path = []
        while cur in parent:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        if start_override and path and path[0] == start_override:
            path = path[1:]
        if path and path[0] == self.player_pos:
            path = path[1:]
        return path

    def start_solver(self, algo_name):
        self.pending_solver = algo_name
        self.start_movement(trigger="solver")

    def start_movement(self, trigger="manual"):
        if self.movement_started:
            return
        self.movement_started = True
        self.algo_start_time = time.time()
        s = self.player_pos
        a_nodes, a_succ, a_len, a_parent, a_time = self.a_star_with_parent(s)
        self.stats["A*"] = {"time": round(a_time, 3), "nodes_expanded": a_nodes, "path_length": a_len, "success": a_succ}
        self.parents_cache["A*"] = a_parent
        g_nodes, g_succ, g_len, g_parent, g_time = self.greedy_with_parent(s)
        self.stats["Greedy"] = {"time": round(g_time, 3), "nodes_expanded": g_nodes, "path_length": g_len, "success": g_succ}
        self.parents_cache["Greedy"] = g_parent
        b_nodes, b_succ, b_len, b_parent, b_time = self.bfs_search_with_parent(s)
        self.stats["BFS"] = {"time": round(b_time, 3), "nodes_expanded": b_nodes, "path_length": b_len, "success": b_succ}
        self.parents_cache["BFS"] = b_parent
        chosen = getattr(self, "pending_solver", None)
        if chosen:
            self.selected_solver = chosen
            parent = self.parents_cache.get(chosen, {})
            main_path = self.reconstruct_path_from_parent(parent, start_override=self.player_pos)
            if main_path:
                self.auto_path = main_path
                self.auto_step_index = 0
                self.last_auto_move_time = time.time() - self.auto_move_delay
            else:
                self.auto_path = []
                self.auto_step_index = 0
            delattr(self, "pending_solver")

    def spread_fire_step(self):
        new_fires = set(self.fires)
        for (fx, fy) in list(self.fires):
            for nx, ny in self.get_neighbors((fx, fy)):
                if (nx, ny) in self.obstacles or (nx, ny) in self.fires or (nx, ny) == self.player_pos or (nx, ny) == self.goal_pos:
                    continue
                if random.random() < FIRE_SPREAD_PROB:
                    new_fires.add((nx, ny))
        self.fires = new_fires

    def move_player(self, dx, dy):
        if not self.start_time:
            self.start_time = time.time()
        if not self.movement_started:
            self.start_movement(trigger="manual")
        x, y = self.player_pos
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and (nx, ny) not in self.obstacles:
            self.player_pos = (nx, ny)
            self.steps += 1
            if self.auto_path:
                self.auto_path = []
                self.auto_step_index = 0
                self.selected_solver = None

    def draw_path_arrows(self):
        if not self.auto_path or self.auto_step_index >= len(self.auto_path):
            return
        path_remaining = self.auto_path[self.auto_step_index:]
        prev = self.player_pos
        for idx, pos in enumerate(path_remaining):
            x, y = pos
            gx = MARGIN_LEFT + x * CELL_SIZE
            gy = MARGIN_TOP + y * CELL_SIZE
            rect = pygame.Rect(gx, gy, CELL_SIZE, CELL_SIZE)
            dx = pos[0] - prev[0]
            dy = pos[1] - prev[1]
            center = (gx + CELL_SIZE // 2, gy + CELL_SIZE // 2)
            size = CELL_SIZE // 3
            if (x, y) == self.player_pos:
                prev = pos
                continue
            if dx == 1 and dy == 0:
                points = [(center[0]-size, center[1]-size), (center[0]-size, center[1]+size), (center[0]+size, center[1])]
            elif dx == -1 and dy == 0:
                points = [(center[0]+size, center[1]-size), (center[0]+size, center[1]+size), (center[0]-size, center[1])]
            elif dx == 0 and dy == 1:
                points = [(center[0]-size, center[1]-size), (center[0]+size, center[1]-size), (center[0], center[1]+size)]
            else:
                points = [(center[0]-size, center[1]+size), (center[0]+size, center[1]+size), (center[0], center[1]-size)]
            pygame.draw.polygon(self.screen, BLACK, points)
            prev = pos

    def draw_end_game_comparison(self):
        dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))
        overlay_rect = pygame.Rect(40, 60, WINDOW_WIDTH - 80, WINDOW_HEIGHT - 160)
        pygame.draw.rect(self.screen, (250, 250, 250), overlay_rect, border_radius=10)
        pygame.draw.rect(self.screen, (40, 40, 40), overlay_rect, 2, border_radius=10)
        title = "End of Level - Comparison"
        title_surf = self.big_font.render(title, True, BLACK)
        self.screen.blit(title_surf, (overlay_rect.x + 20, overlay_rect.y + 12))
        lh = 36
        top_y = overlay_rect.y + 70
        start_x = overlay_rect.x + 60
        col_w = 240
        algos = ["A*", "Greedy", "BFS"]
        for i, algo in enumerate(algos):
            x = start_x + i * col_w
            self.screen.blit(self.font.render(algo, True, BLACK), (x, top_y))
            if algo in self.stats:
                s = self.stats[algo]
                row1 = f"Time: {s['time']}s    Nodes: {s['nodes_expanded']}"
                row2 = f"Path: {s['path_length']}    {'Success' if s['success'] else 'No Path'}"
                self.screen.blit(self.font.render(row1, True, BLACK), (x, top_y + lh))
                self.screen.blit(self.font.render(row2, True, BLACK), (x, top_y + 2 * lh))
            else:
                self.screen.blit(self.font.render("Not run", True, BLACK), (x, top_y + lh))
        manual_y = top_y + 4 * lh + 10
        mt1 = f"Manual Steps: {self.steps}"
        mt2 = f"Manual Time: {round((time.time() - (self.start_time or time.time())), 3)}s"
        t1s = self.font.render(mt1, True, BLUE)
        t2s = self.font.render(mt2, True, BLUE)
        cx = overlay_rect.centerx
        self.screen.blit(t1s, (cx - t1s.get_width() // 2, manual_y))
        self.screen.blit(t2s, (cx - t2s.get_width() // 2, manual_y + lh))
        failed = False
        fail_msg = ""
        if self.player_pos in self.fires:
            failed = True
            fail_msg = "You failed (stepped into fire)"
        else:
            alg_results = [self.stats.get(a, {}).get("success", None) for a in algos]
            if all(r is not None for r in alg_results) and not any(alg_results) and self.player_pos != self.goal_pos:
                failed = True
                fail_msg = "You failed (no solution found by algorithms)"
        if failed:
            fm = self.big_font.render(fail_msg, True, (200, 30, 30))
            self.screen.blit(fm, (overlay_rect.centerx - fm.get_width()//2, manual_y + 2*lh + 8))
        btn_w, btn_h = 140, 44
        bx = overlay_rect.centerx - btn_w - 12
        by = overlay_rect.bottom - 70
        rbtn = pygame.Rect(bx, by, btn_w, btn_h)
        mbtn = pygame.Rect(overlay_rect.centerx + 12, by, btn_w, btn_h)
        pygame.draw.rect(self.screen, BUTTON_BG, rbtn, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, rbtn, 2, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BG, mbtn, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, mbtn, 2, border_radius=8)
        self.screen.blit(self.font.render("Restart", True, BLACK), (rbtn.x + 34, rbtn.y + 12))
        self.screen.blit(self.font.render("Menu", True, BLACK), (mbtn.x + 50, mbtn.y + 12))
        return rbtn, mbtn

    def handle_menu(self):
        self.screen.fill(WHITE)
        title = self.big_font.render("Escape the Fire", True, BLACK)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 80))
        btn_w, btn_h = 220, 48
        spacing = 18
        start_y = 200
        buttons = [("Start Game", WINDOW_WIDTH//2 - btn_w//2, start_y),
                   ("Instructions", WINDOW_WIDTH//2 - btn_w//2, start_y + btn_h + spacing),
                   ("Quit", WINDOW_WIDTH//2 - btn_w//2, start_y + 2*(btn_h + spacing))]
        self.menu_buttons = {}
        for label, bx, by in buttons:
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            pygame.draw.rect(self.screen, BUTTON_BG, rect, border_radius=6)
            pygame.draw.rect(self.screen, BUTTON_BORDER, rect, 2, border_radius=6)
            txt = self.font.render(label, True, BLACK)
            self.screen.blit(txt, (bx + 16, by + 12))
            self.menu_buttons[label] = rect
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.menu_buttons["Start Game"].collidepoint(pos):
                    self.reset_map()
                    self.mode = "playing"
                    self.start_time = None
                elif self.menu_buttons["Instructions"].collidepoint(pos):
                    self.mode = "instructions"
                elif self.menu_buttons["Quit"].collidepoint(pos):
                    pygame.quit(); sys.exit()

    def handle_instructions(self):
        self.screen.fill(WHITE)
        title = self.big_font.render("Instructions", True, BLACK)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 40))
        ins = [
            "Use arrow keys to move.",
            "Use the A*, Greedy, or BFS buttons to auto-solve (auto-movement).",
            "When you choose a solver or start moving manually, all algorithms will start computing",
            "Fires spread every few seconds — avoid them.",
            "If you reach the goal you win. If you step into fire you fail.",
            "Use Back to return to the main menu."
        ]
        for i, line in enumerate(ins):
            t = self.font.render(line, True, BLACK)
            self.screen.blit(t, (80, 120 + i*36))
        bx, by = 40, WINDOW_HEIGHT - 80
        back_rect = pygame.Rect(bx, by, 140, 48)
        pygame.draw.rect(self.screen, BUTTON_BG, back_rect, border_radius=6)
        pygame.draw.rect(self.screen, BUTTON_BORDER, back_rect, 2, border_radius=6)
        if self.back_img:
            self.screen.blit(self.back_img, (bx + 8, by + 6))
            self.screen.blit(self.font.render("Back", True, BLACK), (bx + 52, by + 14))
        else:
            self.screen.blit(self.font.render("Back", True, BLACK), (bx + 16, by + 14))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    self.mode = "menu"

    def handle_playing(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for label, rect in self.buttons.items():
                    if rect.collidepoint((mx, my)):
                        if label in ("A*", "Greedy", "BFS"):
                            self.start_solver(label)
                        elif label == "Restart":
                            self.reset_map()
                            self.mode = "playing"
                        elif label == "Menu":
                            self.mode = "menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.move_player(0, -1)
                elif event.key == pygame.K_DOWN:
                    self.move_player(0, 1)
                elif event.key == pygame.K_LEFT:
                    self.move_player(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_player(1, 0)

        now = time.time()
        if now - self.last_fire_spread >= FIRE_SPREAD_INTERVAL:
            self.spread_fire_step()
            self.last_fire_spread = now

        if self.auto_path and self.selected_solver:
            if time.time() - self.last_auto_move_time >= self.auto_move_delay:
                if self.auto_step_index >= len(self.auto_path):
                    self.auto_path = []
                    self.auto_step_index = 0
                else:
                    next_pos = self.auto_path[self.auto_step_index]
                    if next_pos in self.obstacles or next_pos in self.fires:
                        if self.selected_solver == "A*":
                            n, succ, pl, parent, comp_time = self.a_star_with_parent(self.player_pos)
                            if "A*" not in self.stats:
                                self.stats["A*"] = {"time": 0.0, "nodes_expanded": 0, "path_length": 0, "success": False}
                            self.stats["A*"]["time"] = round(self.stats["A*"]["time"] + comp_time, 3)
                            self.stats["A*"]["nodes_expanded"] = self.stats["A*"]["nodes_expanded"] + n
                            self.stats["A*"]["path_length"] = pl
                            self.stats["A*"]["success"] = succ
                            if succ:
                                new_path = self.reconstruct_path_from_parent(parent, start_override=self.player_pos)
                                self.auto_path = new_path
                                self.auto_step_index = 0
                                self.last_auto_move_time = time.time() - self.auto_move_delay
                            else:
                                self.auto_path = []
                                self.auto_step_index = 0
                                self.selected_solver = None
                                self.stats["A*"]["success"] = False
                        else:
                            self.auto_path = []
                            self.auto_step_index = 0
                            if self.selected_solver not in self.stats:
                                self.stats[self.selected_solver] = {"time": 0.0, "nodes_expanded": 0, "path_length": 0, "success": False}
                            self.selected_solver = None
                    else:
                        if not self.start_time:
                            self.start_time = time.time()
                        self.player_pos = next_pos
                        self.auto_step_index += 1
                        self.last_auto_move_time = time.time()
                        self.steps += 1

        if self.player_pos == self.goal_pos or self.player_pos in self.fires:
            self.mode = "result"

        self.screen.fill(WHITE)
        self.draw_ui_top()
        self.draw_grid()
        hud = self.font.render(f"Steps: {self.steps}   Time: {round((time.time() - (self.start_time or time.time())), 3)}s", True, BLACK)
        self.screen.blit(hud, (WINDOW_WIDTH - hud.get_width() - 20, 12))
        pygame.display.flip()

    def handle_result(self):
        if "A*" not in self.stats or "Greedy" not in self.stats or "BFS" not in self.stats:
            s = self.player_pos
            n, succ, pl, _, comp = self.a_star_with_parent(s)
            self.stats["A*"] = {"time": round(comp, 3), "nodes_expanded": n, "path_length": pl, "success": succ}
            t0 = time.time()
            n, succ, pl, _, compg = self.greedy_with_parent(s)
            self.stats["Greedy"] = {"time": round(compg, 3), "nodes_expanded": n, "path_length": pl, "success": succ}
            t0 = time.time()
            n, succ, pl, _, compb = self.bfs_search_with_parent(s)
            self.stats["BFS"] = {"time": round(compb, 3), "nodes_expanded": n, "path_length": pl, "success": succ}

        self.screen.fill(WHITE)
        self.draw_ui_top()
        self.draw_grid()
        rbtn, mbtn = self.draw_end_game_comparison()
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if rbtn.collidepoint(event.pos):
                        self.reset_map()
                        self.mode = "playing"
                        waiting = False
                    elif mbtn.collidepoint(event.pos):
                        self.mode = "menu"
                        waiting = False
            self.clock.tick(FPS)

    def run(self):
        while True:
            if self.mode == "menu":
                self.handle_menu()
            elif self.mode == "instructions":
                self.handle_instructions()
            elif self.mode == "playing":
                self.handle_playing()
            elif self.mode == "result":
                self.handle_result()
            else:
                self.mode = "menu"
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = EscapeTheFire()
    game.run()
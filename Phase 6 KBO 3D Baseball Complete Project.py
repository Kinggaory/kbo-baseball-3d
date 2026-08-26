import sys
import math
import random
import json
import os

# Pygame & OpenGL Settings
import pygame
from pygame.locals import *

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("PyOpenGL 모듈을 찾을 수 없습니다. 'pip install PyOpenGL PyOpenGL_accelerate'를 실행하세요.")
    sys.exit(1)

# ==========================================
# 1. CONFIGURATION & CONSTANTS
# ==========================================
class Config:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 60
    TITLE = "KBO 3D Baseball - Mobile Phase 6 Final Edition"
    
    # Colors (RGB)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GOLD = (255, 215, 0)
    BLUE = (30, 144, 255)
    RED = (220, 20, 60)
    GREEN = (34, 139, 34)
    GRAY = (100, 100, 100)
    DARK_GRAY = (40, 40, 40)
    NAVY = (20, 30, 50)
    
    # Field Dimensions
    PITCHER_PLATE_Z = -18.44
    HOME_PLATE_Z = 0.0
    STRIKE_ZONE_WIDTH = 0.43
    STRIKE_ZONE_HEIGHT = 0.60
    STRIKE_ZONE_BOTTOM = 0.50
    STRIKE_ZONE_TOP = 1.10

# ==========================================
# 2. EXTENDED DYNAMIC DATABASE & ANIMATION PROFILES (Phase 6)
# ==========================================
# 모듈식 데이터: 현역 10개 구단 + 과거 해체/연고이전 구단 데이터 확장
DEFAULT_TEAMS_JSON = """
{
  "teams": [
    {"id": "KIA", "name": "KIA 타이거즈", "city": "광주", "color": [234, 0, 41], "retired_numbers": [18, 7], "history": "1982년 해태 타이거즈로 창단, KBO 최다 우승 구단"},
    {"id": "LG", "name": "LG 트윈스", "city": "서울", "color": [195, 0, 47], "retired_numbers": [9, 33, 41], "history": "1982년 MBC 청룡으로 시작, 1990년 LG 트윈스로 재창단"},
    {"id": "SSG", "name": "SSG 랜더스", "city": "인천", "color": [206, 14, 45], "retired_numbers": [], "history": "SK 와이번스를 인수하여 2021년 창단"},
    {"id": "NC", "name": "NC 다이노스", "city": "창원", "color": [9, 44, 84], "retired_numbers": [], "history": "2011년 KBO 9번째 구단으로 창단"},
    {"id": "DOOSAN", "name": "두산 베어스", "city": "서울", "color": [19, 23, 46], "retired_numbers": [21, 54], "history": "1982년 OB 베어스로 창단"},
    {"id": "KT", "name": "kt wiz", "city": "수원", "color": [0, 0, 0], "retired_numbers": [], "history": "2013년 KBO 10번째 구단으로 창단"},
    {"id": "LOTTE", "name": "롯데 자이언츠", "city": "부산", "color": [4, 30, 66], "retired_numbers": [11, 43], "history": "1982년 원년 구단으로 부산 연고지 유지"},
    {"id": "SAMSUNG", "name": "삼성 라이온즈", "city": "대구", "color": [7, 75, 153], "retired_numbers": [10, 22], "history": "1982년 원년 구단으로 대구 연고지 유지"},
    {"id": "HANWHA", "name": "한화 이글스", "city": "대전", "color": [243, 115, 33], "retired_numbers": [23, 35, 21, 52], "history": "1986년 빙그레 이글스로 창단"},
    {"id": "KIWOOM", "name": "키움 히어로즈", "city": "서울", "color": [87, 0, 19], "retired_numbers": [], "history": "2008년 우리 히어로즈로 창단"},
    {"id": "HAETAI", "name": "해태 타이거즈 (역대)", "city": "광주", "color": [180, 0, 0], "retired_numbers": [18, 7], "history": "1982~2001년 KBO 9회 우승의 전설적인 구단"},
    {"id": "PACIFIC", "name": "태평양 돌핀스 (해체)", "city": "인천", "color": [30, 80, 160], "retired_numbers": [], "history": "1988~1995년 인천 연고로 활동했던 과거 구단"}
  ]
}
"""

DEFAULT_CARDS_JSON = """
{
  "cards": [
    {
      "card_id": "C2026_01",
      "player_name": "김도영",
      "season": "2026",
      "original_team": "KIA",
      "position": "3B",
      "type": "NORMAL",
      "count": 4,
      "anim_profile": "LEG_KICK_BATTER",
      "stats": {"power": 88, "accuracy": 85, "running": 92, "plate_iq": 82, "defense": 78}
    },
    {
      "card_id": "C2026_02",
      "player_name": "김광현",
      "season": "2026",
      "original_team": "SSG",
      "position": "P",
      "type": "NORMAL",
      "count": 10,
      "anim_profile": "HIGH_THREE_QUARTER_PITCHER",
      "pitcher_stats": {"velocity": 147, "stuff": 82, "control": 78, "stamina": 85},
      "pitches": {"fastball": 0.50, "slider": 0.35, "changeup": 0.15}
    },
    {
      "card_id": "C1993_01",
      "player_name": "선동열",
      "season": "1993",
      "original_team": "HAETAI",
      "position": "P",
      "type": "NATIONAL",
      "count": 1,
      "anim_profile": "DYNAMIC_SLIDER_PITCHER",
      "pitcher_stats": {"velocity": 155, "stuff": 98, "control": 95, "stamina": 92},
      "pitches": {"fastball": 0.40, "slider": 0.50, "curveball": 0.10}
    }
  ]
}
"""

class DatabaseLoader:
    def __init__(self):
        self.teams_file = "database/teams.json"
        self.cards_file = "database/cards.json"
        self.teams_data = []
        self.cards_data = []
        self.load_all()

    def load_all(self):
        # 1. Teams Database Dynamic Loading
        if os.path.exists(self.teams_file):
            try:
                with open(self.teams_file, "r", encoding="utf-8") as f:
                    self.teams_data = json.load(f).get("teams", [])
            except Exception:
                self.teams_data = json.loads(DEFAULT_TEAMS_JSON)["teams"]
        else:
            self.teams_data = json.loads(DEFAULT_TEAMS_JSON)["teams"]

        # 2. Cards Database Dynamic Loading
        if os.path.exists(self.cards_file):
            try:
                with open(self.cards_file, "r", encoding="utf-8") as f:
                    self.cards_data = json.load(f).get("cards", [])
            except Exception:
                self.cards_data = json.loads(DEFAULT_CARDS_JSON)["cards"]
        else:
            self.cards_data = json.loads(DEFAULT_CARDS_JSON)["cards"]

class CardSystemManager:
    @staticmethod
    def calculate_effective_stats(card_data, user_team_id, total_special_cards_in_lineup, has_retired_number_boost):
        stats = card_data.get("stats", card_data.get("pitcher_stats", {})).copy()
        
        team_mismatch = card_data["original_team"] != user_team_id
        penalty_mismatch = -2 if team_mismatch else 0
        penalty_special = -1 if total_special_cards_in_lineup >= 4 else 0
        bonus_retired = +1 if has_retired_number_boost else 0
        
        net_modifier = penalty_mismatch + penalty_special + bonus_retired
        
        for k in stats.keys():
            stats[k] = max(1, stats[k] + net_modifier)
            
        return stats, net_modifier

    @staticmethod
    def combine_golden_glove(card, db_cards):
        if card["count"] >= 4 and card["type"] == "NORMAL":
            card["count"] -= 4
            new_card = card.copy()
            new_card["type"] = "GOLDEN_GLOVE"
            new_card["card_id"] += "_GG"
            new_card["count"] = 1
            if "stats" in new_card:
                for k in new_card["stats"]: new_card["stats"][k] += 5
            elif "pitcher_stats" in new_card:
                for k in new_card["pitcher_stats"]: new_card["pitcher_stats"][k] += 5
            db_cards.append(new_card)
            return True, "골든글러브 카드 조합 성공! (+5 능력치)"
        return False, "조합 조건 부족 (동일 카드 4장 필요)"

    @staticmethod
    def combine_national_team(card, db_cards):
        if card["count"] >= 10 and card["type"] == "NORMAL":
            card["count"] -= 10
            new_card = card.copy()
            new_card["type"] = "NATIONAL"
            new_card["card_id"] += "_NAT"
            new_card["count"] = 1
            if "stats" in new_card:
                for k in new_card["stats"]: new_card["stats"][k] += 6
            elif "pitcher_stats" in new_card:
                for k in new_card["pitcher_stats"]: new_card["pitcher_stats"][k] += 6
            db_cards.append(new_card)
            return True, "국가대표 카드 조합 성공! (+6 능력치)"
        return False, "조합 조건 부족 (동일 카드 10장 필요)"

# ==========================================
# 3. LEAGUE SIMULATION ENGINE
# ==========================================
class LeagueManager:
    def __init__(self, teams, user_team_id):
        self.teams = teams
        self.user_team_id = user_team_id
        self.total_games = 18
        self.current_game_index = 0
        self.standings = {t["id"]: {"wins": 0, "draws": 0, "losses": 0, "pts": 0} for t in teams}
        self.schedule = []
        self.generate_schedule()
        self.champion_reward_claimed = False

    def generate_schedule(self):
        team_ids = [t["id"] for t in self.teams]
        for i in range(self.total_games):
            home = team_ids[i % len(team_ids)]
            away = team_ids[(i + 1) % len(team_ids)]
            if home == away:
                away = team_ids[(i + 2) % len(team_ids)]
            self.schedule.append({"round": i + 1, "home": home, "away": away, "played": False, "score": None})

    def simulate_next_game(self, force_user_win=False):
        if self.current_game_index >= len(self.schedule):
            return None
            
        match = self.schedule[self.current_game_index]
        
        if force_user_win and (match["home"] == self.user_team_id or match["away"] == self.user_team_id):
            if match["home"] == self.user_team_id:
                home_score, away_score = random.randint(5, 10), random.randint(0, 4)
            else:
                home_score, away_score = random.randint(0, 4), random.randint(5, 10)
        else:
            home_score = random.randint(0, 9)
            away_score = random.randint(0, 9)
            
        match["score"] = f"{home_score}:{away_score}"
        match["played"] = True
        
        h_stat = self.standings[match["home"]]
        a_stat = self.standings[match["away"]]
        
        if home_score > away_score:
            h_stat["wins"] += 1; h_stat["pts"] += 3
            a_stat["losses"] += 1
        elif away_score > home_score:
            a_stat["wins"] += 1; a_stat["pts"] += 3
            h_stat["losses"] += 1
        else:
            h_stat["draws"] += 1; h_stat["pts"] += 1
            a_stat["draws"] += 1; a_stat["pts"] += 1
            
        self.current_game_index += 1
        return match

    def get_sorted_standings(self):
        result = []
        for t_id, stat in self.standings.items():
            total = stat["wins"] + stat["draws"] + stat["losses"]
            win_rate = stat["wins"] / total if total > 0 else 0.0
            team_name = next((t["name"] for t in self.teams if t["id"] == t_id), t_id)
            result.append({"id": t_id, "name": team_name, "wins": stat["wins"], "draws": stat["draws"], "losses": stat["losses"], "win_rate": win_rate})
        result.sort(key=lambda x: (x["win_rate"], x["wins"]), reverse=True)
        return result

    def get_user_rank(self):
        sorted_s = self.get_sorted_standings()
        for idx, t in enumerate(sorted_s):
            if t["id"] == self.user_team_id:
                return idx + 1
        return 10

# ==========================================
# 4. 3D OPENGL GRAPHICS ENGINE & ANIMATION PROFILES
# ==========================================
class StadiumRenderer:
    def __init__(self):
        self.quadric = gluNewQuadric()
        self.anim_time = 0.0

    def init_gl(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (width / height), 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 50.0, -10.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0))

    def render_field(self):
        # Turf Field
        glColor3f(0.13, 0.55, 0.13)
        glBegin(GL_QUADS)
        glVertex3f(-60.0, 0.0, -120.0)
        glVertex3f(60.0, 0.0, -120.0)
        glVertex3f(60.0, 0.0, 10.0)
        glVertex3f(-60.0, 0.0, 10.0)
        glEnd()
        
        # Dirt Diamond
        glColor3f(0.55, 0.35, 0.18)
        glBegin(GL_QUADS)
        glVertex3f(-15.0, 0.01, -30.0)
        glVertex3f(15.0, 0.01, -30.0)
        glVertex3f(15.0, 0.01, 2.0)
        glVertex3f(-15.0, 0.01, 2.0)
        glEnd()

        # Mound
        glPushMatrix()
        glTranslatef(0.0, 0.1, Config.PITCHER_PLATE_Z)
        glColor3f(0.6, 0.4, 0.2)
        gluSphere(self.quadric, 1.5, 16, 16)
        glPopMatrix()

        # Home Plate
        glPushMatrix()
        glTranslatef(0.0, 0.02, Config.HOME_PLATE_Z)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(-0.21, 0.0, 0.2)
        glVertex3f(-0.21, 0.0, 0.43)
        glVertex3f(0.21, 0.0, 0.43)
        glVertex3f(0.21, 0.0, 0.2)
        glEnd()
        glPopMatrix()

        # Outfield Fence
        glColor3f(0.05, 0.1, 0.3)
        glBegin(GL_QUAD_STRIP)
        for angle in range(-45, 46, 5):
            rad = math.radians(angle)
            x = 80.0 * math.sin(rad)
            z = -80.0 * math.cos(rad)
            glVertex3f(x, 0.0, z)
            glVertex3f(x, 4.0, z)
        glEnd()

    def render_runners(self, runners):
        base_positions = [(10.0, -10.0), (0.0, -20.0), (-10.0, -10.0)]
        for i, occupied in enumerate(runners):
            if occupied:
                bx, bz = base_positions[i]
                glPushMatrix()
                glTranslatef(bx, 0.5, bz)
                glColor3f(0.1, 0.8, 0.1)
                gluSphere(self.quadric, 0.3, 12, 12)
                glPopMatrix()

    def render_players_with_anim(self, dt, pitcher_profile="DEFAULT", batter_profile="DEFAULT"):
        self.anim_time += dt
        pitcher_sway = math.sin(self.anim_time * 3.0) * 0.05
        batter_leg_lift = abs(math.sin(self.anim_time * 4.0)) * 0.12 if batter_profile == "LEG_KICK_BATTER" else 0.0

        # Pitcher 3D Mesh
        glPushMatrix()
        glTranslatef(0.0, 0.9 + pitcher_sway, Config.PITCHER_PLATE_Z)
        glColor3f(0.8, 0.1, 0.1)
        gluSphere(self.quadric, 0.4, 16, 16)
        glTranslatef(0.0, -0.6, 0.0)
        glColor3f(0.1, 0.1, 0.8)
        gluCylinder(self.quadric, 0.3, 0.2, 0.8, 16, 16)
        glPopMatrix()

        # Batter 3D Mesh
        glPushMatrix()
        glTranslatef(0.8, 0.9 + batter_leg_lift, Config.HOME_PLATE_Z - 0.2)
        glColor3f(0.9, 0.8, 0.1)
        gluSphere(self.quadric, 0.35, 16, 16)
        glTranslatef(0.0, -0.6, 0.0)
        glColor3f(0.2, 0.2, 0.2)
        gluCylinder(self.quadric, 0.25, 0.2, 0.7, 16, 16)
        glPopMatrix()

    def render_strike_zone(self, target_x, target_y):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        half_w = Config.STRIKE_ZONE_WIDTH / 2.0
        z = Config.HOME_PLATE_Z
        
        glColor4f(1.0, 1.0, 1.0, 0.8)
        glLineWidth(3.0)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-half_w, Config.STRIKE_ZONE_BOTTOM, z)
        glVertex3f(half_w, Config.STRIKE_ZONE_BOTTOM, z)
        glVertex3f(half_w, Config.STRIKE_ZONE_TOP, z)
        glVertex3f(-half_w, Config.STRIKE_ZONE_TOP, z)
        glEnd()
        
        glColor4f(1.0, 0.0, 0.0, 0.9)
        glPointSize(10.0)
        glBegin(GL_POINTS)
        glVertex3f(target_x, target_y, z)
        glEnd()
        
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def render_ball(self, x, y, z):
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(1.0, 1.0, 0.9)
        gluSphere(self.quadric, 0.07, 12, 12)
        glPopMatrix()

# ==========================================
# 5. BALL PHYSICS & SIMULATION
# ==========================================
class BallPhysics:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = 0.0
        self.y = 1.2
        self.z = Config.PITCHER_PLATE_Z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.active = False
        self.in_flight = False
        self.hit_state = None

    def start_pitch(self, start_x, start_y, target_x, target_y, speed_kmh, pitch_type):
        self.x = start_x
        self.y = start_y
        self.z = Config.PITCHER_PLATE_Z
        
        speed_ms = speed_kmh / 3.6
        distance = abs(Config.HOME_PLATE_Z - Config.PITCHER_PLATE_Z)
        time_sec = distance / speed_ms
        
        self.vz = distance / time_sec
        self.vx = (target_x - start_x) / time_sec
        
        drop = 0.5 * 9.81 * (time_sec ** 2)
        if pitch_type == "slider": self.vx += 0.8
        elif pitch_type == "changeup": drop += 0.4
        elif pitch_type == "curveball": drop += 0.7; self.vx -= 0.3
            
        self.vy = (target_y - start_y + drop) / time_sec
        self.active = True
        self.in_flight = True
        self.hit_state = "PITCHING"

    def trigger_hit(self, quality, batter_power, stance_type="NORMAL"):
        self.hit_state = "HIT"
        angle_h = random.uniform(-0.6, 0.6)
        
        if stance_type == "BUNT":
            speed_ms = random.uniform(8.0, 15.0)
            angle_v = math.radians(random.uniform(2.0, 10.0))
        else:
            if quality == "PERFECT":
                speed_ms = (batter_power * 0.5) + 35.0
                angle_v = math.radians(28.0)
            elif quality == "GOOD":
                speed_ms = (batter_power * 0.4) + 28.0
                angle_v = math.radians(20.0)
            else:
                speed_ms = 20.0
                angle_v = math.radians(12.0)
            
        self.vx = speed_ms * math.sin(angle_h)
        self.vy = speed_ms * math.sin(angle_v)
        self.vz = -speed_ms * math.cos(angle_h) * math.cos(angle_v)

    def evaluate_defense_result(self):
        distance = math.sqrt(self.x**2 + self.z**2)
        if self.y < 1.0 and distance < 35.0:
            return "GROUNDER_OUT" if random.random() < 0.70 else "INFIELD_HIT"
        elif self.y >= 1.0 and distance < 65.0:
            return "FLY_OUT" if random.random() < 0.80 else "SINGLE_HIT"
        elif distance >= 65.0 and distance < 95.0:
            return "DOUBLE_HIT"
        elif distance >= 95.0:
            return "HOMERUN"
        return "SINGLE_HIT"

    def update(self, dt):
        if not self.active:
            return
            
        if self.hit_state == "PITCHING":
            self.x += self.vx * dt
            self.y += self.vy * dt - 0.5 * 9.81 * (dt ** 2)
            self.z += self.vz * dt
            if self.z >= Config.HOME_PLATE_Z + 0.5:
                self.in_flight = False
                
        elif self.hit_state == "HIT":
            self.x += self.vx * dt
            self.y += self.vy * dt - 0.5 * 9.81 * (dt ** 2)
            self.z += self.vz * dt
            
            if self.y <= 0.07:
                self.y = 0.07
                self.vy = -self.vy * 0.5
                self.vx *= 0.8
                self.vz *= 0.8
                
            if abs(self.z) > 120.0 or abs(self.x) > 80.0:
                self.in_flight = False

# ==========================================
# 6. MAIN GAME APPLICATION & SCENE CONTROL
# ==========================================
class MobileKBOBaseballApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption(Config.TITLE)
        
        self.db = DatabaseLoader()
        self.renderer = StadiumRenderer()
        self.renderer.init_gl(Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        self.physics = BallPhysics()
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.SysFont("malgungothic", 20) if pygame.font.matchfont("malgungothic") else pygame.font.Font(None, 24)
        self.title_font = pygame.font.SysFont("malgungothic", 36) if pygame.font.matchfont("malgungothic") else pygame.font.Font(None, 40)
        
        # User & League State
        self.user_team = self.db.teams_data[0]
        self.league_manager = LeagueManager(self.db.teams_data, self.user_team["id"])
        
        self.current_scene = "MAIN_MENU"
        self.reward_cards = []
        
        # Match State & Runners
        self.inning = 1
        self.is_top_inning = True
        self.home_score = 0
        self.away_score = 0
        self.strikes = 0
        self.balls = 0
        self.outs = 0
        self.runners = [False, False, False]
        
        self.batter_stance = "NORMAL"
        self.selected_pitch = "fastball"
        self.target_x = 0.0
        self.target_y = (Config.STRIKE_ZONE_BOTTOM + Config.STRIKE_ZONE_TOP) / 2.0
        self.match_state = "SELECT_PITCH"
        self.result_text = ""
        self.result_timer = 0

    def grant_league_champion_reward(self):
        self.reward_cards = []
        for i in range(10):
            card = {
                "card_id": f"REWARD_{i+1}",
                "player_name": f"{self.user_team['name']} 선수 {i+1}",
                "season": "2026",
                "original_team": self.user_team["id"],
                "position": random.choice(["P", "C", "1B", "2B", "3B", "SS", "OF"]),
                "type": "NORMAL",
                "count": 1,
                "stats": {"power": random.randint(70, 90), "accuracy": random.randint(70, 90), "running": random.randint(70, 90)}
            }
            self.db.cards_data.append(card)
            self.reward_cards.append(card)
        self.current_scene = "REWARD_PACK_OPEN"

    def handle_input(self, event):
        if event.type == MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            if self.current_scene == "MAIN_MENU":
                if 200 <= my <= 280:
                    if 80 <= mx <= 280: self.current_scene = "LEAGUE_MODE"
                    elif 310 <= mx <= 510: self.current_scene = "MATCH_PLAY"
                    elif 540 <= mx <= 740: self.current_scene = "LINEUP_VIEW"
                    elif 770 <= mx <= 970: self.current_scene = "COMBINE_VIEW"
                        
            elif self.current_scene == "LEAGUE_MODE":
                if my < 60 and mx < 150: self.current_scene = "MAIN_MENU"; return
                if 180 <= my <= 240 and 900 <= mx <= 1180:
                    m = self.league_manager.simulate_next_game()
                    self.result_text = f"결과: {m['home']} {m['score']} {m['away']}" if m else "정규시즌 종료"
                    self.result_timer = 120
                elif 260 <= my <= 320 and 900 <= mx <= 1180:
                    while self.league_manager.current_game_index < len(self.league_manager.schedule):
                        self.league_manager.simulate_next_game(force_user_win=True)
                    self.result_text = "시즌 최종 완료!"
                    self.result_timer = 120
                elif 340 <= my <= 400 and 900 <= mx <= 1180:
                    if self.league_manager.get_user_rank() == 1 and not self.league_manager.champion_reward_claimed:
                        self.league_manager.champion_reward_claimed = True
                        self.grant_league_champion_reward()

            elif self.current_scene == "REWARD_PACK_OPEN":
                if my > 600: self.current_scene = "MAIN_MENU"

            elif self.current_scene in ["LINEUP_VIEW", "COMBINE_VIEW"]:
                if my < 60 and mx < 150: self.current_scene = "MAIN_MENU"; return
                if self.current_scene == "COMBINE_VIEW":
                    if 150 <= my <= 210 and 800 <= mx <= 1000:
                        success, msg = CardSystemManager.combine_golden_glove(self.db.cards_data[0], self.db.cards_data)
                        self.result_text = msg; self.result_timer = 120
                    elif 250 <= my <= 310 and 800 <= mx <= 1000:
                        c = self.db.cards_data[1] if len(self.db.cards_data) > 1 else self.db.cards_data[0]
                        success, msg = CardSystemManager.combine_national_team(c, self.db.cards_data)
                        self.result_text = msg; self.result_timer = 120

            elif self.current_scene == "MATCH_PLAY":
                if my < 60 and mx < 150: self.current_scene = "MAIN_MENU"; return
                if self.match_state == "SELECT_PITCH":
                    if my > Config.SCREEN_HEIGHT - 80:
                        if mx < 200: self.selected_pitch = "fastball"
                        elif mx < 400: self.selected_pitch = "slider"
                        elif mx < 600: self.selected_pitch = "changeup"
                    elif my < Config.SCREEN_HEIGHT - 100:
                        norm_x = (mx / Config.SCREEN_WIDTH) * 2.0 - 1.0
                        norm_y = 1.0 - (my / Config.SCREEN_HEIGHT) * 2.0
                        self.target_x = norm_x * 0.6
                        self.target_y = Config.STRIKE_ZONE_BOTTOM + (norm_y + 0.5) * (Config.STRIKE_ZONE_TOP - Config.STRIKE_ZONE_BOTTOM)
                        self.physics.start_pitch(0.0, 1.2, self.target_x, self.target_y, 145.0, self.selected_pitch)
                        self.match_state = "PITCH_IN_FLIGHT"

                elif self.match_state == "PITCH_IN_FLIGHT":
                    if self.physics.hit_state == "PITCHING":
                        timing = abs(self.physics.z - Config.HOME_PLATE_Z)
                        quality = "PERFECT" if timing < 0.3 else "GOOD" if timing < 0.7 else "NORMAL" if timing < 1.2 else "MISS"
                        if quality != "MISS":
                            self.physics.trigger_hit(quality, 88, self.batter_stance)
                            outcome = self.physics.evaluate_defense_result()
                            self.process_fielding_outcome(outcome)
                        else:
                            self.strikes += 1; self.set_match_result("헛스윙 스트라이크!")

    def process_fielding_outcome(self, outcome):
        if outcome == "HOMERUN":
            runs = 1 + sum(self.runners)
            if self.is_top_inning: self.away_score += runs
            else: self.home_score += runs
            self.runners = [False, False, False]
            self.set_match_result(f"홈런! {runs}득점!")
        elif outcome in ["SINGLE_HIT", "INFIELD_HIT"]:
            if self.runners[2]:
                if self.is_top_inning: self.away_score += 1
                else: self.home_score += 1
            self.runners = [True, self.runners[0], self.runners[1]]
            self.set_match_result("안타 출루!")
        elif outcome == "DOUBLE_HIT":
            runs = (1 if self.runners[2] else 0) + (1 if self.runners[1] else 0)
            if self.is_top_inning: self.away_score += runs
            else: self.home_score += runs
            self.runners = [False, True, self.runners[0]]
            self.set_match_result("2루타 기록!")
        elif outcome in ["GROUNDER_OUT", "FLY_OUT"]:
            self.outs += 1; self.set_match_result("아웃!")

    def set_match_result(self, msg):
        self.result_text = msg; self.result_timer = 120; self.match_state = "RESULT_DISPLAY"
        if "스트라이크" in msg and self.strikes >= 3:
            self.outs += 1; self.strikes = 0; self.balls = 0; self.result_text += " -> 삼진 아웃!"
        if self.outs >= 3:
            self.outs = 0; self.strikes = 0; self.balls = 0; self.runners = [False, False, False]
            self.is_top_inning = not self.is_top_inning
            if self.is_top_inning: self.inning += 1
            self.result_text = "3아웃! 공수 교대"

    def update(self):
        dt = self.clock.tick(Config.FPS) / 1000.0
        if self.current_scene == "MATCH_PLAY":
            if self.match_state == "PITCH_IN_FLIGHT":
                self.physics.update(dt)
                if not self.physics.in_flight and self.physics.hit_state == "PITCHING":
                    is_strike = (abs(self.physics.x) <= Config.STRIKE_ZONE_WIDTH / 2.0) and (Config.STRIKE_ZONE_BOTTOM <= self.physics.y <= Config.STRIKE_ZONE_TOP)
                    if is_strike: self.strikes += 1; self.set_match_result("루킹 스트라이크!")
                    else:
                        self.balls += 1; self.set_match_result("볼!")
                        if self.balls >= 4:
                            self.balls = 0; self.strikes = 0; self.runners = [True, self.runners[0], self.runners[1]]
                            self.set_match_result("볼넷 출루!")
            elif self.match_state == "RESULT_DISPLAY":
                if self.physics.hit_state == "HIT": self.physics.update(dt)
                self.result_timer -= 1
                if self.result_timer <= 0: self.physics.reset(); self.match_state = "SELECT_PITCH"
        else:
            if self.result_timer > 0: self.result_timer -= 1

    def render_ui(self):
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        gluOrtho2D(0, Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT, 0)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
        
        ui_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        if self.current_scene == "MAIN_MENU":
            ui_surface.fill(Config.NAVY)
            title = self.title_font.render("KBO BASEBALL 3D FINAL", True, Config.GOLD)
            ui_surface.blit(title, (Config.SCREEN_WIDTH // 2 - 200, 80))
            
            buttons = [("[ 리그 모드 ]", 80), ("[ 빠른 경기 ]", 310), ("[ 라인업 도감 ]", 540), ("[ 카드 조합 ]", 770)]
            for text, x in buttons:
                pygame.draw.rect(ui_surface, (40, 100, 200) if "리그" in text else (40, 150, 100), (x, 200, 200, 80), border_radius=12)
                ui_surface.blit(self.font.render(text, True, Config.WHITE), (x + 30, 230))
            
            team_info = self.font.render(f"소속 구단: {self.user_team['name']} ({self.user_team['city']})", True, Config.WHITE)
            ui_surface.blit(team_info, (80, 350))

        elif self.current_scene == "LEAGUE_MODE":
            ui_surface.fill((25, 35, 55))
            pygame.draw.rect(ui_surface, Config.RED, (20, 20, 100, 40), border_radius=6)
            ui_surface.blit(self.font.render("< 뒤로", True, Config.WHITE), (35, 30))
            ui_surface.blit(self.title_font.render("KBO 정규시즌 리그 모드", True, Config.GOLD), (150, 20))
            
            pygame.draw.rect(ui_surface, (40, 50, 75), (50, 100, 800, 550), border_radius=10)
            ui_surface.blit(self.font.render("순위   구단명          승   무   패   승률", True, Config.GOLD), (80, 120))
            
            standings = self.league_manager.get_sorted_standings()
            for idx, st in enumerate(standings[:10]):
                line = f" {idx+1:2d}    {st['name']:12s}  {st['wins']:2d}   {st['draws']:2d}   {st['losses']:2d}   {st['win_rate']:.3f}"
                color = Config.GOLD if st['id'] == self.user_team['id'] else Config.WHITE
                ui_surface.blit(self.font.render(line, True, color), (80, 160 + idx * 42))

            pygame.draw.rect(ui_surface, (30, 120, 200), (900, 180, 280, 60), border_radius=8)
            ui_surface.blit(self.font.render("다음 경기 진행", True, Config.WHITE), (970, 198))
            pygame.draw.rect(ui_surface, (200, 100, 40), (900, 260, 280, 60), border_radius=8)
            ui_surface.blit(self.font.render("시즌 빠른 완료", True, Config.WHITE), (970, 278))
            
            rank = self.league_manager.get_user_rank()
            claim_col = (50, 180, 80) if rank == 1 and not self.league_manager.champion_reward_claimed else Config.GRAY
            pygame.draw.rect(ui_surface, claim_col, (900, 340, 280, 60), border_radius=8)
            ui_surface.blit(self.font.render("우승 보상 획득 (10장)", True, Config.WHITE), (950, 358))
            
            if self.result_text: ui_surface.blit(self.font.render(self.result_text, True, Config.GOLD), (900, 430))

        elif self.current_scene == "REWARD_PACK_OPEN":
            ui_surface.fill((15, 20, 35))
            ui_surface.blit(self.title_font.render("★ KBO 리그 우승 보상 카드 10장 획득! ★", True, Config.GOLD), (Config.SCREEN_WIDTH // 2 - 300, 50))
            y_off = 130
            for i, c in enumerate(self.reward_cards[:5]):
                pygame.draw.rect(ui_surface, (50, 70, 110), (80 + i * 230, y_off, 200, 200), border_radius=10)
                ui_surface.blit(self.font.render(c["player_name"], True, Config.WHITE), (100 + i * 230, y_off + 30))
                ui_surface.blit(self.font.render(f"포지션: {c['position']}", True, Config.GOLD), (100 + i * 230, y_off + 70))
            for i, c in enumerate(self.reward_cards[5:]):
                pygame.draw.rect(ui_surface, (50, 70, 110), (80 + i * 230, y_off + 230, 200, 200), border_radius=10)
                ui_surface.blit(self.font.render(c["player_name"], True, Config.WHITE), (100 + i * 230, y_off + 260))
                ui_surface.blit(self.font.render(f"포지션: {c['position']}", True, Config.GOLD), (100 + i * 230, y_off + 300))
            pygame.draw.rect(ui_surface, (200, 50, 50), (Config.SCREEN_WIDTH // 2 - 100, 620, 200, 50), border_radius=8)
            ui_surface.blit(self.font.render("확인 및 메인으로", True, Config.WHITE), (Config.SCREEN_WIDTH // 2 - 70, 635))

        elif self.current_scene == "COMBINE_VIEW":
            ui_surface.fill((35, 45, 65))
            pygame.draw.rect(ui_surface, Config.RED, (20, 20, 100, 40), border_radius=6)
            ui_surface.blit(self.font.render("< 뒤로", True, Config.WHITE), (35, 30))
            ui_surface.blit(self.title_font.render("카드 조합 및 등급 강화", True, Config.GOLD), (150, 20))
            pygame.draw.rect(ui_surface, (50, 60, 90), (50, 120, 1180, 90), border_radius=10)
            ui_surface.blit(self.font.render("골든글러브 조합: 동일 카드 4장 필요 (능력치 +5)", True, Config.GOLD), (70, 140))
            pygame.draw.rect(ui_surface, (200, 150, 30), (800, 140, 180, 50), border_radius=8)
            ui_surface.blit(self.font.render("조합하기", True, Config.WHITE), (855, 155))
            pygame.draw.rect(ui_surface, (50, 60, 90), (50, 230, 1180, 90), border_radius=10)
            ui_surface.blit(self.font.render("국가대표 조합: 동일 카드 10장 필요 (능력치 +6)", True, (100, 200, 255)), (70, 250))
            pygame.draw.rect(ui_surface, (30, 120, 200), (800, 250, 180, 50), border_radius=8)
            ui_surface.blit(self.font.render("조합하기", True, Config.WHITE), (855, 265))
            if self.result_text: ui_surface.blit(self.font.render(self.result_text, True, Config.GOLD), (400, 400))

        elif self.current_scene == "LINEUP_VIEW":
            ui_surface.fill((30, 40, 60))
            pygame.draw.rect(ui_surface, Config.RED, (20, 20, 100, 40), border_radius=6)
            ui_surface.blit(self.font.render("< 뒤로", True, Config.WHITE), (35, 30))
            ui_surface.blit(self.title_font.render("보유 선수 및 카드 정보", True, Config.GOLD), (150, 20))
            y_off = 100
            for card in self.db.cards_data:
                eff_stats, mod = CardSystemManager.calculate_effective_stats(card, self.user_team["id"], 0, True)
                card_box = pygame.Rect(50, y_off, 1180, 80)
                pygame.draw.rect(ui_surface, (50, 60, 80), card_box, border_radius=8)
                info = f"[{card['type']}] {card['player_name']} ({card['season']} / {card['original_team']}) - 수량: {card['count']}장"
                stat_str = f"보정 능력치: ({mod:+d}) | {eff_stats}"
                ui_surface.blit(self.font.render(info, True, Config.GOLD if "GOLDEN" in card['type'] else Config.WHITE), (70, y_off + 15))
                ui_surface.blit(self.font.render(stat_str, True, (180, 220, 255)), (70, y_off + 45))
                y_off += 100

        elif self.current_scene == "MATCH_PLAY":
            pygame.draw.rect(ui_surface, Config.RED, (20, 20, 100, 40), border_radius=6)
            ui_surface.blit(self.font.render("< 메뉴", True, Config.WHITE), (35, 30))
            inning_str = f"{'초' if self.is_top_inning else '말'}"
            score_text = f"KBO LEAGUE | {self.inning}회{inning_str} [AWAY {self.away_score} : {self.home_score} HOME]"
            ui_surface.blit(self.font.render(score_text, True, Config.WHITE), (140, 20))
            bso_text = f"B: {'●'*self.balls}  S: {'●'*self.strikes}  O: {'●'*self.outs}"
            ui_surface.blit(self.font.render(bso_text, True, Config.GOLD), (140, 45))
            runner_info = f"주자: 1루[{'O' if self.runners[0] else 'X'}] 2루[{'O' if self.runners[1] else 'X'}] 3루[{'O' if self.runners[2] else 'X'}]"
            ui_surface.blit(self.font.render(runner_info, True, (150, 230, 150)), (500, 20))
            
            if self.match_state == "SELECT_PITCH":
                pitches = [("직구 (FAST)", 0), ("슬라이더 (SLD)", 200), ("체인지업 (CHG)", 400)]
                for name, x in pitches:
                    color = (200, 50, 50) if name.startswith(self.selected_pitch.upper()[:2]) else (50, 50, 50)
                    pygame.draw.rect(ui_surface, color, (x + 10, Config.SCREEN_HEIGHT - 70, 180, 50), border_radius=8)
                    ui_surface.blit(self.font.render(name, True, Config.WHITE), (x + 25, Config.SCREEN_HEIGHT - 55))
            elif self.match_state == "PITCH_IN_FLIGHT":
                ui_surface.blit(self.font.render("화면을 터치하여 스윙하세요!", True, Config.GOLD), (Config.SCREEN_WIDTH // 2 - 120, Config.SCREEN_HEIGHT - 100))
            if self.result_text: ui_surface.blit(self.font.render(self.result_text, True, Config.GOLD), (Config.SCREEN_WIDTH // 2 - 100, Config.SCREEN_HEIGHT // 2 - 50))

        texture_data = pygame.image.tostring(ui_surface, "RGBA", True)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDrawPixels(Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW); glPopMatrix()
        glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING)

    def run(self):
        running = True
        dt = 0.016
        while running:
            for event in pygame.event.get():
                if event.type == QUIT: running = False
                else: self.handle_input(event)
                    
            self.update()
            
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            
            if self.current_scene == "MATCH_PLAY":
                gluLookAt(0.0, 2.5, Config.PITCHER_PLATE_Z - 4.0, 0.0, 0.8, Config.HOME_PLATE_Z, 0.0, 1.0, 0.0)
                self.renderer.render_field()
                self.renderer.render_runners(self.runners)
                self.renderer.render_players_with_anim(dt, "DEFAULT", "LEG_KICK_BATTER")
                if self.match_state == "SELECT_PITCH": self.renderer.render_strike_zone(self.target_x, self.target_y)
                if self.physics.active: self.renderer.render_ball(self.physics.x, self.physics.y, self.physics.z)
                    
            self.render_ui()
            pygame.display.flip()
            
        pygame.quit()

if __name__ == "__main__":
    app = MobileKBOBaseballApp()
    app.run()
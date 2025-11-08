#!/usr/bin/env python3

import os
import sys
import time
import pygame as pg
from pygame.locals import *


import asyncio
import json
import logging


from minMaxAgent import MinMaxAgent


# --- Setup Logger ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
# --------------------


# --- Constants ---
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 400
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
COLOR_INACTIVE = pg.Color('lightskyblue3')
COLOR_ACTIVE = pg.Color('dodgerblue2')
LINE_COLOR_X = (233, 65, 65)
LINE_COLOR_O = (0, 134, 244)
FPS = 30

def find_assets_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'assets')

ASSETS_PATH = find_assets_path()

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + 100), 0, 32)
        pg.display.set_caption("Tic Tac Toe (Asyncio)")
        self.clock = pg.time.Clock()
        self.bot = MinMaxAgent()
        self.mapping = {'x': 1, None: 0, 'o': -1}
        
        self.game_state = "MAIN_MENU" 
        self.game_mode = None
        
        self.board = [[None] * 3, [None] * 3, [None] * 3]
        self.turn = 'x'
        self.winner = None
        self.draw = False
        self.scores = {'x': 0, 'o': 0, 'draws': 0}
        
        self.reader = None
        self.writer = None
        self.network_task = None
        self.is_my_turn = False
        self.player_char = None
        self.network_status = "Initializing..."

        self.font_large = pg.font.Font(None, 50)
        self.font_medium = pg.font.Font(None, 30)
        
        self.local_play_rect = pg.Rect(100, 150, 200, 50)
        self.remote_host_rect = pg.Rect(100, 220, 200, 50)
        self.remote_join_rect = pg.Rect(100, 290, 200, 50)

        self.input_box = pg.Rect(50, 200, 300, 32)
        self.input_text = ''
        self.input_active = True
        self.input_prompt = ''
        self.host_to_join = ''

        self.load_assets()

    def load_assets(self):
        try:
            self.x_img = pg.image.load(os.path.join(ASSETS_PATH, 'x.png'))
            self.o_img = pg.image.load(os.path.join(ASSETS_PATH, 'o.png'))
            self.one_player_img = pg.image.load(os.path.join(ASSETS_PATH, 'one_player.png'))
            self.two_players_img = pg.image.load(os.path.join(ASSETS_PATH, 'two_players.png'))

            self.x_img = pg.transform.scale(self.x_img, (80, 80))
            self.o_img = pg.transform.scale(self.o_img, (80, 80))
            self.one_player_img = pg.transform.scale(self.one_player_img, (200, 102))
            self.two_players_img = pg.transform.scale(self.two_players_img, (200, 102))
            
            self.one_player_rect = self.one_player_img.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60))
            self.two_players_rect = self.two_players_img.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))

        except pg.error as e:
            logger.error(f"Fatal: Error loading assets: {e}")
            sys.exit()

    def draw_main_menu(self):
        self.screen.fill(WHITE)
        title_surf = self.font_large.render("Tic Tac Toe", True, BLACK)
        self.screen.blit(title_surf, (title_surf.get_rect(centerx=SCREEN_WIDTH/2, y=50)))

        pg.draw.rect(self.screen, GRAY, self.local_play_rect)
        pg.draw.rect(self.screen, GRAY, self.remote_host_rect)
        pg.draw.rect(self.screen, GRAY, self.remote_join_rect)

        local_text = self.font_medium.render("Local Play", True, BLACK)
        host_text = self.font_medium.render("Host Game", True, BLACK)
        join_text = self.font_medium.render("Join Game", True, BLACK)
        
        self.screen.blit(local_text, (self.local_play_rect.centerx - local_text.get_width() / 2, self.local_play_rect.centery - local_text.get_height() / 2))
        self.screen.blit(host_text, (self.remote_host_rect.centerx - host_text.get_width() / 2, self.remote_host_rect.centery - host_text.get_height() / 2))
        self.screen.blit(join_text, (self.remote_join_rect.centerx - join_text.get_width() / 2, self.remote_join_rect.centery - join_text.get_height() / 2))

    def draw_local_menu(self):
        self.screen.fill(WHITE)
        self.screen.blit(self.one_player_img, self.one_player_rect)
        self.screen.blit(self.two_players_img, self.two_players_rect)

    def draw_input_screen(self, prompt):
        self.screen.fill(WHITE)
        
        prompt_surf = self.font_medium.render(prompt, True, BLACK)
        self.screen.blit(prompt_surf, (self.input_box.x, self.input_box.y - 30))
        
        color = COLOR_ACTIVE if self.input_active else COLOR_INACTIVE
        pg.draw.rect(self.screen, color, self.input_box, 2)
        
        text_surf = self.font_medium.render(self.input_text, True, BLACK)
        self.screen.blit(text_surf, (self.input_box.x + 5, self.input_box.y + 5))
        self.input_box.w = max(300, text_surf.get_width() + 10)

    def draw_connecting_screen(self):
        self.screen.fill(BLACK)
        font = pg.font.Font(None, 30)
        text_surface = font.render(self.network_status, True, WHITE)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.screen.blit(text_surface, text_rect)

    def draw_board(self):
        self.screen.fill(WHITE)
        pg.draw.line(self.screen, BLACK, (SCREEN_WIDTH / 3, 0), (SCREEN_WIDTH / 3, SCREEN_HEIGHT), 7)
        pg.draw.line(self.screen, BLACK, (SCREEN_WIDTH / 3 * 2, 0), (SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT), 7)
        pg.draw.line(self.screen, BLACK, (0, SCREEN_HEIGHT / 3), (SCREEN_WIDTH, SCREEN_HEIGHT / 3), 7)
        pg.draw.line(self.screen, BLACK, (0, SCREEN_HEIGHT / 3 * 2), (SCREEN_WIDTH, SCREEN_HEIGHT / 3 * 2), 7)
        self.draw_status()
    
    def draw_status(self):
        total_games = self.scores['x'] + self.scores['o'] + self.scores['draws']
        score_text = (f"Win X: {self.scores['x']}/{total_games} | "
                      f"Win O: {self.scores['o']}/{total_games} | "
                      f"Draws: {self.scores['draws']}/{total_games}")

        if self.winner:
            message = f"Last Match: {self.winner.upper()} won!"
        elif self.draw:
            message = "Last Match: Game Draw!"
        elif "remote" in self.game_mode:
            if self.is_my_turn:
                message = f"Your Turn ({self.player_char.upper()})"
            else:
                message = f"Opponent's Turn ({'O' if self.player_char == 'x' else 'X'})"
        else:
            message = f"{self.turn.upper()}'s Turn"

        font = pg.font.Font(None, 24)
        score_surface = font.render(score_text, True, WHITE)
        message_surface = font.render(message, True, WHITE)
        
        self.screen.fill(BLACK, (0, 400, 500, 100))
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH / 2, 425))
        message_rect = message_surface.get_rect(center=(SCREEN_WIDTH / 2, 465))
        
        self.screen.blit(score_surface, score_rect)
        self.screen.blit(message_surface, message_rect)

    def check_win(self):
        for row in range(3):
            if self.board[row][0] == self.board[row][1] == self.board[row][2] and self.board[row][0] is not None:
                self.winner = self.board[row][0]
                line_color = LINE_COLOR_X if self.winner == 'x' else LINE_COLOR_O
                pg.draw.line(self.screen, line_color, (0, (row + 1) * SCREEN_HEIGHT / 3 - SCREEN_HEIGHT / 6),
                             (SCREEN_WIDTH, (row + 1) * SCREEN_HEIGHT / 3 - SCREEN_HEIGHT / 6), 4)
                break
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] and self.board[0][col] is not None:
                self.winner = self.board[0][col]
                line_color = LINE_COLOR_X if self.winner == 'x' else LINE_COLOR_O
                pg.draw.line(self.screen, line_color, ((col + 1) * SCREEN_WIDTH / 3 - SCREEN_WIDTH / 6, 0),
                             ((col + 1) * SCREEN_WIDTH / 3 - SCREEN_WIDTH / 6, SCREEN_HEIGHT), 4)
                break
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] is not None:
            self.winner = self.board[0][0]
            line_color = LINE_COLOR_X if self.winner == 'x' else LINE_COLOR_O
            pg.draw.line(self.screen, line_color, (50, 50), (350, 350), 4)
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] is not None:
            self.winner = self.board[0][2]
            line_color = LINE_COLOR_X if self.winner == 'x' else LINE_COLOR_O
            pg.draw.line(self.screen, line_color, (350, 50), (50, 350), 4)
        
        if all(all(row) for row in self.board) and self.winner is None:
            self.draw = True
        
        if self.winner:
            self.scores[self.winner] += 1
        elif self.draw:
            self.scores['draws'] += 1
        
        self.draw_status()

    def draw_xo(self, row, col):
        self.board[row-1][col-1] = self.turn
        posx = (col - 1) * (SCREEN_WIDTH / 3) + 30
        posy = (row - 1) * (SCREEN_HEIGHT / 3) + 30
        if self.turn == 'x':
            self.screen.blit(self.x_img, (posx, posy))
            self.turn = 'o'
        else:
            self.screen.blit(self.o_img, (posx, posy))
            self.turn = 'x'
        pg.display.update()

    async def handle_click(self):
        if "remote" in self.game_mode:
            if not self.is_my_turn:
                logger.info("Not your turn!")
                return

        x, y = pg.mouse.get_pos()
        if y > SCREEN_HEIGHT: return

        col = int(x // (SCREEN_WIDTH / 3)) + 1
        row = int(y // (SCREEN_HEIGHT / 3)) + 1

        if row and col and self.board[row-1][col-1] is None:
            self.draw_xo(row, col)
            self.check_win()

            if "remote" in self.game_mode:
                self.is_my_turn = False
                move_msg = {"type": "make_move", "move": [row-1, col-1]}
                await self.send_message(move_msg)
                
                if self.winner or self.draw:
                    game_over_msg = {"type": "game_over", "winner": self.winner, "draw": self.draw}
                    await self.send_message(game_over_msg)
            
            elif self.game_mode == 'vs_bot' and not (self.winner or self.draw):
                agent_board = [[self.mapping[cell] for cell in row] for row in self.board]
                r, c, _ = self.bot.chooseAction(agent_board, self.mapping[self.turn])
                await asyncio.sleep(0.25)
                self.draw_xo(r + 1, c + 1)
                self.check_win()

    def reset_game(self):
        logger.info("Resetting game board.")
        time.sleep(.1)
        self.turn = 'x'
        self.draw = False
        self.winner = None
        self.board = [[None] * 3, [None] * 3, [None] * 3]
        self.draw_board()

    # --- ASYNCIO NETWORKING FUNCTIONS ---
    async def send_message(self, msg_dict):
        if not self.writer:
            logger.warning("Not connected, cannot send message.")
            return
        
        try:
            msg_json = json.dumps(msg_dict) + "\n"
            data = msg_json.encode('utf-8')
            
            self.writer.write(data)
            await self.writer.drain()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.close_connection()

    def handle_network_message(self, msg):
        logger.info(f"Received message: {msg}")
        msg_type = msg.get('type')

        if msg_type == 'make_move':
            if not self.is_my_turn:
                r, c = msg['move']
                self.draw_xo(r + 1, c + 1)
                self.check_win()
                self.is_my_turn = True
        
        elif msg_type == 'game_over':
            self.winner = msg.get('winner')
            self.draw = msg.get('draw', False)
            self.is_my_turn = False
            self.draw_status()
        
        elif msg_type == 'reset':
            self.reset_game()
            self.is_my_turn = (self.player_char == 'x')

    async def network_listen_loop(self):
        try:
            while self.reader:
                data = await self.reader.readline()
                if not data:
                    logger.info("Connection closed by opponent.")
                    break
                
                try:
                    msg = json.loads(data.decode('utf-8'))
                    self.handle_network_message(msg)
                except json.JSONDecodeError:
                    logger.warning(f"Received malformed data: {data.decode('utf-8')}")

        except asyncio.CancelledError:
            logger.info("Network loop cancelled.")
        except Exception as e:
            logger.error(f"Network error in listen loop: {e}")
        
        finally:
            await self.close_connection()

    async def handle_client(self, reader, writer):
        logger.info("Client connected!")
        self.reader = reader
        self.writer = writer
        
        self.game_state = "PLAYING"
        self.player_char = 'x'
        self.is_my_turn = True
        self.draw_board()
        
        self.network_task = asyncio.create_task(self.network_listen_loop())
        await self.network_task

    async def close_connection(self):
        logger.info("Closing connection...")
        if self.network_task:
            self.network_task.cancel()
            self.network_task = None
        
        if self.writer:
            self.writer.close()
            try:
                # Wait for the stream to be fully closed.
                # This is the line that receives the CancelledError on shutdown.
                await self.writer.wait_closed()
            except asyncio.CancelledError:
                # This is expected during a clean shutdown,
                # as asyncio.run() cancels all tasks.
                # We can safely ignore it and continue cleanup.
                logger.info("Cleanup interrupted by task cancellation (normal on exit).")
            
            self.writer = None
            self.reader = None
        
        self.game_state = "MAIN_MENU" 
        self.network_status = "Connection lost."
        logger.info("Connection resources are now clean.")

    async def start_server_task(self, port):
        """Called when user submits port for hosting."""
        logger.info(f"Starting server task on port {port}...")
        self.game_state = "CONNECTING"
        try:
            server = await asyncio.start_server(
                self.handle_client, '', port)
            addr = server.sockets[0].getsockname()
            self.network_status = f"Waiting on {addr[0]}:{addr[1]}..."
            logger.info(self.network_status)
            asyncio.create_task(server.serve_forever())
        except Exception as e:
            logger.error(f"Server start error: {e}")
            self.network_status = f"Server error: {e}"
            self.game_state = "GET_PORT_INPUT"

    async def start_client_task(self, host, port):
        """Called when user submits port for joining."""
        logger.info(f"Starting client task, connecting to {host}:{port}...")
        self.game_state = "CONNECTING"
        try:
            self.network_status = f"Connecting to {host}:{port}..."
            self.reader, self.writer = await asyncio.open_connection(host, port)
            
            logger.info("Connected to server!")
            self.game_state = "PLAYING"
            self.player_char = 'o'
            self.is_my_turn = False
            self.draw_board()
            self.network_task = asyncio.create_task(self.network_listen_loop())
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.network_status = f"Connection failed: {e}"
            self.game_state = "MAIN_MENU" 
            self.input_text = ""
            
    # ---
    # --- MAIN ASYNC RUN FUNCTION  ---
    # ---
    async def run(self):
        """The main game loop, now a state machine."""
        
        logger.info("Game starting...")
        
        # This try block is new
        try:
            running = True
            while running:
                # 1. Process Pygame events
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        running = False
                    
                    # --- State: MAIN_MENU ---
                    if self.game_state == "MAIN_MENU":
                        if event.type == pg.MOUSEBUTTONDOWN:
                            if self.local_play_rect.collidepoint(event.pos):
                                logger.info("Menu: Clicked 'Local Play'")
                                self.game_state = "LOCAL_MENU"
                            
                            elif self.remote_host_rect.collidepoint(event.pos):
                                logger.info("Menu: Clicked 'Host Game'")
                                self.game_mode = "remote_server"
                                self.input_text = "8888" # Default port
                                self.game_state = "GET_PORT_INPUT"
                            
                            elif self.remote_join_rect.collidepoint(event.pos):
                                logger.info("Menu: Clicked 'Join Game'")
                                self.game_mode = "remote_client"
                                self.input_text = "127.0.0.1" # Default host
                                self.game_state = "GET_HOST_INPUT"

                    # --- State: LOCAL_MENU ---
                    elif self.game_state == "LOCAL_MENU":
                        if event.type == pg.MOUSEBUTTONDOWN:
                            if self.one_player_rect.collidepoint(event.pos):
                                logger.info("Menu: Clicked '1 Player'")
                                self.game_mode = "vs_bot"
                                self.game_state = "PLAYING"
                                self.draw_board()
                            elif self.two_players_rect.collidepoint(event.pos):
                                logger.info("Menu: Clicked '2 Players'")
                                self.game_mode = "vs_human"
                                self.game_state = "PLAYING"
                                self.draw_board()
                    
                    # --- State: GET_HOST_INPUT / GET_PORT_INPUT ---
                    elif self.game_state in ("GET_HOST_INPUT", "GET_PORT_INPUT"):
                        if event.type == pg.KEYDOWN:
                            if event.key == pg.K_RETURN:
                                logger.info(f"Input: '{self.input_text}' submitted")
                                if self.game_state == "GET_HOST_INPUT":
                                    self.host_to_join = self.input_text
                                    self.input_text = "8888" # Default port
                                    self.game_state = "GET_PORT_INPUT"
                                
                                elif self.game_state == "GET_PORT_INPUT":
                                    try:
                                        port = int(self.input_text)
                                        if self.game_mode == "remote_server":
                                            logger.info("Creating server task...")
                                            asyncio.create_task(self.start_server_task(port))
                                        else: # game_mode == "remote_client"
                                            logger.info("Creating client task...")
                                            host = self.host_to_join
                                            asyncio.create_task(self.start_client_task(host, port))
                                        self.input_text = ""
                                    except ValueError:
                                        self.input_text = ""
                                        logger.error("Invalid port entered.")
                                        
                            elif event.key == pg.K_BACKSPACE:
                                self.input_text = self.input_text[:-1]
                            else:
                                self.input_text += event.unicode
                        
                    # --- State: PLAYING ---
                    elif self.game_state == "PLAYING":
                        if event.type == pg.MOUSEBUTTONDOWN:
                            if self.winner or self.draw:
                                logger.info("Clicked on finished board, resetting.")
                                if "remote" in self.game_mode:
                                    await self.send_message({"type": "reset"})
                                self.reset_game()
                                if "remote" in self.game_mode:
                                    self.is_my_turn = (self.player_char == 'x')
                            else:
                                await self.handle_click()
                
                # 2. Draw the current state
                if self.game_state == "MAIN_MENU":
                    self.draw_main_menu()
                elif self.game_state == "LOCAL_MENU":
                    self.draw_local_menu()
                elif self.game_state == "GET_HOST_INPUT":
                    self.draw_input_screen("Enter Host IP:")
                elif self.game_state == "GET_PORT_INPUT":
                    if self.game_mode == "remote_server":
                        self.draw_input_screen("Enter Port to Host:")
                    else: 
                        self.draw_input_screen(f"Enter Port for {self.host_to_join}:")
                elif self.game_state == "CONNECTING":
                    self.draw_connecting_screen()
                elif self.game_state == "PLAYING":
                    self.draw_status()
                
                # 3. Update the display
                pg.display.update()
                
                # 4. Yield control to asyncio
                await asyncio.sleep(1 / FPS)

        # --- This 'except' and 'finally' block is new ---
        except asyncio.CancelledError:
            logger.info("Main game loop cancelled.")
        finally:
            logger.info("Main loop finished. Running cleanup...")
            await self.close_connection()
            pg.quit()
            logger.info("Pygame quit. Exiting.")
            sys.exit()

async def main():
    """No args, just creates and runs the game."""
    game = Game()
    await game.run() # Run the async main loop

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Game interrupted by user. Exiting.")

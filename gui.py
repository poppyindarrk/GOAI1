from board import Board, PASS, RESIGN, BLACK, WHITE, INVLD, EMPTY
from gtp import GTP_ENGINE
from config import BOARD_SIZE, KOMI
from mcts import Search, Node
import time
import argparse
import tkinter as tk
from threading import Thread
from tkinter import scrolledtext,PhotoImage
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
class GUI_LOOP(GTP_ENGINE):
    def __init__(self, args):
        super(GUI_LOOP, self).__init__(args)
        self.init_layouts(1200, 800)
        self.window = tk.Tk()
        self.window.resizable(0, 0)
        self.window.title("Deep Learning of Go")
        self.window.geometry("{w}x{h}".format(w=self.width, h=self.height))
        # self.levels = ["15q", "10q", "5q", "1q", "1d", "2d", "3d","4d", "5d"]
        self.levels = ["beginner","intermediate","advanced","expert"]
        self.oval_buffer = [None] * self.board.num_intersections
        self.text_buffer = [None] * self.board.num_intersections
        self.winrate_history = []
        self.game_thread = None
        self.suspend = False
        self.acquire_vtx = None
        self.level_weights = {
            "beginner": "beginner.pt",
            "intermediate": "intermediate.pt",
            "advanced": "advanced.pt",
            "expert": "expert.pt"
        }

        self.init_widgets()
        self.window.mainloop()
    def set_lvl(self, level):
        weight_path = self.level_weights.get(level)
        if weight_path:
            self.network.load_pt(weight_path)
            print(f"游戏难度设置为: {level}，加载权重 {weight_path}")
        else:
            print("未找到对应难度的权重文件")
    def init_layouts(self, width, height):
        min_width = 800
        min_height = 500
        self.widgets_offset_base = 30


        self.width = max(width, min_width)
        self.height = max(height, min_height)

        size_base = min(self.width, self.height)

        # Set the canvas size and coordinate.
        self.canvas_size = size_base - self.widgets_offset_base * 2 # The canvas the always square.
        self.canvas_x = self.widgets_offset_base
        self.canvas_y = self.widgets_offset_base

        # Set the buttons's coordinates.
        buttons_offset_base = self.canvas_x + self.canvas_size + self.widgets_offset_base
        self.buttons_x = [buttons_offset_base + 0 * 90,
                          buttons_offset_base + 1 * 90,
                          buttons_offset_base + 2 * 90,
                          buttons_offset_base + 3 * 90-60,
                          buttons_offset_base + 4 * 90-90]
        self.buttons_y = [self.widgets_offset_base,
                          self.widgets_offset_base,
                          self.widgets_offset_base,
                          self.widgets_offset_base,
                          self.widgets_offset_base-15]

        # Set the scrolled text size and coordinate.
        self.scrolled_x = self.canvas_x + self.canvas_size + self.widgets_offset_base
        self.scrolled_y = 3 * self.widgets_offset_base

        self.scrolled_width = round((self.width - self.scrolled_x - self.widgets_offset_base) / 9)
        self.scrolled_height = round((self.height - self.scrolled_y - self.widgets_offset_base) / 18)

    def init_widgets(self):
        self.canvas = tk.Canvas(self.window, bg="#CD853F", height=self.canvas_size, width=self.canvas_size)
        self.scroll_rext = scrolledtext.ScrolledText(self.window, height=self.scrolled_height, width=self.scrolled_width)

        self.bt_black_start = tk.Button(self.window, text="BLACK START", command=lambda : self.start_new_game(BLACK))
        self.bt_black_start.place(x=self.buttons_x[0], y=self.buttons_y[0])

        self.bt_white_start = tk.Button(self.window, text="WHITE START", command=lambda : self.start_new_game(WHITE))
        self.bt_white_start.place(x=self.buttons_x[1], y=self.buttons_y[1])

        self.bt_self_play = tk.Button(self.window, text="AI", command=lambda : self.start_new_game())
        self.bt_self_play.place(x=self.buttons_x[2], y=self.buttons_y[2])

        self.bt_pass_start = tk.Button(self.window, text="RESIGN", command=lambda : self.acquire_move(PASS))
        self.bt_pass_start.place(x=self.buttons_x[3], y=self.buttons_y[3])

        self.lbl_level = tk.Label(self.window, text="Enter Level:")
        self.lbl_level.place(x=self.buttons_x[4], y=self.buttons_y[4])

        # Level input entry field
        self.entry_level = tk.Entry(self.window)
        self.entry_level.place(x=self.buttons_x[4], y=self.buttons_y[4] + 20)

        # Button to set the level
        self.btn_set_level = tk.Button(self.window, text="Set Level", command=self.set_level_from_input)
        self.btn_set_level.place(x=self.buttons_x[4], y=self.buttons_y[4] + 40)
        self.btn_analysis = tk.Button(self.window, text="After Game Analysis", command=self.perform_analysis)
        self.btn_analysis.place(x=self.width-180, y=self.height - 50)  # Adjust positioning as needed
        self.draw_canvas(self.canvas_x, self.canvas_y)
        self.draw_scroll_text(self.scrolled_x, self.scrolled_y)

    def draw_canvas(self, x, y):
        bsize = self.board.board_size
        square_size = self.canvas_size / bsize
        lower = square_size/2
        upper = self.canvas_size - square_size/2

        for i in range(bsize):
            offset = i * square_size
            self.canvas.create_line(lower        ,lower+offset, upper       , lower+offset)
            self.canvas.create_line(lower+offset ,lower       , lower+offset, upper)
        self.canvas.place(x=x, y=y)

    def draw_scroll_text(self, x, y):
        self.scroll_rext.place(x=x, y=y)
    
    def insert_scroll_text(self, string):
        self.scroll_rext.insert(tk.END, string+'\n')
        self.scroll_rext.see(tk.END)
        self.scroll_rext.update()
    
    def reset_canvas(self):
        self.clear_board()
        self.canvas.delete("all")
        self.scroll_rext.delete(1.0, tk.END)
        self.draw_canvas(self.canvas_x, self.canvas_y)
        self.canvas.bind("<Button-1>", self.scan_move)
        self.rect = None

    def draw_stone(self, to_move, rc_pos, move_num=None):
        r, c = rc_pos
        x, y = self.convert_rc_to_xy(rc_pos)

        bsize = self.board.board_size
        square_size = self.canvas_size/bsize

        color_stone = "black" if to_move == BLACK else "white"
        color_index = "white" if to_move == BLACK else "black"
        color_border = "#696969" if to_move == BLACK else "black"


        radius = max(square_size/2 - 5, 15)
        border = max(round(radius/15), 2)
        self.oval_buffer[self.board.get_index(r, c)] = self.canvas.create_oval(
                x-radius, y-radius, x+radius, y+radius,
                fill=color_stone, outline=color_border, width=border)
        if self.rect == None:
            offset = max(square_size/2 , 20)
            self.rect = self.canvas.create_rectangle(x-offset, y-offset, x+offset, y+offset, outline="#c1005d")
            self.rect_xy_pos = (x, y)
        else:
            rc_pos = self.convert_xy_to_rc((x, y))
            old_x, old_y = self.rect_xy_pos
            new_x, new_y = self.convert_rc_to_xy(rc_pos)
            dx, dy = new_x-old_x, new_y-old_y
            self.canvas.move(self.rect, dx, dy)
            self.rect_xy_pos = (new_x, new_y)

        text_size = round(1*square_size/2)
        if move_num == None:
            move_num = str()

        self.text_buffer[self.board.get_index(r,c)] = self.canvas.create_text(x,y, text=str(move_num), fill=color_index, font=('Arial', text_size))
        self.canvas.update()

    def convert_rc_to_xy(self, rc_pos):
        bsize = self.board.board_size
        square_size = self.canvas_size/bsize
        lower = square_size/2

        r, c = rc_pos

        x = c*square_size + lower
        y = r*square_size + lower
        return x, y

    def convert_xy_to_rc(self, xy_pos):
        bsize = self.board.board_size
        square_size = self.canvas_size/bsize
        lower = square_size/2

        x, y = xy_pos
        r = round((y-lower)/square_size)
        c = round((x-lower)/square_size)
        return r, c

    def start_new_game(self, color=None):
        self.suspend = True # stop the board updating.

        self.acquire_vtx = None
        self.turns = ["compute", "compute"]
        if color != None:
            self.turns[color] = "player"
        self.reset_canvas()
        self.game_over = False

        if self.game_thread == None:
            
            self.game_thread = Thread(target=self.process_game,)
            self.game_thread.setDaemon(True) 
            self.game_thread.start()

        self.suspend = False # start the game.

    def process_game(self):
        resignd = None

        while True:
            # Short sleep in order to avoid busy running.
            time.sleep(0.1)

            if self.suspend or self.game_over:
                continue
            to_move = self.board.to_move
            move_num = self.board.move_num

            if self.turns[to_move] == "compute":
                move = self.genmove("black" if to_move == BLACK else "white")
                self.update_winrate_display()
                vtx = self.board.last_move
                if move == "resign":
                    vtx = RESIGN
                    resignd = to_move

                if move == "pass":
                    self.board.num_passes+=1
                    self.insert_scroll_text("COMPUTER PASS")

                if vtx != PASS or vtx != RESIGN:
                    self.update_canvas(vtx, to_move,  move_num+1)

                    # Dump the search verbose.
                    if self.args.verbose:
                        self.insert_scroll_text(self.last_verbose)
                self.acquire_vtx = None
            else:
                if self.acquire_vtx != None:
                    if self.acquire_vtx == PASS:
                        self.board.play(PASS)
                        self.canvas.delete(self.rect)
                    else:
                        self.board.play(self.acquire_vtx)
                        self.update_canvas(self.acquire_vtx, to_move,  move_num+1)
                    self.acquire_vtx = None

            if resignd != None:
                if resignd == BLACK:
                    self.insert_scroll_text("BLACK RESIGN")
                else:
                    self.insert_scroll_text("WHITE RESIGN")
                resignd = None
                self.game_over = True
                self.network.clear_cache()
            elif self.board.num_passes >= 2:
                score = self.board.final_score()
                if abs(score) <= 0.01:
                    self.insert_scroll_text("DRAW")
                elif score > 0:
                    self.insert_scroll_text("BLACK WIN{} STONES".format(score))
                elif score < 0:
                    self.insert_scroll_text("WHITE WIN{} STONES".format(-score))
                self.game_over = True
                self.network.clear_cache()

    def update_canvas(self, vtx, to_move, move_num):
        # Update the board canvas.

        r = self.board.get_x(vtx)
        c = self.board.get_y(vtx)
        self.draw_stone(to_move, (r,c))

        if self.board.removed_cnt != 0:
            curr = len(self.board.history) - 1
            post_state = self.board.history[curr-1]
            for v in range(len(post_state)):
                if self.board.state[v] == EMPTY and post_state[v] != EMPTY:
                    self.canvas.delete(self.oval_buffer[self.board.vertex_to_index(v)])
                    self.canvas.delete(self.text_buffer[self.board.vertex_to_index(v)])

    def scan_move(self, event):
        # Acquire a move after the player click the board.

        x, y = event.x, event.y
        r, c = self.convert_xy_to_rc((x, y))

        if r < 0 or r >= self.board.board_size:
            return

        if c < 0 or c >= self.board.board_size:
            return

        self.acquire_move(self.board.get_vertex(r,c))

    def acquire_move(self, vtx):
        # Set acquire move if the move is legal.

        if self.board.legal(vtx):
            self.acquire_vtx = vtx
    def set_level_from_input(self):
        level_input = self.entry_level.get().strip()
        if level_input in self.levels:  # Validate the input against predefined levels
            self.set_lvl(level_input)
            self.insert_scroll_text(f"Level set to: {level_input}")
        else:
            self.insert_scroll_text("Invalid level input. Please use: " + ", ".join(self.levels))

    def perform_analysis(self):
        if self.game_over:
            self.insert_scroll_text("Performing after game analysis...")
            if not self.winrate_history:
                self.insert_scroll_text("No winrate data available for analysis.")
                return
            
            moves = list(range(1, len(self.winrate_history) + 1))

            # Plotting and saving the graph
            plt.figure(figsize=(6, 3), dpi=100)  # Adjust dimensions and DPI here
            plt.plot(moves, self.winrate_history, marker='o', linestyle='-', color='b')
            plt.title("Winrate Over Moves")
            plt.xlabel("Move Number")
            plt.ylabel("Winrate (%)")
            plt.grid(True)
            plot_path = "winrate_plot.png"
            plt.savefig(plot_path)
            plt.close()

            # Resize image for GUI
            image = Image.open(plot_path)
            image = image.resize((340, 200), Image.LANCZOS)  # Resize to fit your Text widget or display area
            photo = ImageTk.PhotoImage(image)

            # Display the image in the Text widget
            self.scroll_rext.image_create(tk.END, image=photo)
            self.scroll_rext.image = photo  # Keep a reference
            self.scroll_rext.insert(tk.END, '\n')  # Space after the image

            # Analysis of winrate changes
            largest_drop = 0
            move_of_largest_drop = 0
            for i in range(1, len(self.winrate_history)):
                drop = self.winrate_history[i - 1] - self.winrate_history[i]
                if drop > largest_drop:
                    largest_drop = drop
                    move_of_largest_drop = moves[i]

            self.insert_scroll_text(f"Largest winrate drop was {largest_drop:.2f}% at move {move_of_largest_drop}.")
            self.insert_scroll_text("Analysis graph and details are displayed above.")
        else:
            self.insert_scroll_text("Game is not finished yet. Please finish the game before analysis.")

    def update_winrate_display(self):
        try:
            # Open the win rate log file and read the last line for the latest win rate
            with open("winrate_log.txt", "r") as file:
                lines = file.readlines()
                last_line = lines[-1] if lines else "Win Rate: 0%"  # Default if file is empty
                winrate_percentage = 100*(1-float(last_line.split(":")[1].strip()[:-1]))  # Extract the win rate and convert to float
        except FileNotFoundError:
            winrate_percentage = 0.0  # Default value if file not found
            self.insert_scroll_text("Winrate log file not found. Displaying default win rate: 0.00%")
            return 
        except Exception as e:
            self.insert_scroll_text(f"Error reading winrate file: {e}")
            return  # Exit the function on error

        # Display the latest win rate read from the file
        self.winrate_history.append(winrate_percentage)
        self.insert_scroll_text(f"Current winrate: {winrate_percentage:.2f}%")
        return 



import tkinter as tk
from tkinter import *

from PIL import ImageTk, Image

# VLC NEEDS TO BE INSTALLED
import vlc

import sys
import os
import socket
import threading
import time

import examples_tkvlc

def playPauseVideo(event):
    global playing
    if playing:
        player.pause()
        playing = False
    else:
        player.play()
        playing = True

def stopVideo(event):
    player.stop()

def fastForward(*unused):
    player.player.set_rate(2)

def rewind(*unused):
    player.player.set_rate(-1)

def quit(event):
    player.stop()
    root.destroy()

def exit(*unused):
    if playing:
        player.stop()
    root.destroy()

def up(event):
    if screen == Screens.MainSelect:
        titles_grid.move_selection(-1, 0)
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.move_season_selection(-1)
    elif screen == Screens.ShowEpisodeSelect:
        curr_show_manager.move_episode_selection(-1)

def down(event):
    if screen == Screens.MainSelect:
        titles_grid.move_selection(1, 0)
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.move_season_selection(1)
    elif screen == Screens.ShowEpisodeSelect:
        curr_show_manager.move_episode_selection(1)

def left(event):
    if screen == Screens.MainSelect:
        titles_grid.move_selection(0, -1)
    elif screen == Screens.Player:
        rewind(None)

def right(event):
    if screen == Screens.MainSelect:
        titles_grid.move_selection(0, 1)
    elif screen == Screens.Player:
        fastForward(None)

def select(event):
    global screen
    global player
    
    if screen == Screens.MainSelect:
        
        titles_grid.destroy()
        
        
        #for child in frame.winfo_children():
        #    child.destroy()
        
        video_file = titles_grid.get_video()

        if video_file != None:
            details_pane.destroy()
            grid.pack_forget()

            player = examples_tkvlc.Player(frame, video=video_file)#"D:\VIDEOS\MOVIES\American Sniper.mp4")
            player.OnPlay()

            screen = Screens.Player
        else:
            # We need to destroy and recreate the details pane??? WHY??
            grid.pack_forget()

            show_dir = os.path.join(media_dir, titles_grid.get_title())

            global curr_show_manager
            
            curr_show_manager = ShowManager(grid, show_dir)
            curr_show_manager.draw_seasons()

            screen = Screens.ShowSeasonSelect
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.select_season()

        screen = Screens.ShowEpisodeSelect
    elif screen == Screens.ShowEpisodeSelect:
        video_file = curr_show_manager.get_episode()

        curr_show_manager.select_episode()

        details_pane.destroy()

        player = examples_tkvlc.Player(frame, video=video_file)#"D:\VIDEOS\MOVIES\American Sniper.mp4")
        player.OnPlay()

        screen = Screens.Player
    elif screen == Screens.Player:
        player.stop()
    else:
        print("UNKNOWN SCREEN!")

        #root.protocol("WM_DELETE_WINDOW", player.OnClose)  # XXX unnecessary (on macOS)
        #player.play()
        #playing = True

def back(event):
    global screen

    if screen == Screens.MainSelect:
        pass
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.destroy()

        draw_titles_grid()

        screen = Screens.MainSelect
    elif screen == Screens.ShowEpisodeSelect:
        curr_show_manager.destroy_episodes()

        curr_show_manager.draw_seasons()

        screen = Screens.ShowSeasonSelect
    elif screen == Screens.Player:
        global player
        if player != None:
            player.OnDestroy()

        draw_details_pane()
        draw_titles_grid()

        screen = Screens.MainSelect


class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            print("ACCEPTING CLIENT FROM: " + str(address))
            #client.settimeout(60)
            listen_thread = threading.Thread(target = self.listenToClient,args = (client,address))
            listen_thread.daemon = True
            listen_thread.start()

    def listenToClient(self, client, address):
        self.extra_data = ""
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    # Set the response to echo back the recieved data
                    data_str = data.decode()
                    
                    #print("RECEIVED DATA: " + data_str)
                    
                    commands = data_str.splitlines()

                    first_command = self.extra_data + commands[0]

                    if data_str[-1] != "\n":
                        self.extra_data = commands.pop()
                    
                    self.exec_command(first_command)

                    if len(commands) > 1:
                        for command in commands[1:]:
                            self.exec_command(command)
                    '''
                    client.send(response)
                    '''
                else:
                    raise Exception('Client disconnected')
            except Exception as e:
                print("Closing client:")
                print(e)
                client.close()
                return False

    def exec_command(self, command):
        switcher = {
            "p": playPauseVideo,
            "s": stopVideo,
            "q": exit,
            "up": up,
            "down": down,
            "left": left,
            "right": right,
            "select": select,
            "back": back,
            "ff": fastForward,
            "rewind": rewind
        }
        # Get the function from switcher dictionary
        command_func = switcher.get(command, None)

        if command_func != None:
            #print("Executing command: " + command)
            command_func(None)
        else:
            print("Unknown command: " + command)

server_obj = ThreadedServer('', 65432)

server_thread = threading.Thread(target = server_obj.listen,args = ())
server_thread.daemon = True
server_thread.start()


'''
try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    sys.exit(0)
'''


panel_images = []

class Panel(object):
    def __init__(self, title, image_file, video_file, tk_container, grid_coords):
        self.title = title
        self.image_file = image_file
        self.video_file = video_file

        img = Image.open(image_file)
        img_width = img.size[0]
        img_height = img.size[1]
        img = img.resize((int(img_width * panel_scale), int(img_height * panel_scale)), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        self.image = img

        global panel_images
        panel_images.append(img)

        self.tk_object = tk.Label(tk_container, image=self.image, width=int(img_width * panel_scale + highlight_thickness), height=int(img_height * panel_scale + highlight_thickness))

        self.grid_coords = grid_coords

class PanelGrid(object):
    def __init__(self, num_rows, num_cols, start_row, start_col, containing_frame, media_dir, images_dir):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.start_row = start_row
        self.start_col = start_col
        self.media_dir = media_dir
        self.images_dir = images_dir
        self.containing_frame = containing_frame
        self.grid = []
        self.selected_panel = [0, 0]
        self.scroll_row = 0

        curr_row = 0
        curr_col = 0

        for filename in sorted(os.listdir(media_dir)):
            if filename.endswith(".mp4") or filename.endswith(".mkv") or os.path.isdir(os.path.join(media_dir, filename)): 
                title = filename
                video_file = None

                # If the media file is not a directory, strip the file suffix and get the video source file
                if not os.path.isdir(os.path.join(media_dir, filename)):
                    title = title[:-4]
                    video_file = os.path.join(media_dir, filename)
                # Create the image filename
                image_file = os.path.join(images_dir, title + ".jpg")
                # If there is no image filename for the media, skip it
                if not os.path.exists(image_file):
                    print(image_file)
                    print("Image not found for: " + title + ". Skipping...")
                    continue
                # Add a new row to the 2D grid when we're at the first column
                if curr_col == 0:
                    new_row = []
                    self.grid.append(new_row)

                label_coords = [curr_row, curr_col]
                # Add a new panel to the grid
                self.grid[curr_row].append(Panel(title, image_file, video_file, self.containing_frame, label_coords))

                # Iterate through columns, if we are out of columns go to next row
                curr_col += 1
                if curr_col == self.num_cols:
                    curr_col = 0
                    curr_row += 1

                print(title)


    def get_title(self):
        return self.panel_from_coords(self.selected_panel[0], self.selected_panel[1]).title

    def get_video(self):
        return self.panel_from_coords(self.selected_panel[0], self.selected_panel[1]).video_file

    def move_selection(self, delt_row, delt_col):
        selected_row = self.selected_panel[0]
        selected_col = self.selected_panel[1]

        new_row = selected_row + delt_row
        new_col = selected_col + delt_col

        if new_col >= self.num_cols or new_col < 0:
            return
        elif new_row >= self.num_rows + self.scroll_row:
            if self.scroll_row >= len(self.grid) - self.num_rows:
                return
            self.scroll_down()
        elif new_row < self.scroll_row:
            if self.scroll_row <= 0:
                return
            self.scroll_up()
        
        print("Moving selection from: (" + str(selected_row) + ", " + str(selected_col) + ") to: (" + str(new_row) + ", " + str(new_col) + ")")
        self.selected_panel = [new_row, new_col]

        self.grid[selected_row][selected_col].tk_object.config(background="#000000")
        self.grid[self.selected_panel[0]][self.selected_panel[1]].tk_object.config(background=highlight_color)

        #global title_info
        #title_info.config(text=self.get_title())
        global details_title
        details_title.set(self.get_title())
    

    def draw_grid(self):
        start_row = self.scroll_row
        end_row = self.scroll_row + self.num_rows

        for row_idx, row in enumerate(self.grid[start_row:end_row]):
            for col_idx, panel in enumerate(row):
                grid_coords = self.panel_to_grid_coords(row_idx + self.scroll_row, col_idx)

                #print("Gridding " + panel.title + " to " + str(grid_coords))

                panel.tk_object.grid(row=grid_coords[0], column=grid_coords[1], padx=title_padding, pady=title_padding, sticky=N+S+E+W)
                panel.tk_object.config(background="#000000")

        self.grid[self.selected_panel[0]][self.selected_panel[1]].tk_object.config(background=highlight_color)

    def clean_grid(self):
        start_row = self.scroll_row
        end_row = self.scroll_row + self.num_rows

        for row_idx, row in enumerate(self.grid[start_row:end_row]):
            for col_idx, panel in enumerate(row):
                panel.tk_object.grid_forget()

    def scroll_down(self):
        self.clean_grid()

        self.scroll_row += 1

        self.grid[self.selected_panel[0]][self.selected_panel[1]].tk_object.config(background="#000000")

        self.draw_grid()

    def scroll_up(self):
        self.clean_grid()

        self.scroll_row -= 1

        self.grid[self.selected_panel[0]][self.selected_panel[1]].tk_object.config(background="#000000")

        self.draw_grid()
        
    """ Give this function the grid coords WITH ROW SCROLL SHIFT (not the translated GUI coords) """
    def panel_from_coords(self, row, col):
        #print("Index: " + str((self.num_cols - self.start_col) * (row) + (col)))
        #print("Coords: (" + str(row) + ", " + str(col) + "); Index: " + str((self.num_cols - self.start_col) * (row) + (col)))
        return self.grid[row][col]

    """ The grid coordinates are stored at the 0 indices of row, column but the actual GUI grid coordinates are shifted
        by start_row, start_col respectively.  So this function converts row, column coordinates to GUI grid coordinates. 

        Example: The panel at grid[0][0] will actually be on the GUI as tk.grid(self.start_row, self.start_col, ...) """
    def panel_to_grid_coords(self, panel_grid_row, panel_grid_col):
        return (self.start_row + panel_grid_row - self.scroll_row, self.start_col + panel_grid_col)

    def destroy(self):
        for row in self.grid:
            for panel in row:
                panel.tk_object.grid_forget()

class ShowManager:
    def __init__(self, containing_frame, show_dir):
        self.containing_frame = containing_frame
        self.show_dir = show_dir

        global frame

        #for child in frame.winfo_children():
        #    print(child)

        self.list_frame = tk.Frame(frame)
        self.list_frame.config(background="#000000")

        # List of three-tuples containing season name, tk object, and list of episode filenames
        self.season_labels = []

        for filename in sorted(os.listdir(self.show_dir)):
            subdir = os.path.join(self.show_dir, filename)
            if os.path.isdir(subdir): 
                season = filename

                episodes_list = []
                for episode in os.listdir(subdir):
                    if episode.endswith(".mp4") or episode.endswith(".mkv"):
                        episode_label = tk.Label(self.list_frame, text=episode[:-4], borderwidth=5, relief="solid")
                        episode_label.config(font=("Calibri", 24))
                        episode_label.config(background="#000000")
                        episode_label.config(foreground="#FFFFFF")

                        episodes_list.append((episode[:-4], episode_label, os.path.join(subdir, episode)))
                        #print(episodes_list[-1])

                
                season_label = tk.Label(self.list_frame, text=season, borderwidth=5, relief="solid")
                season_label.config(font=("Calibri", 32))
                season_label.config(background="#000000")
                season_label.config(foreground="#FFFFFF")

                self.season_labels.append((season, season_label, episodes_list))

                #print(season)

        self.selected_season_idx = 0

    def draw_seasons(self):
        self.list_frame.pack(side='right', fill=tk.BOTH, expand=True)

        #self.list_frame.pack_propagate(0)

        for season_idx, season_label in enumerate(self.season_labels):
            if season_idx == self.selected_season_idx:
                season_label[1].config(background="#FFFFFF")
                season_label[1].config(foreground="#000000")

            season_label[1].pack(side='top', fill=tk.X)

    def move_season_selection(self, delta_row):
        new_selection_idx = self.selected_season_idx + delta_row

        if new_selection_idx >= len(self.season_labels) or new_selection_idx < 0:
            return

        curr_selected_label = self.season_labels[self.selected_season_idx][1]
        curr_selected_label.config(background="#000000")
        curr_selected_label.config(foreground="#FFFFFF")

        self.selected_season_idx = new_selection_idx

        new_selected_label = self.season_labels[self.selected_season_idx][1]
        new_selected_label.config(background="#FFFFFF")
        new_selected_label.config(foreground="#000000")

    def select_season(self):
        self.destroy_seasons()
        
        self.draw_episodes()

    def destroy_seasons(self):
        for season_label in self.season_labels:
            season_label[1].pack_forget()


    def draw_episodes(self):
        self.selected_episode_idx = 0

        season_title = self.season_labels[self.selected_season_idx][0]
        episodes_list = self.season_labels[self.selected_season_idx][2]

        self.season_title_label = tk.Label(self.list_frame, text=season_title, borderwidth=5, relief="solid")
        self.season_title_label.config(font=("Calibri", 32))
        self.season_title_label.config(background="#444444")
        self.season_title_label.config(foreground="#FFFFFF")
        self.season_title_label.pack(side='top', fill=tk.X)
        
        for episode_idx, episode_tuple in enumerate(episodes_list):
            if episode_idx == self.selected_episode_idx:
                episode_tuple[1].config(background="#FFFFFF")
                episode_tuple[1].config(foreground="#000000")
            else:
                episode_tuple[1].config(background="#000000")
                episode_tuple[1].config(foreground="#FFFFFF")

            episode_tuple[1].pack(side='top', fill=tk.X)

    def move_episode_selection(self, delta_row):
        new_selection_idx = self.selected_episode_idx + delta_row

        episodes_list = self.season_labels[self.selected_season_idx][2]

        if new_selection_idx >= len(episodes_list) or new_selection_idx < 0:
            return

        curr_selected_label = episodes_list[self.selected_episode_idx][1]
        curr_selected_label.config(background="#000000")
        curr_selected_label.config(foreground="#FFFFFF")

        self.selected_episode_idx = new_selection_idx

        new_selected_label = episodes_list[self.selected_episode_idx][1]
        new_selected_label.config(background="#FFFFFF")
        new_selected_label.config(foreground="#000000")

    def select_episode(self):
        self.destroy_episodes()
        
        self.list_frame.pack_forget()

    def get_episode(self):
        return self.season_labels[self.selected_season_idx][2][self.selected_episode_idx][2]

    def destroy_episodes(self):
        self.season_title_label.pack_forget()

        episodes_list = self.season_labels[self.selected_season_idx][2]
        for episode_tuple in episodes_list:
            episode_tuple[1].pack_forget()

    def destroy(self):
        for season_label in self.season_labels:
            season_label[1].pack_forget()

        self.list_frame.pack_forget()

class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master=master
        pad=3
        self._geom='200x200+0+0'
        # This makes it fullscreen (I think)
        master.geometry("{0}x{1}+0+0".format(master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        master.bind('<Escape>',self.toggle_geom)
    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom



root=tk.Tk()
app=FullScreenApp(root)

frame = Frame(root)
frame.config(background="#000000")
#frame.grid()
frame.pack(fill=tk.BOTH, expand=1)


#initialize grid
grid = Frame(frame)
grid.config(background="#000000")
grid.pack()
#grid.grid(sticky=N+S+E+W, column=0, row=0)

'''
#example values
for x in range(5):
    for y in range(5):
        btn = Button(grid)
        btn.grid(column=x, row=y, sticky=N+S+E+W)
'''

root.wm_title("LUSIO")
root.config(background="#000000")
root.attributes('-fullscreen', True)

#player = vlc.MediaPlayer("bloopers.mp4")
player = None
playing = False

curr_show_manager = None

# Where functions used to be

# binding keyboard shortcuts to buttons on window
root.bind("<p>", playPauseVideo)
root.bind("<s>", stopVideo)
root.bind("<q>", exit)
root.bind('<Up>', up)
root.bind('<Down>', down)
root.bind('<Left>', left)
root.bind('<Right>', right)
root.bind('<space>', select)
root.bind('<Escape>', back)

#media_dir = 'D:\VIDEOS\MOVIES'
media_dir = '/media/pi/Samsung_T5/MOVIES'
images_dir = 'titles'

panel_grid = []
panel_scale = .38
title_padding = 3
details_pane = None
details_pane_bg = "#333333"
title_info = None
details_pane_width = 450
highlight_thickness = 8
highlight_color = "#FFFFFF"
num_rows = 3
num_cols = 6

from enum import Enum

Screens = Enum('Screens', 'MainSelect ShowSeasonSelect ShowEpisodeSelect Player')

screen = Screens.MainSelect

titles_grid = PanelGrid(num_rows, num_cols, 0, 2, grid, media_dir, 'titles')

details_title = StringVar()


def draw_details_pane():

    global details_pane
    details_pane = Frame(frame, width=details_pane_width)
    details_pane.config(background=details_pane_bg)
    #details_pane.grid(row=0, column=0, columnspan=2, rowspan=num_rows, sticky=N+S+E+W)
    details_pane.pack(side='left', fill=tk.Y, anchor='w')
    
    details_pane.pack_propagate(0)

    global titles_grid
    global details_title
    details_title.set(titles_grid.get_title())

    global title_info
    title_info = Message(details_pane, textvariable=details_title, width=details_pane_width)
    title_info.config(font=("Calibri", 36))
    title_info.config(background=details_pane_bg)
    title_info.config(fg="#FFFFFF")
    title_info.pack(side="top", fill='both')


def draw_titles_grid():

    grid.pack(side='right', fill=tk.Y)
    
    global titles_grid
        
    titles_grid.containing_frame = grid
    titles_grid.draw_grid()

    #print("Setting: (" + str(selected_panel[0]) + ", " + str(selected_panel[1]) + ") to WHITE")


draw_details_pane()

draw_titles_grid()



#b = Button(grid, text="QUIT", command=exit)
#b.grid(column=int(num_cols/2), row=0)


#player.set_fullscreen(True)
#player.play()
#playing = True



root.mainloop()

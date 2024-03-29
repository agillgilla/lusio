#!/usr/bin/python3

import tkinter as tk
from tkinter import *
from PIL import ImageTk, Image

# VLC NEEDS TO BE INSTALLED
import vlc

import os
import json
import socket
import subprocess
import sys
import threading
import time

import pickledb

import examples_tkvlc

import webserver


_isLinux = sys.platform.startswith('linux')
force_vlc = False

if _isLinux:
    time.sleep(10)

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

import logging

logging.basicConfig(filename='logfile.log', level=logging.DEBUG, format='[%(levelname)s]: %(asctime)s - %(message)s')

logging.info("Running now...")

MEDIA_INFO_FILENAME = 'media_info.json'
CONFIG_FILENAME = 'config.json'
MEDIA_DIRNAME = 'MOVIES'
DEFAULT_POSTER_FILE = 'default_poster.jpg'

overlay_program_dir = None
overlay_program_path = None

# Variable used to know if we are using omxplayer of vlc (for mp4 files)
use_omx = (not force_vlc) and _isLinux
if use_omx:
    from omxplayer.player import OMXPlayer
    from omxplayer.player import OMXPlayerDeadError
    from pathlib import Path
    
    overlay_program_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'overlay')
    overlay_program_path = os.path.join(overlay_program_dir, 'overlay')

# Variable used to know if we are currently playing something with omxplayer
using_omx = False
# Variable used to know what video we are currently playing
curr_video = None
# Variable for reference to video times key value store
times_db = None
# Dictionary containing keys of media titles to info about the media
media_info_dict = {}
# Process handle for OMX position overlay
overlay_process = None
# Dictionary of configuration values
config_json = {
    "alsa_audio": False
}

def heartbeat(*unused):
    logging.debug("Heartbeat!")

def play_pause_video(event):
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            if omx_player.is_playing():
                omx_player.pause()
                show_pause_overlay(omx_player.position(), omx_player.duration())
            else:
                hide_pause_overlay()
                omx_player.play()
        else:
            vlc_player.OnPause()

def stop_video(event):
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            omx_player.stop()
        else:
            vlc_player.OnStop()

def fast_forward():
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            omx_player.rate(2)
        else:
            vlc_player.player.set_rate(2)

def step_forward(step_size):
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            omx_player.seek(step_size)
        else:
            vlc_player.OnSkip(step_size)

def step_backward(step_size):
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            omx_player.seek(-step_size)
        else:
            vlc_player.OnSkip(-step_size)

def send_omx_info_cmd():
    omx_player.action(5)

def toggle_info(*unused):
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            send_omx_info_cmd()
            threading.Timer(5.0, send_omx_info_cmd).start()
        else:
            print("Info not supported on vlc yet")

def exit(*unused):
    if screen == Screens.Search and curr_search_screen != None and curr_search_screen.typing:
        return

    save_video_position()
    if vlc_player != None:
        vlc_player.OnDestroy()
    global using_omx
    if using_omx:
        hide_pause_overlay()
        omx_player.quit()
    root.destroy()

from subprocess import call

def power(event):
    save_video_position()
    if _isLinux:
        call("sudo shutdown -h now", shell=True)
    else:
        print("Power down only supported on Linux.")

def up(event):
    if screen == Screens.MainSelect:
        if selecting_category:
            categories_manager.move_selection(-1)
        else:
            titles_grid.move_selection(-1, 0)
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.move_season_selection(-1)
    elif screen == Screens.ShowEpisodeSelect:
        curr_show_manager.move_episode_selection(-1)
    elif screen == Screens.PlaybackDialog:
        curr_playback_dialog.move_selection(-1)
    elif screen == Screens.Search:
        if not curr_search_screen.typing:
            curr_search_screen.results_grid.move_selection(-1, 0)

def down(event):
    if screen == Screens.MainSelect:
        if selecting_category:
            categories_manager.move_selection(1)
        else:
            titles_grid.move_selection(1, 0)
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.move_season_selection(1)
    elif screen == Screens.ShowEpisodeSelect:
        curr_show_manager.move_episode_selection(1)
    elif screen == Screens.PlaybackDialog:
        curr_playback_dialog.move_selection(1)
    elif screen == Screens.Search:
        if not curr_search_screen.typing:
            curr_search_screen.results_grid.move_selection(1, 0)

def left(event):
    if screen == Screens.MainSelect:
        if not selecting_category:
            titles_grid.move_selection(0, -1)
    elif screen == Screens.Search:
        if not curr_search_screen.typing:
            curr_search_screen.results_grid.move_selection(0, -1)

def right(event):
    if screen == Screens.MainSelect:
        global selecting_category
        if selecting_category:
            selecting_category = False
            categories_manager.set_inactive()
            titles_grid.update_details_title()
        else:
            titles_grid.move_selection(0, 1)
    elif screen == Screens.Search:
        if not curr_search_screen.typing:
            curr_search_screen.results_grid.move_selection(0, 1)

def select(event):
    global screen
    global vlc_player
    global curr_playback_dialog
    global curr_show_manager
    
    if screen == Screens.MainSelect:
        if selecting_category:
            return
        
        titles_grid.destroy()
        
        
        #for child in frame.winfo_children():
        #    child.destroy()
        
        video_file = titles_grid.get_video()

        # Movie
        if video_file != None:
            if times_db.exists(video_file):
                grid.pack_forget()

                curr_playback_dialog = PlaybackDialog(video_file, False)
                curr_playback_dialog.draw()

                screen = Screens.PlaybackDialog
            else:
                details_pane.pack_forget()
                #details_pane.destroy()
                grid.pack_forget()

                play_video(video_file)
        # TV Show    
        else:
            # We need to destroy and recreate the details pane??? WHY??
            grid.pack_forget()

            show_dir = os.path.join(media_dir, titles_grid.get_title())
            
            curr_show_manager = ShowManager(grid, show_dir)
            curr_show_manager.draw_seasons()

            screen = Screens.ShowSeasonSelect
    elif screen == Screens.ShowSeasonSelect:
        curr_show_manager.select_season()

        screen = Screens.ShowEpisodeSelect
    elif screen == Screens.ShowEpisodeSelect:
        video_file = curr_show_manager.get_episode()

        curr_show_manager.select_episode()

        if times_db.exists(video_file):
            grid.pack_forget()

            curr_playback_dialog = PlaybackDialog(video_file, True)
            curr_playback_dialog.draw()

            screen = Screens.PlaybackDialog

        else:
            details_pane.pack_forget()
            #details_pane.destroy()

            play_video(video_file)

    elif screen == Screens.PlaybackDialog:
        curr_playback_dialog.select()
    elif screen == Screens.Player:
        pass
        #vlc_player.stop()
    elif screen == Screens.Search:
        video_file, title = curr_search_screen.results_grid.get_selection()
        is_show = video_file == None

        if is_show:
            curr_search_screen.destroy()

            show_dir = os.path.join(media_dir, title)

            curr_show_manager = ShowManager(grid, show_dir)
            curr_show_manager.draw_seasons()

            screen = Screens.ShowSeasonSelect
        else:
            if times_db.exists(video_file):
                curr_search_screen.destroy()

                curr_playback_dialog = PlaybackDialog(video_file, False)
                curr_playback_dialog.draw()

                screen = Screens.PlaybackDialog

            else:
                curr_search_screen.destroy()
                details_pane.pack_forget()
                #details_pane.destroy()

                play_video(video_file)
        
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
        save_video_position()

        global vlc_player
        if vlc_player != None:
            vlc_player.OnDestroy()
        global using_omx
        if using_omx:
            hide_pause_overlay()
            omx_player.quit()
            using_omx = False

        #draw_details_pane()
        details_pane.pack(side='left', fill=tk.Y, anchor='w')
        draw_titles_grid()
        titles_grid.update_details_title()

        screen = Screens.MainSelect
    elif screen == Screens.PlaybackDialog:
        if curr_playback_dialog.is_for_show():
            curr_playback_dialog.destroy()

            curr_show_manager.draw_seasons()
            curr_show_manager.destroy_seasons()
        
            curr_show_manager.draw_episodes()

            screen = Screens.ShowEpisodeSelect
        else:
            curr_playback_dialog.destroy()

            draw_titles_grid()
            details_title.set(titles_grid.get_title())

            screen = Screens.MainSelect
    elif screen == Screens.Search:
        curr_search_screen.destroy()

        draw_titles_grid()
        details_title.set(titles_grid.get_title())

        screen = Screens.MainSelect
    elif screen == Screens.InfoDialog:
        curr_info_dialog.destroy()

        draw_titles_grid()
        details_title.set(titles_grid.get_title())
        screen = Screens.MainSelect
    elif screen == Screens.SearchInfoDialog:
        curr_info_dialog.destroy()

        curr_search_screen.show()
        
        screen = Screens.Search

def play_video(video_file, resume=False):
    global using_omx
    global times_db
    
    if use_omx and video_file.endswith(".mp4"):
        if resume:
            curr_time = times_db.get(video_file)[0]

            omx_play(video_file, start_pos=int(float(curr_time)))
        else:
            omx_play(video_file)
        using_omx = True
    else:
        global vlc_player
        vlc_player = examples_tkvlc.Player(frame, video=video_file, show_scrubber=False)
        vlc_player.OnPlay()

        using_omx = False

    global curr_video
    curr_video = video_file

    global screen
    screen = Screens.Player

    if resume:
        curr_time = times_db.get(video_file)[0]

        if not using_omx:
            vlc_player.SetTime(int(curr_time))

def search(*unused, query=None):
    global screen
    global curr_search_screen

    if query is None:
        # Command just sent on GUI (either to open search screen or search again)
        if screen == Screens.MainSelect:
            curr_search_screen = SearchScreen()
            curr_search_screen.draw()

            screen = Screens.Search
        elif screen == Screens.Search and not _isLinux and not curr_search_screen.typing:
            curr_search_screen.start_typing()
    else:
        # Command sent from app with query
        if screen == Screens.MainSelect:
            
            curr_search_screen = SearchScreen()
            curr_search_screen.draw()

            screen = Screens.Search

            curr_search_screen.typing = False
            curr_search_screen.entry_string.set(query)
            curr_search_screen.search()
            
            root.focus()
        elif screen == Screens.Search:
            curr_search_screen.typing = False
            curr_search_screen.entry_string.set(query)
            curr_search_screen.search()
            
            root.focus()

def media_info(event):
    global screen
    global curr_info_dialog

    if screen == Screens.MainSelect:
        grid.pack_forget()

        curr_info_dialog = InfoDialog(titles_grid.get_title())
        curr_info_dialog.draw()
        
        screen = Screens.InfoDialog
    elif screen == Screens.Search:
        curr_search_screen.hide()

        video_file, title = curr_search_screen.results_grid.get_selection()

        curr_info_dialog = InfoDialog(title)
        curr_info_dialog.draw()

        screen = Screens.SearchInfoDialog

def toggle_subtitles(event):
    if screen == Screens.Player:
        global using_omx
        if using_omx:
            pass
            #logging.debug("Subtitles:", omx_player.list_subtitles())
            
def enter(*unused):
    global screen

    if screen == Screens.Search:
        curr_search_screen.search()
        curr_search_screen.typing = False
        root.focus()

def load_config():
    global config_json
    try:
        with open(CONFIG_FILENAME) as f:
            config_json = json.load(f)
    except FileNotFoundError:
        logging.info(f"Config file {CONFIG_FILENAME} doesn't exist! Creating one with default values...")
        
        with open(CONFIG_FILENAME, 'w') as f:
            json.dump(config_json, f)


def init_times_db():
    global times_db
    times_db = pickledb.load('times.db', True)

def init_info_dict():
    global media_info_dict

    try:
        with open(MEDIA_INFO_FILENAME, 'r+') as info_json_file:
            media_info_dict = json.load(info_json_file)
    except FileNotFoundError as fnfe:
        logging.error("The JSON info file wasn't found:")
        logging.error(fnfe)

def omx_play(file, start_pos=None):
    file_path = Path(file)
    global omx_player

    args = []

    if start_pos is not None:
        args += ['--pos', time.strftime('%H:%M:%S', time.gmtime(start_pos))]

    if config_json["alsa_audio"]:
        args += ['-o', 'alsa']

    if len(args) == 0:
        omx_player = OMXPlayer(file_path)
    else:
        omx_player = OMXPlayer(file_path, args=args)

def save_video_position():
    if screen == Screens.Player:
        global using_omx
        global times_db
        curr_time = None
        if using_omx:
            try:
                curr_time = omx_player.position()
                duration = omx_player.duration()
            except OMXPlayerDeadError as oplde:
                if times_db.exists(curr_video):
                    times_db.rem(curr_video)
                return
        else:
            curr_time_millis = vlc_player.GetTime()
            curr_time = curr_time_millis // 1000
            duration = vlc_player.GetDuration() // 1000

        times_db.set(curr_video, (str(curr_time), duration))

def show_pause_overlay(curr_seconds, total_seconds):
    global overlay_process
    if overlay_process == None:
        overlay_process = subprocess.Popen([str(overlay_program_path), str(int(curr_seconds)), str(int(total_seconds))], cwd=overlay_program_dir)

def hide_pause_overlay():
    global overlay_process
    if overlay_process != None:
        overlay_process.terminate()
        overlay_process.wait()
        overlay_process = None

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
                
class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

        self.command_switch = {
            # H is for heartbeat!
            "h": heartbeat,
            "p": play_pause_video,
            "s": search,
            "q": exit,
            "i": toggle_info,
            "c": toggle_subtitles,
            "up": up,
            "down": down,
            "left": left,
            "right": right,
            "select": select,
            "back": back,
            "power": power,
            "m": media_info,
            #"ff": fastForward,
            #"rewind": rewind
        }

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
                logging.error("Closing client:")
                logging.error(e)
                import traceback
                print(traceback.format_exc())
                client.close()
                return False

    def exec_command(self, command):
        # Get the function from command switcher dictionary
        command_func = self.command_switch.get(command, None)

        if command_func != None:
            #print("Executing command: " + command)
            command_func(None)
        else:
            if "sf" in command:
                step_size = int(command.split(':')[1])
                step_forward(step_size)
            elif "sb" in command:
                step_size = int(command.split(':')[1])
                step_backward(step_size)
            elif "f" in command:
                query = command.split(':')[1]
                search(query=query)
            else:
                print("Unknown command: " + command)

server_obj = ThreadedServer('', 65432)

server_thread = threading.Thread(target = server_obj.listen,args = ())
server_thread.daemon = True
server_thread.start()

commandDict = {
    "p": play_pause_video,
    "s": search,
    "q": exit,
    "i": toggle_info,
    "c": toggle_subtitles,
    "up": up,
    "down": down,
    "left": left,
    "right": right,
    "select": select,
    "back": back,
    "power": power,
    "sf": step_forward,
    "sb": step_backward,
    "search": search,
}

webserver.setCommandDict(commandDict)
flask_server_thread = threading.Thread(target = webserver.start,args = ())
flask_server_thread.daemon = True
flask_server_thread.start()

'''
try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    sys.exit(0)
'''

def _create_circle_arc(self, x, y, r, **kwargs):
    if "start" in kwargs and "end" in kwargs:
        kwargs["extent"] = kwargs.pop("end") - kwargs["start"]
    return self.create_arc(x-r, y-r, x+r, y+r, **kwargs)
tk.Canvas.create_circle_arc = _create_circle_arc


def get_img_path_from_title(title):
    image_file = os.path.join(images_dir, title + ".jpg")
    if not os.path.exists(image_file):
        return DEFAULT_POSTER_FILE
    return image_file


panel_images = {}

class Panel(object):
    def __init__(self, title, image_file, video_file, tk_container, grid_coords):
        self.title = title
        self.image_file = image_file
        self.video_file = video_file

        global panel_images
        if title in panel_images:
            img = panel_images[title][0]
            img_width = img.size[0]
            img_height = img.size[1]
            panel_scale = float(panel_scaled_img_width) / img_width
            self.image = panel_images[title][1]
        else:
            img = Image.open(image_file)
            img_width = img.size[0]
            img_height = img.size[1]
            #img = img.resize((int(img_width * panel_scale), int(img_height * panel_scale)), Image.ANTIALIAS)
            panel_scale = float(panel_scaled_img_width) / img_width
            img_resized = img.resize((int(panel_scaled_img_width), int(img_height * panel_scale)), Image.ANTIALIAS)
            photo_img = ImageTk.PhotoImage(img_resized)
            self.image = photo_img

            panel_images[title] = (img, photo_img)


        self.tk_object = tk.Label(tk_container, image=self.image, width=int(img_width * panel_scale + highlight_thickness), height=int(img_height * panel_scale + highlight_thickness))

        self.grid_coords = grid_coords

class PanelGrid(object):
    def __init__(self, num_rows, num_cols, start_row, start_col, containing_frame, media_dir, category=None):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.start_row = start_row
        self.start_col = start_col
        self.media_dir = media_dir
        self.containing_frame = containing_frame
        self.grid = []
        self.selected_panel = [0, 0]
        self.scroll_row = 0

        curr_row = 0
        curr_col = 0

        for filename in sorted(os.listdir(media_dir), key=lambda x : x[:-4] if (x.endswith(".mp4") or x.endswith(".mkv")) else x):
            if filename.endswith(".mp4") or filename.endswith(".mkv") or os.path.isdir(os.path.join(media_dir, filename)):
                title = filename
                video_file = None

                # If the media file is not a directory, strip the file suffix and get the video source file
                if not os.path.isdir(os.path.join(media_dir, filename)):
                    title = title[:-4]
                    video_file = os.path.join(media_dir, filename)
                # Strip x265 suffix for files stored on computer
                if title.endswith(' x265'):
                    img_title = title[:-5]
                else:
                    img_title = title

                # If we are loading a specific category and the media isn't in it, then skip it.
                if category != None and title not in category:
                    continue


                image_file = get_img_path_from_title(img_title)
                # Create the image filename
                #image_file = os.path.join(images_dir, img_title + ".jpg")
                # If there is no image filename for the media, skip it
                if not os.path.exists(image_file):
                    print(image_file)
                    #image_file = DEFAULT_POSTER_FILE
                    print("Image not found for: " + img_title + ". Using default...")
                    #continue
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

                #print(title)


    def get_title(self):
        return self.panel_from_coords(self.selected_panel[0], self.selected_panel[1]).title

    def get_video(self):
        return self.panel_from_coords(self.selected_panel[0], self.selected_panel[1]).video_file

    def move_selection(self, delt_row, delt_col):
        selected_row = self.selected_panel[0]
        selected_col = self.selected_panel[1]

        new_row = selected_row + delt_row
        new_col = selected_col + delt_col

        # This screws up the scrolling for bottom row (if not filled)
        #if not self.test_panel_coords(new_row, new_col):
        #    return

        #print(f"New: {new_row}, {new_col}")
        #translated = self.panel_to_grid_coords(new_row, new_col)
        #print(f"Translated: {translated[0]}, {translated[1]}")

        if new_col >= self.num_cols:
            return
        elif new_col < 0:
            global selecting_category
            selecting_category = True
            categories_manager.set_active()
            return
        elif (new_row == len(self.grid) - 1) and (new_col >= len(self.grid[len(self.grid) - 1])):
            # Last row isn't fully filled
            if selected_row < len(self.grid) - 1:
                # We're not in the bottom row yet
                new_col = len(self.grid[len(self.grid) - 1]) - 1
                if new_row >= self.num_rows + self.scroll_row:
                    self.scroll_down()
            else:
                # We're already in the bottom row
                return
        elif new_row >= self.num_rows + self.scroll_row:
            if self.scroll_row >= len(self.grid) - self.num_rows:
                return
            self.scroll_down()
        elif new_row < self.scroll_row:
            if self.scroll_row <= 0:
                return
            self.scroll_up()
        
        #print("Moving selection from: (" + str(selected_row) + ", " + str(selected_col) + ") to: (" + str(new_row) + ", " + str(new_col) + ")")
        self.selected_panel = [new_row, new_col]

        self.grid[selected_row][selected_col].tk_object.config(background="#000000")
        self.grid[self.selected_panel[0]][self.selected_panel[1]].tk_object.config(background=highlight_color)

        #global title_info
        #title_info.config(text=self.get_title())
        self.update_details_title()

    def update_details_title(self):
        global details_title
        details_title.set(self.get_title())

    def draw_grid(self):
        start_row = self.scroll_row
        end_row = self.scroll_row + self.num_rows

        for row_idx, row in enumerate(self.grid[start_row:end_row]):
            for col_idx, panel in enumerate(row):
                grid_coords = self.panel_to_grid_coords(row_idx + self.scroll_row, col_idx)

                #print("Gridding " + panel.title + " to " + str(grid_coords))
                #print("start_row: {}, panel_grid_row: {}, scroll_row: {}".format(self.start_row, row_idx + self.scroll_row, self.scroll_row))

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

    """ Tests if panel coordinates map to valid grid coordinates.  Returns True of they are valid and false otherwise. """
    def test_panel_coords(self, panel_grid_row, panel_grid_col):
        return panel_grid_row < len(self.grid) and panel_grid_col < len(self.grid[panel_grid_row])

    def destroy(self):
        for row in self.grid:
            for panel in row:
                panel.tk_object.grid_forget()

class SearchGrid(object):
    def __init__(self, num_rows, num_cols, start_row, start_col, containing_frame, media_dir):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.start_row = start_row
        self.start_col = start_col
        self.media_dir = media_dir
        self.containing_frame = containing_frame
        self.grid = []
        self.selected_panel = [0, 0]
        self.scroll_row = 0

    def search(self, query):
        curr_row = 0
        curr_col = 0

        results = search_media(query)

        for result in results:
            # Returns list of three-tuples containing show name (if episode), title, and filename (if not a show)
            show_name = result[0]
            title = result[1]
            video_file = result[2]

            image_file = None

            # Create the image filename
            if show_name != None:
                image_file = get_img_path_from_title(show_name)
            else:            
                image_file = get_img_path_from_title(title)

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

                #print(title)

        if len(results) > 0:
            global details_title
            details_title.set(self.get_title())

    def get_title(self):
        return self.panel_from_coords(self.selected_panel[0], self.selected_panel[1]).title

    def get_video(self):
        return self.panel_from_coords(self.selected_panel[0], self.selected_panel[1]).video_file

    """ Returns two-tuple where first value is video filepath if the selection isn't a show (if it is a show, it is none).  Second value is title."""
    def get_selection(self):
        return (self.get_video(), self.get_title())

    def move_selection(self, delt_row, delt_col):
        selected_row = self.selected_panel[0]
        selected_col = self.selected_panel[1]

        new_row = selected_row + delt_row
        new_col = selected_col + delt_col

        if not self.test_panel_coords(new_row, new_col):
            return

        if new_col >= self.num_cols or new_col < 0:
            return
        elif (new_row == len(self.grid) - 1) and (new_col >= len(self.grid[len(self.grid) - 1])):
            # Last row isn't fully filled
            if selected_row < len(self.grid) - 1:
                # We're not in the bottom row yet
                new_col = len(self.grid[len(self.grid) - 1]) - 1
                if new_row >= self.num_rows + self.scroll_row:
                    self.scroll_down()
            else:
                # We're already in the bottom row
                return
        elif new_row >= self.num_rows + self.scroll_row:
            if self.scroll_row >= len(self.grid) - self.num_rows:
                return
            self.scroll_down()
        elif new_row < self.scroll_row:
            if self.scroll_row <= 0:
                return
            self.scroll_up()
        
        #print("Moving selection from: (" + str(selected_row) + ", " + str(selected_col) + ") to: (" + str(new_row) + ", " + str(new_col) + ")")
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
                #print("start_row: {}, panel_grid_row: {}, scroll_row: {}".format(self.start_row, row_idx + self.scroll_row, self.scroll_row))

                panel.tk_object.grid(row=grid_coords[0], column=grid_coords[1], padx=title_padding, pady=title_padding)#, sticky=N+S+E+W)
                panel.tk_object.config(background="#000000")

        if len(self.grid) > 0 and len(self.grid[0]) > 0:
            self.grid[self.selected_panel[0]][self.selected_panel[1]].tk_object.config(background=highlight_color)

    def clean_grid(self):
        start_row = self.scroll_row
        end_row = self.scroll_row + self.num_rows

        for row_idx, row in enumerate(self.grid[start_row:end_row]):
            for col_idx, panel in enumerate(row):
                panel.tk_object.grid_forget()

    def reset_grid(self):
        self.grid = []
        self.selected_panel = [0, 0]
        self.scroll_row = 0

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

    """ Tests if panel coordinates map to valid grid coordinates.  Returns True of they are valid and false otherwise. """
    def test_panel_coords(self, panel_grid_row, panel_grid_col):
        return panel_grid_row < len(self.grid) and panel_grid_col < len(self.grid[panel_grid_row])

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

        self.episodes_per_page = 20
        self.episode_scroll_num = 0

        self.list_frame = tk.Frame(frame)
        self.list_frame.config(background="#000000")
        #self.list_frame.grid_rowconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(1, weight=1)

        # List of three-tuples containing season name, tk object, and list of episode filenames
        self.season_labels = []

        for filename in sorted(os.listdir(self.show_dir), key=lambda filename: '{:02d}'.format(int(filename.split('Season ')[1])) if ('Season ' in filename) else filename):
            subdir = os.path.join(self.show_dir, filename)
            if os.path.isdir(subdir): 
                season = filename

                episodes_list = []
                for episode in sorted(os.listdir(subdir)):
                    if episode.endswith(".mp4") or episode.endswith(".mkv"):
                        episode_label = tk.Label(self.list_frame, text=episode[:-4], borderwidth=5, relief="solid", anchor='w', padx=show_padding)
                        episode_label.config(font=("Calibri", 24))
                        episode_label.config(background="#000000")
                        episode_label.config(foreground="#FFFFFF")

                        #print(episodes_list[-1])

                        if times_db.exists(os.path.join(subdir, episode)):

                            times = times_db.get(os.path.join(subdir, episode))
                            percent_watched = float(times[0]) / float(times[1])
                            
                            end_degrees = 90 + percent_watched * 360

                            canvas_size = screen_height / 36
                            canvas = tk.Canvas(self.list_frame, width=canvas_size, height=canvas_size, borderwidth=0, highlightthickness=0, bg="black")
                            canvas.create_circle_arc(canvas_size / 2, canvas_size / 2, canvas_size / 2, fill="white", outline="", start=90, end=end_degrees)

                            episodes_list.append((episode[:-4], episode_label, os.path.join(subdir, episode), canvas))
                        else:
                            episodes_list.append((episode[:-4], episode_label, os.path.join(subdir, episode), None))
                
                season_label = tk.Label(self.list_frame, text=season, borderwidth=5, relief="solid", anchor='w', padx=show_padding)
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

            season_label[1].grid(row=season_idx, column=0, columnspan=2, sticky=E+W)
            #season_label[1].pack(side='top', fill=tk.X)

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
        self.episode_scroll_num = 0

        self.draw_episodes()

    def destroy_seasons(self):
        for season_label in self.season_labels:
            #season_label[1].pack_forget()
            season_label[1].grid_forget()


    def draw_episodes(self):
        self.selected_episode_idx = 0

        season_title = self.season_labels[self.selected_season_idx][0]
        episodes_list = self.season_labels[self.selected_season_idx][2]

        self.season_title_label = tk.Label(self.list_frame, text=season_title, borderwidth=5, relief="solid", anchor='w', padx=show_padding)
        self.season_title_label.config(font=("Calibri", 32))
        self.season_title_label.config(background=episode_title_bg)
        self.season_title_label.config(foreground="#FFFFFF")
        #self.season_title_label.pack(side='top', fill=tk.X)
        self.season_title_label.grid(row=0, column=0, columnspan=2, sticky=E+W)
        
        curr_grid_row = 1

        for episode_idx in range(self.episode_scroll_num, min(self.episode_scroll_num + self.episodes_per_page, len(episodes_list))):
            episode_tuple = episodes_list[episode_idx]

            if episode_idx == self.selected_episode_idx:
                episode_tuple[1].config(background="#FFFFFF")
                episode_tuple[1].config(foreground="#000000")
            else:
                episode_tuple[1].config(background="#000000")
                episode_tuple[1].config(foreground="#FFFFFF")

            #episode_tuple[1].pack(side='top', fill=tk.X)
            episode_tuple[1].grid(row=curr_grid_row, column=1, sticky=E+W)

            if episode_tuple[3] is not None:
                episode_tuple[3].grid(row=curr_grid_row, column=0, padx=10)

            curr_grid_row += 1

    def move_episode_selection(self, delta_row):
        new_selection_idx = self.selected_episode_idx + delta_row

        episodes_list = self.season_labels[self.selected_season_idx][2]

        if new_selection_idx >= len(episodes_list) or new_selection_idx < 0:
            return

        if new_selection_idx >= self.episode_scroll_num + self.episodes_per_page:
            print("Scrolling down...")
            self.scroll_episodes_down()
        elif new_selection_idx < self.episode_scroll_num:
            print("Scrolling up...")
            self.scroll_episodes_up()

        curr_selected_label = episodes_list[self.selected_episode_idx][1]
        curr_selected_label.config(background="#000000")
        curr_selected_label.config(foreground="#FFFFFF")

        self.selected_episode_idx = new_selection_idx

        new_selected_label = episodes_list[self.selected_episode_idx][1]
        new_selected_label.config(background="#FFFFFF")
        new_selected_label.config(foreground="#000000")

    def scroll_episodes_down(self):
        #episodes_list = self.season_labels[self.selected_season_idx][2]

        #episodes_list[self.episode_scroll_num][1].grid_forget()
        #print("Loading: " + episodes_list[self.episode_scroll_num + self.episodes_per_page][0])
        #episodes_list[self.episode_scroll_num + self.episodes_per_page][1].pack(side='top', fill=tk.X)
        #episodes_list[self.episode_scroll_num + self.episodes_per_page][1].grid(row=self.episode_scroll_num + self.episodes_per_page, column=0, sticky=E+W)
        self.destroy_episodes()

        self.episode_scroll_num += 1

        self.draw_episodes()

    def scroll_episodes_up(self):
        #episodes_list = self.season_labels[self.selected_season_idx][2]

        #episodes_list[self.episode_scroll_num + self.episodes_per_page - 1][1].grid_forget()
        #episodes_list[self.episode_scroll_num - 1][1].pack(side='top', fill=tk.X)
        #episodes_list[self.episode_scroll_num - 1][1].grid(row=self.episode_scroll_num + 1, column=0, sticky=E+W)

        self.destroy_episodes()

        self.episode_scroll_num -= 1

        self.draw_episodes()

    def select_episode(self):
        self.destroy_episodes()
        
        self.list_frame.pack_forget()

    def get_episode(self):
        return self.season_labels[self.selected_season_idx][2][self.selected_episode_idx][2]

    def destroy_episodes(self):
        self.season_title_label.grid_forget()

        episodes_list = self.season_labels[self.selected_season_idx][2]
        for episode_tuple in episodes_list:
            episode_tuple[1].grid_forget()
            if episode_tuple[3] is not None:
                episode_tuple[3].grid_forget()

    def destroy(self):
        for season_label in self.season_labels:
            season_label[1].grid_forget()

        self.list_frame.pack_forget()

class PlaybackDialog(object):
    def __init__(self, video_file, is_show):
        self.video_file = video_file
        self.is_show = is_show

        global frame

        self.options_frame = tk.Frame(frame)
        self.options_frame.config(background="#000000")
        self.options_frame.grid_columnconfigure(0, weight=1)

        self.resume_button = tk.Label(self.options_frame, text="Resume Playback", borderwidth=5, relief="solid")
        self.resume_button.config(font=("Calibri", 24))
        self.resume_button.config(background="#000000")
        self.resume_button.config(foreground="#FFFFFF")
        self.restart_button = tk.Label(self.options_frame, text="Start From Beginning", borderwidth=5, relief="solid")
        self.restart_button.config(font=("Calibri", 24))
        self.restart_button.config(background="#000000")
        self.restart_button.config(foreground="#FFFFFF")

        self.resume_selected = True

    def draw(self):
        self.options_frame.pack(side='right', fill=tk.BOTH, expand=True)

        if self.resume_selected:
            self.resume_button.config(background="#FFFFFF")
            self.resume_button.config(foreground="#000000")
        else:
            self.restart_button.config(background="#FFFFFF")
            self.restart_button.config(foreground="#000000")
        
        self.resume_button.grid(row=0, column=0, sticky=E+W)
        self.restart_button.grid(row=1, column=0, sticky=E+W)

    def move_selection(self, delta_row):
        if self.resume_selected and delta_row > 0:
            self.resume_selected = False
            self.resume_button.config(background="#000000")
            self.resume_button.config(foreground="#FFFFFF")
            self.restart_button.config(background="#FFFFFF")
            self.restart_button.config(foreground="#000000")
        elif (not self.resume_selected) and delta_row < 0:
            self.resume_selected = True
            self.resume_button.config(background="#FFFFFF")
            self.resume_button.config(foreground="#000000")
            self.restart_button.config(background="#000000")
            self.restart_button.config(foreground="#FFFFFF")

    def reset_selection(self):
        self.resume_selected = True
        self.resume_button.config(background="#FFFFFF")
        self.resume_button.config(foreground="#000000")
        self.restart_button.config(background="#000000")
        self.restart_button.config(foreground="#FFFFFF")

    def is_for_show(self):
        return self.is_show

    def select(self):
        self.destroy()

        details_pane.pack_forget()
        #details_pane.destroy()
        grid.pack_forget()

        play_video(self.video_file, resume=self.resume_selected)

    def destroy(self):
        self.resume_button.grid_forget()
        self.restart_button.grid_forget()

        self.options_frame.pack_forget()

class InfoDialog(object):
    def __init__(self, title):
        self.title = title

        global frame

        self.info_frame = tk.Frame(frame)
        self.info_frame.config(background="#000000")
        self.info_frame.grid_columnconfigure(0, weight=1)

        if title in media_info_dict:
            self.info_exists = True

            media_info = media_info_dict[title]

            title_text = f"{media_info.get('title', '?')} ({media_info.get('year', '?')})"

            self.title_label = tk.Label(self.info_frame, text=title_text, borderwidth=5, relief="solid")
            self.title_label.config(font=("Calibri", 42))
            self.title_label.config(background="#000000")
            self.title_label.config(foreground="#FFFFFF")

            info_strip_text = f"{media_info.get('rated', '?')} | {media_info.get('runtime', '?')} | {media_info.get('genre', '?')}"

            self.info_strip = tk.Label(self.info_frame, text=info_strip_text, borderwidth=5, relief="solid")
            self.info_strip.config(font=("Calibri", 28, 'bold'))
            self.info_strip.config(background="#000000")
            self.info_strip.config(foreground="#FFFFFF")

            ratings_strip_text = f"IMDb: {media_info.get('rating_imdb', '?')}     Rotten Tomatoes: {media_info.get('rating_rotten', '?')}     Metacritic: {media_info.get('rating_meta', '?')}"

            self.ratings_strip = tk.Label(self.info_frame, text=ratings_strip_text, borderwidth=5, relief="solid")
            self.ratings_strip.config(font=("Calibri", 28, 'italic'))
            self.ratings_strip.config(background="#000000")
            self.ratings_strip.config(foreground="#FFFFFF")

            self.plot_label = Message(self.info_frame, text=media_info.get('plot', '?'), borderwidth=5, relief="solid", width=int((1 - details_pane_screen_width_fraction - .1) * screen_width))
            self.plot_label.config(font=("Calibri", 24))
            self.plot_label.config(background="#000000")
            self.plot_label.config(foreground="#FFFFFF")

            director_and_actors_text = f"Director: {media_info.get('director', '?')}\nActors: {media_info.get('actors', '?')}"

            self.director_and_actors_label = tk.Message(self.info_frame, text=director_and_actors_text, borderwidth=5, relief="solid", width=int((1 - details_pane_screen_width_fraction) * screen_width))
            self.director_and_actors_label.config(font=("Calibri", 24))
            self.director_and_actors_label.config(background="#000000")
            self.director_and_actors_label.config(foreground="#FFFFFF")

        else:
            self.info_exists = False

            self.title_label = tk.Label(self.info_frame, text="No Info", borderwidth=5, relief="solid")
            self.title_label.config(font=("Calibri", 42))
            self.title_label.config(background="#000000")
            self.title_label.config(foreground="#FFFFFF")

    def draw(self):
        self.info_frame.pack(side='right', fill=tk.BOTH, expand=True)
        
        self.title_label.grid(row=0, column=0, sticky=E+W)

        if self.info_exists:
            self.info_strip.grid(row=1, column=0, sticky=E+W, pady=(10, 0))
            self.ratings_strip.grid(row=2, column=0, sticky=E+W, pady=(10, 0))
            self.plot_label.grid(row=3, column=0, sticky=E+W, pady=(20, 0))
            self.director_and_actors_label.grid(row=4, column=0, sticky=E+W, pady=(20, 0))

    def destroy(self):
        self.title_label.grid_forget()

        if self.info_exists:
            self.info_strip.grid_forget()
            self.ratings_strip.grid_forget()
            self.plot_label.grid_forget()
            self.director_and_actors_label.grid_forget()

        self.info_frame.pack_forget()

class SearchScreen(object):
    def __init__(self):
        self.search_list_frame = tk.Frame(frame)
        self.search_list_frame.config(background="#000000")
        #for i in range(num_cols):
        #    self.search_list_frame.grid_columnconfigure(i, weight=1)

        for i in range(num_cols):
            self.search_list_frame.columnconfigure(i, weight=1, minsize=panel_scaled_img_width + title_padding*2)

        self.entry_string = StringVar()

        self.search_entry = tk.Entry(self.search_list_frame, textvariable=self.entry_string, borderwidth=5)
        self.search_entry.config(font=("Calibri", 32))
        self.search_entry.config(background="#000000")
        self.search_entry.config(foreground="#FFFFFF")
        self.search_entry.config(insertbackground="#FFFFFF")

        self.results_grid = SearchGrid(num_rows, num_cols, 1, 0, self.search_list_frame, media_dir)

        self.typing = False
        self.showing_hint = True

    def start_typing(self):
        self.search_entry.focus()
        self.typing = True

    def draw(self):
        grid.pack_forget()
        titles_grid.destroy()

        details_title.set('')

        global frame

        self.search_entry.grid(row=0, column=0, sticky=E+W, columnspan=num_cols)

        if not _isLinux:
            self.search_entry.focus()
            self.typing = True

        # List of two-tuples containing search result name and tk object
        self.search_labels = []

        """
        search_results = ['abc123']
        self.selected_result_idx = 0

        for result in sorted(search_results):
            search_label = tk.Label(self.search_list_frame, text=result, borderwidth=5, relief="solid", anchor='w', padx=show_padding)
            search_label.config(font=("Calibri", 32))
            search_label.config(background="#000000")
            search_label.config(foreground="#FFFFFF")

            self.search_labels.append((result, search_label))
        """
        #for i in range(num_cols):
        #    self.search_list_frame.columnconfigure(i, weight=1)

        #self.search_list_frame.rowconfigure(num_rows, weight=1)

        self.search_list_frame.pack(side='right', fill=tk.BOTH, expand=True)
        
        """
        for result_idx, search_label in enumerate(self.search_labels):
            if result_idx == self.selected_result_idx:
                search_label[1].config(background="#FFFFFF")
                search_label[1].config(foreground="#000000")

            search_label[1].grid(row=result_idx + 1, column=0, sticky=E+W)
        """
    def search(self):
        #self.results_grid.containing_frame = self.search_list_frame
        self.results_grid.clean_grid()
        self.results_grid.reset_grid()

        self.results_grid.search(self.entry_string.get())
        self.results_grid.draw_grid()

        self.search_entry.focus()

    def destroy(self):
        self.results_grid.destroy()

        self.search_list_frame.pack_forget()

        for search_label in self.search_labels:
            search_label[1].grid_forget()

    def hide(self):
        self.search_list_frame.pack_forget()

    def show(self):
        self.search_list_frame.pack(side='right', fill=tk.BOTH, expand=True)
            


class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master=master
        pad=3
        self._geom='200x200+0+0'
        # This makes it fullscreen (I think)
        master.geometry("{0}x{1}+0+0".format(master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        #master.bind('<Escape>',self.toggle_geom)
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


# Initialize grid
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
root.config(cursor='none')
root.attributes('-fullscreen', True)

#player = vlc.MediaPlayer("bloopers.mp4")
vlc_player = None
omx_player = None
playing = False

curr_show_manager = None

curr_playback_dialog = None

curr_search_screen = None

curr_info_dialog = None

categories_manager = None

selecting_category = False

# Where functions used to be

# binding keyboard shortcuts to buttons on window
root.bind("<p>", play_pause_video)
root.bind("<s>", search)
root.bind("<q>", exit)
root.bind('<Up>', up)
root.bind('<Down>', down)
root.bind('<Left>', left)
root.bind('<Right>', right)
root.bind('<space>', select)
root.bind('<Escape>', back)
root.bind('<i>', media_info)
root.bind('<c>', toggle_subtitles)
root.bind('<a>', lambda unused: step_backward(5))
root.bind('<d>', lambda unused: step_forward(5))
root.bind('<Return>', enter)

media_dir = None

if _isLinux:
    drive_dir = '/media/pi/'

    # Scan drives
    with os.scandir(drive_dir) as it:
        for entry in it:
            if entry.is_dir():
                # Scan drive for MOVIES folder
                with os.scandir(entry.path) as sub_it:
                    for sub_entry in sub_it:
                        if sub_entry.is_dir() and sub_entry.name == MEDIA_DIRNAME:
                            media_dir = sub_entry.path
else:
    media_dir = 'D:\\MOVIES'

if media_dir is None:
    logging.error("No media directory was found!")
    exit(1)
else:
    print(f"Using media directory: {media_dir}")


images_dir = 'posters'
logo_image_file = os.path.join('logo', 'lusio_logo.jpg')
tk_logo_img = None

panel_grid = []
#panel_scale = .38
screen_height = root.winfo_screenheight()
screen_width = root.winfo_screenwidth()
panel_screen_width_fraction = .11875
panel_scaled_img_width = int(panel_screen_width_fraction * screen_width)
panel_src_img_width = 600
title_padding = 3
details_pane_bg = "#333333"
episode_title_bg = "#333333"
title_info = None
details_pane_screen_width_fraction = .234375
details_pane_width = int(details_pane_screen_width_fraction * screen_width)
highlight_thickness = 8
highlight_color = "#FFFFFF"
num_rows = 3
num_cols = 6
show_padding = 50

from enum import Enum

Screens = Enum('Screens', 'MainSelect ShowSeasonSelect ShowEpisodeSelect Search Player PlaybackDialog InfoDialog SearchInfoDialog')

screen = Screens.MainSelect

titles_grid = PanelGrid(num_rows, num_cols, 0, 2, grid, media_dir)

details_title = StringVar()


class CategoriesManager(object):
    def __init__(self):
        global details_pane
        self.categories_frame = tk.Frame(details_pane)
        self.categories_frame.config(background=details_pane_bg)

        self.selected_category_index = 0

    def load_categories(self):
        self.categories = []     

        all_label_frame = LabelFrame(self.categories_frame,
                        borderwidth=5,
                        bg="#FFFFFF",
                        relief=FLAT)
        all_label_frame.pack(side='top', fill=tk.X, expand="1")

        all_label = Label(all_label_frame,
                      text="All", 
                      font=("Calibri", 32),
                      bg=details_pane_bg,
                      fg="#FFFFFF",
                      relief=FLAT)
        all_label.pack(fill=tk.BOTH)

        self.categories.append(("All", None, all_label, all_label_frame))

        tv_shows = set()
        for filename in sorted(os.listdir(media_dir), key=lambda x : x):
            if os.path.isdir(os.path.join(media_dir, filename)):
                filename_img = filename
                if filename.endswith(' x265'):
                    filename_img = filename_img[:-5]
                image_file = get_img_path_from_title(filename_img)
                tv_shows.add(filename)
                
        self.create_category("TV Shows", tv_shows)

        for filename in os.listdir('categories'):
            if filename.endswith(".txt"):
                category_name = filename[:-4]
                category_filepath = os.path.join('categories', filename)
                category_titles = set()
                with open(category_filepath) as category_file:
                    curr_title = category_file.readline().rstrip('\n')
                    while curr_title:
                        image_file = get_img_path_from_title(curr_title)
                        category_titles.add(curr_title)

                        curr_title = category_file.readline().rstrip('\n')

                self.create_category(category_name, category_titles)

    def create_category(self, category_name, category_titles):
        category_label_frame = LabelFrame(self.categories_frame,
                        borderwidth=5,
                        bg=details_pane_bg,
                        relief=FLAT)
        category_label_frame.pack(side='top', fill=tk.X, expand="1")

        category_label = Label(category_label_frame,
                      text=category_name, 
                      font=("Calibri", 32),
                      bg=details_pane_bg,
                      fg="#FFFFFF",
                      relief=FLAT)
        category_label.pack(fill=tk.BOTH)

        self.categories.append((category_name, category_titles, category_label, category_label_frame))

    def draw_categories(self):
        #self.categories_frame.pack(side='left', fill=tk.X, expand="1")
        self.categories_frame.pack(side='bottom', fill=tk.X, pady=(0, screen_height / 3 - len(self.categories) * 32))

    def set_active(self):
        self.categories[self.selected_category_index][2].config(bg='#FFFFFF')
        self.categories[self.selected_category_index][2].config(fg='#000000')

    def set_inactive(self):
        self.categories[self.selected_category_index][2].config(bg=details_pane_bg)
        self.categories[self.selected_category_index][2].config(fg='#FFFFFF')

    def move_selection(self, delta):
        new_selected_index = self.selected_category_index + delta

        if new_selected_index < 0 or new_selected_index >= len(self.categories):
            return

        self.categories[self.selected_category_index][3].config(bg=details_pane_bg)
        self.categories[self.selected_category_index][2].config(bg=details_pane_bg)
        self.categories[self.selected_category_index][2].config(fg='#FFFFFF')

        self.selected_category_index = new_selected_index

        self.categories[self.selected_category_index][3].config(bg="#FFFFFF")
        self.categories[self.selected_category_index][2].config(bg='#FFFFFF')
        self.categories[self.selected_category_index][2].config(fg='#000000')

        global titles_grid
        titles_grid.destroy()
        titles_grid = PanelGrid(num_rows, num_cols, 0, 2, grid, media_dir, self.get_curr_category_titles())
        draw_titles_grid()

    def get_curr_category_titles(self):
        return self.categories[self.selected_category_index][1]


details_pane = Frame(frame, width=details_pane_width)

def init_details_pane():

    global details_pane
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
    title_info.pack(side="top", fill=tk.X)

    global tk_logo_img
    logo_img = Image.open(logo_image_file)
    logo_img_width = logo_img.size[0]
    logo_img_height = logo_img.size[1]
    logo_img_scale = details_pane_width / logo_img_width

    logo_img = logo_img.resize((int(logo_img_width * logo_img_scale), int(logo_img_height * logo_img_scale)), Image.ANTIALIAS)
    tk_logo_img = ImageTk.PhotoImage(logo_img)

    logo_ref = [tk_logo_img]

    logo_image_label = tk.Label(details_pane, image=tk_logo_img, background=details_pane_bg)# width=int(img_width * panel_scale + highlight_thickness), height=int(img_height * panel_scale + highlight_thickness))
    logo_image_label.pack(side='bottom', fill=tk.X, anchor='s')

    ip_label = Message(details_pane, text = str(get_ip()), width=details_pane_width)
    ip_label.config(font=("Calibri", 36))
    ip_label.config(background=details_pane_bg)
    ip_label.config(fg="#FFFFFF")
    ip_label.pack(side='bottom', fill=tk.X)

    #all_label = tk.Label(details_pane, text="All", highlightthickness=5, relief='solid', anchor='center', padx=show_padding)
    #all_label.config(font=("Calibri", 24))
    #all_label.config(background=details_pane_bg)
    #all_label.config(foreground="#FFFFFF")
    #all_label.config(highlightbackground="#FFFFFF")

    global categories_manager
    if categories_manager == None:
        categories_manager = CategoriesManager()
        categories_manager.load_categories()
    categories_manager.draw_categories()


def draw_titles_grid():

    grid.pack(side='right', fill=tk.Y)
    
    global titles_grid
        
    titles_grid.containing_frame = grid
    titles_grid.draw_grid()

    #print("Setting: (" + str(selected_panel[0]) + ", " + str(selected_panel[1]) + ") to WHITE")

# Dictionary of movie names to filenames
movies = {}
# Dictionary of show names to lists of two tuples containing episode names and episode filenames
shows = {}
def generate_search_index():
    for filename in sorted(os.listdir(media_dir), key=lambda x : x[:-4] if (x.endswith(".mp4") or x.endswith(".mkv")) else x):
        title = filename

        if filename.endswith(".mp4") or filename.endswith(".mkv"): 
            title = title[:-4]
            video_file = os.path.join(media_dir, filename)

            movies[title] = video_file

        elif os.path.isdir(os.path.join(media_dir, filename)):
            shows[title] = []

            show_dir = os.path.join(media_dir, title)
            for filename in sorted(os.listdir(show_dir)):
                subdir = os.path.join(show_dir, filename)
                if os.path.isdir(subdir): 
                    for episode in sorted(os.listdir(subdir)):
                        if episode.endswith(".mp4") or episode.endswith(".mkv"):
                            shows[title].append((episode[:-4], os.path.join(subdir, episode)))
    """
    for movie, movie_filename in movies.items():
        print("{} ==> {}".format(movie, movie_filename))
    
    for show, show_pairs in shows.items():
        print(show)
        for show_pair in show_pairs:
            print("\t{} ==> {}".format(show_pair[0], show_pair[1]))
    """

# Returns list of three-tuples containing show name (if episode), title, and filename (if not a show)
def search_media(query):
    query_lower = query.lower()
    results = []

    for movie, movie_filename in movies.items():
        if query_lower in movie.lower():
            results.append((None, movie, movie_filename))

    for show, show_pairs in shows.items():
        if query_lower in show.lower():
            results.append((None, show, None))
        for show_pair in show_pairs:
            if query_lower in show_pair[0].lower():
                results.append((show, show_pair[0], show_pair[1]))

    return results


generate_search_index()

init_details_pane()

draw_titles_grid()

init_times_db()

init_info_dict()

load_config()

#b = Button(grid, text="QUIT", command=exit)
#b.grid(column=int(num_cols/2), row=0)


#player.set_fullscreen(True)
#player.play()
#playing = True



root.mainloop()

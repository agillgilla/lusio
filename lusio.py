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
            client.settimeout(60)
            listen_thread = threading.Thread(target = self.listenToClient,args = (client,address))
            listen_thread.daemon = True
            listen_thread.start()

    def listenToClient(self, client, address):
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    # Set the response to echo back the recieved data 
                    response = data
                    client.send(response)
                else:
                    raise error('Client disconnected')
            except:
                client.close()
                return False
'''
server_obj = ThreadedServer('', 65432)

server_thread = threading.Thread(target = server_obj.listen,args = ())
server_thread.daemon = True
server_thread.start()



try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    sys.exit(0)
'''

class Medium(object):
    def __init__(self, title, image_file, video_file):
        self.title = title
        self.image_file = image_file
        self.video_file = video_file

class TitlesGrid(object):
    def __init__(self, num_rows, num_cols, start_row, start_col, containing_frame, media_dir, images_dir):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.start_row = start_row
        self.start_col = start_col
        self.media_dir = media_dir
        self.images_dir = images_dir
        self.containing_frame = containing_frame
        self.panel_grid = []
        self.selected_title = [0, 0]
        self.media_list = []
        self.scroll_row = 0

        for filename in os.listdir(media_dir):
            if filename.endswith(".mp4") or filename.endswith(".mkv") or os.path.isdir(os.path.join(media_dir, filename)): 
                #print(os.path.join(media_dir, filename))
                title = filename
                video_file = None

                if not os.path.isdir(os.path.join(media_dir, filename)):
                    title = title[:-4]
                    video_file = os.path.join(media_dir, filename)
                
                image_file = os.path.join(images_dir, title + ".jpg")

                if not os.path.exists(image_file):
                    print(image_file)
                    print("Image not found for: " + title + ". Skipping...")
                    continue
                
                self.media_list.append(Medium(title, image_file, video_file))

                print(title)

    def draw(self):
        self.panel_grid = []

        curr_col = self.start_col
        curr_row = self.start_row

        for media in self.media_list[((self.num_cols - self.start_col) * (self.scroll_row)):]:
            try:
                if curr_col == self.start_col:
                    new_row = []
                    self.panel_grid.append(new_row)

                img = Image.open(media.image_file)
                img = img.resize((int(img.size[0] * title_scale), int(img.size[1] * title_scale)), Image.ANTIALIAS)
                img = ImageTk.PhotoImage(img)

                panel = tk.Label(self.containing_frame, image=img)
                panel.image = img
                panel.grid(column=curr_col, row=curr_row, sticky=N+S+E+W)
                panel.config(background="#000000")
                self.panel_grid[curr_row - self.start_row].append(panel)

                curr_col += 1
                if curr_col == self.num_cols:
                    curr_col = self.start_col
                    curr_row += 1

                if curr_row == self.num_rows:
                    break
            except FileNotFoundError:
                print("Image not found for: " + media.title)
        
        self.panel_grid[self.selected_title[0]][self.selected_title[1]].config(background="#FFFFFF")

    def get_title(self):
        return self.panel_coords_to_medium(self.selected_title[0] + self.scroll_row, self.selected_title[1]).title

    def get_video(self):
        return self.panel_coords_to_medium(self.selected_title[0] + self.scroll_row, self.selected_title[1]).video_file

    def move_selection(self, delt_row, delt_col):
        selected_row = self.selected_title[0]
        selected_col = self.selected_title[1]

        new_row = selected_row + delt_row
        new_col = selected_col + delt_col

        if new_col >= self.num_cols - start_col or new_col < 0:
            return
        elif new_row >= self.num_rows - self.start_row:
            self.scroll_down()
        elif new_row < 0:
            self.scroll_up()
        else:
            print("Moving selection from: (" + str(selected_row) + ", " + str(selected_col) + ") to: (" + str(new_row) + ", " + str(new_col) + ")")
            self.selected_title = [new_row, new_col]

            self.panel_grid[selected_row][selected_col].config(background="#000000")
            self.panel_grid[self.selected_title[0]][self.selected_title[1]].config(background="#FFFFFF")

        global title_info
        title_info.config(text=self.get_title())

    def scroll_down(self):
        self.scroll_row += 1
        self.panel_grid[self.selected_title[0]][self.selected_title[1]].config(background="#000000")
        print("Num rows: " + str(len(self.panel_grid)))
        print("Num cols in last row: " + str(len(self.panel_grid[len(self.panel_grid) - 1])))
        for panel_row, row in enumerate(self.panel_grid):
            for panel_col, panel in enumerate(row):

                panel.grid_forget()
                    
                if panel_row != 0:
                    self.panel_grid[panel_row - 1][panel_col] = panel
                    print("Moving: " + self.panel_coords_to_medium(panel_row, panel_col).title + " to row: " + str(panel_row - 1))
                    panel.grid(column=start_col + panel_col, row=start_row + panel_row - 1, sticky=N+S+E+W)
                    panel.config(background="#000000")

        for panel_col, panel in enumerate(self.panel_grid[len(self.panel_grid) - 1]):
                print("Row index: " + str(panel_row) + " has length: " + str(len(row)))
                
                
                try:
                    print("Calling on row: " + str(panel_row) + " and column: " + str(panel_col))

                    media = self.panel_coords_to_medium(panel_row + self.scroll_row, panel_col)

                    print("Media title: " + media.title)

                    img = Image.open(media.image_file)
                    img = img.resize((int(img.size[0] * title_scale), int(img.size[1] * title_scale)), Image.ANTIALIAS)
                    img = ImageTk.PhotoImage(img)

                    panel = tk.Label(self.containing_frame, image=img)
                    panel.image = img
                    panel.grid(column=start_col + panel_col, row=start_row + panel_row + 1, sticky=N+S+E+W)
                    panel.config(background="#000000")
                    self.panel_grid[panel_row][panel_col] = panel

                except FileNotFoundError:
                    print("Image not found for: " + media.title)
                
                    

        self.panel_grid[self.selected_title[0]][self.selected_title[1]].config(background="#FFFFFF")




    def scroll_up(self):
        pass

    """ Give this function the panel_grid coords WITH ROW SCROLL SHIFT (not the translated GUI coords) """
    def panel_coords_to_medium(self, row, col):
        #print("Index: " + str((self.num_cols - self.start_col) * (row) + (col)))
        #print("Coords: (" + str(row) + ", " + str(col) + "); Index: " + str((self.num_cols - self.start_col) * (row) + (col)))
        return self.media_list[(self.num_cols - self.start_col) * (row) + (col)]

    """ The panel_grid coordinates are stored at the 0 indices of row, column but the actual GUI grid coordinates are shifted
        by start_row, start_col respectively.  So this function converts row, column coordinates to GUI grid coordinates. 

        Example: The panel at panel_grid[0][0] will actually be on the GUI as tk.grid(self.start_row, self.start_col, ...) """
    def panel_coords_to_grid_coords(self, panel_grid_row, panel_grid_col):
        return (self.start_row + panel_grid_row, self.start_col + panel_grid_col)

    def destroy(self):
        for row in self.panel_grid:
            for panel in row:
                panel.grid_forget()


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

def quit(event):
    player.stop()
    root.destroy()

def exit():
    if playing:
        player.stop()
    root.destroy()

def up(event):
    titles_grid.move_selection(-1, 0)

def down(event):
    titles_grid.move_selection(1, 0)

def left(event):
    titles_grid.move_selection(0, -1)

def right(event):
    titles_grid.move_selection(0, 1)

def space(event):
    global playing
    global player
    
    if playing:
        player.stop()
        playing = False
    else:
        
        titles_grid.destroy()
        details_pane.destroy()
        '''
        for child in grid.winfo_children():
            child.destroy()
        '''
        player = examples_tkvlc.Player(frame, video=titles_grid.get_video())#"D:\VIDEOS\MOVIES\American Sniper.mp4")
        player.OnPlay()
        #root.protocol("WM_DELETE_WINDOW", player.OnClose)  # XXX unnecessary (on macOS)
        #player.play()
        #playing = True

def close_player(event):
    global player
    if player != None:
        player.OnDestroy()

    draw_titles()

num_cols = 9
num_rows = 4

selected_title = [0, 0]

def move_selection(delt_row, delt_col):
    global selected_title
    selected_row = selected_title[0]
    selected_col = selected_title[1]

    new_row = selected_row + delt_row
    new_col = selected_col + delt_col

    if new_row >= num_rows - start_row or new_row < 0 or new_col >= num_cols - start_col or new_col < 0:
        return

    selected_title = [new_row, new_col]

    panel_grid[selected_row][selected_col].config(background="#000000")
    panel_grid[selected_title[0]][selected_title[1]].config(background="#FFFFFF")

    #print("Setting: (" + str(selected_row) + ", " + str(selected_col) + ") to BLACK")
    #print("Setting: (" + str(selected_title[0]) + ", " + str(selected_title[1]) + ") to WHITE")



# binding keyboard shortcuts to buttons on window
root.bind("<p>", playPauseVideo)
root.bind("<s>", stopVideo)
root.bind("<q>", quit)
root.bind('<Up>', up)
root.bind('<Down>', down)
root.bind('<Left>', left)
root.bind('<Right>', right)
root.bind('<space>', space)
root.bind('<Escape>', close_player)

media_dir = 'D:\VIDEOS\MOVIES'
images_dir = 'titles'

panel_grid = []
title_scale = .345
start_row = 1
start_col = 2
details_pane = None
details_pane_bg = "#000000"
title_info = None
details_pane_width = 400

titles_grid = TitlesGrid(4, 9, 1, 2, grid, 'D:\VIDEOS\MOVIES', 'titles')

def draw_titles():
    global details_pane
    details_pane = Frame(grid, width=details_pane_width)
    details_pane.config(background=details_pane_bg)
    details_pane.grid(column=0, row=1, columnspan=2, rowspan=num_rows-1, sticky=N+S+E+W)

    details_pane.pack_propagate(0)

    global title_info
    title_info = Message(details_pane, text=titles_grid.get_title(), width=details_pane_width)
    title_info.config(font=("Calibri", 36))
    title_info.config(background=details_pane_bg)
    title_info.config(fg="#FFFFFF")
    title_info.pack(side="top", fill='both')

    titles_grid.draw()

    #print("Setting: (" + str(selected_title[0]) + ", " + str(selected_title[1]) + ") to WHITE")

draw_titles()


b = Button(grid, text="QUIT", command=exit)
b.grid(column=int(num_cols/2), row=0)


#player.set_fullscreen(True)
#player.play()
#playing = True



root.mainloop()

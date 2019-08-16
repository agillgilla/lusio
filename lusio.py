import tkinter as tk

from tkinter import *

# VLC NEEDS TO BE INSTALLED
import vlc

class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master=master
        pad=3
        self._geom='200x200+0+0'
        master.geometry("{0}x{1}+0+0".format(
            master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        master.bind('<Escape>',self.toggle_geom)
    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

def quit():
    root.quit()

root=tk.Tk()
app=FullScreenApp(root)
root.wm_title("LUSIO")
root.config(background = "#FFFFFF")
root.attributes('-fullscreen', True)

player = vlc.MediaPlayer("")
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
    root.quit()

# binding keyboard shortcuts to buttons on window
root.bind("<p>", playPauseVideo)
root.bind("<s>", stopVideo)
root.bind("<q>", quit)

b = Button(root, text="QUIT", command=quit)
b.pack()



player = vlc.MediaPlayer("bloopers.mp4")
player.set_fullscreen(True)
player.play()



root.mainloop()
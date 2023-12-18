#! /usr/bin/python
# -*- coding: utf-8 -*-

# tkinter example for VLC Python bindings
# Copyright (C) 2015 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#
"""A simple example for VLC python bindings using tkinter.

Requires Python 3.4 or later.

Author: Patrick Fay
Date: 23-09-2015
"""

# Tested with Python 3.7.4, tkinter/Tk 8.6.9 on macOS 10.13.6 only.
__version__ = '19.07.29'  # mrJean1 at Gmail dot com

# import external libraries
import vlc
# import standard libraries
import sys

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
from os.path import basename, expanduser, isfile, join as joined
from pathlib import Path
import time

_isWindows = sys.platform.startswith('win')
_isLinux = sys.platform.startswith('linux')


libtk = "N/A"
C_Key = "Control-"  # shortcut key modifier

'''
class _Tk_Menu(tk.Menu):
    """Tk.Menu extended with .add_shortcut method.

       Note, this is a kludge just to get Command-key shortcuts to
       work on macOS.  Other modifiers like Ctrl-, Shift- and Option-
       are not handled in this code.
    """
    _shortcuts_entries = {}
    _shortcuts_widget  = None

    def add_shortcut(self, label='', key='', command=None, **kwds):
        """Like Tk.menu.add_command extended with shortcut key.

           If needed use modifiers like Shift- and Alt_ or Option-
           as before the shortcut key character.  Do not include
           the Command- or Control- modifier nor the <...> brackets
           since those are handled here, depending on platform and
           as needed for the binding.
        """
        # <https://TkDocs.com/tutorial/menus.html>
        if not key:
            self.add_command(label=label, command=command, **kwds)
        else:  # XXX not tested, not tested, not tested
            self.add_command(label=label, underline=label.lower().index(key),
                                          command=command, **kwds)
            self.bind_shortcut(key, command, label)

    def bind_shortcut(self, key, command, label=None):
        """Bind shortcut key, default modifier Command/Control.
        """
        # The accelerator modifiers on macOS are Command-,
        # Ctrl-, Option- and Shift-, but for .bind[_all] use
        # <Command-..>, <Ctrl-..>, <Option_..> and <Shift-..>,
        # <https://www.Tcl.Tk/man/tcl8.6/TkCmd/bind.htm#M6>
        if self._shortcuts_widget:
            if C_Key.lower() not in key.lower():
                key = "<%s%s>" % (C_Key, key.lstrip('<').rstrip('>'))
            self._shortcuts_widget.bind(key, command)
            # remember the shortcut key for this menu item
            if label is not None:
                item = self.index(label)
                self._shortcuts_entries[item] = key
        # The Tk modifier for macOS' Command key is called
        # Meta, but there is only Meta_L[eft], no Meta_R[ight]
        # and both keyboard command keys generate Meta_L events.
        # Similarly for macOS' Option key, the modifier name is
        # Alt and there's only Alt_L[eft], no Alt_R[ight] and
        # both keyboard option keys generate Alt_L events.  See:
        # <https://StackOverflow.com/questions/6378556/multiple-
        # key-event-bindings-in-tkinter-control-e-command-apple-e-etc>

    def bind_shortcuts_to(self, widget):
        """Set the widget for the shortcut keys, usually root.
        """
        self._shortcuts_widget = widget

    def entryconfig(self, item, **kwds):
        """Update shortcut key binding if menu entry changed.
        """
        tk.Menu.entryconfig(self, item, **kwds)
        # adjust the shortcut key binding also
        if self._shortcuts_widget:
            key = self._shortcuts_entries.get(item, None)
            if key is not None and "command" in kwds:
                self._shortcuts_widget.bind(key, kwds["command"])
'''

class Player(tk.Frame):
    """The main window has to deal with events.
    """
    _geometry = ''
    _stopped  = None

    def __init__(self, parent, title=None, video='', show_scrubber=True):
        tk.Frame.__init__(self, parent)

        self.parent = parent  # == root
        #self.parent.title(title or "tkVLCplayer")
        self.video = expanduser(video)

        self.show_scrubber = show_scrubber

        # Menu Bar
        #   File Menu
        menubar = tk.Menu(self.parent)
        #self.parent.config(menu=menubar)

        '''
        fileMenu = _Tk_Menu(menubar)
        fileMenu.bind_shortcuts_to(parent)  # XXX must be root?

        fileMenu.add_shortcut("Open...", 'o', self.OnOpen)
        fileMenu.add_separator()
        fileMenu.add_shortcut("Play", 'p', self.OnPlay)  # Play/Pause
        fileMenu.add_command(label="Stop", command=self.OnStop)
        fileMenu.add_separator()
        fileMenu.add_shortcut("Mute", 'm', self.OnMute)
        fileMenu.add_separator()
        fileMenu.add_shortcut("Close", 's', self.OnClose)


        menubar.add_cascade(label="File", menu=fileMenu)
        self.fileMenu = fileMenu
        self.playIndex = fileMenu.index("Play")
        self.muteIndex = fileMenu.index("Mute")
        '''

        panel_style = ttk.Style()
        panel_style.configure('new.TFrame', background='#000000')

        # first, top panel shows video
        self.videopanel = ttk.Frame(self.parent, style='new.TFrame')
        self.canvas = tk.Canvas(self.videopanel, highlightthickness=0)
        self.canvas.config(background="#000000")
        self.canvas.pack(fill=tk.BOTH, expand=1)
        self.videopanel.pack(fill=tk.BOTH, expand=1)
        
        #self.canvas.grid()#fill=tk.BOTH, expand=1)
        #self.videopanel.grid()#fill=tk.BOTH, expand=1)

        # panel to hold buttons
        buttons = ttk.Frame(self.parent, style='new.TFrame')
        self.playButton = ttk.Button(buttons, text="Play", command=self.OnPlay)
        stop            = ttk.Button(buttons, text="Stop", command=self.OnStop)
        #self.muteButton = ttk.Button(buttons, text="Mute", command=self.OnMute)
        
        #self.playButton.pack(side=tk.LEFT)
        #stop.pack(side=tk.LEFT)
        #self.playButton.grid(side=tk.LEFT)
        #stop.grid(side=tk.LEFT)

        #self.muteButton.pack(side=tk.LEFT)

        '''
        self.volMuted = False
        self.volVar = tk.IntVar()
        self.volSlider = tk.Scale(buttons, variable=self.volVar, command=self.OnVolume,
                                  from_=0, to=100, orient=tk.HORIZONTAL, length=200,
                                  showvalue=0, label='Volume')
        self.volSlider.pack(side=tk.LEFT)
        '''
        #buttons.grid()#side=tk.BOTTOM)
        buttons.pack(side=tk.BOTTOM)

        
        if self.show_scrubber:
            # panel to hold player time slider
            self.timers = ttk.Frame(self.parent, style='new.TFrame')
            self.timeVar = tk.DoubleVar()
            self.timeSliderLast = 0
            self.timeSlider = tk.Scale(self.timers, variable=self.timeVar, command=self.OnTime,
                                       from_=0, to=1000, orient=tk.HORIZONTAL, length=500,
                                       showvalue=0)  # label='Time',
            self.timeSlider.pack(side=tk.BOTTOM, fill=tk.X, expand=1)
            #self.timeSlider.grid()#side=tk.BOTTOM, fill=tk.X, expand=1)
            
            self.timeSliderUpdate = time.time()
            self.timers.pack(side=tk.BOTTOM, fill=tk.X)
            #timers.grid()#side=tk.BOTTOM, fill=tk.X)
        

        # VLC player
        args = []
        if _isLinux:
            args.append('--no-xlib')
            #args.append('-V omxil_vout')
            #args.append('--codec omxil')
        print("VLC ARGS:")
        print(args)
        #args.append('--no-sub-autodetect-file')
        #args.append(['--sub-track', '200'])
        self.Instance = vlc.Instance(args)
        self.player = self.Instance.media_player_new()



        self.parent.bind("<Configure>", self.OnConfigure)  # catch window resize, etc.
        self.parent.update()

        self.OnTick()  # set the timer up

    def OnClose(self, *unused):
        """Closes the window and quit.
        """
        # print("_quit: bye")
        self.parent.quit()  # stops mainloop
        self.parent.destroy()  # this is necessary on Windows to avoid
        # ... Fatal Python Error: PyEval_RestoreThread: NULL tstate
        sys.exit(0)

    def OnConfigure(self, *unused):
        """Some widget configuration changed.
        """
        # <https://www.Tcl.tk/man/tcl8.6/tkCmd/bind.htm#M12>
        self._geometry = ''  # force .OnResize in .OnTick, recursive?

    def OnDestroy(self, *unused):
        """Destroy the player.
        """
        self.player.stop()
        self.videopanel.destroy()
        if self.show_scrubber:
            self.timers.destroy()

    def OnFullScreen(self, *unused):
        """Toggle full screen, macOS only.
        """
        # <https://www.Tcl.tk/man/tcl8.6/tkCmd/wm.htm#M10>
        f = not self.parent.attributes("-fullscreen")  # or .wm_attributes
        if f:
            self._previouscreen = self.parent.geometry()
            self.parent.attributes("-fullscreen", f)  # or .wm_attributes
            self.parent.bind("<Escape>", self.OnFullScreen)
        else:
            self.parent.attributes("-fullscreen", f)  # or .wm_attributes
            self.parent.geometry(self._previouscreen)
            self.parent.unbind("<Escape>")

    def OnMute(self, *unused):
        """Mute/Unmute audio.
        """
        # audio un/mute may be unreliable, see vlc.py docs.
        self.volMuted = m = not self.volMuted  # self.player.audio_get_mute()
        self.player.audio_set_mute(m)
        u = "Unmute" if m else "Mute"
        #self.fileMenu.entryconfig(self.muteIndex, label=u)
        #self.muteButton.config(text=u)
        # update the volume slider text
        self.OnVolume()

    def OnOpen(self, *unused):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        self.OnStop()
        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a video".
        video = askopenfilename(initialdir = Path(expanduser("~")),
                                title = "Choose a video",
                                filetypes = (("all files", "*.*"),
                                             ("mp4 files", "*.mp4"),
                                             ("mov files", "*.mov")))
        self._Play(video)

    def _Pause_Play(self, playing):
        # re-label menu item and button, adjust callbacks
        p = 'Pause' if playing else 'Play'
        c = self.OnPlay if playing is None else self.OnPause
        #self.fileMenu.entryconfig(self.playIndex, label=p, command=c)
        # self.fileMenu.bind_shortcut('p', c)  # XXX handled
        self.playButton.config(text=p, command=c)
        self._stopped = False

    def _Play(self, video):
        # helper for OnOpen and OnPlay
        if isfile(video):  # Creation
            m = self.Instance.media_new(str(video))  # Path, unicode
            self.player.set_media(m)
            #self.parent.title("tkVLCplayer - %s" % (basename(video),))

            print("Loaded media: " + str(video))

            print("Available sub tracks:")
            print(self.player.video_get_spu())

            subtrack = -1
            result = self.player.video_set_spu(subtrack)
            print("Return value of set_spu({}): ".format(subtrack) + str(result))

            result2 = self.player.video_set_subtitle_file("")
            print("Return value of set_subtitle_file(\"\"): " + str(result2))

            # set the window id where to render VLC's video output
            h = self.videopanel.winfo_id()  # .winfo_visualid()?
            if _isWindows:
                self.player.set_hwnd(h)
            else:
                self.player.set_xwindow(h)  # fails on Windows
            # FIXME: this should be made cross-platform
            self.OnPlay()

    def OnPause(self, *unused):
        """Toggle between Pause and Play.
        """
        if self.player.get_media():
            self._Pause_Play(not self.player.is_playing())
            self.player.pause()  # toggles

    def OnPlay(self, *unused):
        """Play video, if none is loaded, open the dialog window.
        """
        # if there's no video to play or playing,
        # open a tk.FileDialog to select a file
        if not self.player.get_media():
            if self.video:
                self._Play(expanduser(self.video))
                self.video = ''
            else:
                self.OnOpen()
        # Try to play, if this fails display an error message
        elif self.player.play():  # == -1
            self.showError("Unable to play the video.")
        else:
            self._Pause_Play(True)
            # set volume slider to audio level
            
            #vol = self.player.audio_get_volume()
            #if vol > 0:
            #    self.volVar.set(vol)
            #    self.volSlider.set(vol)

    def OnResize(self, *unused):
        """Adjust the window/frame to the video aspect ratio.
        """
        '''
        g = self.parent.geometry()
        if g != self._geometry and self.player:
            u, v = self.player.video_get_size()  # often (0, 0)
            if v > 0 and u > 0:
                # get window size and position
                g, x, y = g.split('+')
                w, h = g.split('x')
                # alternatively, use .winfo_...
                # w = self.parent.winfo_width()
                # h = self.parent.winfo_height()
                # x = self.parent.winfo_x()
                # y = self.parent.winfo_y()
                # use the video aspect ratio ...
                if u > v:  # ... for landscape
                    # adjust the window height
                    h = round(float(w) * v / u)
                else:  # ... for portrait
                    # adjust the window width
                    w = round(float(h) * u / v)
                self.parent.geometry("%sx%s+%s+%s" % (w, h, x, y))
                self._geometry = self.parent.geometry()  # actual
        '''

    def OnStop(self, *unused):
        """Stop the player, resets media.
        """
        if self.player:
            self.player.stop()
            self._Pause_Play(None)
            # reset the time slider
            if self.show_scrubber:
                self.timeSlider.set(0)
            self._stopped = True
        # XXX on macOS libVLC prints these error messages:
        # [h264 @ 0x7f84fb061200] get_buffer() failed
        # [h264 @ 0x7f84fb061200] thread_get_buffer() failed
        # [h264 @ 0x7f84fb061200] decode_slice_header error
        # [h264 @ 0x7f84fb061200] no frame!

    def OnTick(self):
        """Timer tick, update the time slider to the video time.
        """
        if self.player:
            # since the self.player.get_length may change while
            # playing, re-set the timeSlider to the correct range
            t = self.player.get_length() * 1e-3  # to seconds
            if self.show_scrubber and t > 0:
                self.timeSlider.config(to=t)

                t = self.player.get_time() * 1e-3  # to seconds
                # don't change slider while user is messing with it
                if t > 0 and time.time() > (self.timeSliderUpdate + 2):
                    self.timeSlider.set(t)
                    self.timeSliderLast = int(self.timeVar.get())
        # start the 1 second timer again
        self.parent.after(1000, self.OnTick)
        # adjust window to video aspect ratio, done periodically
        # on purpose since the player.video_get_size() only
        # returns non-zero sizes after playing for a while
        if not self._geometry:
            self.OnResize()

    def OnSkip(self, seconds):
        if self.player:
            curr_time = self.player.get_time()
            delta_millis = seconds * 1e3
            self.player.set_time(int(curr_time + delta_millis))

    def GetTime(self):
        if self.player:
            return self.player.get_time()

    def GetDuration(self):
        if self.player:
            return self.player.get_length()

    def SetTime(self, seconds):
        if self.player:
            time = seconds * 1e3
            self.player.set_time(int(time))

    def OnTime(self, *unused):
        if self.player:
            t = self.timeVar.get()
            if self.show_scrubber and self.timeSliderLast != int(t):
                # this is a hack. The timer updates the time slider.
                # This change causes this rtn (the 'slider has changed' rtn)
                # to be invoked.  I can't tell the difference between when
                # the user has manually moved the slider and when the timer
                # changed the slider.  But when the user moves the slider
                # tkinter only notifies this rtn about once per second and
                # when the slider has quit moving.
                # Also, the tkinter notification value has no fractional
                # seconds.  The timer update rtn saves off the last update
                # value (rounded to integer seconds) in timeSliderLast if
                # the notification time (sval) is the same as the last saved
                # time timeSliderLast then we know that this notification is
                # due to the timer changing the slider.  Otherwise the
                # notification is due to the user changing the slider.  If
                # the user is changing the slider then I have the timer
                # routine wait for at least 2 seconds before it starts
                # updating the slider again (so the timer doesn't start
                # fighting with the user).
                self.player.set_time(int(t * 1e3))  # milliseconds
                self.timeSliderUpdate = time.time()

    def OnVolume(self, *unused):
        """Volume slider changed, adjust the audio volume.
        """
        #vol = min(self.volVar.get(), 100)
        v_M = "%d%s" % (vol, " (Muted)" if self.volMuted else '')
        self.volSlider.config(label="Volume " + v_M)
        if self.player and not self._stopped:
            # .audio_set_volume returns 0 if success, -1 otherwise,
            # e.g. if the player is stopped or doesn't have media
            if self.player.audio_set_volume(vol):  # and self.player.get_media():
                self.showError("Failed to set the volume: %s." % (v_M,))

    def showError(self, message):
        """Display a simple error dialog.
        """
        self.OnStop()
        #showerror(self.parent.title(), message)

'''
if __name__ == "__main__":

    _video = ""

    # Create a tk.App() to handle the windowing event loop
    root = tk.Tk()
    player = Player(root, video=_video)
    root.protocol("WM_DELETE_WINDOW", player.OnClose)  # XXX unnecessary (on macOS)
    root.mainloop()
'''

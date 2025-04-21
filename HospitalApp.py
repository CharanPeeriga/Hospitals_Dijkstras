import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from geopy.geocoders import Nominatim
import geocoder
import tkinter as tk

#UI
from tkinter import ttk, messagebox

import threading
import time
from functools import partial

from dijkstras_algorithm import coordinate_convert, dijkstra_snapshots

class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dijkstra Hospital Finder")
        self.root.geometry("1920x1080")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=4)

        self.df = pd.read_csv("us_hospital_locations/us_hospital_locations.csv")
        self.geolocator = Nominatim(user_agent="hospital_app")

        self.snapshots = []
        self.prev = {}
        self.final_path_edges = set()

        self.var_addr = tk.StringVar()
        self.var_city = tk.StringVar()
        self.var_state = tk.StringVar()
        self.var_zip = tk.StringVar()
        self.var_use_current = tk.BooleanVar(value=False)
        self.radius = tk.DoubleVar(value=23.3)
        self.var_radius_text = tk.StringVar(value=f"{self.radius.get():.1f}")
        self.speed = tk.DoubleVar(value=1)
        self.step = 0
        self.playing = False

        self._dragging = False
        self._prev_mouse = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self.root)
        style.configure('L.TEntry', font=('Times New Roman', 14))
        style.configure('L.TButton', font=('Times New Roman', 14), padding=8)

        frm = ttk.Frame(self.root, padding=15)
        frm.grid(row=0, column=0, sticky="nsew")
        frm.grid_columnconfigure(0, weight=0)
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(frm, text="Address Fields", font=('Arial', 16, 'bold'))\
            .grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,10))

        ttk.Label(frm, text="Address:", font=('Times New Roman', 14))\
            .grid(row=1, column=0, sticky="w")
        self.entry_addr = ttk.Entry(frm, textvariable=self.var_addr,
                                    width=30, style='L.TEntry')
        self.entry_addr.grid(row=1, column=1, sticky="we", pady=5)

        ttk.Label(frm, text="City:", font=('Times New Roman', 14))\
            .grid(row=2, column=0, sticky="w")
        self.entry_city = ttk.Entry(frm, textvariable=self.var_city,
                                    width=30, style='L.TEntry')
        self.entry_city.grid(row=2, column=1, sticky="we", pady=5)

        ttk.Label(frm, text="State:", font=('Times New Roman', 14))\
            .grid(row=3, column=0, sticky="w")
        self.entry_state = ttk.Entry(frm, textvariable=self.var_state,
                                     width=30, style='L.TEntry')
        self.entry_state.grid(row=3, column=1, sticky="we", pady=5)

        ttk.Label(frm, text="Zipcode:", font=('Times New Roman', 14))\
            .grid(row=4, column=0, sticky="w")
        self.entry_zip = ttk.Entry(frm, textvariable=self.var_zip,
                                   width=30, style='L.TEntry')
        self.entry_zip.grid(row=4, column=1, sticky="we", pady=5)

        ttk.Label(frm, text="Radius (km):", font=('Times New Roman', 14))\
            .grid(row=5, column=0, sticky="w", pady=(15,0))
        ttk.Scale(frm, from_=1, to=200, variable=self.radius,
                  orient=tk.HORIZONTAL).grid(row=5, column=1,
                                              sticky="we", pady=5)
        self.radius.trace_add('write', self._update_radius_text)

        ttk.Label(frm, text="Custom Radius:", font=('Times New Roman', 14))\
            .grid(row=6, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_radius_text,
                  width=10, style='L.TEntry')\
            .grid(row=6, column=1, sticky="w", pady=5)
        self.var_radius_text.trace_add('write', self._on_radius_text_change)

        ttk.Button(frm, text="Use my current location",
                   style='L.TButton', command=self._on_use_current)\
            .grid(row=7, column=0, columnspan=2,
                  sticky="we", pady=(15,10))

        ttk.Button(frm, text="Start", style='L.TButton',
                   command=self.on_start)\
            .grid(row=8, column=0, columnspan=2,
                  sticky="we", pady=(0,20))

        ttk.Label(frm, text="Algorithm and Graph Controls",
                  font=('Arial', 16, 'bold'))\
            .grid(row=9, column=0, columnspan=2,
                  sticky="w", pady=(0,10))

        play_frame = ttk.Frame(frm)
        play_frame.grid(row=10, column=0, columnspan=2,
                        sticky="we")
        play_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        ttk.Button(play_frame, text="⏮ Prev", command=self.prev_step,
                   style='L.TButton')\
            .grid(row=0, column=0, padx=2)
        self.play_btn = ttk.Button(play_frame, text="▶ Play",
                                   command=self.toggle_play,
                                   style='L.TButton')
        self.play_btn.grid(row=0, column=1, padx=2)
        ttk.Button(play_frame, text="⏭ Next", command=self.next_step,
                   style='L.TButton')\
            .grid(row=0, column=2, padx=2)
        ttk.Label(play_frame, text="Speed:", font=('Times New Roman', 14))\
            .grid(row=0, column=3, sticky="e")
        ttk.OptionMenu(play_frame, self.speed, "1", "1", "2", "3", "4")\
            .grid(row=0, column=4, padx=2)

        zoom_frame = ttk.Frame(frm)
        zoom_frame.grid(row=11, column=0, columnspan=2,
                        sticky="we", pady=(10,0))
        ttk.Button(zoom_frame, text="Zoom In",
                   style='L.TButton', command=self.zoom_in)\
            .grid(row=0, column=0, padx=5)
        ttk.Button(zoom_frame, text="Zoom Out",
                   style='L.TButton', command=self.zoom_out)\
            .grid(row=0, column=1, padx=5)

        self.fig, self.ax = plt.subplots(figsize=(10.4, 10.4))
        self.canvas = None

    def _update_radius_text(self, *args):
        self.var_radius_text.set(f"{self.radius.get():.1f}")

    def _on_radius_text_change(self, *args):
        try:
            val = float(self.var_radius_text.get())
            self.radius.set(val)
        except ValueError:
            pass

    def _on_use_current(self):
        use = not self.var_use_current.get()
        self.var_use_current.set(use)
        self.toggle_address_fields()

    def toggle_address_fields(self):
        state = 'disabled' if self.var_use_current.get() else 'normal'
        for w in (self.entry_addr, self.entry_city,
                  self.entry_state, self.entry_zip):
            w.config(state=state)

    def on_start(self):
        if self.var_use_current.get():
            g = geocoder.ip('me')
            if not (g.ok and g.latlng):
                messagebox.showerror("Error", "Could not detect current location.")
                return
            self.user_point = tuple(g.latlng)
        else:
            query = ", ".join(filter(None, [
                self.var_addr.get(), self.var_city.get(),
                self.var_state.get(), self.var_zip.get()
            ]))
            if not query:
                messagebox.showerror(
                    "Error",
                    "Enter an address or click 'Use my current location'."
                )
                return
            loc = self.geolocator.geocode(query)
            if not loc:
                messagebox.showerror("Error", "Could not geocode address.")
                return
            self.user_point = (loc.latitude, loc.longitude)

        df = self.df
        city = self.var_city.get().strip().lower()
        st = self.var_state.get().strip().upper()
        zp = self.var_zip.get().strip()
        mask = pd.Series(True, index=df.index)
        if city:
            mask &= df['CITY'].str.lower().eq(city)
        if st:
            mask &= df['STATE'].eq(st)
        if zp:
            mask &= df['ZIP'].astype(str).str.startswith(zp)
        df = df.loc[mask].copy()

        df['dist'] = df.apply(
            lambda r: coordinate_convert(self.user_point,
                                         (r.LATITUDE, r.LONGITUDE)),
            axis=1
        )
        df = df[df['dist'] <= self.radius.get()]
        if df.empty:
            messagebox.showinfo("No hospitals",
                                "No hospitals found in that radius.")
            return

        self.nodes = {'user': self.user_point}
        for idx, row in df.iterrows():
            self.nodes[idx] = (row.LATITUDE, row.LONGITUDE, row.NAME)

        G = nx.Graph()
        for u, a in self.nodes.items():
            G.add_node(u, pos=a[:2])
        for u, a in self.nodes.items():
            for v, b in self.nodes.items():
                if u == v:
                    continue
                d = coordinate_convert(a[:2], b[:2])
                G.add_edge(u, v, weight=d)

        self.snapshots, self.prev = dijkstra_snapshots(G, 'user')
        self.G = G

        last_dist = self.snapshots[-1]['dist']
        hospitals = [n for n in G.nodes if n != 'user']
        target = min(hospitals,
                     key=lambda n: last_dist.get(n, float('inf')))
        path_edges = set()
        cur = target
        while cur != 'user':
            p = self.prev[cur]
            path_edges.add((p, cur))
            path_edges.add((cur, p))
            cur = p
        self.final_path_edges = path_edges

        self.step = 0
        self.playing = False
        self.update_plot()

    def update_plot(self):
        if not self.snapshots:
            return
        snap = self.snapshots[self.step]
        self.ax.clear()
        pos = nx.get_node_attributes(self.G, 'pos')
        ys = [y for (_, y) in pos.values()]
        delta = (max(ys) - min(ys)) * 0.02

        nc, ec = [], []
        last_frame = (self.step == len(self.snapshots) - 1)
        for n in self.G.nodes:
            nc.append('red' if n == snap['current']
                      else 'blue' if n in snap['visited']
                      else 'gray')
        for u, v in self.G.edges:
            if last_frame and ((u, v) in self.final_path_edges):
                ec.append('green')
            elif u in snap['visited'] and v in snap['visited']:
                ec.append('blue')
            else:
                ec.append('gray')

        nx.draw_networkx_nodes(self.G, pos, node_color=nc,
                               ax=self.ax, node_size=390)
        nx.draw_networkx_edges(self.G, pos, edge_color=ec,
                               ax=self.ax, width=1.3)
        labels = {n: ('You' if n == 'user' else self.nodes[n][2])
                  for n in self.G.nodes}
        label_pos = {n: (x, y - delta) for n, (x, y) in pos.items()}
        nx.draw_networkx_labels(self.G, label_pos, labels,
                                font_size=13, ax=self.ax)
        edge_w = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(
            self.G, pos,
            edge_labels={k: f"{v:.1f}" for k, v in edge_w.items()},
            font_size=10, ax=self.ax
        )

        self.ax.set_title(
            f"Step {self.step+1}/{len(self.snapshots)} — action={snap['action']}",
            fontsize=18
        )
        self.ax.set_axis_off()
        self.fig.tight_layout()

        if self.canvas is None:
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget()\
                .grid(row=0, column=1, sticky="nsew")
            self.canvas.mpl_connect('button_press_event', self._on_press)
            self.canvas.mpl_connect('button_release_event',
                                    self._on_release)
            self.canvas.mpl_connect('motion_notify_event',
                                    self._on_motion)

        self.canvas.draw()

    def next_step(self):
        if self.step < len(self.snapshots) - 1:
            self.step += 1
            self.update_plot()

    def prev_step(self):
        if self.step > 0:
            self.step -= 1
            self.update_plot()

    def toggle_play(self):
        if not self.snapshots:
            return
        self.playing = not self.playing
        self.play_btn.config(text='❚❚ Pause' if self.playing else '▶ Play')
        if self.playing:
            threading.Thread(target=self._auto_play,
                             daemon=True).start()

    def _auto_play(self):
        while self.playing and self.step < len(self.snapshots) - 1:
            time.sleep(1.0 / self.speed.get())
            self.step += 1
            self.root.after(0, self.update_plot)
        self.playing = False
        self.root.after(0, partial(self.play_btn.config,
                                  text='▶ Play'))

    def _on_press(self, event):
        if event.inaxes:
            self._dragging = True
            self._prev_mouse = (event.xdata, event.ydata)

    def _on_release(self, event):
        self._dragging = False
        self._prev_mouse = None

    def _on_motion(self, event):
        if not self._dragging or event.inaxes is None or self._prev_mouse is None:
            return
        dx = self._prev_mouse[0] - event.xdata
        dy = self._prev_mouse[1] - event.ydata
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        self.ax.set_xlim(x0 + dx, x1 + dx)
        self.ax.set_ylim(y0 + dy, y1 + dy)
        self._prev_mouse = (event.xdata, event.ydata)
        self.canvas.draw()

    def zoom_in(self):
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        factor = 0.8
        dx = (x1 - x0) * factor / 2
        dy = (y1 - y0) * factor / 2
        self.ax.set_xlim(cx - dx, cx + dx)
        self.ax.set_ylim(cy - dy, cy + dy)
        self.canvas.draw()

    def zoom_out(self):
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        factor = 1.2
        dx = (x1 - x0) * factor / 2
        dy = (y1 - y0) * factor / 2
        self.ax.set_xlim(cx - dx, cx + dx)
        self.ax.set_ylim(cy - dy, cy + dy)
        self.canvas.draw()

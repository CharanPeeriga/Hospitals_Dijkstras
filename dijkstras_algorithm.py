from math import radians, sin, cos, sqrt, atan2
import tkinter as tk
import HospitalApp

def coordinate_convert(a, b):
    #converting distance in kilometers between latitude and longitude pairs.
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6371.0
    x = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * atan2(sqrt(x), sqrt(1 - x))

def dijkstra_snapshots(G, start):
    dist = {n: float('inf') for n in G.nodes}
    prev = {}
    dist[start] = 0
    visited = set()
    snaps = []

    def snap(current=None, action=""):
        snaps.append({
            'dist': dist.copy(),
            'prev': prev.copy(),
            'visited': visited.copy(),
            'current': current,
            'action': action
        })

    snap(action="init")
    nodes = set(G.nodes)
    while nodes:
        u = min(nodes, key=lambda n: dist[n])
        if dist[u] == float('inf'):
            break
        snap(current=u, action="visit")
        for v in G[u]:
            alt = dist[u] + G[u][v]['weight']
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                snap(current=u, action=f"relax {u}->{v}")
        visited.add(u)
        nodes.remove(u)
        snap(current=u, action="mark_visited")

    return snaps, prev

if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp.HospitalApp(root)
    root.mainloop()
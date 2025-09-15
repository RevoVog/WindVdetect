"""
live_packet_monitor.py
Simple real-time packet monitor using Scapy and Tkinter (Windows-friendly).
Shows Time, Source IP, Destination IP, Protocol, Info.
Requirements:
  - Install Npcap on Windows and run script as Administrator.
  - pip install scapy
"""

import threading
import queue
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP

# Configuration
MAX_ROWS = 500  # max number of rows to keep in the table

def pkt_to_row(pkt):
    """Extract a row (time, src, dst, proto, info) from a Scapy packet."""
    ts = datetime.now().strftime("%H:%M:%S")
    src = ""
    dst = ""
    proto = ""
    info = ""

    # ARP (no IP layer)
    if pkt.haslayer(ARP):
        proto = "ARP"
        src = pkt[ARP].psrc
        dst = pkt[ARP].pdst
        info = f"op={pkt[ARP].op}"
        return (ts, src, dst, proto, info)

    if pkt.haslayer(IP):
        ip = pkt[IP]
        src = ip.src
        dst = ip.dst

        if pkt.haslayer(TCP):
            tcp = pkt[TCP]
            proto = "TCP"
            info = f"{tcp.sport}->{tcp.dport} flags={tcp.flags} len={len(tcp.payload)}"
        elif pkt.haslayer(UDP):
            udp = pkt[UDP]
            proto = "UDP"
            info = f"{udp.sport}->{udp.dport} len={len(udp.payload)}"
        elif pkt.haslayer(ICMP):
            icmp = pkt[ICMP]
            proto = "ICMP"
            info = f"type={icmp.type} code={icmp.code}"
        else:
            proto = ip.proto if hasattr(ip, "proto") else "IP"
            info = pkt.summary()
    else:
        # Non-IP fallback
        proto = pkt.lastlayer().name if pkt.lastlayer() is not None else "OTHER"
        info = pkt.summary()

    # Shorten info to keep table tidy
    if len(info) > 120:
        info = info[:117] + "..."

    return (ts, src, dst, proto, info)


class PacketSnifferThread(threading.Thread):
    def __init__(self, out_queue, iface=None, bpf_filter=None):
        super().__init__(daemon=True)
        self.out_queue = out_queue
        self.iface = iface
        self.bpf_filter = bpf_filter
        self._stop_event = threading.Event()

    def run(self):
        # sniff runs until stop; we use a small timeout to check stop flag periodically
        try:
            while not self._stop_event.is_set():
                sniff(
                    iface=self.iface,
                    filter=self.bpf_filter,
                    prn=self._process_pkt,
                    store=False,
                    timeout=1  # return to check stop flag
                )
        except PermissionError as e:
            self.out_queue.put(("ERROR", f"Permission error: {e}"))
        except Exception as e:
            self.out_queue.put(("ERROR", f"Sniffer exception: {e}"))

    def _process_pkt(self, pkt):
        row = pkt_to_row(pkt)
        self.out_queue.put(("DATA", row))

    def stop(self):
        self._stop_event.set()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Live Packet Monitor")
        self.root.geometry("900x500")

        top = ttk.Frame(root)
        top.pack(side="top", fill="x", padx=6, pady=6)

        ttk.Label(top, text="Interface (optional):").pack(side="left")
        self.iface_entry = ttk.Entry(top, width=20)
        self.iface_entry.pack(side="left", padx=(4, 10))

        ttk.Label(top, text="BPF filter (optional):").pack(side="left")
        self.filter_entry = ttk.Entry(top, width=30)
        self.filter_entry.pack(side="left", padx=(4, 10))
        ttk.Label(top, text="(e.g. tcp port 80 or udp)").pack(side="left")

        btn_frame = ttk.Frame(root)
        btn_frame.pack(side="top", fill="x", padx=6, pady=4)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_capture)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_capture, state="disabled")
        self.stop_btn.pack(side="left", padx=4)
        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_table)
        self.clear_btn.pack(side="left", padx=4)

        # Treeview table
        columns = ("time", "src", "dst", "proto", "info")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        self.tree.heading("time", text="Time")
        self.tree.heading("src", text="Source IP")
        self.tree.heading("dst", text="Destination IP")
        self.tree.heading("proto", text="Protocol")
        self.tree.heading("info", text="Info")
        self.tree.column("time", width=80)
        self.tree.column("src", width=150)
        self.tree.column("dst", width=150)
        self.tree.column("proto", width=80)
        self.tree.column("info", width=420)
        self.tree.pack(side="top", fill="both", expand=True, padx=6, pady=6)

        # queue for inter-thread communication
        self.q = queue.Queue()
        self.sniffer = None
        self.root.after(200, self.poll_queue)

    def start_capture(self):
        iface = self.iface_entry.get().strip() or None
        bpf = self.filter_entry.get().strip() or None

        # start sniffer thread
        self.sniffer = PacketSnifferThread(self.q, iface=iface, bpf_filter=bpf)
        self.sniffer.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop_capture(self):
        if self.sniffer:
            self.sniffer.stop()
            self.sniffer = None
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def clear_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def poll_queue(self):
        """Poll queue for new rows and update GUI"""
        processed = 0
        while True:
            try:
                kind, payload = self.q.get_nowait()
            except queue.Empty:
                break

            if kind == "DATA":
                ts, src, dst, proto, info = payload
                self.tree.insert("", 0, values=(ts, src, dst, proto, info))
                # trim rows
                if len(self.tree.get_children()) > MAX_ROWS:
                    # remove oldest (bottom) rows
                    children = self.tree.get_children()
                    for child in children[MAX_ROWS:]:
                        self.tree.delete(child)
            elif kind == "ERROR":
                messagebox.showerror("Sniffer Error", payload)
            processed += 1
            if processed > 500:
                break

        self.root.after(200, self.poll_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

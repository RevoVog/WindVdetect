# client_reporter.py
import asyncio
import datetime
import json
import platform
import socket
import os
import psutil
import traceback
import websockets

SERVER_WS = "ws://localhost:8000/ws?role=client"  # change to your server host if needed
SEND_INTERVAL = 3  # seconds between snapshots

def safe_asdict(obj):
    try:
        return obj._asdict()
    except Exception:
        return str(obj)

def collect_system_snapshot():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # basic host info
        hostname = socket.gethostname()
        platform_info = {
            "system": platform.system(),
            "platform": platform.platform(),
            "release": platform.release(),
            "python_version": platform.python_version(),
            "hostname": hostname,
            "pid": os.getpid()
        }

        # CPU
        cpu = {
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_percent": psutil.cpu_percent(interval=None),  # non-blocking
            "cpu_times": safe_asdict(psutil.cpu_times()),
            "cpu_stats": safe_asdict(psutil.cpu_stats())
        }

        # Memory
        vm = psutil.virtual_memory()._asdict()
        sm = psutil.swap_memory()._asdict()

        # Disk: iterate partitions and usage but catch exceptions for paths that fail
        partitions = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)._asdict()
            except Exception:
                usage = {"error": "Could not access mountpoint"}
            partitions.append({**p._asdict(), "usage": usage})
        # try a popular Windows drive and ignore errors:
        disk_usage_c = None
        try:
            disk_usage_c = psutil.disk_usage("C:\\")._asdict()
        except Exception:
            disk_usage_c = None

        # disk io
        disk_io = safe_asdict(psutil.disk_io_counters())

        # network
        net_if_addrs = {k: [a._asdict() for a in v] for k, v in psutil.net_if_addrs().items()}
        net_if_stats = {k: v._asdict() for k, v in psutil.net_if_stats().items()}
        net_io = safe_asdict(psutil.net_io_counters())

        # sensors (may not exist on all platforms)
        battery = None
        try:
            bat = psutil.sensors_battery()
            battery = bat._asdict() if bat else None
        except Exception:
            battery = None

        # processes: top 5 by cpu and memory
        procs = []
        try:
            for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_percent']):
                procs.append(p.info)
            # sort and keep top 5 cpu and top 5 mem
            top_cpu = sorted(procs, key=lambda x: x.get('cpu_percent',0), reverse=True)[:5]
            top_mem = sorted(procs, key=lambda x: x.get('memory_percent',0), reverse=True)[:5]
        except Exception:
            top_cpu = []
            top_mem = []

        snapshot = {
            "Timestamp": now,
            "Host": platform_info,
            "CPU": cpu,
            "Virtual Memory": vm,
            "Swap Memory": sm,
            "Disk Partitions": partitions,
            "Disk Usage (C:)": disk_usage_c,
            "Disk IO Counters": disk_io,
            "Network Interfaces": net_if_addrs,
            "Network Stats": net_if_stats,
            "Network IO Counters": net_io,
            "Battery": battery,
            "Top CPU Processes": top_cpu,
            "Top Memory Processes": top_mem,
            "Boot Time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            "Users": [u._asdict() for u in psutil.users()]
        }
        return snapshot
    except Exception:
        traceback.print_exc()
        return {"Timestamp": now, "error": "failed collecting snapshot"}

async def send_loop():
    async with websockets.connect(SERVER_WS, max_size=2**25) as ws:
        print("Connected to server", SERVER_WS)
        try:
            while True:
                snap = collect_system_snapshot()
                payload = json.dumps(snap, default=str)
                await ws.send(payload)
                await asyncio.sleep(SEND_INTERVAL)
        except Exception as e:
            print("Client send loop error:", e)
            raise

if __name__ == "__main__":
    print("System reporter client starting. Server:", SERVER_WS)
    try:
        asyncio.run(send_loop())
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Client error:", e)

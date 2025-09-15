import psutil
import csv
import time
from datetime import datetime
import os

def collect_system_info():
    """Collects system information and saves it into a timestamped CSV file."""
    
    # Generate filename with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"system_info_{timestamp}.csv"
    
    # Collect system info
    info = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # CPU
        "CPU Count (Logical)": psutil.cpu_count(logical=True),
        "CPU Count (Physical)": psutil.cpu_count(logical=False),
        "CPU Usage (%)": psutil.cpu_percent(interval=1),
        "CPU Times": psutil.cpu_times()._asdict(),
        "CPU Stats": psutil.cpu_stats()._asdict(),
        
        # Memory
        "Virtual Memory": psutil.virtual_memory()._asdict(),
        "Swap Memory": psutil.swap_memory()._asdict(),
        
        # Disk
        "Disk Partitions": [p._asdict() for p in psutil.disk_partitions()],
        "Disk Usage (C:)": psutil.disk_usage("C:\\")._asdict(),
        "Disk IO Counters": psutil.disk_io_counters()._asdict(),
        
        # Network
        "Network Interfaces": {k: [a._asdict() for a in v] for k, v in psutil.net_if_addrs().items()},
        "Network Stats": {k: v._asdict() for k, v in psutil.net_if_stats().items()},
        "Network IO Counters": psutil.net_io_counters()._asdict(),
        
        # Sensors
        "Battery": psutil.sensors_battery()._asdict() if psutil.sensors_battery() else "No Battery",
        
        # Other
        "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
        "Users": [u._asdict() for u in psutil.users()]
    }
    
    # Write info to CSV
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for key, value in info.items():
            writer.writerow([key, value])
    
    print(f"[INFO] System information saved to {filename}")

if __name__ == "__main__":
    collect_system_info()

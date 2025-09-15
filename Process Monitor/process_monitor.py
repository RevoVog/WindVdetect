import psutil
import time
import datetime
import csv
import os

def get_process_data():
    """
    Collects a list of all running processes with their details.
    """
    process_list = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'create_time']):
        try:
            # Get process info as a dictionary
            process_info = proc.info
            process_info['create_time'] = datetime.datetime.fromtimestamp(process_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
            process_list.append(process_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Handle cases where a process might disappear or access is denied
            continue
    return process_list

def save_to_file(data, file_format='csv'):
    """
    Saves the collected process data to a file.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'process_data_{timestamp}.{file_format}'

    if file_format == 'csv':
        keys = ['pid', 'name', 'exe', 'cmdline', 'create_time']
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
    
    print(f"Data saved to {filename}")

def display_data(data):
    """
    Prints process data to the terminal.
    """
    print("\n" + "="*50)
    print(f"Process Data collected at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Simple display for readability
    for proc in data[:15]: # Displaying first 15 for brevity
        print(f"PID: {proc['pid']:<5} | Name: {proc['name']:<20} | CMD: {' '.join(proc['cmdline']) if proc['cmdline'] else ''}")
    
    print("...") # Indicate that there's more data

def collect_system_info():
    """Collects system information and saves it into a timestamped CSV file."""
    
    # Generate filename with current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"system_info_{timestamp}.csv"
    
    # Collect system info
    info = {
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
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
        "Boot Time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
        "Users": [u._asdict() for u in psutil.users()]
    }
    
    # Write info to CSV
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for key, value in info.items():
            writer.writerow([key, value])
    

def main():
    """
    Main loop to run the data collection.
    """
    while True:
        # 1. Collect data
        data = get_process_data()
        
        # 2. Display data in terminal
        display_data(data)
        
        # 3. Export to a file
        save_to_file(data, 'csv')

        # 4. Collect system data
        collect_system_info()
        
        # 5. Wait for one minute
        print("\nWaiting for 60 seconds before next collection...")
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
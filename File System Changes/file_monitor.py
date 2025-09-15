import time
import logging
import csv
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the directory to monitor
# You can change this to any path you want to watch
# For this example, we'll monitor a 'monitored_folder' in the same directory as the script.
MONITORED_PATH = 'D:\\'

# Define the log file path
LOG_FILE_NAME = 'file_events.csv'

# Set up logging to the console
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def write_to_csv(event_type, src_path, dest_path=None):
    """Writes a new event to the CSV log file."""
    # Check if the file exists to write headers only once
    file_exists = os.path.isfile(LOG_FILE_NAME)

    with open(LOG_FILE_NAME, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'Event Type', 'Source Path', 'Destination Path'])
        
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([timestamp, event_type, src_path, dest_path])

class MyEventHandler(FileSystemEventHandler):
    """A custom event handler that logs file system events."""
    
    def on_moved(self, event):
        """Called when a file or a directory is moved or renamed."""
        logging.info(f"Moved: from {event.src_path} to {event.dest_path}")
        write_to_csv('moved', event.src_path, event.dest_path)

    def on_created(self, event):
        """Called when a file or a directory is created."""
        logging.info(f"Created: {event.src_path}")
        write_to_csv('created', event.src_path)

    def on_deleted(self, event):
        """Called when a file or a directory is deleted."""
        logging.info(f"Deleted: {event.src_path}")
        write_to_csv('deleted', event.src_path)

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        logging.info(f"Modified: {event.src_path}")
        write_to_csv('modified', event.src_path)

def main():
    """Main function to start the file system observer."""
    # Create the monitored directory if it doesn't exist
    if not os.path.exists(MONITORED_PATH):
        os.makedirs(MONITORED_PATH)
        print(f"Created directory: {MONITORED_PATH}")

    # Set up the event handler and observer
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, MONITORED_PATH, recursive=True)

    # Start the observer and keep the script running
    observer.start()
    logging.info(f"Monitoring started for: {MONITORED_PATH}")
    logging.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
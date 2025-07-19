
import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the path to the downloads directory
DOWNLOADS_DIR = os.path.abspath("../collector/downloads")

class NewFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            print(f"New folder detected: {event.src_path}")
            self.process_folder(event.src_path)

    def process_folder(self, folder_path):
        info_json_path = os.path.join(folder_path, "info.json")
        if os.path.exists(info_json_path):
            print(f"Found info.json in {folder_path}")
            with open(info_json_path, 'r') as f:
                info = json.load(f)
            
            # Logic for video
            if any(file.endswith((".mp4", ".mov", ".avi")) for file in os.listdir(folder_path)):
                print("Video file found. Processing video...")
                # Add your video processing logic here

            # Logic for images
            image_files = [file for file in os.listdir(folder_path) if file.endswith((".jpg", ".jpeg", ".png"))]
            if image_files:
                print("Image files found. Processing images...")
                self.upload_images(folder_path, image_files)

    def upload_images(self, folder_path, image_files):
        for image_file in image_files:
            image_path = os.path.join(folder_path, image_file)
            # In a real implementation, you would use a tool to upload the image and get a URL.
            # For this example, we'll just print a placeholder URL.
            print(f"Public URL for {image_file}: https://example.com/placeholder_url_for_{image_file}")

def start_watching():
    print(f"Watching for new folders in: {DOWNLOADS_DIR}")
    event_handler = NewFolderHandler()
    observer = Observer()
    observer.schedule(event_handler, DOWNLOADS_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # Before starting, we need to install watchdog
    try:
        import watchdog
    except ImportError:
        print("Watchdog library not found. Please install it by running: pip install watchdog")
    else:
        start_watching()

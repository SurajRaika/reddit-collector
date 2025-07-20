import os
import json
import shutil
import time
import threading

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Path to the downloads folder
DOWNLOADS_DIR = Path(__file__).resolve().parent.parent / "collector" / "downloads"


def upload_post(info: dict, media_paths: list[str]) -> bool:
    """
    Dummy upload function. Replace this with your actual upload logic.
    """
    print("Uploading:")
    print("  Title:", info.get("title"))
    print("  Author:", info.get("author"))
    print("  URL:", info.get("url"))
    print("  Media files:", media_paths)
    return False


def try_upload_post(post_folder: Path):
    info_path = post_folder / "info.json"
    if not info_path.exists():
        return  # Still incomplete, wait for info.json to appear

    try:
        with open(info_path, "r") as f:
            info = json.load(f)
    except json.JSONDecodeError:
        print(f"Skipping {post_folder.name} (invalid JSON)")
        return

    media_files = [str(p) for p in post_folder.rglob("*") 
                   if p.is_file() and p.name != "info.json"]

    if not media_files:
        print(f"Skipping {post_folder.name} (no media files)")
        return

    success = upload_post(info, media_files)

    if success:
        print(f"Uploaded: {post_folder.name}. Deleting folder.")
        shutil.rmtree(post_folder)
    else:
        print(f"Failed to upload: {post_folder.name}. Skipping delete.")


def process_existing_posts():
    print("Processing existing post folders...")
    for post_folder in sorted(DOWNLOADS_DIR.iterdir()):
        if post_folder.is_dir():
            try_upload_post(post_folder)


class DownloadFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            post_folder = Path(event.src_path)
            print(f"Detected new folder: {post_folder.name}")

            def wait_and_process():
                for _ in range(30):  # Wait up to 30 seconds
                    if (post_folder / "info.json").exists():
                        try_upload_post(post_folder)
                        return
                    time.sleep(1)
                print(f"Timeout waiting for info.json in {post_folder.name}")

            threading.Thread(target=wait_and_process, daemon=True).start()


def start_watching():
    print(f"Watching for new posts in: {DOWNLOADS_DIR}")
    observer = Observer()
    handler = DownloadFolderHandler()
    observer.schedule(handler, str(DOWNLOADS_DIR), recursive=False)
    observer.start()
    return observer


if __name__ == "__main__":
    if not DOWNLOADS_DIR.exists():
        print(f"Downloads folder not found at: {DOWNLOADS_DIR}")
        exit(1)

    # Step 1: Process all existing folders
    process_existing_posts()

    # Step 2: Start watching for new folders
    observer = start_watching()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher...")
        observer.stop()
    observer.join()

import os
import json
import shutil

from pathlib import Path

# Change this to your path if needed
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

    # Simulate successful upload
    return True


def process_and_upload():
    for post_folder in sorted(DOWNLOADS_DIR.iterdir()):
        if not post_folder.is_dir():
            continue
        
        info_path = post_folder / "info.json"
        if not info_path.exists():
            print(f"Skipping {post_folder.name} (missing info.json)")
            continue

        # Load post metadata
        try:
            with open(info_path, "r") as f:
                info = json.load(f)
        except json.JSONDecodeError:
            print(f"Skipping {post_folder.name} (invalid JSON)")
            continue

        # Find all media files (recursively)
        media_files = [str(p) for p in post_folder.rglob("*") 
                       if p.is_file() and p.name != "info.json"]

        if not media_files:
            print(f"Skipping {post_folder.name} (no media files)")
            continue

        # Try uploading
        success = upload_post(info, media_files)

        if success:
            print(f"Uploaded: {post_folder.name}. Deleting folder.")
            # shutil.rmtree(post_folder)
        else:
            print(f"Failed to upload: {post_folder.name}. Skipping delete.")


if __name__ == "__main__":
    if not DOWNLOADS_DIR.exists():
        print(f"Downloads folder not found at: {DOWNLOADS_DIR}")
        exit(1)

    process_and_upload()

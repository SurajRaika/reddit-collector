import json
import time
from datetime import datetime
from pathlib import Path

import requests
from RedDownloader import RedDownloader

CONFIG_FILE       = Path("config.json")
CACHE_FILE        = Path("downloaded_urls.txt")
BASE_DOWNLOAD_DIR = Path("downloads")
USER_AGENT_HEADER = {"User-Agent": "RedDownloaderScript/1.0"}
CONFIG = {}  # Global config dictionary

def load_config() -> dict:
    return json.loads(CONFIG_FILE.read_text())

def ensure_cache_file():
    CACHE_FILE.touch(exist_ok=True)

def already_downloaded(url: str) -> bool:
    return url in CACHE_FILE.read_text().splitlines()

def mark_downloaded(url: str):
    with open(CACHE_FILE, "a") as f:
        f.write(url + "\n")

def fetch_top_post(subreddit: str, sort: str = "hot", top_post_rank=0) -> dict:

    max_attempts_by_sort = CONFIG.get("max_attempts", {"hot": 2, "top": 2, "new": 1})
    max_allowed = max_attempts_by_sort.get(sort, 2)  # fallback to 2 if missing
    if max_allowed <= top_post_rank:
        return {}
    # Fetch top 10 (or more) to allow skipping already-downloaded posts
    api_url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit=10&raw_json=1"
    try:
        resp = requests.get(api_url, headers=USER_AGENT_HEADER, timeout=10)
        resp.raise_for_status()
        children = resp.json()["data"]["children"]
    except Exception as e:
        print(f"✖ Failed to fetch posts: {e}")
        return {}

    if not children or top_post_rank >= len(children):
        print("⚠ No more new posts available.")
        return {}

    post = children[top_post_rank]["data"]
    post_url = f"https://reddit.com{post.get('permalink', '')}"

    if already_downloaded(post_url):
        print(f"⚠ Post #{top_post_rank + 1} already downloaded, trying next...")
        return fetch_top_post(subreddit, sort, top_post_rank + 1)

    return post


def try_one(subreddit: str, sort: str, only_vid: bool = False) -> bool:
    print(f"→ Fetching r/{subreddit} ({sort}){'[VIDEOS ONLY]' if only_vid else ''}…")

    if only_vid:
        # Use RedDownloader.DownloadVideosBySubreddit for videos only
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder = BASE_DOWNLOAD_DIR / f"{ts}_{subreddit}_{sort}_videos"
        folder.mkdir(parents=True, exist_ok=True)

        dest = str(folder) + "/"

        try:
            file_obj = RedDownloader.DownloadVideosBySubreddit(
                Subreddit=subreddit,
                NumberOfPosts=1,
                SortBy=sort,
                output=f"video",
                destination=dest,
                verbose=True,
                cachefile=str(CACHE_FILE)
            )
            

            # Check if anything was downloaded
            if not any(folder.iterdir()):
                print("✖ No videos downloaded — folder is empty.")
                folder.rmdir()
                return False

            # Save basic info for batch download
            info = {
                "subreddit": subreddit,
                "sort_type": sort,
                "download_type": "videos_only",
                "downloaded": datetime.now().isoformat()
            }
            with open(folder / "info.json", "w", encoding="utf-8") as jf:
                json.dump(info, jf, indent=2, ensure_ascii=False)

            print(f"✔ Saved videos + info.json → {folder}")
            return True

        except Exception as e:
            print(f"✖ Video download failed: {e}")
            if not any(folder.iterdir()):
                folder.rmdir()
            return False

    else:
        # Original single post download logic
        post = fetch_top_post(subreddit, sort)
        if not post:
            print("⚠ No posts returned.")
            return False

        full_url = f"https://reddit.com{post.get('permalink','')}"
        if already_downloaded(full_url):
            print("⚠ Already downloaded, skipping.")
            return False

        print("→ Post title:", post.get("title"))
        print("→ Post hint:", post.get("post_hint", "N/A"))
        print("→ Reddit URL:", full_url)
        print("→ Media URL:", post.get("url", "N/A"))

        # Create folder for saving media
        ts      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        post_id = post.get("id", "unknown")
        folder  = BASE_DOWNLOAD_DIR / f"{ts}_{post_id}"
        folder.mkdir(parents=True, exist_ok=True)

        dest = str(folder) + "/"

        try:
            file_obj = RedDownloader.Download(
                full_url,
                output="image",
                destination=dest,
                verbose=True
            )

            # Check if anything was downloaded
            if not any(folder.iterdir()):
                print("✖ No media downloaded — folder is empty.")
                mark_downloaded(full_url)
                folder.rmdir()
                return False

            # Try getting media type
            if file_obj:
                try:
                    print("✔ Media Type:", file_obj.GetMediaType())
                except Exception:
                    print("⚠ Could not determine media type.")
            else:
                print("⚠ RedDownloader did not return any file object.")

        except Exception as e:
            print(f"✖ Download failed: {e}")
            if not any(folder.iterdir()):
                folder.rmdir()
            return False

        # Save post metadata
        info = {
            "title":      post.get("title", ""),
            "url":        full_url,
            "author":     post.get("author", ""),
            "text_body":  post.get("selftext", ""),
            "subreddit":  post.get("subreddit", ""),
            "sort_type":  sort,
            "downloaded": datetime.now().isoformat()
        }
        with open(folder / "info.json", "w", encoding="utf-8") as jf:
            json.dump(info, jf, indent=2, ensure_ascii=False)

        mark_downloaded(full_url)
        print(f"✔ Saved media + info.json → {folder}")
        return True

def main():
    if not CONFIG_FILE.exists():
        print("❌ config.json missing.")
        return
    global CONFIG
    CONFIG = load_config()
    cfg       = load_config()
    subreddit = cfg.get("subreddit", "india_tourism")
    interval  = cfg.get("interval_minutes", 10)
    subreddits = cfg.get("subreddits", [
        ["india_tourism", "hot", True],
        ["india_tourism", "hot", False],
        ["india_tourism", "top", False],
        ["IncredibleIndia", "top", False],
        ["india_tourism", "new", False],
    ])
    max_attempts = cfg.get("max_attempts", {"hot": 2, "top": 2, "new": 1})  # default fallback

    BASE_DOWNLOAD_DIR.mkdir(exist_ok=True)
    ensure_cache_file()

    print(f"[START] Processing {len(subreddits)} subreddit configurations every {interval} min")
    while True:

        for subreddit_name, sort_mode, vid_only in subreddits:
            if try_one(subreddit_name, sort_mode, vid_only):
                break
        else:
            print("⚠ Nothing downloaded this cycle.")
        print(f"[WAIT] {interval} minutes…\n")
        time.sleep(interval * 60)

if __name__ == "__main__":
    main()

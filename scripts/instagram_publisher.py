#!/usr/bin/env python3
"""
Instagram Content Publishing Client via Meta Graph API
Direct, free, and officially supported method to publish Reels on Instagram Professional accounts.
"""

import os
import time
import requests

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class InstagramPublisher:
    def __init__(self, ig_user_id=None, access_token=None):
        self.ig_user_id = ig_user_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")

    def check_connection(self):
        """Verifies access token validity and Instagram account connection."""
        url = f"{BASE_URL}/{self.ig_user_id}"
        params = {
            "fields": "id,username,name,biography,followers_count",
            "access_token": self.access_token
        }
        res = requests.get(url, params=params)
        res.raise_for_status()
        return res.json()

    def create_reel_container(self, video_url, caption):
        """Step 1: Create a media container for a Reel."""
        url = f"{BASE_URL}/{self.ig_user_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": self.access_token
        }
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return res.json().get("id")

    def wait_for_container(self, creation_id, timeout_sec=180):
        """Step 2: Poll container status until FINISHED."""
        url = f"{BASE_URL}/{creation_id}"
        params = {
            "fields": "status_code",
            "access_token": self.access_token
        }
        start = time.time()
        while time.time() - start < timeout_sec:
            res = requests.get(url, params=params).json()
            status = res.get("status_code")
            print(f"Container status: {status}")
            if status == "FINISHED":
                return True
            elif status == "ERROR":
                raise RuntimeError(f"Meta failed to process video: {res}")
            time.sleep(5)
        raise TimeoutError("Timed out waiting for Meta to transcode video.")

    def publish_container(self, creation_id):
        """Step 3: Publish the container to the Instagram account."""
        url = f"{BASE_URL}/{self.ig_user_id}/media_publish"
        payload = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return res.json().get("id")

    def publish_reel(self, video_url, caption):
        """End-to-end publishing pipeline."""
        print(f"Creating Reel container for {video_url}...")
        creation_id = self.create_reel_container(video_url, caption)
        print(f"Container created with ID: {creation_id}. Waiting for transcode...")
        self.wait_for_container(creation_id)
        print("Publishing Reel...")
        media_id = self.publish_container(creation_id)
        print(f"Reel successfully published! Media ID: {media_id}")
        return media_id

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Publish Reel to Instagram via Graph API")
    parser.add_argument("--check", action="store_true", help="Check account connection")
    parser.add_argument("--video-url", help="Public HTTPS URL of video")
    parser.add_argument("--caption", help="Caption text for Reel")
    args = parser.parse_args()

    client = InstagramPublisher()
    if args.check:
        print(client.check_connection())
    elif args.video_url and args.caption:
        client.publish_reel(args.video_url, args.caption)
    else:
        parser.print_help()

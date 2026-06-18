#!/usr/bin/env python3
"""
Scraper for app.revidapi.com/prompts
Fetches prompt metadata + full prompt_text via public API endpoints.

WARNING:
  - robots.txt of app.revidapi.com disallows /api/ for all user agents.
  - This script is for educational / personal research only.
  - Do not run a full 20k+ scrape without explicit permission from the site owner.
  - Respect rate limits, server load, and copyright of user-submitted prompts.

Usage:
  python tools/scraper.py --max-items 100 --delay 0.8
  python tools/scraper.py --max-items 0 --delay 0.8 --output data/prompts.json

After running, the output JSON is ready to be used by the static website.
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://app.revidapi.com"
LIST_ENDPOINT = f"{BASE_URL}/api/prompts"
DETAIL_ENDPOINT = f"{BASE_URL}/api/prompts"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://app.revidapi.com/prompts",
}

IMAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://app.revidapi.com/prompts",
}


def fetch_json(url, retries=3, backoff=1.0):
    """Fetch a JSON endpoint with retries and exponential backoff."""
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = backoff * (2 ** attempt)
                print(f"  Rate limited (429). Sleeping {wait}s...")
                time.sleep(wait)
                continue
            print(f"  HTTP error {e.code} for {url}: {e.reason}")
            if attempt == retries:
                return None
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            if attempt == retries:
                return None
        time.sleep(backoff * attempt)
    return None


def fetch_list_page(page, limit=50):
    """Fetch one page of prompt list."""
    params = {"page": page, "limit": limit}
    url = f"{LIST_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return fetch_json(url)


def fetch_detail(prompt_id):
    """Fetch full prompt details including prompt_text."""
    url = f"{DETAIL_ENDPOINT}/{prompt_id}"
    return fetch_json(url)


def download_image(url, path, retries=3, backoff=1.0):
    """Download an image to local path. Returns True on success."""
    if not url:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=IMAGE_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(path, "wb") as f:
                    f.write(resp.read())
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = backoff * (2 ** attempt)
                print(f"  Rate limited downloading image (429). Sleeping {wait}s...")
                time.sleep(wait)
                continue
            print(f"  HTTP error {e.code} downloading image: {e.reason}")
            if attempt == retries:
                return False
        except Exception as e:
            print(f"  Error downloading image {url}: {e}")
            if attempt == retries:
                return False
        time.sleep(backoff * attempt)
    return False


def local_image_path(source_id, url):
    """Generate a local image path from URL extension."""
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if not ext or ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif"}:
        ext = ".jpg"
    return f"assets/revid/{source_id}{ext}"


def map_to_website_format(detail, idx, local_image=None):
    """Convert revidapi detail object to website prompts.json format."""
    title = detail.get("title") or "Untitled prompt"
    prompt_text = detail.get("prompt_text") or ""
    description = detail.get("description") or ""
    model = detail.get("model") or "unknown"
    category = detail.get("category") or "general"
    media_type = detail.get("media_type") or "image"
    output_url = detail.get("output_url") or ""
    created_at = detail.get("created_at") or ""
    likes = detail.get("likes_count") or 0
    views = detail.get("views_count") or 0

    # Try to parse ISO date; fallback to today
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Build tags from model + category + media type
    tags = [model]
    if category and category.lower() not in tags:
        tags.append(category)
    if media_type and media_type.lower() not in tags:
        tags.append(media_type)

    # Estimate popularity score from likes/views mix
    popularity = int((likes * 10) + (views / 10))

    image = local_image if local_image else output_url

    return {
        "id": idx,
        "title": title.strip(),
        "tool": normalize_tool(model),
        "desc": description.strip() or title.strip(),
        "prompt": prompt_text.strip(),
        "tags": tags,
        "image": image,
        "date": date_str,
        "popular": min(popularity, 999),
        "source_id": detail.get("id"),
        "source": "revidapi",
        "model": model,
        "media_type": media_type,
    }


def normalize_tool(model_name):
    """Map revidapi model names to website tool keys."""
    if not model_name:
        return "unknown"
    m = model_name.lower()
    if "gpt" in m:
        return "chatgpt"
    if "gemini" in m:
        return "gemini"
    if "flux" in m:
        return "flux"
    if "midjourney" in m:
        return "midjourney"
    if "stable" in m or "sd" in m:
        return "stable-diffusion"
    # Default: categorize by model label from revidapi
    if "banana" in m:
        return "nano-banana"
    return "other"


def main():
    parser = argparse.ArgumentParser(description="Scrape prompts from app.revidapi.com")
    parser.add_argument("--max-items", type=int, default=100,
                        help="Maximum number of prompts to fetch (0 = unlimited, use with care)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Page size for list API (default 50)")
    parser.add_argument("--delay", type=float, default=0.8,
                        help="Delay in seconds between detail requests")
    parser.add_argument("--page-delay", type=float, default=1.0,
                        help="Delay in seconds between list pages")
    parser.add_argument("--output", type=str, default="data/prompts.json",
                        help="Output JSON file path for the website")
    parser.add_argument("--raw-output", type=str, default="data/revid_prompts_raw.json",
                        help="Raw combined output file path")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing raw output file")
    parser.add_argument("--merge", action="store_true",
                        help="Merge new prompts into existing output instead of overwriting")
    parser.add_argument("--media-type", type=str, default="image",
                        help="Filter by media_type: image, video, or all")
    parser.add_argument("--download-images", action="store_true",
                        help="Download demo images to local assets/ folder")
    parser.add_argument("--images-dir", type=str, default="assets/revid",
                        help="Local directory for downloaded images")
    parser.add_argument("--image-delay", type=float, default=0.5,
                        help="Delay in seconds between image downloads")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.raw_output) or ".", exist_ok=True)
    if args.download_images:
        os.makedirs(args.images_dir, exist_ok=True)

    raw_items = []
    if args.resume and os.path.exists(args.raw_output):
        print(f"Resuming from {args.raw_output}")
        with open(args.raw_output, "r", encoding="utf-8") as f:
            raw_items = json.load(f)
        print(f"Loaded {len(raw_items)} existing raw items")

    if not raw_items:
        page = 1
        fetched_count = 0
        max_items = args.max_items if args.max_items > 0 else float("inf")

        while True:
            print(f"Fetching list page {page} (limit {args.limit})...")
            data = fetch_list_page(page, args.limit)
            if not data or "prompts" not in data:
                print("No more list data or error. Stopping.")
                break

            prompts = data.get("prompts", [])
            total = data.get("total", 0)
            if not prompts:
                print("Empty page. Stopping.")
                break

            for item in prompts:
                if fetched_count >= max_items:
                    print(f"Reached max-items limit ({args.max_items}).")
                    break

                media_type = item.get("media_type", "image")
                if args.media_type != "all" and media_type != args.media_type:
                    continue

                raw_items.append(item)
                fetched_count += 1

            print(f"  Page {page}: {len(prompts)} items, total collected so far: {len(raw_items)} / {total}")

            if fetched_count >= max_items:
                break

            if len(prompts) < args.limit:
                print("Last page reached.")
                break

            page += 1
            time.sleep(args.page_delay)

        with open(args.raw_output, "w", encoding="utf-8") as f:
            json.dump(raw_items, f, ensure_ascii=False, indent=2)
        print(f"Saved raw list to {args.raw_output}")

    # Fetch details for each item
    details = []
    output_base = os.path.splitext(args.output)[0]
    resume_detail_path = f"{output_base}_details.json"

    if args.resume and os.path.exists(resume_detail_path):
        print(f"Resuming details from {resume_detail_path}")
        with open(resume_detail_path, "r", encoding="utf-8") as f:
            details = json.load(f)
        print(f"Loaded {len(details)} existing detail items")

    completed_ids = {d.get("id") for d in details}
    print(f"Fetching details for {len(raw_items)} prompts with {args.delay}s delay...")

    for i, item in enumerate(raw_items):
        prompt_id = item.get("id")
        if prompt_id in completed_ids:
            continue

        print(f"[{i+1}/{len(raw_items)}] Detail for prompt {prompt_id}...")
        detail = fetch_detail(prompt_id)
        if detail:
            details.append(detail)
            completed_ids.add(prompt_id)

            # Periodically save resume file
            if len(details) % 20 == 0:
                with open(resume_detail_path, "w", encoding="utf-8") as f:
                    json.dump(details, f, ensure_ascii=False, indent=2)
        else:
            print(f"  Skipping prompt {prompt_id} due to fetch error.")

        time.sleep(args.delay)

    with open(resume_detail_path, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print(f"Saved raw details to {resume_detail_path}")

    # Download images if requested
    image_paths = {}  # source_id -> local path
    if args.download_images:
        print(f"\nDownloading images to {args.images_dir}...")
        skipped_existing = 0
        for i, detail in enumerate(details):
            source_id = detail.get("id")
            output_url = detail.get("output_url") or ""
            if not output_url:
                continue
            local_path = os.path.join(args.images_dir, os.path.basename(local_image_path(source_id, output_url)))
            rel_path = local_path.replace("\\", "/")

            # Skip if image already exists locally
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                image_paths[source_id] = rel_path
                skipped_existing += 1
                continue

            print(f"[{i+1}/{len(details)}] Download image for prompt {source_id}...")
            if download_image(output_url, local_path):
                image_paths[source_id] = rel_path
            else:
                image_paths[source_id] = output_url
            time.sleep(args.image_delay)
        print(f"Downloaded images for {len(image_paths)} prompts ({skipped_existing} already existed)")

    # Convert to website format
    website_prompts = []
    existing_source_ids = set()

    if args.merge and os.path.exists(args.output):
        print(f"\nMerging with existing {args.output}...")
        with open(args.output, "r", encoding="utf-8") as f:
            existing = json.load(f)
        for p in existing:
            sid = p.get("source_id")
            if sid:
                existing_source_ids.add(sid)
            website_prompts.append(p)
        print(f"Loaded {len(website_prompts)} existing prompts")

    new_count = 0
    for detail in details:
        source_id = detail.get("id")
        if source_id in existing_source_ids:
            continue
        existing_source_ids.add(source_id)
        local_img = image_paths.get(source_id)
        mapped = map_to_website_format(detail, len(website_prompts) + 1, local_image=local_img)
        if mapped["prompt"] or mapped["image"]:
            website_prompts.append(mapped)
            new_count += 1

    # Sort by date descending to keep newest first
    website_prompts.sort(key=lambda x: x.get("date", ""), reverse=True)
    # Reassign sequential IDs after sort/merge
    for idx, p in enumerate(website_prompts, start=1):
        p["id"] = idx

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(website_prompts, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Wrote {len(website_prompts)} prompts to {args.output} ({new_count} new)")
    print(f"Raw list saved to {args.raw_output}")
    print(f"Raw details saved to {resume_detail_path}")
    if args.download_images:
        print(f"Images saved to {args.images_dir}")


if __name__ == "__main__":
    main()

import os
import datetime
import csv
import isodate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_youtube_service():
    if not API_KEY:
        raise ValueError("Error: YOUTUBE_API_KEY not found in environment variables.")
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def get_most_popular_videos(youtube, region_code='US', max_results_per_category=50):
    """
    Fetches most popular videos by specific categories to improve Shorts yield.
    Categories: Comedy(23), Gaming(20), Entertainment(24), Sports(17), People & Blogs(22)
    """
    # High-density Shorts categories
    target_categories = [
        ('15', 'Animals & Pets') # Added Animals & Pets
    ]
    
    all_videos = {} # Use dict to deduplicate by ID
    
    print(f"Requesting top videos from {len(target_categories)} specific categories (Region: {region_code})...")
    
    for cat_id, cat_name in target_categories:
        print(f"  Fetching Category: {cat_name} ({cat_id})...", end=" ")
        try:
            request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                chart="mostPopular",
                regionCode=region_code,
                videoCategoryId=cat_id,
                maxResults=max_results_per_category
            )
            response = request.execute()
            items = response.get('items', [])
            print(f"Got {len(items)} items.")
            
            for item in items:
                all_videos[item['id']] = item
                
        except HttpError as e:
            print(f"\n  Error fetching category {cat_name}: {e}")
            
    unique_videos = list(all_videos.values())
    print(f"\nTotal unique videos fetched: {len(unique_videos)}")
    return unique_videos

def parse_duration(duration_iso):
    try:
        dt = isodate.parse_duration(duration_iso)
        return dt.total_seconds()
    except Exception:
        return 0

def is_short(video):
    """
    Checks if a video is likely a Short based on duration.
    As of late 2024, Shorts can be up to 3 minutes (180 seconds).
    """
    duration_iso = video['contentDetails']['duration']
    seconds = parse_duration(duration_iso)
    # Duration <= 60 seconds (1 min)
    return seconds <= 60 and seconds > 0

def filter_videos(videos):
    filtered_videos = []
    
    # Statistics counters
    stats = {
        'total': len(videos),
        'music_excluded': 0,
        'duration_excluded': 0,
        'old_excluded': 0,
        'kept': 0
    }
    
    now = datetime.datetime.now(datetime.timezone.utc)
    
    for video in videos:
        # Step 3: Category Filter
        # Exclude Music (10)
        category_id = video['snippet'].get('categoryId')
        if category_id == '10':
            stats['music_excluded'] += 1
            continue
            
        # Step 2: Format Filter (Shorts Check)
        if not is_short(video):
            stats['duration_excluded'] += 1
            continue
            
        # Step 4: Viral Velocity Analysis
        published_at_str = video['snippet']['publishedAt']
        published_at = isodate.parse_datetime(published_at_str)
        
        # Calculate hours since published
        time_diff = now - published_at
        hours_since_published = time_diff.total_seconds() / 3600
        
        # Freshness: Published < 48 hours
        if hours_since_published >= 48 or hours_since_published <= 0:
            stats['old_excluded'] += 1
            continue
            
        view_count = int(video['statistics'].get('viewCount', 0))
        
        # Calculate VPH
        vph = view_count / hours_since_published if hours_since_published > 0 else 0
        
        video_data = {
            'Rank': 0,
            'Title': video['snippet']['title'],
            'Channel': video['snippet']['channelTitle'],
            'Views': view_count,
            'VPH': int(vph),
            'Published_Time': published_at_str,
            'URL': f"https://www.youtube.com/shorts/{video['id']}"
        }
        filtered_videos.append(video_data)
        stats['kept'] += 1

    # Print stats
    print("\n=== Filtering Statistics ===")
    print(f"Total videos processed: {stats['total']}")
    print(f"[-] Excluded Music (Cat 10): {stats['music_excluded']}")
    print(f"[-] Excluded Duration (> 3m): {stats['duration_excluded']}")
    print(f"[-] Excluded Old (> 48h): {stats['old_excluded']}")
    print(f"[=] Candidates Remaining: {stats['kept']}")
    print("============================")
        
    return filtered_videos

def main():
    print("Initializing YouTube Shorts Monitor (Updated Dec 2025)...")
    
    try:
        youtube = get_youtube_service()
    except ValueError as e:
        print(e)
        print("Please ensure your .env file has the correct YOUTUBE_API_KEY.")
        return

    # Fetch videos using Category Scanning strategy
    raw_videos = get_most_popular_videos(youtube)
    
    print("Filtering and analyzing data...")
    processed_videos = filter_videos(raw_videos)
    
    # Sort by VPH descending
    processed_videos.sort(key=lambda x: x['VPH'], reverse=True)
    
    # Add Rank
    for idx, video in enumerate(processed_videos):
        video['Rank'] = idx + 1
        
    print(f"\nFound {len(processed_videos)} viral shorts.")
    
    # Output to CSV
    output_file = "viral_shorts.csv"
    if processed_videos:
        keys = processed_videos[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(processed_videos)
        print(f"Report saved to {output_file}")
        
        # Print top 5 to console
        print("\nTop 5 Viral Shorts:")
        print(f"{'Rank':<5} {'VPH':<10} {'Title'}")
        print("-" * 60)
        for v in processed_videos[:5]:
            print(f"{v['Rank']:<5} {v['VPH']:<10} {v['Title'][:40]}...")
    else:
        print("No viral shorts found. Try relaxing the filters or changing the region.")

if __name__ == "__main__":
    main()
import yt_dlp
import pandas as pd
import datetime
from src.utils.config import COOKIES_FILE, ONLINE_DATA_FILE, USERNAME



def run_web_scraping():
    print(f"Scraping data for user: {USERNAME}...")
    
    ydl_opts ={
        'extract_flat': True,
        'dump_single_json': True,
        'quiet': True,
        'ignoreerrors': True,
        'cookiefile': str(COOKIES_FILE) #updated the cookie logic, now it takes the cookies straight from the file
    }
    data = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        url = f"https://www.tiktok.com/@{USERNAME}"
        try:
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                print("Error: Could not retrieve data.")
                return

            if 'entries' in info:
                total_videos = len(info['entries'])
                print(f"Found {total_videos} videos. Processing...")

                for i, video in enumerate(info['entries']):
                    video_id = video.get('id')
                    
                    # If yt-dlp doesn't give a URL, we build it ourselves
                    web_url = video.get('webpage_url')
                    if not web_url and video_id:
                        web_url = f"https://www.tiktok.com/@{USERNAME}/video/{video_id}"

                    # TikTok often gives a 'timestamp' (numbers) instead of 'upload_date'
                    timestamp = video.get('timestamp')
                    upload_date = "Unknown"
                    
                    if timestamp:
                        # Convert Unix timestamp to YYYY-MM-DD
                        upload_date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                    else:
                        # Fallback to standard yt-dlp format
                        upload_date = video.get('upload_date', 'Unknown')

                    stats = {
                        "Title": video.get('title', ''),
                        "Video_ID": video_id,
                        "Views": video.get('view_count', 0),
                        "Likes": video.get('like_count', 0),
                        "Comments": video.get('comment_count', 0),
                        "Shares": video.get('repost_count', 0),
                        "Duration_Online": video.get('duration', 0),
                        "Upload_Date": upload_date,
                        "Web_URL": web_url
                    }
                    data.append(stats)
                    
                    if i % 10 == 0:
                        print(f"Processed {i}/{total_videos}...")
            else:
                print("No videos found!")

        except Exception as e:
            print(f"Error: {e}")

    # Save to CSV
    if data:
        df = pd.DataFrame(data)
        df.to_csv(ONLINE_DATA_FILE, index=False)
        print(f"\nSuccess! Scraped {len(df)} rows to {ONLINE_DATA_FILE}")
    else:
        print("\nFailed to scrape data.")

if __name__ == "__main__":
    run_web_scraping()
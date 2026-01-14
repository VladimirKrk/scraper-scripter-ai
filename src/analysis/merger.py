import pandas as pd
from rapidfuzz import fuzz, process
from datetime import datetime, timedelta
import re
from src.utils.config import LOCAL_DATA_FILE, ONLINE_DATA_FILE, MERGED_DATA_FILE
#configuration imported 

def run_merge():
    print("Starting Smart Merge (Duration + Date)")

    if not LOCAL_DATA_FILE.exists() or not ONLINE_DATA_FILE.exists():
        print("Error missing input files")
        return
    
    local_df = pd.read_csv(LOCAL_DATA_FILE)
    online_df = pd.read_csv(ONLINE_DATA_FILE)

    #converting dates to datetime obj
    local_df['File_Creation_Date'] = pd.to_datetime(local_df['File_Creation_Date'], errors='coerce')
    online_df['Upload_Date'] = pd.to_datetime(online_df['Upload_Date'], errors='coerce')

    online_df['matched'] = False
    matches = []
    matched_idx = [] 

    print(f"Local files: {len(local_df)}")
    print(f"Online videos: {len(online_df)}")


    for _,local_row in local_df.iterrows():
        l_dur = local_row['Duration_Sec']
        l_date = local_row['File_Creation_Date']
        l_name = str(local_row['Filename']).lower().replace(".mp4","")

        candidates = online_df[
            (online_df['Duration_Online'] >= l_dur - 1.0) &
            (online_df['Duration_Online'] <= l_dur + 1.0) &
            (online_df['matched'] == False)
        ].copy()

        if candidates.empty:
            continue


        #--scoring--

        best_score = -1
        best_idx = -1

        for idx, online_row in candidates.iterrows():
            current_score = 0

            #dates 
            if pd.notnull(l_date) and pd.notnull(online_row['Upload_Date']):
                o_date = online_row['Upload_Date']
                days_diff = (o_date - l_date).days

                if -1 <= days_diff <= 3:
                    current_score +=50
                elif 3 < days_diff <= 14:
                    current_score +=20
                elif 14 < days_diff <= 60:
                    current_score -= 20
                elif days_diff < -2:
                    current_score -=100

            #duration
            dur_diff  = abs(online_row['Duration_Online'] - l_dur)
            if dur_diff < 0.1:
                current_score +=30
            
            #text
            title = str(online_row['Title']).lower()
            text_score = fuzz.partial_ratio(l_name, title)

            current_score += (text_score * 0.3)

            if current_score > best_score:
                best_score = current_score
                best_idx = idx

            THRESHOLD = 50
            if best_idx != -1 and best_score >THRESHOLD and best_idx not in matched_idx:
                matched_idx.append(best_idx)
                online_row = online_df.loc[best_idx]

                merged_row = {**local_row.to_dict(), **online_row.to_dict()}
                if pd.notnull(l_date):
                    merged_row['File_Creation_Date'] = l_date.strftime('%Y-%m-%d')
                if pd.notnull(online_row['Upload_Date']):
                    merged_row['Upload_Date'] = online_row['Upload_Date'].strftime('%Y-%m-%d')

                matches.append(merged_row)
                online_df.at[best_idx, 'matched'] = True

    final_df = pd.DataFrame(matches)
    final_df.to_csv(MERGED_DATA_FILE, index=False)

    match_rate = len(final_df) / len(local_df) * 100
    print("-" * 30)
    print("Mergin complete")
    print(f"Matches found: {len(final_df)} / {len(local_df)} , with {match_rate} matching rate")
    print(f"Saved to {MERGED_DATA_FILE}")


if __name__ == "__main__":
    run_merge()
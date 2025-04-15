import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

def fetch_all_nse_announcements(start_date_str="01-01-2024"):
    all_announcements = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Load NSE homepage (for cookies)
        page.goto("https://www.nseindia.com", timeout=15000)
        page.wait_for_timeout(3000)

        # Step 2: Loop from start_date to today, 1-day intervals
        start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
        end_date = datetime.today()

        while start_date <= end_date:
            from_date_str = start_date.strftime("%d-%m-%Y")
            to_date_str = start_date.strftime("%d-%m-%Y")  # same day, since the API doesn't support large ranges

            url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&from_date={from_date_str}&to_date={to_date_str}"
            response = page.request.get(url)

            if response.status == 200:
                data = response.json()
                items = data if isinstance(data, list) else data.get("data", [])
                all_announcements.extend(items)
                print(f"✅ Fetched {len(items)} announcements for {from_date_str}")
            else:
                print(f"❌ Failed on {from_date_str} with status: {response.status}")

            # Move to next day
            start_date += timedelta(days=1)

        browser.close()

    # Convert to DataFrame and save
    if all_announcements:
        df = pd.DataFrame(all_announcements)
        df = df.rename(columns={
            "symbol": "symbol",
            "sm_name": "companyName",
            "desc": "subject",
            "an_dt": "announcementDate",
            "attchmntText": "desc",
            "smIndustry": "sector",
            "sort_date": "pdate"
        })

        # Add missing columns if not present
        for col in ["exDate", "recordDate"]:
            if col not in df.columns:
                df[col] = ""

        # Final columns to keep in JSON
        df = df[[
            "symbol",
            "companyName",
            "subject",
            "desc",               # this is the full description
            "sector",
            "announcementDate",
            "exDate",
            "recordDate",
            "pdate"               # parsed datetime for sorting or filtering
        ]]
        df = df.sort_values("pdate", ascending=False)

        df.to_json("nse_all_announcements.json", indent=2, orient="records")
        print(f"✅ Total announcements saved: {len(df)}")
    else:
        print("⚠️ No announcements found.")

fetch_all_nse_announcements("10-04-2025")
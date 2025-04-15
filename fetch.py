import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

def fetch_all_nse_corporate_actions(start_date_str="01-01-2024"):
    all_actions = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Load homepage for cookies
        page.goto("https://www.nseindia.com", timeout=15000)
        page.wait_for_timeout(3000)

        start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
        end_date = datetime.today()

        while start_date <= end_date:
            from_date_str = start_date.strftime("%d-%m-%Y")
            to_date_str = start_date.strftime("%d-%m-%Y")

            url = f"https://www.nseindia.com/api/corporate-actions?index=equities&from_date={from_date_str}&to_date={to_date_str}"
            response = page.request.get(url)

            if response.status == 200:
                data = response.json()
                items = data.get("data", []) if isinstance(data, dict) else data
                all_actions.extend(items)
                print(f"✅ Fetched {len(items)} actions for {from_date_str}")
            else:
                print(f"❌ Failed on {from_date_str} with status: {response.status}")

            start_date += timedelta(days=1)

        browser.close()

    # Process and save the data
    if all_actions:
        df = pd.DataFrame(all_actions)

        df = df.rename(columns={
            "symbol": "symbol",
            "companyName": "companyName",
            "subject": "actionType",
            "exDate": "exDate",
            "recordDate": "recordDate",
            "bcStartDate": "bookClosureStart",
            "bcEndDate": "bookClosureEnd",
            "ndStartDate": "noDeliveryStart",
            "ndEndDate": "noDeliveryEnd",
            "remarks": "remarks"
        })

        for col in ["bookClosureStart", "bookClosureEnd", "noDeliveryStart", "noDeliveryEnd", "remarks"]:
            if col not in df.columns:
                df[col] = ""

        df = df[[
            "symbol",
            "companyName",
            "actionType",
            "exDate",
            "recordDate",
            "bookClosureStart",
            "bookClosureEnd",
            "noDeliveryStart",
            "noDeliveryEnd",
            "remarks"
        ]]

        df.to_json("nse_corporate_actions.json", indent=2, orient="records")
        print(f"✅ Total corporate actions saved: {len(df)}")
    else:
        print("⚠️ No corporate actions found.")

# Example call
fetch_all_nse_corporate_actions("01-04-2025")

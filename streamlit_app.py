import streamlit as st
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Function to fetch place odds
def fetch_place_odds(race_no):
    api_url = f"https://racing.stheadline.com/api/raceOdds/latest?raceNo={race_no}&type=win,place,quin,place-quin&rev=2"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        r.raise_for_status()
        json_data = r.json()
    except requests.RequestException as e:
        st.error(f"Error fetching odds: {e}")
        return {}

    race_odds_list = json_data.get("data", {}).get("place", {}).get("raceOddsList", [])
    odds = {}
    for item in race_odds_list:
        horse_no = item.get("horseNo1")
        value = item.get("value")
        if horse_no and value > 0:
            odds[horse_no] = value
    return odds

# Dutching calculator
def dutching_calculator(selected_horses, odds, total_stake):
    inverse_sum = sum(1 / odds[h] for h in selected_horses)
    stakes = {h: total_stake / (odds[h] * inverse_sum) for h in selected_horses}
    potential_profit = {h: stakes[h] * odds[h] for h in selected_horses}
    return stakes, potential_profit

# Streamlit layout
st.title("🏇 HKJC Place Odds & Dutching Calculator")

# Sidebar inputs
race_no = st.sidebar.number_input("Select Race Number:", min_value=1, max_value=12, value=1, step=1)
total_stake = st.sidebar.number_input("Total Stake (HKD):", min_value=0.0, value=100.0, step=10.0)
auto_refresh = st.sidebar.checkbox("Auto-refresh every 15s", value=True)

# Auto-refresh
if auto_refresh:
    st_autorefresh(interval=15*1000, key="refresh")

# Fetch odds
odds = fetch_place_odds(race_no)

if not odds:
    st.warning("No Place odds available.")
else:
    st.subheader(f"Race {race_no} - Place Odds")
    df = pd.DataFrame(list(odds.items()), columns=["Horse No", "Place Odd"])
    st.dataframe(df)

    # Horse selection with unique key
    selected_horses = st.multiselect(
        "Select horses to bet on:",
        options=list(odds.keys()),
        key=f"select_horses_{race_no}"
    )

    if selected_horses:
        stakes, profit = dutching_calculator(selected_horses, odds, total_stake)
        result_df = pd.DataFrame({
            "Horse": list(stakes.keys()),
            "Bet Amount (HKD)": [round(v, 2) for v in stakes.values()],
            "Potential Return (HKD)": [round(v, 2) for v in profit.values()]
        })
        st.subheader("💰 Dutching Allocation")
        st.dataframe(result_df)
        expected_profit = round(list(profit.values())[0] - total_stake, 2)
        st.write(f"Expected Profit (approx, same for all selected horses): **{expected_profit} HKD**")

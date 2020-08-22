import lxml.html
import pandas as pd
from datetime import datetime

def parse_cents(s):
    return int(s.replace('.',''))

def unmangle_name(s):
    s = s.replace("ÃP", "P")
    s = s.replace("Ãv", "v")
    s = s.replace("Ãp", "p")
    s = s.replace("ÃÃ", "Ã")
    return str(bytes(s, 'latin-1'), 'utf-8')

def add_date_columns(df):
    df["weekday"] = df["date"].map(lambda d : d.weekday())
    df["month"] = df["date"].map(lambda d : d.month)
    df["hour"] = df["date"].map(lambda d : d.hour)

def read_from_file(filename):

    f = open(filename, 'r', encoding="utf-8")
    s = f.read()
    tree = lxml.html.fromstring(s)
    events = tree.cssselect('.right code')[:-1] # skip final line

    print("Found",len(events),"RV events")

    buy_data = []
    deposit_data = []

    for e in events:
        event_text = e.text_content()
        tokens = event_text.split()
        datetime_str = ' '.join(tokens[:2])
        date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        event_type = tokens[3]

        if event_type == "deposited":
            deposit_amount = tokens[4]
            deposit_record = {
                "date": date,
                "amount_cents": parse_cents(deposit_amount)
            }
            deposit_data.append(deposit_record)
        else: # bought
            item_price = tokens[-2]
            item_name = ' '.join(tokens[4:-3])
            buy_record = {
                "date": date,
                "price_cents": parse_cents(item_price),
                "item": unmangle_name(item_name)
            }
            buy_data.append(buy_record)

    buy_df = pd.DataFrame.from_records(buy_data)
    buy_df.sort_values(by=["date"], inplace=True)

    deposit_df = pd.DataFrame.from_records(deposit_data)
    deposit_df.sort_values(by=["date"], inplace=True)

    buy_df["cumulative_buys"] = buy_df["price_cents"].cumsum()
    deposit_df["cumulative_deposits"] = deposit_df["amount_cents"].cumsum()

    add_date_columns(buy_df)
    add_date_columns(deposit_df)

    buy_df["amount_cents"] = buy_df["price_cents"].map(lambda x: -x)
    balance_df = pd.concat(
        [buy_df[["date", "amount_cents"]], deposit_df[["date", "amount_cents"]]],
        ignore_index=True
    ).sort_values(by=["date"]).reset_index(drop=True)
    balance_df["balance"] = balance_df["amount_cents"].cumsum()

    return buy_df, deposit_df, balance_df

if __name__ == "__main__":
    buy_df, deposit_df, _ = read_from_file("rv.html")

    print(buy_df.describe())
    print(buy_df.head())
    print(buy_df["item"].nunique())

    hourly = buy_df.groupby("hour", as_index=False)
    print(hourly["price_cents"].sum())
    print(hourly["price_cents"].count())

    hourly_daily_counts = buy_df.groupby(["hour", "weekday"], as_index=False)["price_cents"].count()
    print(hourly_daily_counts)
    hourly_daily_mat = hourly_daily_counts.pivot_table(columns="weekday", index="hour", values="price_cents")
    print(hourly_daily_mat.values)

    item_counts = buy_df.groupby("item")["item"].count().sort_values(ascending=False)
    print(list(item_counts.head().index))

    buy_df["amount_cents"] = buy_df["price_cents"].map(lambda x: -x)
    balance_df = pd.concat(
        [buy_df[["date", "amount_cents"]], deposit_df[["date", "amount_cents"]]],
        ignore_index=True
    ).sort_values(by=["date"]).reset_index(drop=True)
    balance_df["balance"] = balance_df["amount_cents"].cumsum()
    balance_df["is_negative"] = balance_df["balance"] < 0
    print(balance_df.head())
    print(len(balance_df))
    print(len(buy_df))
    print(len(deposit_df))
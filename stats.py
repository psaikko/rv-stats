import lxml.html
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

f = open("rv.html", 'r', encoding="utf-8")
s = f.read()

tree = lxml.html.fromstring(s)

title_elem = tree.cssselect('title')[0]

print(title_elem.text_content())

events = tree.cssselect('.right code')[:-1] # skip final line

print("Found",len(events),"events")

buy_data = []
deposit_data = []

def parse_cents(s):
    return int(s.replace('.',''))

def unmangle_name(s):
    s = s.replace("ÃP", "P")
    s = s.replace("Ãv", "v")
    s = s.replace("Ãp", "p")
    s = s.replace("ÃÃ", "Ã")
    return str(bytes(s, 'latin-1'), 'utf-8')

for e in events:
    event_text = e.text_content()
    tokens = event_text.split()
    datetime_str = ' '.join(tokens[:2])
    date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    user = tokens[2]
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

print(buy_df.describe())
print(buy_df.head())
print(buy_df["item"].nunique())

buy_df["cumulative_buys"] = buy_df["price_cents"].cumsum()
deposit_df["cumulative_deposits"] = deposit_df["amount_cents"].cumsum()

buy_df["weekday"] = buy_df["date"].map(lambda d : d.weekday())
buy_df["month"] = buy_df["date"].map(lambda d : d.month)
buy_df["hour"] = buy_df["date"].map(lambda d : d.hour)

deposit_df["weekday"] = deposit_df["date"].map(lambda d : d.weekday())
deposit_df["month"] = deposit_df["date"].map(lambda d : d.month)
deposit_df["hour"] = deposit_df["date"].map(lambda d : d.hour)

hourly = buy_df.groupby("hour", as_index=False)
print(hourly["price_cents"].sum())
print(hourly["price_cents"].count())

hourly_daily_counts = buy_df.groupby(["hour", "weekday"], as_index=False)["price_cents"].count()
print(hourly_daily_counts)
hourly_daily_mat = hourly_daily_counts.pivot_table(columns="weekday", index="hour", values="price_cents")

print(hourly_daily_mat.values)

fig1 = px.histogram(buy_df,
    labels={'price_cents':"purchases", 'hour':"Hour of day"},
    x="hour", 
    y="price_cents", 
    nbins=24)
fig1['layout']['title'] = "Total purchases by hour"

fig_coffee = px.histogram(buy_df[buy_df["item"] == "Coffee"],
    labels={'price_cents':"coffees", 'hour':"Hour of day"},
    x="hour", 
    y="price_cents",
    histfunc="count",
    nbins=24)
fig_coffee['layout']['title'] = "Total coffee consumption by hour"
fig_coffee.update_traces(marker_color='saddlebrown')

fig2 = go.Figure(
    data=go.Heatmap(
        z=hourly_daily_mat.fillna(0).values,
        x=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 
        y=sorted(buy_df["hour"].unique()))
)
fig2['layout']['yaxis']['autorange'] = "reversed"
fig2['layout']['title'] = "Activity map"

fig3 = go.Figure(data=[
    go.Scatter(x=buy_df["date"], y=buy_df["cumulative_buys"], mode="lines", name="purchases"),
    go.Scatter(x=deposit_df["date"], y=deposit_df["cumulative_deposits"], mode="lines", name="deposits")
])


app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='RV Stats'),

    html.Div(children='''
        Your RV data, visualized!.
    '''),

    dcc.Graph(
        id='hourly-buys',
        figure=fig1
    ),
    dcc.Graph(
        id='hourly-coffee',
        figure=fig_coffee
    ),
    dcc.Graph(
        id='time-heatmap',
        figure=fig2
    ),
    dcc.Graph(
        id="cumulative-buys",
        figure=fig3
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
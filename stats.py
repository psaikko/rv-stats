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

print(buy_df.describe())
print(buy_df.head())
print(buy_df["item"].nunique())

buy_df["weekday"] = buy_df["date"].map(lambda d : d.weekday())
buy_df["month"] = buy_df["date"].map(lambda d : d.month)
buy_df["hour"] = buy_df["date"].map(lambda d : d.hour)

hourly = buy_df.groupby("hour", as_index=False)
print(hourly["price_cents"].sum())
print(hourly["price_cents"].count())

fig1 = px.histogram(buy_df,
    x="hour", 
    y="price_cents", 
    nbins=24)

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

])

if __name__ == '__main__':
    app.run_server(debug=True)
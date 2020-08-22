import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
from rvdata import read_from_file

buy_df, deposit_df = read_from_file("rv.html")

hourly_daily_counts = buy_df.groupby(["hour", "weekday"], as_index=False)["price_cents"].count()
hourly_daily_mat = hourly_daily_counts.pivot_table(columns="weekday", index="hour", values="price_cents").fillna(0)

fig_hourly = px.histogram(buy_df,
    labels={'price_cents':"purchases", 'hour':"Hour of day"},
    x="hour", 
    y="price_cents", 
    nbins=24)
fig_hourly['layout']['title'] = "Total purchases by hour"

fig_coffee = px.histogram(buy_df[buy_df["item"] == "Coffee"],
    labels={'price_cents':"coffees", 'hour':"Hour of day"},
    x="hour", 
    y="price_cents",
    histfunc="count",
    nbins=24)
fig_coffee['layout']['title'] = "Total coffee consumption by hour"
fig_coffee.update_traces(marker_color='saddlebrown')

fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=hourly_daily_mat.values,
        x=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 
        y=sorted(buy_df["hour"].unique()))
)
fig_heatmap['layout']['yaxis']['autorange'] = "reversed"
fig_heatmap['layout']['title'] = "Activity map"

fig_cumulative = go.Figure(data=[
    go.Scatter(x=buy_df["date"], y=buy_df["cumulative_buys"], mode="lines", name="purchases"),
    go.Scatter(x=deposit_df["date"], y=deposit_df["cumulative_deposits"], mode="lines", name="deposits")
])
fig_cumulative['layout']['title'] = "Cumulative deposits and purchases"

item_purchase_counts = buy_df.groupby("item")["item"].count().sort_values(ascending=False)
top_list_rows = []
for i, (item, count) in enumerate(item_purchase_counts.head(7).items()):
    top_list_rows.append(html.Tr([
            html.Td(str(i+1)),
            html.Td(item),
            html.Td(str(count))
        ]))
top_list = html.Table([
    html.Thead(
        html.Tr([html.Th(col) for col in ["Rank", "Item", "Count"]])
    ),
    html.Tbody(top_list_rows)
])

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

app.layout = html.Div(children=[
    html.H1(children='RV Stats'),

    html.Div(children='''
        Your RV data, visualized!.
    '''),
    html.H3(children="Top buys"),

    html.Div(children=[
        html.Div(
            top_list, 
            style={'display': 'inline-block', 'vertical-align': 'top'}
        ),
        html.Div(
            dcc.Graph(
                id='hourly-buys',
                figure=fig_hourly
        ), style={'display': 'inline-block'})
    ]),

    html.Div(children=[
        html.Div(
            dcc.Graph(
                id='hourly-coffee',
                figure=fig_coffee
            ), style={'display': 'inline-block'}),
        html.Div(
            dcc.Graph(
                id='time-heatmap',
                figure=fig_heatmap
            ), style={'display': 'inline-block'})
    ]),

    dcc.Graph(
        id="cumulative-buys",
        figure=fig_cumulative
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output
from rvdata import read_from_network, read_from_file

def add_range_slider(fig):
    # https://plotly.com/python/range-slider/#range-slider-with-vertically-stacked-subplots
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label="1m",
                        step="month",
                        stepmode="backward"),
                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="YTD",
                        step="year",
                        stepmode="todate"),
                    dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

buy_df, deposit_df, balance_df = read_from_file("rv.html")

hourly_daily_counts = buy_df.groupby(["hour", "weekday"], as_index=False)["price_cents"].count()
hourly_daily_mat = hourly_daily_counts.pivot_table(columns="weekday", index="hour", values="price_cents").fillna(0)

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

fig_balance = go.Figure()
fig_balance.add_trace(
    go.Scatter(
        x=balance_df["date"], 
        y=balance_df["balance"] * (balance_df["balance"] >= 0), 
        fill='tozeroy',
        name="Positive",
        line=dict(color='green')))
fig_balance.add_trace(
    go.Scatter(
        x=balance_df["date"], 
        y=balance_df["balance"] * (balance_df["balance"] < 0), 
        fill='tozeroy',
        name="Negative",
        line=dict(color='red')))
fig_balance['layout']['title'] = "Account balance"
add_range_slider(fig_balance)

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

app.layout = html.Div(children=[
    html.H1(children='RV Stats'),

    html.Div(children='''
        Your RV data, visualized!.
    '''),

    

    html.Div(children=[
        html.Div(
            [html.H3(children="Top buys"),
            top_list], 
            className="six columns"
        ),
        html.Div(
            dcc.Graph(
                id='time-heatmap',
                figure=fig_heatmap
            ), className="six columns"
        )
    ], className="row"),

    html.Div([
        html.Div([
            dcc.Graph(
                id='hourly-buys'
            ),
            dcc.RangeSlider(
                id='year-range-slider',
                min=balance_df['year'].min(),
                max=balance_df['year'].max(),
                value=[balance_df['year'].min(), balance_df['year'].max()],
                marks={str(year): str(year) for year in balance_df["year"].unique()},
                step=None
            )
        ], className="six columns"),

        html.Div([
            dcc.Graph(
                id='hourly-by-item'
            ),
            dcc.Dropdown(
                id='item-dropdown',
                options=[{'label': i, 'value': i} for i in sorted(buy_df["item"].unique())],
                value='Coffee'
            )
        ], className="six columns")
    ], className="row"),

    html.Div(children=[
        html.Div(
            dcc.Graph(
                id="cumulative-buys",
                figure=fig_cumulative
            ), className="six columns"),
        html.Div(
            dcc.Graph(
                id="account-balance",
                figure=fig_balance
            ), className="six columns")
    ], className="row")
])

@app.callback(Output('hourly-buys','figure'),
    [Input('year-range-slider', 'value')])
def update_hourly_figure(selected_range):
    range_df = buy_df[buy_df["year"].between(selected_range[0], selected_range[1], inclusive=True)]
    fig_hourly = go.Figure()
    fig_hourly.add_trace(go.Histogram(
        x = range_df["hour"],
        y = range_df["price_cents"],
        histfunc = "count",
        xbins=dict(start=0,end=24,size=1)
    ))
    fig_hourly.update_layout(
        title_text = "Total purchases by hour from {} to {}".format(*selected_range),
        xaxis = {"range":[0,24]}
    )
    return fig_hourly

@app.callback(Output('hourly-by-item','figure'),
    [Input('item-dropdown', 'value')])
def update_item_figure(selected_item):
    item_df = buy_df[buy_df["item"] == selected_item]
    fig_item = go.Figure()
    fig_item.add_trace(go.Histogram(
        x=item_df["hour"],
        y=item_df["price_cents"],
        histfunc="count",
        xbins=dict(start=0,end=24,size=1)
    ))
    fig_item.update_layout(
        title_text = "{} purchases by hour".format(selected_item),
        xaxis = {"range":[0,24]}
    )
    if selected_item == "Coffee":
        fig_item.update_traces(marker_color='saddlebrown')
    return fig_item

if __name__ == '__main__':
    app.run_server(debug=True) 

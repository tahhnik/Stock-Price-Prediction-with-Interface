# -*- coding: utf-8 -*-
"""
pip install quandl

import quandl
import numpy as np 
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
"""

import pandas as pd
import numpy as np
import keras
import tensorflow as tf
from keras.preprocessing.sequence import TimeseriesGenerator
import dash
import dash_core_components as dcc
import dash_html_components as html

# pip install yfinance

import yfinance

from datetime import datetime

# start=datetime(2007,2,12)

# end = datetime.today()

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}
tab_selected_style = {
    'borderTop': '1px solid #111111',
    'borderBottom': '1px solid #111111',
    'backgroundColor': 'hotpink',
    'color': '#111111',
}
tab_style = {
    'fontWeight': 'bold',
    'backgroundColor': '#111111',
    'color': 'hotpink',
}

def download_and_process_data(stock_name):
    import yfinance
    import pandas as pd
    df = yfinance.download(stock_name,period='max')
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_axis(df['Date'], inplace=True)
    close_data = df['Close'].values
    close_data = close_data.reshape((-1,1))
    info = yfinance.Ticker(stock_name)
    return df, close_data, info

def split_data(close_data, df):
    split_percent = 80/100
    split = int(split_percent * len(close_data))
    close_train = close_data[:split]
    close_test = close_data[split:]
    date_train = df['Date'][:split]
    date_test = df['Date'][split:]
    return close_train, close_test, date_train, date_test

def sequence_to_supervised(look_back, close_train, close_test):
    from keras.preprocessing.sequence import TimeseriesGenerator
    train_generator = TimeseriesGenerator(close_train, close_train, length=look_back, batch_size=20)
    test_generator = TimeseriesGenerator(close_test, close_test, length=look_back, batch_size=1)
    return train_generator, test_generator

def train_model(look_back, train_generator, epochs):
    from keras.models import Sequential
    from keras.layers import LSTM, Dense
    lstm_model = Sequential()
    lstm_model.add(
        LSTM(10,
        activation='relu',
        input_shape=(look_back,1))
    )
    lstm_model.add(Dense(1))
    lstm_model.compile(optimizer='adam', loss='mse')
    lstm_model.fit_generator(train_generator,epochs=epochs)
    
    return lstm_model

def plot_train_test_graph(stock, model, test_generator, close_train, close_test, date_train, date_test):
    from plotly import graph_objs as go
    prediction = model.predict_generator(test_generator)
    close_train = close_train.reshape((-1))
    close_test = close_test.reshape((-1))
    prediction = prediction.reshape((-1))
    trace1 = go.Scatter(
        x = date_train,
        y = close_train,
        mode = 'lines',
        name = 'Data'
    )
    trace2 = go.Scatter(
        x = date_test,
        y = prediction,
        mode = 'lines',
        name = 'Prediction',
        line=dict(color='red')
    )
    trace3 = go.Scatter(
        x = date_test,
        y = close_test,
        mode='lines',
        name = 'Ground Truth'
    )
    layout = go.Layout(
        title = stock,
        xaxis = {'title' : "Date"},
        yaxis = {'title' : "Close"}
    )
    figure = go.Figure(data=[trace1, trace2, trace3], layout=layout)
    from sklearn.metrics import r2_score
    score = r2_score(close_test[:-15],prediction)
    figure.update_layout(
    paper_bgcolor=colors['background'],
    plot_bgcolor=colors["background"],
    font_color=colors['text'])
    return figure, score

def predict(num_prediction, model, close_data, look_back):
    prediction_list = close_data[-look_back:]
    
    for _ in range(num_prediction):
        x = prediction_list[-look_back:]
        x = x.reshape((1, look_back, 1))
        out = model.predict(x)[0][0]
        prediction_list = np.append(prediction_list, out)
    prediction_list = prediction_list[look_back-1:]
        
    return prediction_list

def predict_dates(num_prediction, df):
    last_date = df['Date'].values[-1]
    prediction_dates = pd.date_range(last_date, periods=num_prediction+1).tolist()
    return prediction_dates

def predicting(close_data, model, look_back, df):
    close_data = close_data.reshape((-1))
    num_prediction = 30
    forecast = predict(num_prediction, model, close_data, look_back)
    forecast_dates = predict_dates(num_prediction, df)
    return close_data, forecast, forecast_dates

def plot_future_prediction(model, test_generator, close_train, close_test, df, forecast_dates, forecast):
    from plotly import graph_objs as go
    prediction = model.predict_generator(test_generator)
    close_train = close_train.reshape((-1))
    close_test = close_test.reshape((-1))
    prediction = prediction.reshape((-1))
    trace1 = go.Scatter(
        x = df['Date'],
        y = df['Close'],
        mode = 'lines',
        name = 'Data'
    )
    trace2 = go.Scatter(
        x = forecast_dates,
        y = forecast,
        mode = 'lines',
        name = 'Prediction'
    )

    layout = go.Layout(
        title = "FUTURE PREDICTION",
        xaxis = {'title' : "Date"},
        yaxis = {'title' : "Close"}
    )
    figure = go.Figure(data=[trace1, trace2], layout=layout)
    figure.update_layout(
    paper_bgcolor=colors['background'],
    plot_bgcolor=colors["background"],
    font_color=colors['text'])
    return figure

'''
Main Variables : 
stock_name, df, close_data, look_back, close_train, close_test, train_generator, epochs
model, test_generator, date_train, date_test, num_predictions
'''
'''
1. download & process data
2. split the data
3. convert sequenced data to supervised data.
4. train the model
5. plot the training prediction 
6. predict future rates
'''

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(
    external_stylesheets=external_stylesheets,
    title="Predikter",
    update_title='Predicting ...')
server = app.server
# df,close_data =download_and_process_data('RELIANCE.NS')


app.layout = html.Div([
    html.H1('Predikter', style={"textAlign": "center", "margin_top":"8px"}),
    html.H2('Created By - Rishabh Panesar', style={"textAlign": "center", "margin_top":"8px"}),
    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label="Some Basic Information", children=[
            html.Div([
                html.P("This project is made just for educational purpose. All the predictions made by the Machine Learning Model are entirely probablistic based.", style={"textAlign": "center"}),
                html.H2("How to use?", style={"textAlign":"center"}),
                html.Ol(children=[
                    html.Li("Web app only takes the TICKER name of the desired asset"),
                    html.Li("Type the ticker name of the desired stock or index & hit enter"),
                    html.Li("First Plot is the plot obtained from testing the model again past data"),
                    html.Li("Second Plot is the plot that contains the future predictions made by the model")
                ]
                ),
                html.H2("Some other information", style={"textAlign":"center"}),
                html.Ul(children=[
                    html.Li("Model Used : Squential LSTM Model"),
                    html.Li("Lookbacks : 15"),
                    html.Li("Epochs : 25"),
                    html.Li("Forecast Duration : 1 Month")
                ]
                )
            ], style={"height":"100vh", "padding":"20px"})
        ], style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label="See the model in Action", children=[
            html.Div([
                html.H1('Type a Stock Name & hit enter', style={'textAlign':'center'}),
                dcc.Input(
                    id='stock_name',
                    type='text',
                    debounce= True,
                    placeholder="Type a stock name & hit enter",
                    style={
                        "display": "block", "margin-left": "auto", "margin-right": "auto", "width": "60%"
                    }
                ),
                html.Div(id='r2_score', style={'textAlign':'center'})
            ]),
            html.Div([
                dcc.Graph(id="training_plot")
            ]),
            html.Div([
                html.H1('Stock Info Section', style={'textAlign':'center'}),
                html.Div(id='stock_info', style={"color":"#f5f5f5", "text-align":"justify", "text-justify":"inter-word", "padding":"32px", "marginLeft":"16px","marginRight":"16px"}),
                ]),
            html.H1('Future Price Prediction', style={'textAlign':'center', "margin":"0px"}),
            html.Div([
                dcc.Graph(id='future_plot')
            ], style={"margin":"0px"}),
        ], style=tab_style, selected_style=tab_selected_style)
    ], style={"height":"100%"})
], style={"color":"hotpink", 'backgroundColor': colors['background'], "paddingTop":"16px"})

def return_empty_graph():
    empty = {
            "layout": {
                "xaxis": {
                    "visible": False
                    },
                "yaxis": {
                    "visible": False
                    },
                "annotations": [
                    {
                        "text": "No matching data found\nOr\nYou entered incorrect stock name...",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {
                            "size": 28
                        }
                    }
                    ],
                'plot_bgcolor': colors['background'],
                "paper_bgcolor":"#111111",
                "font_color":colors["text"]
                }
            }
    return empty

@app.callback(
    [dash.dependencies.Output('training_plot','figure'), 
    dash.dependencies.Output('future_plot','figure'),
    dash.dependencies.Output('r2_score', 'children')],
    dash.dependencies.Output('stock_info', 'children'),
    dash.dependencies.Input('stock_name','value'),
    )
def update_graph(value):
    try:
        stock = value
        df, close_data, info = download_and_process_data(stock)
    except:
        empty = return_empty_graph()
        return empty, empty, "No R2 Score to display", "No Asset Queried or Selected"
    try:
        close_train, close_test, date_train, date_test = split_data(close_data, df)
        train_generator, test_generator = sequence_to_supervised(15,close_train,close_test)
        lstm_model = train_model(15,train_generator, 25)
        # lstm_model.save('lstm_model.h5')
        figure_1, r2_score = plot_train_test_graph(stock, lstm_model, test_generator, close_train, close_test, date_train, date_test)
        close_data, forecast, forecast_dates = predicting(close_data, lstm_model, 15, df)
        figure_2 = plot_future_prediction(lstm_model, test_generator, close_train, close_test, df, forecast_dates, forecast)
        r2_score = "R2 Score : {}".format(r2_score)
        return figure_1, figure_2, r2_score, info.info['longBusinessSummary']
    except:
        empty = return_empty_graph()
        return empty, empty, "No R2 Score to display", "No Asset Queried or Selected"
# fig.show()

if __name__=='__main__':
    app.run_server(debug=True)
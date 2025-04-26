import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objs as go
import sqlite3
import pandas as pd
import datetime

DB_NAME = "robot_telemetry.db"

def load_data(start_date=None, end_date=None):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM telemetry"
    if start_date and end_date:
        query += f" WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.sort_values("timestamp")

app = dash.Dash(__name__)
app.title = "Исторические данные телеметрии"

app.layout = html.Div([
    html.H2("Исторические графики показателей робота", style={"textAlign": "center"}),

    html.Div([
        html.Label("Выберите диапазон дат:"),
        dcc.DatePickerRange(
            id="date-picker",
            start_date=datetime.date.today() - datetime.timedelta(days=1),
            end_date=datetime.date.today(),
            display_format="YYYY-MM-DD"
        ),
        html.Br(),
        html.Label("Показатель:"),
        dcc.Dropdown(
            id="param-dropdown",
            options=[{"label": col, "value": col} for col in [
                "temperature", "vibration", "voltage", "current", "energy", "speed", "motor_load", "pitch", "roll"
            ]],
            value="temperature",
            clearable=False,
            style={"width": "300px"}
        )
    ], style={"textAlign": "center", "padding": "20px"}),

    dcc.Graph(id="history-graph")
])

@app.callback(
    Output("history-graph", "figure"),
    [Input("param-dropdown", "value"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date")]
)
def update_graph(param, start_date, end_date):
    if not start_date or not end_date:
        return px.line(title="Нет данных")

    df = load_data(start_date, end_date)
    if df.empty or param not in df.columns:
        return px.line(title="Нет данных за выбранный период")

    # Альтернативные визуализации
    if param == "motor_load":
        latest = df[param].iloc[-1]
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest,
            title={"text": "Нагрузка на мотор (%)"},
            gauge={"axis": {"range": [0, 100]}}
        ))
        return fig

    elif param == "vibration":
        fig = px.histogram(df, x=param, nbins=20, title="Распределение вибрации")
        fig.update_layout(xaxis_title="Вибрация (g)", yaxis_title="Количество")
        return fig

    elif param == "energy":
        fig = px.bar(df, x="timestamp", y="energy", title="Потребление энергии по времени")
        fig.update_layout(xaxis_title="Время", yaxis_title="Энергия (Вт·с)")
        return fig

    # Обычный линейный график
    fig = px.line(df, x="timestamp", y=param, title=f"{param.capitalize()} за период")
    fig.update_layout(xaxis_title="Время", yaxis_title=param.capitalize())
    return fig

if __name__ == "__main__":
    app.run(debug=True)

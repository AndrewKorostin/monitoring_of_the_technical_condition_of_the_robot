import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import datetime
import random
import numpy as np
import math
from db_helper import init_db, insert_telemetry

app = dash.Dash(__name__)
app.title = "Мониторинг технического состояния мобильного робота"

card_style = {
    "background": "#f4f4f4",
    "padding": "15px",
    "margin": "10px",
    "borderRadius": "10px",
    "textAlign": "center",
    "width": "22%",
    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
}

history = {
    "time": [],
    "motor_temp": [],
    "vibration": [],
    "voltage": [],
    "current": [],
    "imu_gyro": [],
    "imu_acc_x": [],
    "imu_acc_y": [],
    "imu_acc_z": [],
    "wheel_speeds": [[], [], [], []]
}

# Глобальные переменные
distance_total = 0.0
I_MAX = 5.5  # Максимальный ток (А)

# Интерфейс
app.layout = html.Div([
    html.H2("Мониторинг технического состояния мобильного робота", style={"textAlign": "center"}),

    html.Div([
        html.Div([html.H4("Температура мотора"), html.Div(id="motor-temp", style={"fontSize": 28})], style=card_style),
        html.Div([html.H4("Пробег (м)"), html.Div(id="distance", style={"fontSize": 28})], style=card_style),
        html.Div([html.H4("Энергопотребление (Вт·с)"), html.Div(id="energy", style={"fontSize": 28})], style=card_style),
        html.Div([html.H4("Пиковая вибрация (g)"), html.Div(id="vib-peak", style={"fontSize": 28})], style=card_style)
    ], style={"display": "flex", "justifyContent": "space-around", "flexWrap": "wrap"}),

    html.Div([
        html.Div([html.H4("Скорость (м/с)"), html.Div(id="speed", style={"fontSize": 28})], style=card_style),
        html.Div([html.H4("Заряд батареи (%)"), html.Div(id="battery", style={"fontSize": 28})], style=card_style),
        html.Div([html.H4("Нагрузка на мотор (%)"), html.Div(id="motor-load", style={"fontSize": 28})], style=card_style),
        html.Div([
            html.H4("Пробуксовка по колёсам"),
            html.Ul(id="wheel-slip", style={"fontSize": 20, "color": "red"})
        ], style={**card_style, "width": "45%"})
    ], style={"display": "flex", "justifyContent": "space-around", "flexWrap": "wrap"}),

    html.Div([
        html.Div([
            html.H4("Наклон корпуса"),
            html.Div(id="pitch-roll", style={"fontSize": 24})
        ], style={**card_style, "width": "45%"})
    ], style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"}),

    html.Div([
        dcc.Graph(id='gyro-graph', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id='vibration-graph', style={'width': '48%', 'display': 'inline-block'})
    ]),

    dcc.Interval(id='update', interval=2000, n_intervals=0)
])

@app.callback(
    [Output("motor-temp", "children"),
     Output("distance", "children"),
     Output("energy", "children"),
     Output("vib-peak", "children"),
     Output("gyro-graph", "figure"),
     Output("vibration-graph", "figure"),
     Output("speed", "children"),
     Output("battery", "children"),
     Output("motor-load", "children"),
     Output("pitch-roll", "children"),
     Output("wheel-slip", "children")],
    [Input("update", "n_intervals")]
)
def update(n):

    global distance_total

    now = datetime.datetime.now().strftime("%H:%M:%S")
    temp = round(random.uniform(40, 85), 1)
    vibration = round(random.uniform(0.1, 1.5), 2)
    voltage = round(random.uniform(11.5, 14.4), 2)
    current = round(random.uniform(0.5, I_MAX), 2)
    gyro = round(random.uniform(-300, 300), 1)

    acc_x = round(random.uniform(-1.5, 1.5), 2)
    acc_y = round(random.uniform(-1.5, 1.5), 2)
    acc_z = round(random.uniform(9.5, 10.5), 2)

    wheel_speeds = [round(random.uniform(5, 15), 2) for _ in range(4)]
    wheel_avg_speed = round(np.mean(wheel_speeds), 2)
    dt = 2
    speed_m_s = round(wheel_avg_speed * 0.1, 2)

    distance_total += speed_m_s * dt
    energy_now = round(voltage * current * dt, 2)

    # История
    history["time"].append(now)
    history["motor_temp"].append(temp)
    history["vibration"].append(vibration)
    history["voltage"].append(voltage)
    history["current"].append(current)
    history["imu_gyro"].append(gyro)
    history["imu_acc_x"].append(acc_x)
    history["imu_acc_y"].append(acc_y)
    history["imu_acc_z"].append(acc_z)
    for i in range(4):
        history["wheel_speeds"][i].append(wheel_speeds[i])

    vib_peak = round(max(history["vibration"][-20:]), 2)
    battery_percent = 85  # фиксированное значение
    motor_load = round(current / I_MAX * 100)

    pitch = math.degrees(math.atan2(acc_x, math.sqrt(acc_y**2 + acc_z**2)))
    roll = math.degrees(math.atan2(acc_y, math.sqrt(acc_x**2 + acc_z**2)))

    acc_total = math.sqrt(acc_x**2 + acc_y**2)
    slipping_wheels = [f"Колесо {i+1}" for i in range(4) if wheel_speeds[i] > 8 and acc_total < 0.2]
    slip_list = [html.Li(w) for w in slipping_wheels] if slipping_wheels else [html.Li("Нет")]

    for key in ["time", "motor_temp", "vibration", "voltage", "current", "imu_gyro", "imu_acc_x", "imu_acc_y", "imu_acc_z"]:
        history[key] = history[key][-20:]
    for i in range(4):
        history["wheel_speeds"][i] = history["wheel_speeds"][i][-20:]

    fig_gyro = go.Figure(go.Scatter(x=history["time"], y=history["imu_gyro"], mode='lines+markers'))
    fig_gyro.update_layout(title="Угловая скорость (°/с)", yaxis=dict(range=[-350, 350]))

    fig_vib = go.Figure(go.Scatter(x=history["time"], y=history["vibration"], mode='lines+markers'))
    fig_vib.update_layout(title="Вибрация (g)", yaxis=dict(range=[0, 2]))
    insert_telemetry({
        "temperature": temp,
        "vibration": vibration,
        "voltage": voltage,
        "current": current,
        "energy": energy_now,
        "speed": speed_m_s,
        "motor_load": motor_load,
        "pitch": pitch,
        "roll": roll
    })
    return (
        f"{temp} °C",
        f"{round(distance_total, 2)} м",
        f"{energy_now} Вт·с",
        f"{vib_peak} g",
        fig_gyro,
        fig_vib,
        f"{speed_m_s} м/с",
        f"{battery_percent}%",
        f"{motor_load}%",
        f"Pitch: {pitch:.1f}° | Roll: {roll:.1f}°",
        slip_list
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

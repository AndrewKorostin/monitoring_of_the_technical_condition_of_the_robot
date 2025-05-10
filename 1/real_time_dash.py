import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import random
import base64
import math
import time
from collections import deque

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Пределы параметров
PARAM_LIMITS = {
    'motor_temp': {'warn': 70, 'critical': 85},
    'vibration': {'warn': 0.15, 'critical': 0.25},
    'battery_voltage': {'warn': 22, 'critical': 20},
    'current': {'warn': 5, 'critical': 7},
    'wheel_slip': {'warn': 0.2, 'critical': 0.3}
}

# Приоритеты сообщений
ALERT_PRIORITY = {
    'critical_temp': 50,
    'critical_vibration': 45,
    'critical_voltage': 40,
    'critical_current': 40,
    'critical_slip': 55,
    'warn_temp': 30,
    'warn_vibration': 25,
    'warn_voltage': 20,
    'warn_current': 20,
    'warn_slip': 35,
    'normal': 0
}

# Стили
CARD_STYLE = {
    'backgroundColor': '#2a2a2a',
    'border': '1px solid #333',
    'borderRadius': '10px',
    'padding': '10px',
    'height': '100%'
}

ALERTS_WINDOW_STYLE = {
    'height': '100%',  # Теперь занимает всю доступную высоту
    'overflowY': 'auto',
    'backgroundColor': '#1e1e1e',
    'borderRadius': '5px',
    'padding': '10px',
}

BATTERY_INDICATOR_STYLE = {
    'container': {
        'width': '100%',
        'height': '30px',
        'backgroundColor': '#1e1e1e',
        'borderRadius': '15px',
        'overflow': 'hidden',
        'position': 'relative'
    },
    'level': {
        'height': '100%',
        'transition': 'width 0.5s ease',
        'background': 'linear-gradient(90deg, #ff5555, #ffaa00, #00ff99)',
        'position': 'relative'
    },
    'text': {
        'position': 'absolute',
        'right': '10px',
        'top': '50%',
        'transform': 'translateY(-50%)',
        'color': 'white',
        'fontWeight': 'bold'
    }
}

WARNING_STYLE = {
    'critical': {'color': 'red', 'fontWeight': 'bold'},
    'warning': {'color': 'orange'},
    'normal': {'color': '#00ff99'}
}

# Класс для имитации работы двигателя
class MotorSimulator:
    def __init__(self):
        self.time = 0
        self.temp = 25.0
        self.load = 0.3
        self.left_slip = 0.0
        self.right_slip = 0.0

    def update(self, dt):
        self.time += dt
        self.load = 0.3 + 0.5 * (0.5 + 0.5 * math.sin(self.time * 0.2))
        temp_change = (self.load * 0.1 - 0.02) * dt
        self.temp += temp_change
        self.temp = max(25.0, min(self.temp, 95.0))
        vibration = 0.05 + 0.15 * self.load + 0.03 * random.random()

        # Имитация пробуксовки (значения теперь не превышают пределы слишком часто)
        slip_change = random.uniform(-0.02, 0.03)
        self.left_slip = max(0, min(0.35, self.left_slip + slip_change))
        self.right_slip = max(0, min(0.35, self.right_slip + slip_change))

        return {
            'temp': self.temp,
            'vibration': vibration,
            'load': self.load,
            'left_slip': self.left_slip,
            'right_slip': self.right_slip
        }


# Класс для имитации батареи
class BatterySimulator:
    def __init__(self):
        self.voltage = 24.8
        self.capacity = 3000
        self.max_capacity = 5000

    def update(self, current, dt):
        self.capacity -= current * 1000 * dt / 3600
        self.capacity = max(0, self.capacity)
        charge_percent = self.capacity / self.max_capacity * 100
        base_voltage = 24.0 * (charge_percent / 100.0)
        # Уменьшил падение напряжения, чтобы оно реже опускалось ниже предупреждений
        voltage_drop = 10
        self.voltage = base_voltage - voltage_drop

        return {
            'voltage': self.voltage,
            'capacity': self.capacity,
            'charge_percent': charge_percent
        }


# Глобальные объекты симуляторов
motor = MotorSimulator()
battery = BatterySimulator()

# Имитация пройденного расстояния и скорости
distance = 0.0
speed = 0.0

app.layout = dbc.Container(
    fluid=True,
    style={'backgroundColor': '#121212', 'padding': '20px', 'height': '100vh'},
    children=[
        html.Audio(id='alert-audio',
                   src="audio/Error_Tone.wav",
                   autoPlay=False),

        dbc.Row(
            dbc.Col(
                html.H2("МОНИТОРИНГ РОБОТА", style={'color': '#00ff99', 'textAlign': 'center'}),
                width=12
            ),
            className="mb-3"
        ),

        dbc.Row([
            dbc.Col([
                dbc.Row(
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader("ИНФОРМАЦИЯ О СИСТЕМЕ", className="text-white"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Row([
                                            dbc.Col([
                                                html.Div("Температура", className="text-muted"),
                                                html.Div("25.0°C", id="motor-temp",
                                                         style={'fontSize': '1.5rem', 'textAlign': 'center'})
                                            ]),
                                            dbc.Col([
                                                html.Div("Вибрация", className="text-muted"),
                                                html.Div("0.05g", id="vibration",
                                                         style={'fontSize': '1.5rem', 'textAlign': 'center'})
                                            ])
                                        ]),
                                        dbc.Row([
                                            dbc.Col([
                                                html.Div("Пробуксовка (L)", className="text-muted"),
                                                html.Div("0.0", id="left-slip",
                                                         style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                            ]),
                                            dbc.Col([
                                                html.Div("Пробуксовка (R)", className="text-muted"),
                                                html.Div("0.0", id="right-slip",
                                                         style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                            ])
                                        ], className="mt-3")
                                    ], md=6),

                                    dbc.Col([
                                        dbc.Row([
                                            dbc.Col([
                                                html.Div("Напряжение", className="text-muted"),
                                                html.Div("24.8V", id="voltage",
                                                         style={'fontSize': '1.5rem', 'textAlign': 'center'})
                                            ]),
                                            dbc.Col([
                                                html.Div("Ток", className="text-muted"),
                                                html.Div("3.2A", id="current",
                                                         style={'fontSize': '1.5rem', 'textAlign': 'center'})
                                            ])
                                        ]),
                                        dbc.Row([
                                            dbc.Col([
                                                html.Div("Заряд батареи", className="text-muted mb-2"),
                                                html.Div(
                                                    style=BATTERY_INDICATOR_STYLE['container'],
                                                    children=[
                                                        html.Div(
                                                            id='battery-level',
                                                            style=BATTERY_INDICATOR_STYLE['level']
                                                        ),
                                                        html.Div(
                                                            "100%",
                                                            id='battery-text',
                                                            style=BATTERY_INDICATOR_STYLE['text']
                                                        )
                                                    ]
                                                )
                                            ])
                                        ], className="mt-3"),
                                        dbc.Row([
                                            dbc.Col([
                                                html.Div("Пройдено", className="text-muted"),
                                                html.Div("0.0 м", id="distance",
                                                         style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                            ]),
                                            dbc.Col([
                                                html.Div("Скорость", className="text-muted"),
                                                html.Div("0.0 м/с", id="speed",
                                                         style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                            ])
                                        ], className="mt-3")
                                    ], md=6)
                                ])
                            ])
                        ], style=CARD_STYLE),
                    ),
                    className="mb-3"
                ),

                dbc.Row(
                    dbc.Col(
                        dbc.Card([
                            dbc.CardBody([
                                html.Img(
                                    id="camera-view",
                                    src="http://localhost:8081/video_feed",
                                    style={
                                        'width': '100%',
                                        'height': '400px',
                                        'objectFit': 'cover',
                                        'borderRadius': '8px',
                                    }
                                ),
                                dbc.ButtonGroup([
                                    dbc.Button("Передняя камера", id='btn-front-cam', active=True),
                                    dbc.Button("Задняя камера", id='btn-rear-cam')
                                ], className="mt-2")
                            ])
                        ], style=CARD_STYLE),
                    )
                )
            ], md=8),

            dbc.Col([
                dbc.Row(
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader("АКТИВНЫЕ ПРЕДУПРЕЖДЕНИЯ", className="text-white"),
                            dbc.CardBody([
                                html.Div(
                                    id="active-alerts-container",
                                    style=ALERTS_WINDOW_STYLE,
                                    children=[
                                        dbc.Alert("Все системы в норме", color="success")
                                    ]
                                )
                            ])
                        ], style={**CARD_STYLE, 'height': '100%'}),  # Добавлена фиксированная высота
                    ),
                    className="mb-3",
                    style={'height': '50%'}  # Занимает половину высоты колонки
                ),

                dbc.Row(
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader("ИНЕРЦИАЛЬНАЯ СИСТЕМА", className="text-white"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div("Крен", className="text-muted"),
                                        html.Div("0.0°", id="roll", style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                    ]),
                                    dbc.Col([
                                        html.Div("Тангаж", className="text-muted"),
                                        html.Div("0.0°", id="pitch",
                                                 style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                    ]),
                                    dbc.Col([
                                        html.Div("Рысканье", className="text-muted"),
                                        html.Div("0.0°", id="yaw", style={'fontSize': '1.2rem', 'textAlign': 'center'})
                                    ])
                                ])
                            ])
                        ], style={**CARD_STYLE, 'height': '100%'}),  # Добавлена фиксированная высота
                    ),
                    style={'height': '50%'}  # Занимает вторую половину высоты колонки
                )
            ], md=4, style={'display': 'flex', 'flexDirection': 'column', 'height': 'calc(100vh - 100px)'})
        ], style={'height': 'calc(100vh - 100px)'}),

        dcc.Interval(id='data-update', interval=1000),
        dcc.Store(id='sensor-data'),
        html.Div(id='dummy-output', style={'display': 'none'})
    ]
)


def create_alert_message(param, value):
    """Создает сообщение об ошибке с приоритетом"""
    if param == 'motor_temp':
        if value > PARAM_LIMITS['motor_temp']['critical']:
            return {
                'message': f"КРИТИЧЕСКАЯ температура: {value:.1f}°C",
                'color': 'danger',
                'priority': ALERT_PRIORITY['critical_temp']
            }
        elif value > PARAM_LIMITS['motor_temp']['warn']:
            return {
                'message': f"Высокая температура: {value:.1f}°C",
                'color': 'warning',
                'priority': ALERT_PRIORITY['warn_temp']
            }

    elif param == 'vibration':
        if value > PARAM_LIMITS['vibration']['critical']:
            return {
                'message': f"КРИТИЧЕСКАЯ вибрация: {value:.2f}g",
                'color': 'danger',
                'priority': ALERT_PRIORITY['critical_vibration']
            }
        elif value > PARAM_LIMITS['vibration']['warn']:
            return {
                'message': f"Высокая вибрация: {value:.2f}g",
                'color': 'warning',
                'priority': ALERT_PRIORITY['warn_vibration']
            }

    elif param == 'voltage':
        if value < PARAM_LIMITS['battery_voltage']['critical']:
            return {
                'message': f"КРИТИЧЕСКОЕ напряжение: {value:.1f}V",
                'color': 'danger',
                'priority': ALERT_PRIORITY['critical_voltage']
            }
        elif value < PARAM_LIMITS['battery_voltage']['warn']:
            return {
                'message': f"Низкое напряжение: {value:.1f}V",
                'color': 'warning',
                'priority': ALERT_PRIORITY['warn_voltage']
            }

    elif param == 'current':
        if value > PARAM_LIMITS['current']['critical']:
            return {
                'message': f"КРИТИЧЕСКИЙ ток: {value:.1f}A",
                'color': 'danger',
                'priority': ALERT_PRIORITY['critical_current']
            }
        elif value > PARAM_LIMITS['current']['warn']:
            return {
                'message': f"Высокий ток: {value:.1f}A",
                'color': 'warning',
                'priority': ALERT_PRIORITY['warn_current']
            }

    elif param == 'wheel_slip':
        if value > PARAM_LIMITS['wheel_slip']['critical']:
            return {
                'message': f"КРИТИЧЕСКАЯ пробуксовка: {value:.2f}",
                'color': 'danger',
                'priority': ALERT_PRIORITY['critical_slip']
            }
        elif value > PARAM_LIMITS['wheel_slip']['warn']:
            return {
                'message': f"Пробуксовка: {value:.2f}",
                'color': 'warning',
                'priority': ALERT_PRIORITY['warn_slip']
            }

    return None


@app.callback(
    [Output('motor-temp', 'children'),
     Output('motor-temp', 'style'),
     Output('vibration', 'children'),
     Output('vibration', 'style'),
     Output('left-slip', 'children'),
     Output('left-slip', 'style'),
     Output('right-slip', 'children'),
     Output('right-slip', 'style'),
     Output('voltage', 'children'),
     Output('voltage', 'style'),
     Output('current', 'children'),
     Output('current', 'style'),
     Output('distance', 'children'),
     Output('speed', 'children'),
     Output('roll', 'children'),
     Output('pitch', 'children'),
     Output('yaw', 'children'),
     Output('battery-level', 'style'),
     Output('battery-text', 'children'),
     Output('active-alerts-container', 'children'),
     Output('alert-audio', 'autoPlay')],
    Input('data-update', 'n_intervals')
)
def update_data(n):
    global distance, speed

    dt = 1.0
    motor_data = motor.update(dt)
    current = 2.0 + 3.0 * motor_data['load']
    battery_data = battery.update(current, dt)
    speed = 0.01 * (1200 + 50 * math.sin(n * 0.5))
    distance += speed * dt
    roll = 2.5 * math.sin(n * 0.1)
    pitch = -1.2 * math.sin(n * 0.15)
    yaw = n % 360

    # Создаем все возможные сообщения
    temp_alert = create_alert_message('motor_temp', motor_data['temp'])
    vib_alert = create_alert_message('vibration', motor_data['vibration'])
    volt_alert = create_alert_message('voltage', battery_data['voltage'])
    curr_alert = create_alert_message('current', current)
    left_slip_alert = create_alert_message('wheel_slip', motor_data['left_slip'])
    right_slip_alert = create_alert_message('wheel_slip', motor_data['right_slip'])

    # Собираем все сообщения в список
    all_alerts = [alert for alert in [temp_alert, vib_alert, volt_alert, curr_alert,
                                      left_slip_alert, right_slip_alert] if alert is not None]

    # Сортируем по приоритету (сначала самые важные)
    all_alerts.sort(key=lambda x: x['priority'], reverse=True)

    # Берем 3 самых важных сообщения
    top_alerts = all_alerts[:3]

    # Проверяем, есть ли критические сообщения для звукового оповещения
    play_alert = any(alert['color'] == 'danger' for alert in top_alerts)

    # Создаем компоненты Alert
    alert_components = []
    for alert in top_alerts:
        alert_components.append(
            dbc.Alert(
                alert['message'],
                color=alert['color'],
                className="mb-2",
                style={'borderLeft': '4px solid red'} if alert['color'] == 'danger' else {
                    'borderLeft': '4px solid orange'}
            )
        )

    if not alert_components:
        alert_components = [dbc.Alert("Все системы в норме", color="success", className="mb-2")]

    # Определяем стили для значений
    motor_temp_style = WARNING_STYLE['critical'] if temp_alert and temp_alert['color'] == 'danger' else \
        WARNING_STYLE['warning'] if temp_alert and temp_alert['color'] == 'warning' else \
            WARNING_STYLE['normal']

    vibration_style = WARNING_STYLE['critical'] if vib_alert and vib_alert['color'] == 'danger' else \
        WARNING_STYLE['warning'] if vib_alert and vib_alert['color'] == 'warning' else \
            WARNING_STYLE['normal']

    left_slip_style = WARNING_STYLE['critical'] if left_slip_alert and left_slip_alert['color'] == 'danger' else \
        WARNING_STYLE['warning'] if left_slip_alert and left_slip_alert['color'] == 'warning' else \
            WARNING_STYLE['normal']

    right_slip_style = WARNING_STYLE['critical'] if right_slip_alert and right_slip_alert['color'] == 'danger' else \
        WARNING_STYLE['warning'] if right_slip_alert and right_slip_alert['color'] == 'warning' else \
            WARNING_STYLE['normal']

    voltage_style = WARNING_STYLE['critical'] if volt_alert and volt_alert['color'] == 'danger' else \
        WARNING_STYLE['warning'] if volt_alert and volt_alert['color'] == 'warning' else \
            WARNING_STYLE['normal']

    current_style = WARNING_STYLE['critical'] if curr_alert and curr_alert['color'] == 'danger' else \
        WARNING_STYLE['warning'] if curr_alert and curr_alert['color'] == 'warning' else \
            WARNING_STYLE['normal']

    battery_level_style = {
        **BATTERY_INDICATOR_STYLE['level'],
        'width': f"{max(0, min(100, battery_data['charge_percent']))}%",
    }

    return (
        f"{motor_data['temp']:.1f}°C", motor_temp_style,
        f"{motor_data['vibration']:.2f}g", vibration_style,
        f"{motor_data['left_slip']:.2f}", left_slip_style,
        f"{motor_data['right_slip']:.2f}", right_slip_style,
        f"{battery_data['voltage']:.1f}V", voltage_style,
        f"{current:.1f}A", current_style,
        f"{distance:.1f} м",
        f"{speed:.1f} м/с",
        f"{roll:.1f}°",
        f"{pitch:.1f}°",
        f"{yaw:.1f}°",
        battery_level_style,
        f"{battery_data['charge_percent']:.1f}%",
        alert_components,
        play_alert
    )


if __name__ == '__main__':
    app.run(debug=True)
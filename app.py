# Procfile server config
# web: gunicorn --bind 0.0.0.0:$PORT --worker-class eventlet -w 1  app:app
# Procfile local config
# web: gunicorn --bind 0.0.0.0:$PORT app:app

from flask import Flask, url_for, render_template
import os
from flask_socketio import SocketIO
from flask_cors import CORS
from simulationClass import start_simulation_res

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
restaurant = None

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

@app.route('/')
def home():
    global restaurant
    if restaurant:
        restaurant.pause_simulation()
        restaurant = None
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    print('Conexión establecida')

@socketio.on('start')
def start(message):
    global restaurant
    if not restaurant or not restaurant.state:
        print('Start | hours: ' + message['data'])
        restaurant = start_simulation_res(int(message['data']), socketio)

@socketio.on('pause')
def pause(message):
    global restaurant
    if restaurant:
        print(message['data'])
        restaurant.pause_simulation()

@socketio.on('play')
def play(message):
    global restaurant
    if restaurant:
        print(message['data'])
        restaurant.play_simulation()

@socketio.on('cancel')
def cancel(message):
    global restaurant
    print(message['data'])
    if restaurant:
        restaurant.pause_simulation()
        restaurant = None

if __name__ == '__main__':
    socketio.run(app)

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import base64
import socketio
import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
from keras.losses import MeanSquaredError
from io import BytesIO
from PIL import Image
import cv2


sio = socketio.Server()

app = Flask(__name__) #'__main__'
speed_limit = 20

def img_preprocess(img):
    img = img[60:135,:,:]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    return img

@sio.on('telemetry')
def telemetry(sid, data):
    if data:
        speed = float(data['speed'])
        image = Image.open(BytesIO(base64.b64decode(data['image'])))
        image = np.asarray(image)
        image = img_preprocess(image)
        image = np.array([image])
        steering_angle = float(model.predict(image))
        throttle = 1.0 - speed / speed_limit
        print('{} {} {}'.format(steering_angle, throttle, speed))
        send_control(steering_angle, throttle)
    else:
        sio.emit('manual', data={}, skip_sid=True)

@sio.on('connect')
def connect(sid, environ):
    print('Connected')
    send_control(0, 0)

def send_control(steering_angle, throttle):
    sio.emit('steer', data={
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

if __name__ == '__main__':
    model = load_model(r'D:\Courses\NTI_ETA\Final Project\NTI_Project\model.keras', custom_objects={'mse': MeanSquaredError()})
    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)
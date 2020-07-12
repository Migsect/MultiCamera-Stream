#!/usr/bin/env python
from flask import Flask, render_template, Response, request, redirect, url_for
from camera import VideoCameraThread, VideoCamera, VideoCameraConsumer
import json

app = Flask(__name__)

cameras = []


def parse_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
        cameras.extend(data.get("cameras", []))


camera_threads = []
camera_threads_map = {}


def start_threads():
    print(cameras)
    for camera in cameras:
        # v_camera = VideoCamera(camera)
        v_camera_thread = VideoCameraThread(camera)
        camera_threads.append(v_camera_thread)
        camera_threads_map[v_camera_thread.camera.camera_id] = v_camera_thread

        print("Starting Thread")
        v_camera_thread.start()


@app.route('/')
def index():
    return render_template('index.html', cameras=cameras)


@app.route('/video_feed/')
def video_feed():
    camera_id = request.args.get('camera', default=cameras[0]["id"], type=str)

    is_thumbnail = bool(int(request.args.get(
        'thumbnail', default="0", type=int)))

    print(camera_id, is_thumbnail)
    return Response(
        VideoCameraConsumer(
            camera_threads_map[camera_id], is_thumbnail).generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == '__main__':

    parse_config()
    print("Starting All Threads")
    start_threads()

    app.run(host='0.0.0.0', debug=True, use_reloader=False)

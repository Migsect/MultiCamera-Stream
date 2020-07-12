#!/usr/bin/env python
from flask import Flask, render_template, Response, request, redirect, url_for
from camera import VideoCamera
import json

app = Flask(__name__)

cameras = []
camera_map = {}


def parse_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
        cameras.extend(data.get("cameras", []))
        for index, camera in enumerate(cameras):
            camera_id = camera.get("id", "camera_" + str(index))
            camera_map[camera_id] = camera
            camera["video"] = VideoCamera(
                device=camera["device-number"],
                resolution=camera["resolution"]
            )


parse_config()
print(cameras)


@app.route('/')
def index():
    return render_template('index.html', cameras=cameras)


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )


@app.route('/video_feed/')
def video_feed():
    camera_id = request.args.get('camera', default=cameras[0]["id"], type=str)

    is_thumbnail = bool(int(request.args.get(
        'thumbnail', default="0", type=int)))

    print(camera_id, is_thumbnail)
    return Response(
        camera_map[camera_id]["video"].generate(thumbnail=is_thumbnail),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

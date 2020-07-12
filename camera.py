import cv2
import threading
from queue import Queue, Empty
from readerwriterlock import rwlock
import time

THUMBAIL_SIZE = 120


def resize_to_resolution(image, resolution):
    # We are going to resize the image into one we see fit.
    height = int(resolution)
    width = int(image.shape[1] * height / image.shape[0])
    dims = (width, height)
    return cv2.resize(
        image, dims,
        interpolation=cv2.INTER_AREA
    )


class DataQueue:
    def __init__(self):
        self.queue = Queue(maxsize=16)

        self.current_data = None
        self.lock = rwlock.RWLockFair()

    def update_data(self):
        next_data = None
        try:
            next_data = self.queue.get(block=False)
        except Empty:
            # There is no new data to update.
            return None
        with self.lock.gen_wlock():
            self.current_data = next_data

    def get_data(self):
        result = None
        with self.lock.gen_rlock():
            result = self.current_data

        # We are going to try to update the data if there is any new data in the queue.
        # It is the reader's responsibility to update the data being held if there is new data.
        self.update_data()

        return result

    def add_data(self, data):
        if self.queue.full():
            try:
                # emptying one of the items in the queue if its full.
                self.update_data()
            except Empty:
                pass

        self.queue.put(data)


class VideoCamera(object):
    def __init__(self, configuration):
        self.camera_id = configuration["id"]
        self.camera_name = configuration["name"]
        self.device = configuration["device-number"]
        self.resolution = configuration.get("resolution", 1080)
        self.pollrate = configuration.get("pollrate", 10)
        self.polltime = 1 / self.pollrate

        # self._video = None
        self._video = cv2.VideoCapture(self.device, cv2.CAP_DSHOW)

    def __del__(self):
        self._video.release()

    def get_frame(self, thumbnail=False):

        retval, image = self._video.read()
        if retval != True:
            print("Camera can't read frame: " + self.camera_id)

        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        return image


class VideoCameraThread(threading.Thread):
    def __init__(self, camera_config):

        self.camera = VideoCamera(camera_config)

        threading.Thread.__init__(
            self, name=self.camera.camera_id, daemon=True)

        self.data_queue = DataQueue()

    def run(self):
        print("Starting video camera thread for " + self.camera.camera_id)

        data = self.camera.get_frame()
        self.data_queue.add_data(data)

        count = 0
        while True:
            seconds = time.time()

            count += 1

            data = self.camera.get_frame()

            if data is None:
                print("Video stream invalid for " +
                      self.camera.camera_id + ", stopping thread.")
                break

            self.data_queue.add_data(data)

            difference = time.time() - seconds
            if difference < self.camera.polltime:
                time.sleep(self.camera.polltime - difference)


class VideoCameraConsumer(object):
    def __init__(self, thread, is_thumbnail):
        self.thread = thread
        self.is_thumbnail = is_thumbnail

    def generate(self):
        while True:
            seconds = time.time()

            frame = self.thread.data_queue.get_data()
            if frame is None:
                print("frame is none")
                continue

            if self.is_thumbnail:
                frame = resize_to_resolution(frame, THUMBAIL_SIZE)
            else:
                frame = frame = resize_to_resolution(
                    frame, self.thread.camera.resolution)

            _, jpeg = cv2.imencode('.jpg', frame)
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n'
            )

            difference = time.time() - seconds
            if difference < self.thread.camera.polltime:
                time.sleep(self.thread.camera.polltime - difference)

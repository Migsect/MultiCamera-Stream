import cv2

THUMBAIL_SIZE = 120

devices = {}


class VideoCamera(object):
    def __init__(self, device=0, resolution=1080):
        if device in devices:
            self.video = devices[device]
        else:
            self.video = cv2.VideoCapture(device)
            devices[device] = self.video

        self.resolution = resolution

    def __del__(self):
        self.video.release()

    def generate(self, thumbnail=False):
        while True:
            frame = self.get_frame(thumbnail=thumbnail)
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
            )

    def get_frame(self, thumbnail=False):
        success, image = self.video.read()

        height = int(self.resolution if not thumbnail else THUMBAIL_SIZE)
        width = int(image.shape[1] * height / image.shape[0])
        dims = (width, height)
        image = cv2.resize(image, dims,
                           interpolation=cv2.INTER_AREA)
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

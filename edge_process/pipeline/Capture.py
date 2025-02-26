import dataclasses
import time

import numpy as np
from configuration.Configuration import Camera
import cv2


class Capture:
    """Interface for reading camera frames"""

    def __init__(self, config: Camera) -> None:
        raise NotImplementedError

    def get_frame(self) -> tuple[bool, np.ndarray]:
        raise NotImplementedError

    @classmethod
    def _config_changed(cls, config_a: Camera, config_b: Camera) -> bool:
        if config_a == None and config_b == None:
            return False
        if config_a == None or config_b == None:
            return True

        remote_a = config_a
        remote_b = config_b

        return (
            remote_a.id != remote_b.id
            or remote_a.res_w != remote_b.res_w
            or remote_a.res_h != remote_b.res_h
            or remote_a.auto_exposure != remote_b.auto_exposure
            or remote_a.exposure != remote_b.exposure
            or remote_a.gain != remote_b.gain
        )


class DefaultCapture(Capture):
    """Use OpenCV's capture to read from camera"""

    _video = None

    def __init__(self, config: Camera) -> None:
        self._video = cv2.VideoCapture(config.id, cv2.CAP_V4L2)
        self._video.set(cv2.CAP_PROP_FRAME_WIDTH, config.res_w)
        self._video.set(cv2.CAP_PROP_FRAME_HEIGHT, config.res_h)
        self._video.set(cv2.CAP_PROP_GAIN, config.gain)
        self._video.set(cv2.CAP_PROP_FPS, config.fps)

    def get_frame(self) -> tuple[bool, np.ndarray]:
        retval, image = self._video.read()
        return retval, image


class GStreamerCapture(Capture):
    """Use GStreamer to read from camera"""

    _video = None
    _last_config: Camera = None

    def __init__(self) -> None:
        pass

    def get_frame(self, config: Camera) -> tuple[bool, np.ndarray]:
        if self._video != None and self._config_changed(self._last_config, config):
            print("Refreshing capture lock")
            self._video.release()
            self._video = None
            time.sleep(2)

        if self._video == None:
            if config.id == -1:
                print("Camera id is not set. Not starting capture.")
            else:
                print("Creating capture lock")
                _str = (
                    f"libcamerasrc ! video/x-raw,format=BGRx,width={config.res_w},height={config.res_h},framerate=60/1 "
                    + f"! videoconvert ! video/x-raw,format=BGR ! appsink drop=true"
                )
                print(_str)
                self._video = cv2.VideoCapture(_str, cv2.CAP_GSTREAMER)
                print("Capture lock ready")
                time.sleep(5)

        self._last_config = dataclasses.replace(config)

        if self._video != None:
            retval, image = self._video.read()
            if not retval:
                print("Capture session failed, restarting")
                self._video.release()
                self._video = None  # Force reconnect
            return retval, image
        else:
            return False, cv2.Mat(np.ndarray([]))

import datetime
import os
from typing import List

import cv2
import numpy as np

from configuration.ConfigurationRetriever import ConfigurationRetriever


class Calibrator:
    _all_charuco_corners: List[np.ndarray] = []
    _all_charuco_ids: List[np.ndarray] = []
    _imsize = None
    _iter: int = 0

    def __init__(self) -> None:
        self._aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
        self._aruco_params = cv2.aruco.DetectorParameters()
        self._charuco_board = cv2.aruco.CharucoBoard(
            (12, 9), 0.030, 0.023, self._aruco_dict
        )

    def process_frame(self, image: np.ndarray, save: bool) -> None:
        # Get image size
        if self._imsize == None:
            self._imsize = (image.shape[0], image.shape[1])

        # Detect tags
        (corners, ids, rejected) = cv2.aruco.detectMarkers(
            image, self._aruco_dict, parameters=self._aruco_params
        )
        if len(corners) > 0:
            cv2.aruco.drawDetectedMarkers(image, corners)

            # Find Charuco corners
            (
                retval,
                charuco_corners,
                charuco_ids,
            ) = cv2.aruco.interpolateCornersCharuco(
                corners, ids, image, self._charuco_board
            )
            if retval:
                cv2.aruco.drawDetectedCornersCharuco(
                    image, charuco_corners, charuco_ids
                )
                # Save corners
                if save:
                    print(len(charuco_corners))
                    if len(charuco_corners) < 4:
                        print("less than 4 corners detected, not saving")
                        return
                    self._all_charuco_corners.append(charuco_corners)
                    self._all_charuco_ids.append(charuco_ids)
                    self._iter += 1
                    print("Saved calibration frame %s", (self._iter))

    def finish(self) -> None:
        if len(self._all_charuco_corners) == 0:
            print("ERROR: No calibration data")
            return

        if os.path.exists(ConfigurationRetriever.CALIBRATION_FILENAME):
            os.remove(ConfigurationRetriever.CALIBRATION_FILENAME)

        (
            retval,
            camera_matrix,
            distortion_coefficients,
            rvecs,
            tvecs,
        ) = cv2.aruco.calibrateCameraCharuco(
            self._all_charuco_corners,
            self._all_charuco_ids,
            self._charuco_board,
            self._imsize,
            None,
            None,
        )

        if retval:
            calibration_store = cv2.FileStorage(
                ConfigurationRetriever.CALIBRATION_FILENAME, cv2.FILE_STORAGE_WRITE
            )
            calibration_store.write("calibration_date", str(datetime.datetime.now()))
            calibration_store.write("camera_resolution", self._imsize)
            calibration_store.write("camera_matrix", camera_matrix)
            calibration_store.write("distortion_coefficients", distortion_coefficients)
            calibration_store.release()
            print("Calibration finished")
        else:
            print("ERROR: Calibration failed")

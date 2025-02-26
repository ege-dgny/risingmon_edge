import time
import cv2
import numpy as np
import ntcore
import threading

from configuration.Configuration import PolarisConfiguration
from configuration.ConfigurationRetriever import ConfigurationRetriever
from calibration.Calibration import Calibrator
from calibration.CalibrationController import NTCalibrationController
from Observations import FiducialObservation2d
from output.StreamServer import MjpegServer
from output.NTPublisher import NTPublisher

from pipeline.PoseEstimator import PoseEstimator
from pipeline.Detector import Detector
from pipeline.Capture import GStreamerCapture

# Load Configuration
configuration = PolarisConfiguration()
sub = ConfigurationRetriever()
pub = NTPublisher()
calibrator = Calibrator()
calibration_controller = NTCalibrationController()
processor = Detector()
pose_estimator = PoseEstimator()
stream = MjpegServer()

sub.updateLocal(configuration)
stream.start(configuration.device)

calibration_started = False
frame_counts = [0, 0]
last_print = time.time()

# RTP Stream Details (Adjust ports based on Raspberry Pi settings)
rtp_streams = [
    {"camera_id": 0, "port": 5000},  # Camera 1
    {"camera_id": 1, "port": 5001}   # Camera 2
]

def process_rtp_stream(camera_id, port, mjpeg_server):
    """ Processes an RTP video stream and performs detection & pose estimation. """
    print(f"Starting RTP Stream Processing for Camera {camera_id} on Port {port}")

    # Define GStreamer pipeline for receiving RTP stream
    gst_pipeline = (
        f"udpsrc port={port} caps=\"application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96\" ! "
        f"rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink sync=false"
    )

    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print(f"Error: Failed to open RTP stream for Camera {camera_id}!")
        return

    global calibration_started, last_print
    fps = 0  # ✅ Fix: Initialize fps to avoid UnboundLocalError

    while True:
        ret, frame = cap.read()
        timestamp = time.time()

        if not ret:
            print(f"⚠️ Warning: Frame not received from Camera {camera_id}, skipping...")
            time.sleep(0.1)
            continue

        # FPS Calculation
        frame_counts[camera_id] += 1
        elapsed_time = time.time() - last_print
        if elapsed_time > 1:
            fps = int(frame_counts[camera_id] // elapsed_time)  # ✅ Ensure fps is always assigned
            print(f"Camera {camera_id} - FPS: {fps:.2f}")
            frame_counts[camera_id] = 0
            last_print = time.time()

        # Handle Calibration Mode
        if calibration_controller.get_calibration_mode(configuration.device):
            calibration_started = True
            calibrator.process_frame(
                frame, calibration_controller.get_wants_frame(configuration.device)
            )
        elif calibration_started:
            calibrator.finish()
            time.sleep(5)
            sub.updateLocal(configuration)
            calibration_started = False
        else:
            # Detect 2D Markers
            markers = processor.detectAruco(frame)
            cv2.aruco.drawDetectedMarkers(
                frame,
                [m.corners for m in markers],
                np.fromiter((m.tag_id for m in markers), dtype=int),
            )
            observations2d = [
                FiducialObservation2d(m.tag_id, m.corners) for m in markers
            ]

            # Pose Estimation
            pose_observation = pose_estimator.solve_camera_pose(
                observations2d, configuration, configuration.intrinsics
            )

            # Send Data to NetworkTables
            pub.send(configuration.device, timestamp, pose_observation, fps)

        # Display the frame on screen
        cv2.imshow(f"Camera {camera_id} Output", frame)

        # Stream processed frame
        mjpeg_server.set_frame(frame)

        # Press 'q' to exit the display
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Start Threads for Both Camera Streams
if __name__ == "__main__":
    print("Using OpenCV Version %s" % (cv2.__version__))
    # Initialize NetworkTables
    ntcore.NetworkTableInstance.getDefault().setServer("10.16.78.2")
    ntcore.NetworkTableInstance.getDefault().startClient4(configuration.device.device_id)

    # Wait until the environment is ready
    while configuration.environment.tag_map is None:
        sub.updateNT(configuration)

    threads = []
    for cam_stream in rtp_streams:
        thread = threading.Thread(
            target=process_rtp_stream, 
            args=(cam_stream["camera_id"], cam_stream["port"], stream)
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

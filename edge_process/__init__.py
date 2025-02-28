import time
import cv2
import numpy as np
import ntcore
import threading
from queue import Queue

from configuration.Configuration import RisingMoonConfiguration
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
configuration = RisingMoonConfiguration()
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

rtp_streams = [
    {"camera_id": 0, "port": 5000}, 
    {"camera_id": 1, "port": 5001}  
]

frame_queues = {0: Queue(), 1: Queue()}

def process_rtp_stream(camera_id, port):
    """Processes an RTP video stream, performs detection & pose estimation, and stores frames in a queue."""
    print(f"Starting RTP Stream Processing for Camera {camera_id} on Port {port}")

    gst_pipeline = (
        f"udpsrc port={port} caps=\"application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96\" ! "
        f"rtpjitterbuffer latency=100 ! "
        f"rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! queue ! appsink sync=true max-buffers=1 drop=true"
    )

    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print(f"Error: Failed to open RTP stream for Camera {camera_id}!")
        return

    global calibration_started, last_print
    fps = 0
    target_fps = 30 
    frame_time = 1 / target_fps

    while True:
        start_time = time.time()
        ret, frame = cap.read()
        timestamp = time.time()

        if not ret:
            print(f"⚠️ Warning: Frame not received from Camera {camera_id}, skipping...")
            time.sleep(0.1)
            continue

        frame_counts[camera_id] += 1
        elapsed_time = time.time() - last_print
        if elapsed_time > 1:
            fps = int(frame_counts[camera_id] // elapsed_time)
            print(f"Camera {camera_id} - FPS: {fps:.2f}")
            frame_counts[camera_id] = 0
            last_print = time.time()

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
            markers = processor.detectAruco(frame)
            cv2.aruco.drawDetectedMarkers(
                frame,
                [m.corners for m in markers],
                np.fromiter((m.tag_id for m in markers), dtype=int),
            )
            observations2d = [
                FiducialObservation2d(m.tag_id, m.corners) for m in markers
            ]

            pose_observation = pose_estimator.solve_camera_pose(
                observations2d, configuration, configuration.intrinsics
            )

            pub.send(configuration.device, timestamp, pose_observation, fps)

        frame_queues[camera_id].put(frame)

        stream.set_frame(frame)

        elapsed_time = time.time() - start_time
        sleep_time = max(0, frame_time - elapsed_time)
        time.sleep(sleep_time)

    cap.release()

def display_frames():
    """Displays frames from the queue."""
    while True:
        for cam_id, queue in frame_queues.items():
            if not queue.empty():
                frame = queue.get()
                cv2.imshow(f"Camera {cam_id} Output", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    #print("Using OpenCV Version %s" % (cv2.__version__))

    #print(f"Tag Map: {configuration.environment.tag_map}")

    # Initialize NetworkTables
    ntcore.NetworkTableInstance.getDefault().setServer("10.85.61.2")
    ntcore.NetworkTableInstance.getDefault().startClient4(configuration.device.device_id)
    ntcore.NetworkTableInstance.getDefault().startServer(port4=8000) 

    # Wait until the environment is ready
    while configuration.environment.tag_map is None:
        sub.updateNT(configuration)

    threads = []
    for cam_stream in rtp_streams:
        thread = threading.Thread(
            target=process_rtp_stream, 
            args=(cam_stream["camera_id"], cam_stream["port"]),
            daemon=True
        )
        thread.start()
        threads.append(thread)

    display_thread = threading.Thread(target=display_frames, daemon=True)
    display_thread.start()

    for thread in threads:
        thread.join()

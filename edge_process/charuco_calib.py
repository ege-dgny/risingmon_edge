import cv2
import datetime
import os

def main():
    # Configuration
    CALIBRATION_FILENAME = "Calibration.yaml"
    PORT = 5001

    # GStreamer pipeline for receiving H.264 on UDP port 5001
    gst_pipeline = (
        f"udpsrc port={PORT} caps=\"application/x-rtp,media=video,clock-rate=90000,encoding-name=H264,payload=96\" ! "
        f"rtpjitterbuffer latency=100 ! "
        f"rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! queue ! "
        f"appsink sync=true max-buffers=1 drop=true"
    )

    # OpenCV VideoCapture
    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("Error: Could not open video stream on port", PORT)
        return

    # Create the dictionary and Charuco board
    # - Dictionary: DICT_5X5_1000
    # - Board size: 12 x 9 (12 squares wide, 9 squares tall)
    # - Square size: 30mm (0.03 in meters)
    # - Marker size: 22mm (0.022 in meters)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
    charuco_board = cv2.aruco.CharucoBoard_create(
        squaresX=12,
        squaresY=9,
        squareLength=0.03,
        markerLength=0.022,
        dictionary=dictionary
    )

    # Lists for storing detected corners/ids from each frame
    all_charuco_corners = []
    all_charuco_ids = []
    imsize = None

    print("Press 'c' to capture a frame for calibration, 'q' to quit and run calibration.")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Warning: Could not read frame from video capture.")
            continue

        # Optionally resize or show the frame
        cv2.imshow("Charuco Calibration - Press 'c' to capture, 'q' to quit", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            # Detect ArUco markers
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, dictionary)

            if ids is not None and len(ids) > 0:
                # Refine detection (optional)
                # corners, ids, rejected, recovered_ids = cv2.aruco.refineDetectedMarkers(
                #     gray, charuco_board, corners, ids, rejected
                # )

                # Interpolate charuco corners
                retval, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
                    markerCorners=corners,
                    markerIds=ids,
                    image=gray,
                    board=charuco_board
                )

                if retval and charuco_corners is not None and charuco_ids is not None and len(charuco_corners) > 0:
                    all_charuco_corners.append(charuco_corners)
                    all_charuco_ids.append(charuco_ids)

                    # Store image size once
                    if imsize is None:
                        imsize = gray.shape[::-1]  # (width, height)

                    print(f"Captured frame with {len(charuco_corners)} Charuco corners.")
                else:
                    print("Not enough Charuco corners detected. Please try again.")
            else:
                print("No ArUco markers detected in this frame. Please try again.")

        elif key == ord('q'):
            # Quit and proceed to calibration
            print("Exiting capture loop.")
            break

    cap.release()
    cv2.destroyAllWindows()

    # Now perform calibration if we have enough data
    if len(all_charuco_corners) < 1:
        print("Not enough captures for calibration. Exiting without calibration.")
        return

    # Remove old calibration file if it exists
    if os.path.exists(CALIBRATION_FILENAME):
        os.remove(CALIBRATION_FILENAME)

    # Charuco-based calibration
    print("Starting calibration...")
    (
        retval,
        camera_matrix,
        distortion_coefficients,
        rvecs,
        tvecs,
    ) = cv2.aruco.calibrateCameraCharuco(
        charucoCorners=all_charuco_corners,
        charucoIds=all_charuco_ids,
        board=charuco_board,
        imageSize=imsize,
        cameraMatrix=None,
        distCoeffs=None
    )

    if retval:
        # Save to YAML
        calibration_store = cv2.FileStorage(CALIBRATION_FILENAME, cv2.FILE_STORAGE_WRITE)
        calibration_store.write("calibration_date", str(datetime.datetime.now()))
        calibration_store.write("camera_resolution", imsize)
        calibration_store.write("camera_matrix", camera_matrix)
        calibration_store.write("distortion_coefficients", distortion_coefficients)
        calibration_store.release()

        print(f"Calibration finished successfully. Results saved to {CALIBRATION_FILENAME}")
    else:
        print("ERROR: Calibration failed")

if __name__ == "__main__":
    main()
import cv2
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import time
import dlib

# Thresholds and parameters
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 30
COUNTER = 0

# Load Models
detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def generate_frames(stream_event, model_result):
    global COUNTER
    vs = VideoStream(src=0).start()  # Start video stream
    time.sleep(1.0)
    
    try:
        while stream_event.is_set():  # Loop while the event is set
            frame = vs.read()
            if frame is None:
                break

            frame = cv2.resize(frame, (640, 480))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            for (x, y, w, h) in rects:
                rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                
                # Process eyes and lips
                (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
                (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
                leftEye = shape[lStart:lEnd]
                rightEye = shape[rStart:rEnd]
                
                # Draw landmarks
                cv2.polylines(frame, [cv2.convexHull(leftEye)], True, (0, 255, 0), 1)
                cv2.polylines(frame, [cv2.convexHull(rightEye)], True, (0, 255, 0), 1)
                lip = shape[48:60]
                cv2.polylines(frame, [cv2.convexHull(lip)], True, (0, 255, 0), 1)

                # Compute EAR and detect drowsiness
                ear_left = eye_aspect_ratio(leftEye)
                ear_right = eye_aspect_ratio(rightEye)
                ear = (ear_left + ear_right) / 2.0

                if ear < EYE_AR_THRESH:
                    COUNTER += 1
                    if COUNTER >= EYE_AR_CONSEC_FRAMES:
                        model_result["status"] = "Drowsy"
                else:
                    COUNTER = 0
                    model_result["status"] = "Awake"

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        vs.stop()  # Stop video stream
        cv2.destroyAllWindows()  # Clean up any OpenCV windows

def eye_aspect_ratio(eye):
    # Compute the eye aspect ratio (EAR) for drowsiness detection
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

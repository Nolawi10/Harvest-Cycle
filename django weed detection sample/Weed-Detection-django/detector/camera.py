import cv2
from ultralytics import YOLO
import threading
import time

class VideoCamera(object):
    def __init__(self, video_path=None):
        if video_path:
            self.video = cv2.VideoCapture(video_path)
        else:
            # Use webcam with DirectShow backend, which is more stable on Windows
            self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        self.model = YOLO('Model/weights/best.pt')
        self.lock = threading.Lock()
        self.raw_frame = None
        self.running = True

        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False
        # Wait for the thread to finish
        if self.thread.is_alive():
            self.thread.join()
        self.video.release()

    def update(self):
        """This thread continuously grabs frames from the camera."""
        while self.running:
            (success, frame) = self.video.read()
            if not success:
                # If the video ends or the camera fails, stop the thread
                self.running = False
                break
            
            with self.lock:
                self.raw_frame = frame
            # Small sleep to prevent busy-waiting and reduce CPU usage
            time.sleep(0.01)

    def get_frame(self):
        """Process the latest raw frame and return it as a JPEG."""
        processed_frame = None
        with self.lock:
            if self.raw_frame is not None:
                # Make a copy for processing
                frame_to_process = self.raw_frame.copy()
            else:
                return None

        # Perform inference on the copied frame
        results = self.model(frame_to_process, stream=True)

        # Visualize results on the frame
        for r in results:
            processed_frame = r.plot()

        if processed_frame is None:
            return None

        # Encode the processed frame in JPEG format
        (flag, encodedImage) = cv2.imencode(".jpg", processed_frame)
        if not flag:
            return None

        return encodedImage.tobytes()

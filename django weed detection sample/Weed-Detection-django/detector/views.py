from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from django.core.files.storage import FileSystemStorage
from .camera import VideoCamera
import os
import threading

# Use a thread-safe dictionary to store camera instances, keyed by session ID
cameras = {}
cameras_lock = threading.Lock()

def video_feed(request):
    """Returns the video feed stream."""
    cid = request.session.session_key
    camera_instance = None
    with cameras_lock:
        if cid in cameras:
            camera_instance = cameras[cid]

    if not camera_instance or not camera_instance.running:
        return redirect('index')

    def stream_generator(camera):
        # This generator loop runs until the camera is stopped
        while camera.running:
            frame = camera.get_frame()
            if frame:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n'
                )
        # Once the loop breaks, the camera has stopped. Clean up.
        with cameras_lock:
            if cid in cameras:
                del cameras[cid]

    return StreamingHttpResponse(stream_generator(camera_instance), content_type='multipart/x-mixed-replace; boundary=frame')

def stop_stream(request):
    """Stops the video stream by signaling the camera's running flag to false."""
    cid = request.session.session_key
    with cameras_lock:
        if cid and cid in cameras:
            cameras[cid].stop()  # This signals the generator to stop and cleanup

    # Clean up any uploaded video file path from the session
    if 'video_path' in request.session:
        video_path = request.session.pop('video_path')
        if os.path.exists(video_path):
            os.remove(video_path)

    return redirect('index')

def index(request):
    """Home page. Renders the main control panel."""
    return render(request, 'detector/index.html')

def start_stream(request, source_type):
    """Starts the video stream from webcam or an uploaded file."""
    if not request.session.session_key:
        request.session.create()
    cid = request.session.session_key

    video_path = None
    if source_type == 'video' and 'video_path' in request.session:
        video_path = request.session['video_path']

    with cameras_lock:
        # Stop and signal for cleanup of any existing camera for this session
        if cid in cameras:
            cameras[cid].stop()

        # Create the new camera instance
        cameras[cid] = VideoCamera(video_path=video_path)

    return render(request, 'detector/index.html', {'stream_active': True})

def upload_video(request):
    """Handles video upload and redirects to start the stream."""
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)

        # Store the path in the session
        request.session['video_path'] = fs.path(filename)

        # Redirect to the start_stream view for video files
        return redirect('start_stream', source_type='video')

    # If not a POST request or no file, redirect to home
    return redirect('index')

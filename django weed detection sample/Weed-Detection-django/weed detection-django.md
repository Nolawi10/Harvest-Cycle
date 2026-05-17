## **Weed Detection App using Django and yolov8**

This guide will walk you through setting up a new Django project, structuring your application, and implementing the enhanced features.

### **1\. Project Setup and Requirements**

First, you'll need to have Python installed, along with pip. Then, install the necessary packages:

pip install django opencv-python ultralytics

Next, create a new Django project and an application within it.

django-admin startproject weed\_detection\_project  
cd weed\_detection\_project  
python manage.py startapp detector

This will create a standard Django project structure. You will also need to create a few new files and directories. Your final detector app directory should look like this:

detector/  
├── \_\_init\_\_.py  
├── admin.py  
├── apps.py  
├── migrations/  
├── models.py  
├── tests.py  
├── views.py  
├── urls.py          \# \<-- Create this file  
├── camera.py        \# \<-- Create this file  
└── templates/  
    └── detector/  
        └── index.html \# \<-- Create this directory and file

Finally, place your YOLOv8 model file (best.pt) in a directory at the root of your project, for example: weed\_detection\_project/Model/weights/best.pt.

### **2\. Django Project Configuration**

Now, let's configure your Django project to recognize your new app and handle file uploads.

#### **weed\_detection\_project/settings.py**

In this file, you need to add your detector app to the INSTALLED\_APPS list and configure settings for handling media files (like uploaded videos).

\# weed\_detection\_project/settings.py

\# ... (other settings)

INSTALLED\_APPS \= \[  
    'django.contrib.admin',  
    'django.contrib.auth',  
    'django.contrib.contenttypes',  
    'django.contrib.sessions',  
    'django.contrib.messages',  
    'django.contrib.staticfiles',  
    'detector',  \# Add your app here  
\]

\# ... (other settings)

\# Add this at the end of the file for media file handling  
import os

MEDIA\_URL \= '/media/'  
MEDIA\_ROOT \= os.path.join(BASE\_DIR, 'media')

#### **weed\_detection\_project/urls.py**

Next, configure your project's main URL file to include the URLs from your detector app. This tells Django where to send requests.

\# weed\_detection\_project/urls.py

from django.contrib import admin  
from django.urls import path, include  
from django.conf import settings  
from django.conf.urls.static import static

urlpatterns \= \[  
    path('admin/', admin.site.urls),  
    path('', include('detector.urls')),  \# Include your app's URLs  
\]

\# This is important for serving uploaded files during development  
if settings.DEBUG:  
    urlpatterns \+= static(settings.MEDIA\_URL, document\_root=settings.MEDIA\_ROOT)

### **3\. Building the Backend Logic**

This is the core of your application. We'll create clean, separated logic for handling web requests and for processing video.

#### **detector/urls.py (Create this file)**

This file will define the specific URL paths for the detector app.

\# detector/urls.py

from django.urls import path  
from . import views

urlpatterns \= \[  
    path('', views.index, name='index'),  
    path('video\_feed/', views.video\_feed, name='video\_feed'),  
    path('start\_stream/\<str:source\_type\>/', views.start\_stream, name='start\_stream'),  
    path('stop\_stream/', views.stop\_stream, name='stop\_stream'),  
\]

#### **detector/camera.py (Create this file)**

This is a major enhancement. We encapsulate all the OpenCV and YOLO logic into a VideoCamera class. This makes your code much cleaner and easier to maintain than having this logic directly in your views.

\# detector/camera.py

import cv2  
from ultralytics import YOLO  
import threading

class VideoCamera(object):  
    def \_\_init\_\_(self, video\_path=None):  
        if video\_path:  
            self.video \= cv2.VideoCapture(video\_path)  
        else:  
            self.video \= cv2.VideoCapture(0)  \# Use webcam  
          
        \# Load the YOLO model  
        self.model \= YOLO("Model/weights/best.pt")  
          
        self.is\_running \= True  
        self.frame \= None  
        self.lock \= threading.Lock()  
        self.thread \= threading.Thread(target=self.update, args=())  
        self.thread.daemon \= True  
        self.thread.start()

    def \_\_del\_\_(self):  
        self.stop()

    def stop(self):  
        self.is\_running \= False  
        self.thread.join()  
        self.video.release()

    def update(self):  
        while self.is\_running:  
            (grabbed, frame) \= self.video.read()  
            if not grabbed:  
                self.is\_running \= False  
                break  
              
            \# Run YOLOv8 inference  
            results \= self.model(frame, stream=True, verbose=False)  
              
            \# Visualize results on the frame  
            for r in results:  
                annotated\_frame \= r.plot()  
                with self.lock:  
                    self.frame \= annotated\_frame

    def get\_frame(self):  
        with self.lock:  
            if self.frame is None:  
                return None  
              
            \# Encode the frame in JPEG format  
            (flag, encodedImage) \= cv2.imencode(".jpg", self.frame)  
            if not flag:  
                return None

            \# Yield the output frame in byte format  
            return encodedImage.tobytes()

#### **detector/views.py**

This file handles the web requests. It uses Django's session framework to manage state (like the path to an uploaded video), which is a significant improvement over global variables.

\# detector/views.py

from django.shortcuts import render, redirect  
from django.http import StreamingHttpResponse  
from django.core.files.storage import FileSystemStorage  
from django.conf import settings  
from .camera import VideoCamera  
import os

\# Using a simple dictionary to hold the camera instance.  
\# For a multi-user production app, you might use a more robust caching system.  
camera\_instance \= {} 

def gen(camera):  
    """Video streaming generator function."""  
    while True:  
        frame \= camera.get\_frame()  
        if frame is None:  
            continue  
        yield (b'--frame\\r\\n'  
               b'Content-Type: image/jpeg\\r\\n\\r\\n' \+ frame \+ b'\\r\\n\\r\\n')

def video\_feed(request):  
    """Video streaming route."""  
    cid \= request.session.session\_key  
    if cid in camera\_instance:  
        return StreamingHttpResponse(gen(camera\_instance\[cid\]),  
                                     content\_type='multipart/x-mixed-replace; boundary=frame')  
    return redirect('index')

def index(request):  
    """Home page."""  
    \# Ensure any previous camera is stopped when visiting the home page  
    stop\_stream(request)  
    return render(request, 'detector/index.html')

def start\_stream(request, source\_type):  
    """Starts the video stream from webcam or uploaded file."""  
    cid \= request.session.session\_key  
      
    video\_path \= None  
    if source\_type \== 'upload' and 'video\_path' in request.session:  
        video\_path \= request.session\['video\_path'\]  
      
    \# If there's an existing camera, stop it first  
    if cid in camera\_instance:  
        camera\_instance\[cid\].stop()  
        del camera\_instance\[cid\]  
          
    camera\_instance\[cid\] \= VideoCamera(video\_path=video\_path)  
      
    return render(request, 'detector/index.html', {'stream\_active': True})

def stop\_stream(request):  
    """Stops the video stream."""  
    cid \= request.session.session\_key  
    if cid in camera\_instance:  
        camera\_instance\[cid\].stop()  
        del camera\_instance\[cid\]  
      
    \# Clean up uploaded file if it exists  
    if 'video\_path' in request.session:  
        video\_path \= request.session.pop('video\_path')  
        if os.path.exists(video\_path):  
            os.remove(video\_path)  
              
    return redirect('index')

def upload\_video(request):  
    """Handles video upload and redirects to start the stream."""  
    if request.method \== 'POST' and request.FILES.get('video'):  
        video\_file \= request.FILES\['video'\]  
        fs \= FileSystemStorage()  
        filename \= fs.save(video\_file.name, video\_file)  
          
        \# Store the full path in the session  
        request.session\['video\_path'\] \= os.path.join(settings.MEDIA\_ROOT, filename)  
          
        \# Redirect to the start stream view for uploads  
        return redirect('start\_stream', source\_type='upload')  
      
    return redirect('index')

\# Add this to your detector/urls.py  
\# path('upload\_video/', views.upload\_video, name='upload\_video'),

**Note:** You'll need to add the upload\_video path to your detector/urls.py file as indicated in the comment above.

### **4\. Crafting the Modern UI/UX**

This new frontend is cleaner, more intuitive, and provides a better user experience with JavaScript for dynamic updates.

#### **detector/templates/detector/index.html (Create this file)**

\<\!DOCTYPE html\>  
\<html lang="en"\>  
\<head\>  
    \<meta charset="UTF-8"\>  
    \<meta name="viewport" content="width=device-width, initial-scale=1.0"\>  
    \<title\>Advanced Weed Detection\</title\>  
    \<script src="https://cdn.tailwindcss.com"\>\</script\>  
    \<style\>  
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700\&display=swap');  
        body {  
            font-family: 'Inter', sans-serif;  
        }  
    \</style\>  
\</head\>  
\<body class="bg-gray-100 text-gray-800"\>

    \<\!-- Header \--\>  
    \<header class="bg-white shadow-md"\>  
        \<div class="container mx-auto px-6 py-4"\>  
            \<h1 class="text-3xl font-bold text-green-700"\>🌿 Advanced Weed Detection System\</h1\>  
            \<p class="text-gray-600 mt-1"\>Leveraging AI to protect your crops\</p\>  
        \</div\>  
    \</header\>

    \<main class="container mx-auto px-6 py-8"\>  
        \<div class="grid md:grid-cols-2 gap-8"\>

            \<\!-- Control Panel \--\>  
            \<div class="bg-white p-6 rounded-lg shadow-lg"\>  
                \<h2 class="text-2xl font-semibold mb-4 border-b pb-2 text-green-600"\>Control Panel\</h2\>  
                  
                \<\!-- Webcam Option \--\>  
                \<div class="mb-6"\>  
                    \<h3 class="text-xl font-medium mb-2"\>Real-Time Detection\</h3\>  
                    \<p class="text-gray-600 mb-3"\>Use your webcam for live weed detection.\</p\>  
                    \<a href="{% url 'start\_stream' 'webcam' %}" class="w-full text-center bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out"\>  
                        Start Webcam Feed  
                    \</a\>  
                \</div\>

                \<\!-- Upload Option \--\>  
                \<div\>  
                    \<h3 class="text-xl font-medium mb-2"\>Process a Video File\</h3\>  
                    \<p class="text-gray-600 mb-3"\>Upload a video to detect weeds frame by frame.\</p\>  
                    \<form action="{% url 'upload\_video' %}" method="POST" enctype="multipart/form-data" class="space-y-3"\>  
                        {% csrf\_token %}  
                        \<input type="file" name="video" accept="video/\*" required class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"\>  
                        \<button type="submit" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out"\>  
                            Upload and Process  
                        \</button\>  
                    \</form\>  
                \</div\>  
            \</div\>

            \<\!-- Video Stream Display \--\>  
            \<div class="bg-white p-6 rounded-lg shadow-lg"\>  
                \<h2 class="text-2xl font-semibold mb-4 border-b pb-2 text-green-600"\>Detection Feed\</h2\>  
                \<div id="video-container" class="bg-gray-900 rounded-lg overflow-hidden aspect-video flex items-center justify-center"\>  
                    {% if stream\_active %}  
                        \<img id="video-stream" src="{% url 'video\_feed' %}" alt="Video Stream"\>  
                    {% else %}  
                        \<div id="placeholder" class="text-center text-gray-400"\>  
                            \<svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"\>\<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.55a2 2 0 01.45 2.99l-2.5 4A2 2 0 0115.5 18H8.5A2 2 0 016.5 16v-4a2 2 0 012-2h7zM6 10V6a2 2 0 012-2h3.5a2 2 0 012 2v4"\>\</path\>\</svg\>  
                            \<p class="mt-2"\>Video stream will appear here\</p\>  
                        \</div\>  
                    {% endif %}  
                \</div\>  
                {% if stream\_active %}  
                    \<a href="{% url 'stop\_stream' %}" class="mt-4 w-full block text-center bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out"\>  
                        Stop Stream  
                    \</a\>  
                {% endif %}  
            \</div\>

        \</div\>  
    \</main\>  
\</body\>  
\</html\>

### **5\. Running Your New Application**

You're all set\! To run your enhanced weed detection system, follow these steps:

1. **Apply database migrations** (a standard Django step):  
   python manage.py migrate

2. **Start the development server**:  
   python manage.py runserver

3. **Access the application**: Open your web browser and navigate to http://127.0.0.1:8000/.

You will now see the new, modern interface. You can choose to either start the real-time webcam feed or upload a video file. The backend will process the stream using YOLOv8 and display the results on the page.
from flask import Flask, Response, render_template_string
import cv2

app = Flask(__name__)
video = cv2.VideoCapture(0)

html_template = """
<!DOCTYPE html>
<html>
  <head>
    <title>Webcam Stream</title>
  </head>
  <body>
    <h1>Live Webcam Feed</h1>
    <img src="{{ url_for('video_feed') }}" width="640" height="480">
  </body>
</html>
"""

def generate_frames():
    while True:
        success, frame = video.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/video')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
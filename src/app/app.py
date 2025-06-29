from flask import Flask, Response, render_template_string
import cv2

CAMERAS = [0, 1, 3]

app = Flask(__name__)
caps = [cv2.VideoCapture(i) for i in CAMERAS]

def gen_frames(cam_index):
    cap = caps[cam_index]
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    imgs_html = ""
    for i, cam_id in enumerate(CAMERAS):
        imgs_html += f"""
        <div style='margin:20px; display:inline-block; text-align:center;'>
          <h3>Camera {cam_id}</h3>
          <a href="/video_stream/{cam_id}">
            <img src='/video_feed/{i}' width='320' height='240' style='cursor:pointer;'/>
          </a>
        </div>
        """

    html = f"""
    <html>
      <head><title>Multi-Cam Stream</title></head>
      <body>
        <h1>Multi-Camera Live Feed</h1>
        {imgs_html}
      </body>
    </html>
    """
    return render_template_string(html)

@app.route('/video_feed/<int:cam_index>')
def video_feed(cam_index):
    if cam_index >= len(caps):
        return "Camera not found", 404
    return Response(gen_frames(cam_index),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_stream/<int:cam_id>')
def video_stream(cam_id):
    if cam_id not in CAMERAS:
        return "Camera not found", 404
    cam_index = CAMERAS.index(cam_id)
    html = f"""
    <html>
      <head><title>Camera {cam_id} Stream</title></head>
      <body style='text-align:center;'>
        <h1>Camera {cam_id}</h1>
        <img src='/video_feed/{cam_index}' style='max-width:100%; height:auto;'/>
        <p><a href='/'>Back to all cameras</a></p>
      </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, Response, render_template_string
import cv2
from datetime import datetime
import threading
import time

CAMERAS = {
    0: "Bedroom",
    1: "Living Room",
}

app = Flask(__name__)

frames = {}
locks = {}

def capture_loop(cam_id):
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"[ERROR] Camera {cam_id} could not be opened.")
        return

    label = CAMERAS.get(cam_id, f"Camera {cam_id}")
    while True:
        success, frame = cap.read()
        if success:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            overlay_text = f"{label} | {timestamp}"
            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.5
            color = (255, 255, 255)
            thickness = 1
            margin = 10

            (text_width, text_height), _ = cv2.getTextSize(overlay_text, font, font_scale, thickness)
            x = frame.shape[1] - text_width - margin
            y = frame.shape[0] - margin
            cv2.putText(frame, overlay_text, (x + 1, y + 1), font, font_scale, (0, 0, 0), 2)
            cv2.putText(frame, overlay_text, (x, y), font, font_scale, color, thickness)

            with locks[cam_id]:
                frames[cam_id] = frame
        else:
            print(f"[WARN] Failed to read frame from camera {cam_id}")
        time.sleep(0.05)

def gen_frames(cam_id):
    while True:
        with locks[cam_id]:
            frame = frames.get(cam_id)
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        else:
            time.sleep(0.1)

@app.route('/')
def index():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cam_cards = ""
    for cam_id, label in CAMERAS.items():
        cam_cards += f"""
        <div class="camera-card">
          <div class="camera-label">{label}</div>
          <a href="/video_stream/{cam_id}">
            <img src="/video_feed/{cam_id}" alt="{label}" />
          </a>
        </div>
        """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>NVR</title>
      <style>
        body {{
          margin: 0;
          font-family: 'Segoe UI', sans-serif;
          background: #0e0e0e;
          color: #f0f0f0;
        }}
        header {{
          background: #1b1b1b;
          padding: 16px 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #333;
        }}
        .logo {{
          font-size: 1.2rem;
          font-weight: bold;
        }}
        .timestamp {{
          font-size: 0.95rem;
          color: #aaa;
        }}
        .grid {{
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 16px;
          padding: 16px;
        }}
        .camera-card {{
          background: #161616;
          border: 1px solid #2a2a2a;
          border-radius: 8px;
          overflow: hidden;
          transition: all 0.2s ease;
        }}
        .camera-card:hover {{
          transform: scale(1.01);
          border-color: #444;
        }}
        .camera-label {{
          padding: 8px 12px;
          font-size: 0.9rem;
          background: #222;
          border-bottom: 1px solid #333;
        }}
        .camera-card img {{
          width: 100%;
          display: block;
        }}
        a {{
          text-decoration: none;
          color: inherit;
        }}
      </style>
    </head>
    <body>
      <header>
        <div class="logo">NVR</div>
        <div class="timestamp">{now}</div>
      </header>
      <div class="grid">
        {cam_cards}
      </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    if cam_id not in CAMERAS:
        return "Camera not found", 404
    return Response(gen_frames(cam_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_stream/<int:cam_id>')
def video_stream(cam_id):
    label = CAMERAS.get(cam_id, f"Camera {cam_id}")
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>{label} - Live Stream</title>
      <style>
        body {{
          margin: 0;
          background: #000;
          color: #fff;
          text-align: center;
          font-family: sans-serif;
        }}
        img {{
          width: 100%;
          height: auto;
          max-height: 95vh;
          border: 4px solid #333;
        }}
        a {{
          display: inline-block;
          margin-top: 12px;
          color: #0af;
          font-size: 1.1rem;
        }}
      </style>
    </head>
    <body>
      <h1>{label}</h1>
      <img src="/video_feed/{cam_id}" />
      <br><a href="/">← Back to Dashboard</a>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    for cam_id in CAMERAS:
        frames[cam_id] = None
        locks[cam_id] = threading.Lock()
        thread = threading.Thread(target=capture_loop, args=(cam_id,), daemon=True)
        thread.start()
    app.run(host='0.0.0.0', port=5000)
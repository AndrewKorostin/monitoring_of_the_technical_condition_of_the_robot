import cv2
from flask import Response, Flask

camera_app = Flask(__name__)
  # 0 — стандартная веб-камера

for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"✅ Камера найдена по индексу: {i}")
        cap.release()
    else:
        print(f"❌ Камера не найдена по индексу: {i}")
def generate():
    video = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = video.read()
            if not success:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        video.release()

@camera_app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    camera_app.run(host='0.0.0.0', port=8081, threaded=True)


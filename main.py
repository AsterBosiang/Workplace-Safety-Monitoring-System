from flask import Flask, jsonify, render_template_string, request, Response
from flask_sqlalchemy import SQLAlchemy
import cv2
import face_recognition
import numpy as np
import os
import threading
import time
from ultralytics import YOLO
import requests
import queue

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Personnel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    arrived_at = db.Column(db.DateTime, default=db.func.now())
    has_helmet = db.Column(db.Boolean, default=None)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/api/personnel', methods=['GET'])
def get_personnel():
    personnel = Personnel.query.all()
    return jsonify([{
        "name": p.name,
        "arrived_at": p.arrived_at.strftime('%Y-%m-%d %H:%M:%S'),
        "has_helmet": p.has_helmet
    } for p in personnel])

@app.route('/api/upload_face', methods=['POST'])
def upload_face():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400
    person = Personnel.query.filter_by(name=name).first()
    if not person:
        person = Personnel(name=name, has_helmet=False)  # 新增時即預設未戴
        db.session.add(person)
        db.session.commit()
        push_event("face_update")
    return jsonify({"status": "success", "message": f"{name} face uploaded"}), 200

@app.route('/api/update_helmet', methods=['POST'])
def update_helmet():
    data = request.get_json()
    name = data.get("name")
    has_helmet = data.get("has_helmet")
    person = Personnel.query.filter_by(name=name).first()
    if person:
        if person.has_helmet != has_helmet:
            person.has_helmet = has_helmet
            db.session.commit()
            push_event("helmet_update")
        return jsonify({"status": "success", "message": f"{name} helmet status updated"}), 200
    else:
        return jsonify({"status": "error", "message": "Person not found"}), 404

events_queue = queue.Queue()

def push_event(event_type):
    events_queue.put(event_type)

@app.route('/events')
def sse_events():
    def event_stream():
        while True:
            event_type = events_queue.get()
            yield f"data: {event_type}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/')
def index():
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>工地安全系統</title>
        <style>
            body {
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                height: 100vh; 
                background-color: #f4f4f9; 
                display: flex; 
                flex-direction: column;
            }
            h1 {
                text-align: center; 
                margin: 20px 0; 
            }
            .main-container {
                display: flex; 
                flex: 1; 
                overflow: hidden;
            }
            .left-container {
                width: 33%; 
                display: flex; 
                flex-direction: column; 
                padding: 10px;
                box-sizing: border-box;
            }
            .right-container {
                width: 67%; 
                display: flex; 
                flex-direction: column; 
                padding: 10px; 
                box-sizing: border-box;
            }
            .panel {
                background-color: #fff; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
                border-radius: 8px; 
                padding: 20px; 
                margin-bottom: 20px;
                flex: 1; 
                overflow-y: auto;
            }
            .panel h2 {
                font-size: 20px; 
                margin-bottom: 15px; 
            }
            .panel ul {
                list-style-type: none; 
                padding: 0; 
                margin: 0;
            }
            .panel ul li {
                background-color: #f9f9f9; 
                padding: 10px; 
                margin-bottom: 8px; 
                border-radius: 5px;
            }
            .panel ul li:last-child {
                margin-bottom: 0;
            }
            .video-panel {
                background-color: #ccc; 
                flex: 2; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                border-radius: 8px; 
                margin-bottom: 20px;
                overflow: hidden;
            }
            .info-panel {
                background-color: #fff; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                border-radius: 8px; 
                padding: 20px;
                flex: 1; 
                overflow-y: auto;
            }
            img {
                width: 100%;
                height: auto;
            }
            #recognized-list {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            #recognized-list li {
                margin-bottom: 5px;
            }
        </style>
    </head>
    <body>
        <h1>工地安全系統</h1>
        <div class="main-container">
            <div class="left-container">
                <div class="panel" id="no-helmet-panel">
                    <h2>沒戴安全帽人員</h2>
                    <ul id="no-helmet-list"></ul>
                    <p><strong>人數:</strong> <span id="no-helmet-count">0</span></p>
                </div>
                <div class="panel" id="helmet-panel">
                    <h2>有戴安全帽人員</h2>
                    <ul id="helmet-list"></ul>
                    <p><strong>人數:</strong> <span id="helmet-count">0</span></p>
                </div>
            </div>
            <div class="right-container">
                <div class="video-panel">
                    <img src="/video_feed" id="video-feed">
                </div>
                <div class="info-panel">
                    <h2>辨識結果</h2>
                    <ul id="recognized-list"></ul>
                    <p id="no-recognized-msg"></p>
                </div>
            </div>
        </div>
        <script>
            async function fetchPersonnel() {
                try {
                    const response = await fetch('/api/personnel');
                    const data = await response.json();

                    const helmetList = document.getElementById('helmet-list');
                    const noHelmetList = document.getElementById('no-helmet-list');
                    const helmetCount = document.getElementById('helmet-count');
                    const noHelmetCount = document.getElementById('no-helmet-count');

                    const recognizedList = document.getElementById('recognized-list');
                    const noRecognizedMsg = document.getElementById('no-recognized-msg');

                    helmetList.innerHTML = '';
                    noHelmetList.innerHTML = '';
                    recognizedList.innerHTML = '';
                    noRecognizedMsg.textContent = '';

                    let helmeted = 0;
                    let noHelmet = 0;

                    if (data.length > 0) {
                        data.forEach(person => {
                            const li = document.createElement('li');
                            li.textContent = person.name + ' - ' + (person.has_helmet ? '有戴' : '未戴');
                            recognizedList.appendChild(li);

                            if (person.has_helmet) {
                                helmeted++;
                            } else {
                                noHelmet++;
                            }
                        });
                    } else {
                        noRecognizedMsg.textContent = '辨識中 (無)';
                    }

                    data.forEach(person => {
                        const li = document.createElement('li');
                        li.textContent = person.name;
                        if (person.has_helmet) {
                            helmetList.appendChild(li);
                        } else {
                            noHelmetList.appendChild(li);
                        }
                    });

                    helmetCount.textContent = helmeted;
                    noHelmetCount.textContent = noHelmet;

                } catch (error) {
                    console.error('Error fetching personnel data:', error);
                }
            }

            const evtSource = new EventSource('/events');
            evtSource.onmessage = function(e) {
                console.log('Received event:', e.data);
                fetchPersonnel();
            };

            // 初始化
            fetchPersonnel();
        </script>
    </body>
    </html>
    '''
    return render_template_string(HTML_TEMPLATE)

latest_frame = None

def generate_frames():
    global latest_frame
    while True:
        if latest_frame is not None:
            ret, buffer = cv2.imencode('.jpg', latest_frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def upload_person_to_server(name):
    url = 'http://localhost:8000/api/upload_face'
    data = {"name": name}
    try:
        response = requests.post(url, json=data)
        print(f"Uploaded {name} to server: {response.json()}")
    except Exception as e:
        print(f"Error uploading {name}: {e}")

def load_known_faces(directory="known_faces"):
    known_encodings = []
    known_names = []
    if not os.path.exists(directory):
        print(f"Error: The directory '{directory}' does not exist.")
        return known_encodings, known_names

    for file_name in os.listdir(directory):
        if file_name.lower().endswith((".jpg", ".png")):
            image_path = os.path.join(directory, file_name)
            print(f"Loading image: {image_path}")
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                encoding = encodings[0]
                known_encodings.append(encoding)
                known_names.append(os.path.splitext(file_name)[0])
            else:
                print(f"No face found in {file_name}")

    if not known_encodings:
        print("No known faces loaded.")
    else:
        print(f"Loaded {len(known_encodings)} known faces.")
    return known_encodings, known_names

known_face_encodings, known_face_names = load_known_faces()
model = YOLO('best.pt')

def run_face_and_yolo():
    global latest_frame
    with app.app_context():
        capture = cv2.VideoCapture(0)
        while True:
            ret, frame = capture.read()
            if not ret:
                time.sleep(0.1)
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            results = model.predict(frame, conf=0.2)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                name = "Unknown"
                has_helmet = False

                if known_face_encodings:
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    if True in matches:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            upload_person_to_server(name)

                found_hardhat = False
                for r in results[0].boxes:
                    box = r.xyxy[0].cpu().numpy()
                    obj_x1, obj_y1, obj_x2, obj_y2 = box
                    inter_x1 = max(left, obj_x1)
                    inter_y1 = max(top, obj_y1)
                    inter_x2 = min(right, obj_x2)
                    inter_y2 = min(bottom, obj_y2)

                    if inter_x2 > inter_x1 and inter_y2 > inter_y1:
                        class_id = int(r.cls)
                        if "hardhat" in model.names[class_id].lower():
                            found_hardhat = True
                            break

                if name != "Unknown":
                    update_url = 'http://localhost:8000/api/update_helmet'
                    data = {"name": name, "has_helmet": found_hardhat}
                    try:
                        requests.post(update_url, json=data)
                    except Exception as e:
                        print(f"Error updating helmet status: {e}")

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            annotated_frame = results[0].plot()
            latest_frame = annotated_frame

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        capture.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    with app.app_context():
        all_personnel = Personnel.query.all()
        for p in all_personnel:
            p.has_helmet = False
        db.session.commit()

    threading.Thread(target=run_face_and_yolo, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=8000)


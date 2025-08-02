# Workplace Safety Monitoring System

A real-time workplace safety monitoring system that integrates **YOLOv8 object detection** and **face recognition** to identify personnel and determine whether they are wearing safety helmets. The system features a **Flask-based web dashboard**, real-time video feed, and **SQLite** database for logging personnel safety status.

![System Demo](images/display.png)


## Features

- **Live Video Detection**:
  - Real-time detection using YOLOv8 (`best.pt`)
  - Safety helmet recognition
  - Face recognition against known personnel

- **Face Recognition Integration**:
  - Automatically uploads recognized personnel from `known_faces/`
  - Uses `face_recognition` library for encoding and matching

- **Personnel Database**:
  - Logs name, arrival time, and helmet status
  - Stored via SQLite (`site.db`)

- **RESTful API**:
  - `GET /api/personnel` – Retrieve personnel safety info
  - `POST /api/upload_face` – Upload new face record
  - `POST /api/update_helmet` – Update helmet status

- **Responsive Web Interface**:
  - Displays live feed and recognition results
  - Dynamic lists of personnel with/without helmets
  - Real-time updates via Server-Sent Events


## Project Structure

<pre>
Workplace-Safety-Monitoring-System/
|-- app.py               # Flask backend with APIs and web UI
|-- best.pt              # YOLOv8 model for helmet detection
|-- known_faces/         # Face images for recognition
|-- images/
|   |-- display.png      # UI preview image
|-- requirements.txt     # Python dependencies
|-- site.db              # SQLite database (auto-generated)
</pre>


## Web Dashboard Preview

The dashboard provides a categorized list of recognized personnel with or without helmets, along with a real-time video feed and face recognition results.

- **Helmeted Personnel**
- **Non-Helmeted Personnel**
- **Live Recognition List**


## Technologies Used

- **Python**
- **Flask** – Web server & API
- **YOLOv8** – Helmet detection
- **face_recognition** – Personnel identity recognition
- **SQLite** – Lightweight database
- **HTML/CSS/JS** – Custom UI dashboard


## Live System Workflow

1. Capture frame from camera.
2. Run face recognition and helmet detection.
3. Match faces with local dataset in `known_faces/`.
4. Update server via REST APIs.
5. Show results on the web dashboard.


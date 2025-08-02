# Workplace Safety Monitoring System

A real-time workplace safety monitoring system that integrates **YOLOv8 object detection** and **face recognition** to identify personnel and determine whether they are wearing safety helmets. The system features a **Flask-based web dashboard**, real-time video feed, and **SQLite** database for logging personnel safety status.

## System Preview

- No Helmet Detected  
  ![No Helmet](images/display1.png)

- Helmet Detected  
  ![With Helmet](images/display2.png)

## Features

- **Live Video Detection**
  - Real-time detection using YOLOv8 (`best.pt`)
  - Safety helmet recognition
  - Face recognition against known personnel

- **Face Recognition Integration**
  - Automatically uploads recognized personnel from `known_faces/`
  - Uses `face_recognition` library for encoding and matching

- **Personnel Database**
  - Logs name, arrival time, and helmet status
  - Stored via SQLite (`site.db`)

- **RESTful API**
  - `GET /api/personnel` – Retrieve personnel safety info
  - `POST /api/upload_face` – Upload new face record
  - `POST /api/update_helmet` – Update helmet status

- **Responsive Web Interface**
  - Displays live feed and recognition results
  - Dynamic lists of personnel with or without helmets
  - Real-time updates via Server-Sent Events

## Project Structure

| File / Folder       | Description                                      |
|---------------------|--------------------------------------------------|
| `app.py`            | Main Flask backend with API endpoints and UI     |
| `best.pt`           | YOLOv8 model for helmet detection                |
| `known_faces/`      | Local dataset of face images                     |
| `images/`           | System preview images (`display1.png`, `display2.png`) |
| `requirements.txt`  | Python dependencies                              |
| `site.db`           | Auto-generated SQLite database                   |

## Web Dashboard Preview

The dashboard provides categorized lists of recognized personnel with or without helmets, a real-time video feed, and live recognition updates.

- **Helmeted Personnel**
- **Non-Helmeted Personnel**
- **Live Recognition List**

## Technologies Used

- Python
- Flask – Web server & API
- YOLOv8 – Helmet detection
- face_recognition – Personnel identity recognition
- SQLite – Lightweight database
- HTML/CSS/JS – Custom UI dashboard

## Live System Workflow

1. Capture frame from camera.
2. Run face recognition and helmet detection.
3. Match faces with local dataset in `known_faces/`.
4. Update server via REST APIs.
5. Show results on the web dashboard.

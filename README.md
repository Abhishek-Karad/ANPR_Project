# 🚗 ANPR Tracking System (CV + OCR)

An Automatic Number Plate Recognition (ANPR) system built using **YOLOv8**, **EasyOCR**, and **OpenCV**.
The system detects vehicle license plates, extracts text, performs tracking with entry/exit logging, and EV classification.
Features both a **standalone Python script** and a **FastAPI web server** with MySQL database integration.

---

## 📌 Features

* 🔍 License Plate Detection (YOLOv8)
* 🔠 Text Recognition (EasyOCR)
* 🚗 Entry / Exit Tracking with Database Logging
* ⚡ EV vs Non-EV Classification (color-based)
* 📷 Supports Webcam, Image, and Video input
* 💾 Saves output frames (optional)
* 🌐 FastAPI Web Server with Real-time Processing
* 🗄️ MySQL Database Integration
* 🔐 Environment-based Configuration Management

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <your-repo-link>
cd ANPR_Tracking_CV
```

### 2. Create a Virtual Environment

```bash
python3 -m venv aenv
source aenv/bin/activate  # On Windows: aenv\Scripts\activate
```

### 3. Install Dependencies

For **standalone testing**:
```bash
pip install -r requirements.txt
```

For **FastAPI web server**:
```bash
pip install -r requirements-app.txt
```

> ⚠️ **Important**: Do NOT install `opencv-python-headless`, as it breaks display (`cv2.imshow`).

### 4. Setup Environment Variables

Create a `.env` file in the project root with your database credentials:

```bash
cp .env.example .env  # if available
# OR manually create .env with:
```

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=anpr_db
SERVER_PORT=8000
```

### 5. Setup MySQL Database

Install MySQL and create a database:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE anpr_db;
```

The application will automatically create the `vehicles` table on startup.

---

## ▶️ Usage

### 🔹 Option 1: Standalone Testing

#### Webcam Input

```bash
python test_model.py --model yolov8n.pt --source webcam --display
```

#### Image Input

```bash
python test_model.py --model yolov8n.pt --source car.jpg --display
```

#### Video Input

```bash
python test_model.py --model yolov8n.pt --source video.mp4 --display
```

#### Without Display (Save Output Frames)

```bash
python test_model.py --model yolov8n.pt --source car.jpg
```

---

### 🔹 Option 2: FastAPI Web Server

Start the server with your custom model:

```bash
python app.py --model best.pt --port 8000
```

Or with default model:

```bash
python app.py
```

The API will be available at:
- **API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`

#### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/detect` | POST | Upload image for detection |
| `/webcam/stream` | GET | Real-time webcam stream (MJPEG) |
| `/vehicles` | GET | Get all tracked vehicles |
| `/vehicles/{plate}` | GET | Get specific vehicle info |

#### Example API Usage

**Upload an image for detection:**
```bash
curl -X POST "http://localhost:8000/detect" \
  -F "file=@car.jpg"
```

**Get all vehicles:**
```bash
curl "http://localhost:8000/vehicles"
```

---

## 📂 Arguments

### test_model.py

| Argument    | Description                                   |
| ----------- | --------------------------------------------- |
| `--model`   | Path to YOLO `.pt` model (required)           |
| `--source`  | Input source (`webcam`, image, or video path) |
| `--display` | Enable live display window                    |

### app.py

| Argument    | Description                  |
| ----------- | ---------------------------- |
| `--model`   | Path to YOLO `.pt` model     |
| `--port`    | Server port (default: 8000)  |

---

## 🔑 Environment Variables

The following variables are loaded from `.env`:

| Variable      | Default    | Description          |
| ------------- | ---------- | -------------------- |
| `DB_HOST`     | localhost  | MySQL host           |
| `DB_USER`     | root       | MySQL username       |
| `DB_PASSWORD` | (empty)    | MySQL password       |
| `DB_NAME`     | anpr_db    | Database name        |
| `SERVER_PORT` | 8000       | FastAPI server port  |

---

## ⚠️ Important Notes

### 1. Model Selection

* `yolov8n.pt` is a **general object detection model**
* It detects **people, cars, etc.**, NOT license plates

👉 For best results, use a **custom-trained license plate model**:

```bash
# Standalone
python test_model.py --model best.pt --source webcam --display

# FastAPI server
python app.py --model best.pt
```

---

### 2. Database Connection Issues

If you get a connection error:

```
Error connecting to MySQL: [2003] Can't connect to MySQL server
```

**Solutions:**
- Ensure MySQL is running: `mysql.server start` (macOS) or `systemctl start mysql` (Linux)
- Check database credentials in `.env`
- Verify the database exists: `mysql -u root -p -e "SHOW DATABASES;"`

---

### 3. OpenCV Display Issue Fix

If you get:

```
cv2.imshow not implemented
```

Run:

```bash
pip uninstall opencv-python-headless
pip install opencv-python
```

---

### 4. CPU vs GPU

* Runs on CPU by default (slower)
* GPU (CUDA) will significantly improve performance

---

## 📸 Output

* **Standalone**: Displays annotated frames (if `--display` is used) and saves as `output_0.jpg`, `output_1.jpg`, etc.
* **FastAPI**: Returns JSON response with detected plates and database stores vehicle entry/exit logs

---

## 🗄️ Database Schema

The `vehicles` table stores:

| Column      | Type         | Description              |
| ----------- | ------------ | ------------------------ |
| `id`        | INT          | Primary key              |
| `plate`     | VARCHAR(20)  | License plate number     |
| `entry_time`| VARCHAR(20)  | Entry timestamp          |
| `exit_time` | VARCHAR(20)  | Exit timestamp           |
| `ev_status` | VARCHAR(10)  | "EV" or "NON-EV"        |
| `duration`  | VARCHAR(20)  | Stay duration            |
| `created_at`| TIMESTAMP    | Record creation time     |

---

## 🔄 Workflow

1. Input frame (webcam/image/video)
2. YOLO detects license plate region
3. Crop is passed to EasyOCR
4. Text is cleaned and validated
5. Entry/Exit logged to database
6. EV detection based on green color
7. Output displayed or returned via API

---

## 🚀 Future Improvements

* ✅ Train custom license plate detection model
* ✅ Improve OCR accuracy for Indian plates
* ✅ Add vehicle tracking (DeepSORT / ByteTrack)
* ✅ Database integration (MongoDB / Firebase)
* ✅ Real-time dashboard
* ✅ Webhook notifications on plate detection

---

## 📋 Project Structure

```
ANPR_Tracking_CV/
├── app.py                    # FastAPI web server
├── test_model.py             # Standalone test script
├── setup_model.py            # Model setup utility
├── requirements.txt          # Dependencies for test_model.py
├── requirements-app.txt      # Dependencies for app.py
├── database_schema.sql       # SQL schema
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore file
├── best.pt                  # Custom trained model (optional)
├── yolov8n.pt              # Default YOLOv8 model
└── aenv/                    # Virtual environment
```

---

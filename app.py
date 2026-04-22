from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import time
import re
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os
import argparse
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models once at startup
def load_model(model_arg=None):
    """Load YOLO model with priority order"""
    model_path = None
    
    if model_arg and os.path.exists(model_arg):
        model_path = model_arg
        print(f"✅ Using specified model: {model_arg}")
    elif os.path.exists("best.pt"):
        model_path = "best.pt"
        print("✅ Using custom license plate model: best.pt")
    elif os.path.exists("best/best.pt"):
        model_path = "best/best.pt"
        print("✅ Using custom license plate model: best/best.pt")
    else:
        if not model_arg:
            print("⚠️  No model specified. Using yolov8n.pt")
        else:
            print(f"⚠️  Model '{model_arg}' not found. Using yolov8n.pt")
        model_path = "yolov8n.pt"
    
    print(f"Loading model: {model_path}\n")
    return YOLO(model_path)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default=None, help='Path to YOLO model (.pt file)')
parser.add_argument('--port', type=int, default=8000, help='Server port')
args, unknown = parser.parse_known_args()

model = load_model(args.model)
reader = easyocr.Reader(['en'])

# MySQL Connection Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'anpr_db'),
    'autocommit': True
}

# Global state for webcam streaming
vehicle_db = {}
latest_plate = None
latest_plate_time = None
webcam_frame = None
frame_lock = threading.Lock()

def get_db_connection():
    """Create MySQL database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initialize database and create tables"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        connection.database = DB_CONFIG['database']
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plate VARCHAR(20) NOT NULL,
                entry_time VARCHAR(20),
                exit_time VARCHAR(20),
                ev_status VARCHAR(10),
                duration VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        connection.commit()
        cursor.close()
        connection.close()
        print("✅ Database initialized successfully!")
    except Error as e:
        print(f"Database initialization error: {e}")

init_db()

def clean_plate(text):
    """Clean and normalize plate text"""
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def is_ev_plate(crop):
    """Detect if plate is for electric vehicle (green color)"""
    if crop is None or crop.size == 0:
        return False
    
    crop = cv2.resize(crop, (200, 80))
    h, w, _ = crop.shape
    crop = crop[int(h*0.2):int(h*0.8), int(w*0.1):int(w*0.9)]
    
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    lower_green = np.array([25, 30, 30])
    upper_green = np.array([100, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    green_pixels = np.count_nonzero(mask)
    ratio = green_pixels / mask.size
    
    return ratio > 0.08

def preprocess_for_ocr(crop):
    """Preprocess image for better OCR accuracy"""
    crop = cv2.resize(crop, (300, 100))
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 11, 17, 17)
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharpen = cv2.filter2D(blur, -1, kernel)
    thresh = cv2.adaptiveThreshold(sharpen, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh

def detect_plates(frame):
    """Detect and recognize plates in frame"""
    results = model(frame)
    detected_plates = []
    
    for result in results:
        if result.boxes is None:
            continue
        
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]
            
            if crop.size == 0:
                continue
            
            # OCR - Original and Preprocessed
            processed = preprocess_for_ocr(crop)
            ocr_result1 = reader.readtext(crop)
            ocr_result2 = reader.readtext(processed)
            ocr_result = ocr_result1 + ocr_result2
            
            if len(ocr_result) == 0:
                continue
            
            candidates = []
            for res in ocr_result:
                text = clean_plate(res[1])
                conf = res[2]
                if len(text) >= 6 and conf > 0.3:
                    candidates.append((text, conf))
            
            if candidates:
                plate = max(candidates, key=lambda x: x[1])[0]
                status = "EV" if is_ev_plate(crop) else "NON-EV"
                detected_plates.append({
                    "plate": plate,
                    "status": status,
                    "coordinates": [x1, y1, x2, y2]
                })
    
    return detected_plates

def webcam_worker():
    """Background thread that captures and processes webcam frames"""
    global webcam_frame, latest_plate, latest_plate_time
    
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not cap.isOpened():
                print("❌ Cannot open webcam! Retrying...")
                retry_count += 1
                time.sleep(2)
                continue
            
            print("📹 Webcam connected! Streaming frames...")
            retry_count = 0
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Failed to read frame, reconnecting...")
                    break
                
                try:
                    # Detect plates
                    plates = detect_plates(frame)
                    
                    # Draw detected plates on frame
                    if plates:
                        for plate_info in plates:
                            x1, y1, x2, y2 = plate_info["coordinates"]
                            plate = plate_info["plate"]
                            status = plate_info["status"]
                            
                            # Update global plate
                            latest_plate = plate
                            latest_plate_time = datetime.now().strftime('%H:%M:%S')
                            
                            print(f"🚗 Detected: {plate} | {status}")
                            
                            # Draw rectangle
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            # Draw text with background
                            text = f"{plate} | {status}"
                            cv2.putText(frame, text, (x1, y1 - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    # Store frame for streaming
                    with frame_lock:
                        webcam_frame = frame.copy()
                    
                    frame_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Error processing frame: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ Webcam error: {e}")
            retry_count += 1
            time.sleep(2)
        
        finally:
            if 'cap' in locals():
                cap.release()
    
    print("❌ Webcam worker stopped after max retries")

def generate_frames():
    """Generator for streaming frames as MJPEG - continuous real-time video"""
    frame_count = 0
    while True:
        try:
            with frame_lock:
                if webcam_frame is None:
                    time.sleep(0.01)
                    continue
                
                frame = webcam_frame.copy()
            
            # Encode frame to high-quality JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                   + frame_bytes + b'\r\n')
            
            frame_count += 1
            # 30 FPS - adjust for real-time video
            time.sleep(0.033)
            
        except Exception as e:
            print(f"❌ Frame generation error: {e}")
            time.sleep(0.1)
            continue

# ======================= API ENDPOINTS =======================
def calculate_fare(entry_time, exit_time):
    """Simple fare calculation"""
    fmt = "%H:%M:%S"
    entry = datetime.strptime(entry_time, fmt)
    exit = datetime.strptime(exit_time, fmt)

    minutes = (exit - entry).total_seconds() / 60

    # Pricing logic
    if minutes <= 30:
        fare = 20
    else:
        hours = minutes / 60
        fare = 20 + (hours * 40)

    return round(fare, 2), round(minutes, 2)
@app.get("/")
async def read_root():
    """Serve HTML page"""
    return FileResponse("index.html")

@app.get("/video_feed")
async def video_feed():
    """Stream video feed with detected plates"""
    return StreamingResponse(generate_frames(),
                           media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/current-plate")
async def get_current_plate():
    """Get the current detected plate"""
    global latest_plate
    return {
        "success": True,
        "plate": latest_plate if latest_plate else "Detecting...",
        "timestamp": latest_plate_time
    }

@app.post("/api/record-entry")
async def record_entry(plate: str = None):
    """Record vehicle entry"""
    try:
        global latest_plate
        
        # Use provided plate or latest detected plate
        plate_to_record = plate or latest_plate
        
        if not plate_to_record:
            return {"success": False, "message": "⚠️ No plate detected!"}
        
        now = datetime.now().strftime('%H:%M:%S')
        
        if plate_to_record not in vehicle_db:
            vehicle_db[plate_to_record] = {'entry': now, 'exit': None}
            
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO vehicles (plate, entry_time, ev_status) VALUES (%s, %s, %s)",
                    (plate_to_record, now, "")
                )
                connection.commit()
                cursor.close()
                connection.close()
            
            print(f"✅ ENTRY: {plate_to_record} at {now}")
            return {"success": True, "message": f"✅ Entry recorded for {plate_to_record} at {now}"}
        else:
            return {"success": False, "message": "⚠️ Plate already in system"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/record-exit")
async def record_exit(plate: str = None):
    """Record vehicle exit"""
    try:
        global latest_plate
        
        # Use provided plate or latest detected plate
        plate_to_record = plate or latest_plate
        
        if not plate_to_record:
            return {"success": False, "message": "⚠️ No plate detected!"}
        
        now = datetime.now().strftime('%H:%M:%S')
        
        if plate_to_record in vehicle_db and vehicle_db[plate_to_record]['exit'] is None:
            vehicle_db[plate_to_record]['exit'] = now

            # 💰 FARE CALCULATION (NEW)
            entry_time = vehicle_db[plate_to_record]['entry']
            fare, duration = calculate_fare(entry_time, now)
            
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                
                # If you DID NOT add fare column → use this
                cursor.execute(
                    "UPDATE vehicles SET exit_time = %s, duration = %s WHERE plate = %s ORDER BY id DESC LIMIT 1",
                    (now, f"{duration} mins", plate_to_record)
                )

                # If you ADDED fare column → use this instead
                # cursor.execute(
                #     "UPDATE vehicles SET exit_time = %s, duration = %s, fare = %s WHERE plate = %s ORDER BY id DESC LIMIT 1",
                #     (now, f"{duration} mins", fare, plate_to_record)
                # )

                connection.commit()
                cursor.close()
                connection.close()
            
            print(f"💰 EXIT: {plate_to_record} | Duration: {duration} mins | Fare: ₹{fare}")

            return {
                "success": True,
                "message": f"✅ Exit recorded for {plate_to_record}",
                "duration": f"{duration} mins",
                "fare": f"₹{fare}"
            }

        else:
            return {"success": False, "message": "⚠️ Cannot record exit for this plate"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
@app.get("/api/vehicles")
async def get_vehicles():
    """Get all vehicle logs"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "vehicles": []}
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicles ORDER BY id DESC LIMIT 100")
        vehicles = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return {"success": True, "vehicles": vehicles}
    
    except Exception as e:
        return {"success": False, "error": str(e), "vehicles": []}

@app.get("/api/stats")
async def get_stats():
    """Get parking statistics"""
    try:
        connection = get_db_connection()
        if not connection:
            return {"success": False, "stats": {}}
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM vehicles")
        total = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as ev_count FROM vehicles WHERE ev_status = 'EV'")
        ev_count = cursor.fetchone()['ev_count']
        cursor.execute("SELECT COUNT(*) as active FROM vehicles WHERE exit_time IS NULL")
        active = cursor.fetchone()['active']
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "stats": {
                "total_vehicles": total,
                "ev_vehicles": ev_count,
                "active_vehicles": active,
                "non_ev_vehicles": total - ev_count
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/model-info")
async def get_model_info():
    """Get current model information"""
    return {
        "success": True,
        "message": "Server is running with webcam streaming"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Start webcam worker thread (same as test_model.py)
    webcam_thread = threading.Thread(target=webcam_worker, daemon=True)
    webcam_thread.start()
    
    print(f"\n🚀 Starting ANPR server on http://localhost:{args.port}")
    print(f"📱 Open browser and go to http://localhost:{args.port}")
    print(f"📹 Webcam feed will stream to browser in real-time\n")
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)

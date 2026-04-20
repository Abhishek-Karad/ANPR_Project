# 🚗 ANPR Tracking System - Full Stack with MySQL

A complete full-stack Automatic Number Plate Recognition (ANPR) system with:
- **Backend**: FastAPI + Python (vehicle detection & OCR)
- **Frontend**: Simple HTML UI with real-time updates
- **Database**: MySQL (persistent storage)

---

## 📋 Prerequisites

- **Python 3.8+**
- **MySQL Server** (installed and running)
- **Webcam** (for live detection)

---

## 🛠️ Installation & Setup

### 1. **Install Python Dependencies**

```bash
pip install -r requirements-app.txt
```

### 2. **Setup MySQL Database**

#### Option A: Using MySQL CLI

```bash
mysql -u root -p < database_schema.sql
```

**When prompted for password, press Enter (if no password set) or enter your MySQL password**

#### Option B: Using MySQL Workbench or GUI

Open `database_schema.sql` file and execute the SQL commands.

#### Option C: Check MySQL Credentials in app.py

Edit `app.py` and find the `DB_CONFIG` section:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change if you have a MySQL password
    'database': 'anpr_db',
    'autocommit': True
}
```

**If you have a MySQL password, update the `password` field.**

---

## ▶️ Running the Application

### **Terminal 1: Start the Backend Server**

```bash
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
Database initialized successfully!
```

### **Terminal 2: Open the Frontend**

Open your browser and go to:
```
http://localhost:8000
```

---

## 📱 How to Use

1. **Allow Webcam Access** - Browser will ask for webcam permission
2. **Live Feed** - You'll see the webcam feed in the UI
3. **Detect Plates** - System automatically detects license plates
4. **Record Entry** - Press **E** key or click **📥 Entry** button
5. **Record Exit** - Press **X** key or click **📤 Exit** button
6. **View Logs** - Vehicle history appears in the right sidebar
7. **Watch Stats** - Real-time statistics update at the top

---

## 🎯 Features

✅ Real-time plate detection from webcam  
✅ Automatic OCR text recognition  
✅ EV (Electric Vehicle) detection  
✅ Manual entry/exit logging  
✅ MySQL database persistence  
✅ Live statistics dashboard  
✅ Keyboard shortcuts (E for Entry, X for Exit)  
✅ Responsive HTML UI  

---

## 📊 Database Table Structure

```sql
CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate VARCHAR(20),
    entry_time VARCHAR(20),
    exit_time VARCHAR(20),
    ev_status VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/detect-plate` | POST | Detect plates in frame |
| `/api/record-entry` | POST | Log vehicle entry |
| `/api/record-exit` | POST | Log vehicle exit |
| `/api/vehicles` | GET | Get all vehicle logs |
| `/api/stats` | GET | Get parking statistics |
| `/` | GET | Serve HTML UI |

---

## ⚙️ Configuration

### Change MySQL Credentials

Edit `app.py`:

```python
DB_CONFIG = {
    'host': 'localhost',       # Your MySQL host
    'user': 'root',            # Your MySQL username
    'password': 'your_pass',   # Your MySQL password
    'database': 'anpr_db',
    'autocommit': True
}
```

### Change Server Port

Edit `app.py` (last line):

```python
uvicorn.run(app, host="0.0.0.0", port=8080)  # Change 8000 to 8080
```

---

## 🐛 Troubleshooting

### **"Connection refused" error**

MySQL is not running. Start it:

**macOS:**
```bash
brew services start mysql
```

**Windows:**
```bash
net start MySQL80
```

**Linux:**
```bash
sudo systemctl start mysql
```

---

### **"Access denied for user 'root'@'localhost'"**

1. Check your MySQL password in `app.py`
2. Update the `DB_CONFIG` with the correct password:

```python
DB_CONFIG = {
    'password': 'your_actual_password',  # Add your password here
}
```

---

### **"Database does not exist"**

Run the database setup again:

```bash
mysql -u root -p < database_schema.sql
```

---

### **Webcam not working**

- Allow browser permission to access webcam
- Check if webcam is being used by another app
- Refresh the page

---

## 📁 Project Structure

```
ANPR_Tracking_CV-main/
├── app.py                    # FastAPI backend
├── index.html               # Frontend UI
├── database_schema.sql      # MySQL schema
├── requirements-app.txt     # Python dependencies
├── yolov8n.pt              # YOLOv8 model
├── test_model.py           # Original script
└── README.md               # This file
```

---

## 🚀 Next Steps

- Add user authentication
- Deploy to cloud (AWS, Heroku)
- Add vehicle image capture
- Export reports to PDF
- Add SMS/Email notifications

---

## 📞 Support

For issues, check the terminal logs or browser console (F12).


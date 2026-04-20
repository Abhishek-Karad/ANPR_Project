# 🚗 ANPR Tracking System (CV + OCR)

An Automatic Number Plate Recognition (ANPR) system built using **YOLOv8**, **EasyOCR**, and **OpenCV**.
The system detects vehicle license plates, extracts text, and performs basic tracking with entry/exit logging and EV classification.

---

## 📌 Features

* 🔍 License Plate Detection (YOLOv8)
* 🔠 Text Recognition (EasyOCR)
* 🚗 Entry / Exit Tracking
* ⚡ EV vs Non-EV Classification (color-based)
* 📷 Supports Webcam, Image, and Video input
* 💾 Saves output frames (optional)

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone <your-repo-link>
cd ANPR_Tracking_CV
```

### 2. Install dependencies

```bash
pip install ultralytics easyocr numpy opencv-python
```

> ⚠️ Make sure you **do NOT install `opencv-python-headless`**, as it breaks display (`cv2.imshow`).

---

## ▶️ Usage

### 🔹 Webcam Input

```bash
python test_model.py --model yolov8n.pt --source webcam --display
```

---

### 🔹 Image Input

```bash
python test_model.py --model yolov8n.pt --source car.jpg --display
```

---

### 🔹 Video Input

```bash
python test_model.py --model yolov8n.pt --source video.mp4 --display
```

---

### 🔹 Without Display (Save Output Frames)

```bash
python test_model.py --model yolov8n.pt --source car.jpg
```

---

## 📂 Arguments

| Argument    | Description                                   |
| ----------- | --------------------------------------------- |
| `--model`   | Path to YOLO `.pt` model (required)           |
| `--source`  | Input source (`webcam`, image, or video path) |
| `--display` | Enable live display window                    |

---

## ⚠️ Important Notes

### 1. Model Selection

* `yolov8n.pt` is a **general object detection model**
* It detects **people, cars, etc.**, NOT license plates

👉 For best results, use a **custom-trained license plate model**:

```bash
python test_model.py --model best.pt --source webcam --display
```

---

### 2. OpenCV Display Issue Fix

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

### 3. CPU vs GPU

* Runs on CPU by default (slower)
* GPU (CUDA) will significantly improve performance

---

## 📸 Output

* Displays annotated frames (if `--display` is used)
* Saves frames as:

```
output_0.jpg
output_1.jpg
...
```

---

## 🔄 Workflow

1. Input frame (webcam/image/video)
2. YOLO detects license plate region
3. Crop is passed to EasyOCR
4. Text is cleaned and validated
5. Entry/Exit logged
6. EV detection based on green color
7. Output displayed or saved

---

## 🚀 Future Improvements

* ✅ Train custom license plate detection model
* ✅ Improve OCR accuracy for Indian plates
* ✅ Add vehicle tracking (DeepSORT / ByteTrack)
* ✅ Database integration (MongoDB / Firebase)
* ✅ Real-time dashboard

---

## 👨‍💻 Author

Developed as part of IPPR coursework.

---

## 📜 License

This project is for academic and research purposes.

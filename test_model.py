import cv2
import argparse
import time
import re
import numpy as np
import os
from ultralytics import YOLO
import easyocr
import csv

# -------------------------
# DEBUG FLAG (ADDED)
# -------------------------
DEBUG = False

# -------------------------
# Utils
# -------------------------

def clean_plate(text):
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def is_ev_plate(crop):
    if crop is None or crop.size == 0:
        return False

    crop = cv2.resize(crop, (200, 80))

    h, w, _ = crop.shape
    crop = crop[int(h*0.2):int(h*0.8), int(w*0.1):int(w*0.9)]

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    lower_green = np.array([25, 30, 30])
    upper_green = np.array([100, 255, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)

    if DEBUG:
        cv2.imshow("crop", crop)
        cv2.imshow("mask", mask)

    green_pixels = np.count_nonzero(mask)
    ratio = green_pixels / mask.size

    return ratio > 0.08

# -------------------------
# OCR Improvement
# -------------------------

def preprocess_for_ocr(crop):
    crop = cv2.resize(crop, (300, 100))

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    blur = cv2.bilateralFilter(gray, 11, 17, 17)

    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharpen = cv2.filter2D(blur, -1, kernel)

    thresh = cv2.adaptiveThreshold(
        sharpen, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    return thresh

# -------------------------
# Main
# -------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='webcam',
                        help='webcam OR path to image/video')
    parser.add_argument('--model', type=str, required=True,
                        help='Path to .pt model')
    parser.add_argument('--display', action='store_true',
                        help='Enable display (only if GUI available)')
    args = parser.parse_args()

    model = YOLO(args.model)
    reader = easyocr.Reader(['en'])

    vehicle_db = {}

    # -------------------------
    # CSV LOG SETUP
    # -------------------------
    log_file = "plate_log.csv"

    if not os.path.exists(log_file):
        with open(log_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Plate", "Entry Time", "Exit Time", "EV Status"])

    # -------------------------
    # Source Handling
    # -------------------------

    mode = None

    if args.source == 'webcam':
        cap = cv2.VideoCapture(0)
        mode = "video"

    elif os.path.isfile(args.source):
        if args.source.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(args.source)
            if image is None:
                print("Failed to load image")
                return
            mode = "image"
        else:
            cap = cv2.VideoCapture(args.source)
            mode = "video"
    else:
        print("Invalid source")
        return

    frame_count = 0

    # -------------------------
    # Processing Loop
    # -------------------------

    while True:

        if mode == "image":
            frame = image.copy()
        else:
            ret, frame = cap.read()
            if not ret:
                break

        results = model(frame)

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                crop = frame[y1:y2, x1:x2]

                if crop.size == 0:
                    continue

                # OCR
                processed = preprocess_for_ocr(crop)

                if DEBUG:
                    cv2.imshow("processed", processed)

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

                if not candidates:
                    continue

                plate = max(candidates, key=lambda x: x[1])[0]

                now = time.strftime('%H:%M:%S')

                status = "EV" if is_ev_plate(crop) else "NON-EV"

                # ENTRY LOG
                if plate not in vehicle_db:
                    vehicle_db[plate] = {'entry': now, 'exit': None}
                    print(f"ENTRY: {plate} at {now}")

                    with open(log_file, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([plate, now, "", status])

                # EXIT LOG
                else:
                    if vehicle_db[plate]['exit'] is None:
                        vehicle_db[plate]['exit'] = now
                        print(f"EXIT: {plate} at {now}")

                        with open(log_file, mode='a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([plate, "", now, status])

                # Draw overlays
                cv2.putText(frame, f"{plate} | {status}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)

                cv2.rectangle(frame, (x1, y1), (x2, y2),
                              (0, 255, 0), 2)

        # Output Handling
        if args.display:
            cv2.imshow("ANPR", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
        else:
            output_name = f"output_{frame_count}.jpg"
            cv2.imwrite(output_name, frame)
            print(f"Saved {output_name}")

        frame_count += 1

        if mode == "image":
            break

    if mode != "image":
        cap.release()

    if args.display:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
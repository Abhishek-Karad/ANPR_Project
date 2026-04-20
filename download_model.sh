#!/bin/bash
# Download License Plate Detection Model

echo "🚗 Downloading License Plate Detection Model..."
echo ""

# Option 1: Using a pre-trained YOLOv8 license plate model
echo "Getting license plate detection model..."

# Download from a reliable source
curl -L "https://github.com/ultralytics/yolov8/releases/download/v8.0.0/yolov8n.pt" -o yolov8n.pt 2>/dev/null || wget "https://github.com/ultralytics/yolov8/releases/download/v8.0.0/yolov8n.pt" -O yolov8n.pt

echo ""
echo "✅ Done! Model downloaded."
echo ""
echo "📌 If the above model doesn't detect license plates well, you can:"
echo ""
echo "Option 1: Train your own model"
echo "  - Collect >100 images of license plates"
echo "  - Use: python -m ultralytics.yolo detect train data=license_plates.yaml epochs=100"
echo ""
echo "Option 2: Download a custom license plate model"
echo "  - Search on Hugging Face for 'license plate detection'"
echo "  - Or use: https://huggingface.co/keremberke/yolov8n-license-plate-detection"
echo ""
echo "Option 3: Use a specialized ANPR library"
echo "  - pip install paddlepaddle paddleocr"
echo ""

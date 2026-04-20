"""
Download License Plate Detection Model
Supports multiple sources for getting a proper ANPR model
"""

import os
import sys
import urllib.request
import zipfile

def download_huggingface_model():
    """Download license plate model from Hugging Face"""
    print("🤗 Downloading from Hugging Face...")
    print("This model is specifically trained for license plate detection\n")
    
    try:
        # Using a lighter weight model from Hugging Face
        url = "https://huggingface.co/keremberke/yolov8n-license-plate-detection/resolve/main/weights/best.pt"
        print(f"Downloading from: {url}")
        print("(This may take a few minutes...)\n")
        
        urllib.request.urlretrieve(url, "best.pt")
        print("✅ Model downloaded successfully!")
        print("📍 Saved as: best.pt\n")
        return True
    except Exception as e:
        print(f"❌ Failed to download from Hugging Face: {e}")
        return False

def download_yolo_models():
    """Download standard YOLOv8 model for fallback"""
    print("📥 Downloading YOLOv8 model...\n")
    
    try:
        from ultralytics import YOLO
        print("Downloading model...")
        model = YOLO('yolov8n.pt')  # This downloads if not exists
        print("✅ YOLOv8n model ready\n")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚗 License Plate Detection Model Downloader")
    print("="*60 + "\n")
    
    print("Choose an option:\n")
    print("1️⃣  Download specialized license plate model (RECOMMENDED)")
    print("   - Best for license plate detection")
    print("   - ~30-40 MB\n")
    print("2️⃣  Download standard YOLOv8 model")
    print("   - General object detection")
    print("   - Better for cars/vehicles\n")
    print("3️⃣  Exit\n")
    
    choice = input("Enter your choice (1/2/3): ").strip()
    
    if choice == "1":
        print("\n" + "-"*60)
        success = download_huggingface_model()
        if success:
            print("-"*60)
            print("\n✨ Next steps:")
            print("1. Make sure MySQL is running: brew services start mysql")
            print("2. Run the app: python app.py")
            print("3. Open browser: http://localhost:8000\n")
        else:
            print("\n⚠️  Hugging Face download failed.")
            print("Falling back to standard YOLOv8...\n")
            download_yolo_models()
            print("\n📝 Note: License plates may not be detected well.")
            print("Consider training a custom model or using Option 1.\n")
    
    elif choice == "2":
        print("\n" + "-"*60)
        download_yolo_models()
        print("-"*60)
        print("\n⚠️  Using general object detection model")
        print("This will detect cars but may struggle with license plates.\n")
    
    elif choice == "3":
        print("Exiting...\n")
        sys.exit(0)
    
    else:
        print("❌ Invalid choice. Please try again.\n")
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user\n")
        sys.exit(0)

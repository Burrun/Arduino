import requests
import time
import base64
import os

BASE_URL = "http://localhost:5000"

def test_esp32_integration():
    print("Testing ESP32 Integration...")
    
    # 1. Upload Image (ESP32 -> Server)
    print("1. Uploading Image...")
    dummy_image = b"fake_image_data"
    try:
        res = requests.post(f"{BASE_URL}/upload_image", data=dummy_image)
        assert res.status_code == 200
        print("   Upload Image OK")
    except Exception as e:
        print(f"   Upload Image FAILED: {e}")
        return

    # 2. Get Camera (Frontend -> Server)
    print("2. Getting Camera Image...")
    try:
        res = requests.get(f"{BASE_URL}/api/camera")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "path" in data
        print(f"   Get Camera OK: {data['path']}")
    except Exception as e:
        print(f"   Get Camera FAILED: {e}")

    # 3. Upload GPS (ESP32 -> Server)
    print("3. Uploading GPS...")
    dummy_gps = "37.5665,126.9780,2023-10-27T10:00:00"
    try:
        res = requests.post(f"{BASE_URL}/upload_gps", data=dummy_gps)
        assert res.status_code == 200
        print("   Upload GPS OK")
    except Exception as e:
        print(f"   Upload GPS FAILED: {e}")

    # 4. Get GPS (Frontend -> Server)
    print("4. Getting GPS Location...")
    try:
        res = requests.get(f"{BASE_URL}/api/gps")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        gps_data = data["data"]
        assert gps_data["latitude"] == "37.5665"
        assert gps_data["longitude"] == "126.9780"
        print(f"   Get GPS OK: {gps_data}")
    except Exception as e:
        print(f"   Get GPS FAILED: {e}")

def test_signature_integration():
    print("\nTesting Signature Integration...")
    
    # 5. Upload Signature (Frontend -> Server)
    print("5. Uploading Signature...")
    # Create a small white 1x1 png base64
    dummy_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
    try:
        res = requests.post(f"{BASE_URL}/api/signature", json={"image": dummy_b64})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "path" in data
        print(f"   Upload Signature OK: {data['path']}")
    except Exception as e:
        print(f"   Upload Signature FAILED: {e}")

if __name__ == "__main__":
    # Wait for server to start
    print("Waiting for server...")
    time.sleep(2)
    try:
        test_esp32_integration()
        test_signature_integration()
    except requests.ConnectionError:
        print("Could not connect to server. Is it running?")

from flask import Flask, request, jsonify
import time
import os
from datetime import datetime

app = Flask(__name__)

# ======================
# 创建保存目录
# ======================
os.makedirs("images", exist_ok=True)
os.makedirs("gps", exist_ok=True)


# ======================
#  接收摄像头 JPEG
# ======================
@app.route("/upload_image", methods=["POST"])
def upload_image():
    try:
        img_bytes = request.data
        
        if not img_bytes:
            return jsonify({"status": "ERROR", "msg": "empty body"}), 400

        # 时间戳作为文件名
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"images/{ts}.jpg"

        with open(filename, "wb") as f:
            f.write(img_bytes)

        print(f"[IMAGE] Received {len(img_bytes)} bytes → {filename}")

        return jsonify({"status": "OK", "filename": filename})

    except Exception as e:
        print("[ERROR] upload_image:", e)
        return jsonify({"status": "ERROR"}), 500



# ======================
#  接收 GPS 数据
# ======================
@app.route("/upload_gps", methods=["POST"])
def upload_gps():
    try:
        gps_text = request.data.decode("utf-8", errors="ignore").strip()

        if len(gps_text) == 0:
            return jsonify({"status": "ERROR", "msg": "empty gps"}), 400

        filename = "gps/gps_data.txt"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(filename, "a", encoding="utf8") as f:
            f.write(f"[{ts}] {gps_text}\n")

        print(f"[GPS] {gps_text}  → appended to {filename}")

        return jsonify({"status": "OK"})

    except Exception as e:
        print("[ERROR] upload_gps:", e)
        return jsonify({"status": "ERROR"}), 500



# ======================
#  启动服务
# ======================
if __name__ == "__main__":
    print("\n=== Python 服务已启动，等待 ESP32 发送数据... ===")
    app.run(host="0.0.0.0", port=10001, debug=False, threaded=True)
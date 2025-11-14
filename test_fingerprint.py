from modules.sensors import fingerprint

def main():
    finger = fingerprint.connect_fingerprint_sensor()
    print("센서 연결 OK!")
    print("템플릿 개수:", getattr(finger, "template_count", "unknown"))

if __name__ == "__main__":
    main()

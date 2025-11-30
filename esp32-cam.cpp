#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <HardwareSerial.h>

// ========== WiFi 信息 ==========
//const char* ssid = "GLMT3000";
//const char* password = "jiang1229464665";
const char* ssid = "op13";
const char* password = "12345679";
// ========== 上传服务器地址 ==========
//String upload_url_img = "http://192.168.8.127:10001/upload_image";
//String upload_url_gps = "http://192.168.8.127:10001/upload_gps";
String upload_url_img = "http://192.168.145.127:10001/upload_image";
String upload_url_gps = "http://192.168.145.127:10001/upload_gps";
// ========== GPS 串口（使用 IO15）==========
HardwareSerial GPS(2);  
// RX = IO15, TX 不用（设为 -1）
#define GPS_RX_PIN 15
#define GPS_TX_PIN -1

// ========== AI Thinker 引脚配置 ==========
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22


// ================= 摄像头初始化 =================
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 10;
  config.fb_count = 2;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] 初始化失败 %s\n", esp_err_to_name(err));
    return false;
  }

  Serial.println("[CAM] 摄像头初始化成功");
  return true;
}


// ================= 上传图片 =================
void uploadImage() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("[IMG] 获取帧失败");
    return;
  }

  HTTPClient http;
  http.begin(upload_url_img);
  http.addHeader("Content-Type", "image/jpeg");

  int httpCode = http.POST(fb->buf, fb->len);
  Serial.printf("[UPLOAD IMG] 状态码: %d, 大小: %d 字节\n", httpCode, fb->len);

  http.end();
  esp_camera_fb_return(fb);
}


// ================= 上传 GPS 数据 =================
void uploadGPS(String gps) {
  if (gps.length() < 3) return;

  HTTPClient http;
  http.begin(upload_url_gps);
  http.addHeader("Content-Type", "text/plain");

  int httpCode = http.POST(gps);
  Serial.printf("[UPLOAD GPS] 状态码: %d\n", httpCode);

  http.end();
}


// ================= 系统初始化 =================
void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n===== 系统启动 =====");

  // GPS 串口初始化
  GPS.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  Serial.println("[GPS] 初始化完成 (IO15)");

  // 摄像头
  if (!initCamera()) {
    Serial.println("[FATAL] 摄像头初始化失败");
    while (1) delay(1000);
  }

  // WiFi
  Serial.println("[WiFi] 开始连接...");
  WiFi.begin(ssid, password);

  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 40) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\n[WiFi] 连接失败，重启中...");
    ESP.restart();
  }

  Serial.printf("\n[WiFi] 已连接: %s\n", WiFi.localIP().toString().c_str());
  Serial.println("===== 系统运行中 =====");
}


// ================= 主循环 =================
void loop() {

  // ----- GPS 数据处理 -----
  while (GPS.available()) {
    String line = GPS.readStringUntil('\n');
    line.trim();

    if (line.length() > 3) {
      Serial.println("[GPS] " + line);
      uploadGPS(line);  // 上传 GPS 数据
    }
  }

  // ----- 上传摄像头图像 -----
  uploadImage();

  delay(3000);  // 每 3 秒一轮
}
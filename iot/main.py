from machine import Pin
import ujson
import network
import utime as time
import dht
import urequests as request

# Pin setup
PIR_PIN = Pin(23, Pin.IN, Pin.PULL_DOWN)
LED_PIN = Pin(2, Pin.OUT)
DHT_PIN = Pin(5)
dht_sensor = dht.DHT11(DHT_PIN)

# Konfigurasi
DEVICE_ID = "esp32-sic6"
WIFI_SSID = "Puspa Asri" # Ganti dengan nama WiFi yang Anda gunakan
WIFI_PASSWORD = "tanyabukos" # Ganti dengan password WiFi yang Anda gunakan
UBIDOTS_TOKEN = "BBUS-ImMQsZkyWNWzawAtANIMFU7k2RBXIf"

API_SERVICE_URL = "http://localhost:5000/api/data" # Ganti "localhost" dengan IP Anda

motion_detected = False

# Handler untuk deteksi gerakan
def handle_motion(pin):
    global motion_detected
    motion_detected = True
    print("Motion detected!")
    LED_PIN.value(1)
    time.sleep(1)
    LED_PIN.value(0)

PIR_PIN.irq(trigger=Pin.IRQ_RISING, handler=handle_motion)

# Mengirim data ke Ubidots
def send_to_ubidots(temperature, humidity, motion):
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/" + DEVICE_ID
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": UBIDOTS_TOKEN
    }
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "motion": 1 if motion else 0,
    }
    try:
        response = request.post(url, json=data, headers=headers)
        print("Data sent to Ubidots:", response.status_code)
        response.close()
        return True
    except Exception as e:
        print("Error sending data to Ubidots:", e)
        return False
        
# Mengirim data ke API kustom
def send_to_api_service(temperature, humidity, motion):
    data = {
        "device_id": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity,
        "motion": 1 if motion else 0,
        "timestamp": int(time.mktime(time.localtime()))

    }
    try:
        headers = {"Content-Type": "application/json"}
        response = request.post(API_SERVICE_URL, json=data, headers=headers)
        print("Data sent to API service:", response.status_code)
        response.close()
        return True
    except Exception as e:
        print("Error sending data to API service:", e)
        return False

# Koneksi WiFi
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    print("Connecting to WiFi...")
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    
    retry_count = 0
    while not wifi.isconnected() and retry_count < 10:
        print("Attempting connection...")
        time.sleep(1)
        retry_count += 1
    
    if wifi.isconnected():
        print("WiFi Connected! IP:", wifi.ifconfig()[0])
        return True
    else:
        print("Failed to connect to WiFi")
        return False

def main():
    if not connect_wifi():
        return
        
    global motion_detected
    
    while True:
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            
            motion = motion_detected
            motion_detected = False 
            
            print(f"Temperature: {temperature}°C, Humidity: {humidity}%, Motion: {motion}")
            
            # Kirim data ke Ubidots
            ubidots_success = send_to_ubidots(temperature, humidity, motion)
            
            # Kirim data ke API service
            api_success = send_to_api_service(temperature, humidity, motion)
            
            # Jika pengiriman data ke Ubidots dan API sukses
            if ubidots_success and api_success:
                for _ in range(3): 
                    LED_PIN.value(1)
                    time.sleep(0.1)
                    LED_PIN.value(0)
                    time.sleep(0.1)
            
        except Exception as e:
            print("Error in main loop:", e)
        
        time.sleep(5)

if __name__ == "__main__":
    main()
import streamlit as st
import requests
import time
from datetime import datetime, timedelta

# Masukkan API Token kamu di sini
UBIDOTS_TOKEN = st.secrets["UBIDOTS_TOKEN"]
DEVICE_LABEL = "ESP32-SIC6"

def get_data(variable):
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}/{variable}/lv"
    headers = {"X-Auth-Token": UBIDOTS_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return float(response.text)
    else:
        return None

st.title("📊 Dashboard IoT Tanaman (Live dari Ubidots)")

suhu = get_data("temperature")
kelembapan = get_data("humidity")
tanah = get_data("soil_moisture")

col1, col2, col3 = st.columns(3)
col1.metric("🌡️ Suhu", f"{suhu} °C" if suhu else "❌ Gagal ambil data")
col2.metric("💧 Kelembapan Udara", f"{kelembapan} %" if kelembapan else "❌")
col3.metric("🌾 Kelembapan Tanah", f"{tanah}" if tanah else "❌")

# Simpan waktu mulai jika kondisi terpenuhi
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# Cek kondisi
if suhu is not None and kelembapan is not None:
    kondisi_terpenuhi = suhu > 35 or kelembapan < 40

    if kondisi_terpenuhi:
        if st.session_state.start_time is None:
            st.session_state.start_time = datetime.now()
        else:
            elapsed = datetime.now() - st.session_state.start_time
            if elapsed >= timedelta(minutes=60):
                st.warning("Tanah terlalu kering! 💦 Siram tanaman.")
    else:
        st.session_state.start_time = None 

    if not kondisi_terpenuhi:
        st.success("✅ Suhu dan kelembapan normal.")
else:
    st.error("❌ Gagal mengambil data suhu atau kelembapan.")


# Kita belum menggunakan soil moisture sensor

# if tanah is not None:
#     if tanah < 300:
#         st.warning("Tanah terlalu kering! 💦 Siram tanaman.")
#     else:
#         st.success("Tanah cukup lembap ✅")

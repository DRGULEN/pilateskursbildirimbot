import os
import time
import asyncio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Bot
from dotenv import load_dotenv

# --- Ortam değişkenlerini yükle ---
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

REFERANS_TARIH = datetime.strptime("08.09.2025", "%d.%m.%Y")
URL = "https://www.tcf.gov.tr/branslar/pilates/"

async def telegram_mesaj_gonder(mesaj):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=mesaj)
    print("Telegram'a bildirim gönderildi.")

def kurslari_getir():
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(URL)

    # "Kurs" sekmesine tıklamak
    try:
        kurs_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Kurs"))
        )
        kurs_tab.click()
    except:
        print("Kurs sekmesi bulunamadı.")
        driver.quit()
        return []

    # Tabloyu bekle
    try:
        tablo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        rows = tablo.find_elements(By.TAG_NAME, "tr")[1:]  # başlık satırını atla
    except:
        print("Tablo bulunamadı.")
        driver.quit()
        return []

    kurslar = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 3:
            baslik = cols[0].text.strip()
            yer = cols[1].text.strip()
            tarih = cols[2].text.strip()
            try:
                bas_tarih = datetime.strptime(tarih.split(" - ")[0], "%d.%m.%Y")
            except:
                continue
            kurslar.append({"baslik": baslik, "yer": yer, "tarih": tarih, "bas_tarih": bas_tarih})

    driver.quit()
    return kurslar

async def yeni_kurslari_kontrol_et():
    kurslar = kurslari_getir()
    if not kurslar:
        print("Kurs bilgileri alınamadı.")
        return

    yeni = [k for k in kurslar if k["bas_tarih"] > REFERANS_TARIH]
    if yeni:
        mesaj = "🚨 Yeni kurslar bulundu:\n\n"
        for k in yeni:
            mesaj += f"- {k['baslik']} / {k['yer']} / {k['tarih']}\n"
        await telegram_mesaj_gonder(mesaj)
    else:
        print("Yeni kurs bulunamadı.")

def bekle_saat_basi():
    import datetime
    now = datetime.datetime.now()
    next_hour = (now.replace(minute=0, second=0, microsecond=0)
                 + datetime.timedelta(hours=1))
    sleep_seconds = (next_hour - now).total_seconds()
    print(f"{sleep_seconds:.0f} saniye bekleniyor, sonraki tarama saat başı yapılacak.")
    time.sleep(sleep_seconds)

# -------------------------
# Saat başı loop
# -------------------------
if __name__ == "__main__":
    while True:
        try:
            asyncio.run(yeni_kurslari_kontrol_et())
        except Exception as e:
            print(f"Hata oluştu: {e}")
        bekle_saat_basi()

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
from telegram import Bot
from dotenv import load_dotenv
import time
import asyncio

# --- Ortam değişkenlerini yükle ---
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Son bilinen kurs başlangıç tarihi (referans)
REFERANS_TARIH = datetime.strptime("08.09.2025", "%d.%m.%Y")

URL = "https://www.tcf.gov.tr/branslar/pilates/#kurs"

def kurslari_getir():
    """Web sayfasındaki kurs bilgilerini parse eder ve olası hataları yönetir."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0 Safari/537.36"
    }
    try:
        resp = requests.get(URL, headers=headers, timeout=10)
        resp.raise_for_status()
        print("DEBUG: Web sayfası başarıyla çekildi.")
    except requests.exceptions.RequestException as e:
        print(f"Hata: Web sayfasına bağlanılamadı. {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    try:
        rows = soup.select("table:nth-of-type(2) tr")[1:]
    except IndexError:
        print("Hata: Kurs tablosu bulunamadı veya site yapısı değişmiş.", file=sys.stderr)
        return []

    kurslar = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            baslik = cols[0].get_text(strip=True)
            yer = cols[1].get_text(strip=True)
            tarih = cols[2].get_text(strip=True)

            try:
                bas_tarih = datetime.strptime(tarih.split(" - ")[0], "%d.%m.%Y")
            except (ValueError, IndexError):
                continue

            kurslar.append({
                "baslik": baslik,
                "yer": yer,
                "tarih": tarih,
                "bas_tarih": bas_tarih
            })
    return kurslar

async def telegram_mesaj_gonder(mesaj):
    """Belirtilen mesajı Telegram'a gönderir."""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mesaj)
        print("Telegram'a bildirim gönderildi.")
    except Exception as e:
        print(f"Telegram'a mesaj gönderilirken hata oluştu: {e}", file=sys.stderr)

# ---
# Burası önemli: `yeni_kurslari_kontrol_et` artık `async` bir fonksiyon
# ---
async def yeni_kurslari_kontrol_et():
    """Yeni kurs olup olmadığını kontrol eder ve sonuçları Telegram'a bildirir."""
    kurslar = kurslari_getir()

    if not kurslar:
        mesaj = "Kurs bilgileri alınamadı. Lütfen daha sonra tekrar deneyin."
        print(mesaj)
        # Hata burada düzeltildi: `await` eklendi
        await telegram_mesaj_gonder(mesaj)
        return

    yeni = [k for k in kurslar if k["bas_tarih"] > REFERANS_TARIH]

    if yeni:
        mesaj = "🚨 Yeni kurslar bulundu:\n\n"
        for k in yeni:
            mesaj += f"- {k['baslik']} / {k['yer']} / {k['tarih']}\n"
        print(mesaj)
        # Hata burada düzeltildi: `await` eklendi
        await telegram_mesaj_gonder(mesaj)
    else:
        mesaj = "Yeni kurs bulunamadı."
        print(mesaj)
        # Hata burada düzeltildi: `await` eklendi
        await telegram_mesaj_gonder(mesaj)

# -------------------------
# `asyncio.run` ile ana döngüyü çalıştırma
# -------------------------
if __name__ == "__main__":
    while True:
        try:
            # `async` fonksiyonu, `asyncio.run` ile çağırıyoruz.
            asyncio.run(yeni_kurslari_kontrol_et())
        except Exception as e:
            print(f"Genel bir hata oluştu: {e}", file=sys.stderr)
        
        # 30 dakika bekle (1800 saniye)
        time.sleep(1800)
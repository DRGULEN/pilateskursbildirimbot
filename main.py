import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import asyncio
from telegram import Bot
from dotenv import load_dotenv
import time

# --- Ortam değişkenlerini yükle ---
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

        # --- DEBUG: HTML’in ilk 500 karakterini logla ---
        print("DEBUG HTML:", resp.text[:500])

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
    """Belirtilen mesajı Telegram'a gönderir (async)."""
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=mesaj)
        print("Telegram'a bildirim gönderildi.")
    except Exception as e:
        print(f"Telegram'a mesaj gönderilirken hata oluştu: {e}", file=sys.stderr)


async def yeni_kurslari_kontrol_et():
    """Yeni kurs olup olmadığını kontrol eder ve yalnızca yeni kurs varsa Telegram'a bildirir."""
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
    """Bir sonraki saat başına kadar bekler."""
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
            print(f"Hata oluştu: {e}", file=sys.stderr)
        # Bir sonraki saat başını bekle
        bekle_saat_basi()

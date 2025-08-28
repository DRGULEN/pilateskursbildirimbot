import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

REFERANS_TARIH = datetime.strptime("08.09.2025", "%d.%m.%Y")
URL = "https://www.tcf.gov.tr/branslar/pilates/#kurs"


def kurslari_getir():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(URL, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"Hata: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("table:nth-of-type(2) tr")[1:]
    kurslar = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            baslik = cols[0].get_text(strip=True)
            yer = cols[1].get_text(strip=True)
            tarih = cols[2].get_text(strip=True)
            try:
                bas_tarih = datetime.strptime(tarih.split(" - ")[0], "%d.%m.%Y")
            except:
                continue
            kurslar.append({"baslik": baslik, "yer": yer, "tarih": tarih, "bas_tarih": bas_tarih})
    return kurslar


async def telegram_mesaj_gonder(mesaj):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=mesaj)
    print("Telegram'a mesaj gönderildi.")


async def yeni_kurslari_kontrol_et():
    kurslar = kurslari_getir()
    if not kurslar:
        await telegram_mesaj_gonder("Kurs bilgileri alınamadı ❌")
        return

    yeni = [k for k in kurslar if k["bas_tarih"] > REFERANS_TARIH]
    if yeni:
        mesaj = "🚨 Yeni kurslar bulundu:\n\n"
        for k in yeni:
            mesaj += f"- {k['baslik']} / {k['yer']} / {k['tarih']}\n"
        await telegram_mesaj_gonder(mesaj)
    else:
        await telegram_mesaj_gonder("Yeni kurs bulunamadı ✅")


if __name__ == "__main__":
    async def main():
        while True:
            try:
                await yeni_kurslari_kontrol_et()
            except Exception as e:
                print(f"Hata oluştu: {e}", file=sys.stderr)
            await asyncio.sleep(1800)  # 30 dk bekle

    asyncio.run(main())

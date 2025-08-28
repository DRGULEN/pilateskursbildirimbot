import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import telegram
from dotenv import load_dotenv
import time

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
                      "Chrome/116.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(URL, headers=headers, timeot=10)

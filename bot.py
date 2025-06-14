import requests
import re
import time
import logging
import os

# Log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vavoo.tv API ayarları
URL = "https://vavoo.to/channels"
PROXY_BASE = "https://kerimmkirac-vavoo.hf.space/proxy/m3u?url=https://vavoo.to/play/{}/index.m3u8"
LOGO_URL = ""
OUTPUT_FILE = "vavooall.m3u"

# Karakter dönüşüm tablosu
TURKISH_CHAR_MAP = str.maketrans({
    'ç': 'c', 'Ç': 'C',
    'ğ': 'g', 'Ğ': 'G',
    'ı': 'i', 'İ': 'I',
    'ö': 'o', 'Ö': 'O',
    'ş': 's', 'Ş': 'S',
    'ü': 'u', 'Ü': 'U'
})

# Kanal ismi düzeltmeleri
NAME_CORRECTIONS = {
    "S NEMA": "SİNEMA",
    "T RK": "TÜRK",
    "M Z K": "MÜZİK",
    "A LE": "AİLE",
    "AKS YON": "AKSİYON",
    "KOMED": "KOMEDİ",
    "YERL": "YERLİ",
    "KURD": "KURDİ",
    "OCUK": "ÇOCUK",
    "CAY": "ÇAY",
    "D Ğ N": "DOĞAN",
    "VINC": "VINCI",
    "KOMEDİI": "KOMEDİ",
    "ÇÇOÇUK": "ÇOCUK",
    "M N KA": "MİNİKA",
    "CÇOÇUK": "ÇOCUK",
    "ÇÇOCUK": "ÇOCUK",
    "CÇOCUK": "ÇOCUK",
}

# Ülke ve dil eşleştirmeleri
COUNTRY_LANG_MAP = {
    "Albania": "Arnavutça",
    "Arabia": "Arapça",
    "Balkans": "Balkan Dilleri",
    "Bulgaria": "Bulgarca",
    "France": "Fransızca",
    "Germany": "Almanca",
    "Italy": "İtalyanca",
    "Netherlands": "Felemenkçe",
    "Poland": "Lehçe",
    "Portugal": "Portekizce",
    "Romania": "Romence",
    "Russia": "Rusça",
    "Spain": "İspanyolca",
    "Turkey": "Türkçe",
    "United Kingdom": "İngilizce"
}

# Ülke isimleri
COUNTRY_NAME_MAP = {
    "Albania": "Arnavutluk",
    "Arabia": "Arabistan",
    "Balkans": "Balkanlar",
    "Bulgaria": "Bulgaristan",
    "France": "Fransa",
    "Germany": "Almanya",
    "Italy": "İtalya",
    "Netherlands": "Hollanda",
    "Poland": "Polonya",
    "Portugal": "Portekiz",
    "Romania": "Romanya",
    "Russia": "Rusya",
    "Spain": "İspanya",
    "Turkey": "Türkiye",
    "United Kingdom": "İngiltere"
}

def normalize_tvg_id(name):
    """Kanal isimlerini normalize eder"""
    name_ascii = name.translate(TURKISH_CHAR_MAP)
    return re.sub(r'\W+', '_', name_ascii.strip()).upper()

def fix_channel_name(name):
    """Kanal isimlerindeki hataları düzeltir"""
    for wrong, correct in NAME_CORRECTIONS.items():
        name = re.sub(wrong, correct, name, flags=re.IGNORECASE)
    return name.strip()

def fetch_all_channels():
    """Tüm kanalları Vavoo API'den çeker"""
    try:
        logger.info("Kanal listesi çekiliyor...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()  # HTTP hataları için
        
        channels = response.json()
        logger.info(f"{len(channels)} kanal bulundu")
        
        # Kanal isimlerini düzelt
        for ch in channels:
            ch["name"] = fix_channel_name(ch.get("name", ""))
            ch["country"] = ch.get("country", "Unknown")
        
        # Ülke ve isme göre sırala
        def sort_key(ch):
            country = ch.get("country", "").lower()
            name = ch.get("name", "").lower()
            return (country, name)
        
        return sorted(channels, key=sort_key)
    
    except Exception as e:
        logger.error(f"Kanal listesi alınamadı: {str(e)}")
        return []

def generate_m3u(channels):
    """M3U dosyasını oluşturur"""
    if not channels:
        logger.warning("Kanal listesi boş, dosya oluşturulmadı")
        return False
    
    try:
        # Ülkelere göre kanal sayılarını hesapla
        country_counts = {}
        for ch in channels:
            country = ch.get("country", "Unknown")
            country_counts[country] = country_counts.get(country, 0) + 1
        
        # Dosyayı oluştur
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ch in channels:
                name = ch.get("name", "Unknown").strip()
                tvg_id = normalize_tvg_id(name)
                proxy_url = PROXY_BASE.format(ch.get("id"))
                country_en = ch.get("country", "Unknown")

                lang = COUNTRY_LANG_MAP.get(country_en, "Bilinmiyor")
                country_tr = COUNTRY_NAME_MAP.get(country_en, country_en)
                group_title = f"{country_tr} ({country_counts.get(country_en, 0)})"

                f.write(
                    f'#EXTINF:-1 tvg-name="{name}" tvg-language="{lang}" '
                    f'tvg-country="{country_tr}" tvg-id="{tvg_id}" tvg-logo="{LOGO_URL}" '
                    f'group-title="{group_title}",{name}\n{proxy_url}\n'
                )
        
        logger.info(f"{len(channels)} kanal başarıyla kaydedildi → '{OUTPUT_FILE}'")
        return True
    except Exception as e:
        logger.error(f"Dosya yazma hatası: {str(e)}")
        return False

def main_task():
    """Ana görevi yürütür"""
    logger.info("\n" + "="*50)
    logger.info(f"Güncelleme başlatıldı: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)
    
    channels = fetch_all_channels()
    result = generate_m3u(channels)
    
    logger.info("="*50)
    return result

if __name__ == "__main__":
    # GitHub Actions için tek seferlik çalıştırma
    logger.info("GitHub Actions için başlatılıyor...")
    start_time = time.time()
    
    main_task()
    
    duration = time.time() - start_time
    logger.info(f"Playlist başarıyla oluşturuldu! Süre: {duration:.2f} saniye")

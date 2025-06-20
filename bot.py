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
PROXY_BASE = "https://myiptv2-vpn.hf.space/proxy/m3u?url=https://vavoo.to/play/{}/index.m3u8"
LOGO_URL = ""
OUTPUT_FILE = "vavooall.m3u"
TARGET_COUNTRY = "Turkey"  # Sadece Türkiye kanallarını işle

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

def fetch_turkish_channels():
    """Sadece Türkiye kanallarını Vavoo API'den çeker"""
    try:
        logger.info("Türkiye kanal listesi çekiliyor...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()  # HTTP hataları için
        
        all_channels = response.json()
        
        # Sadece Türkiye kanallarını filtrele
        turkish_channels = [
            ch for ch in all_channels 
            if ch.get("country", "").lower() == TARGET_COUNTRY.lower()
        ]
        
        logger.info(f"Toplam {len(all_channels)} kanaldan {len(turkish_channels)} Türkiye kanalı bulundu")
        
        # Kanal isimlerini düzelt ve tvg-id oluştur
        for ch in turkish_channels:
            ch["name"] = fix_channel_name(ch.get("name", ""))
            ch["tvg_id"] = normalize_tvg_id(ch["name"])
            ch["country"] = ch.get("country", "Unknown")
        
        # İsime göre sırala
        return sorted(turkish_channels, key=lambda x: x.get("name", "").lower())
    
    except Exception as e:
        logger.error(f"Kanal listesi alınamadı: {str(e)}")
        return []

def generate_m3u(channels):
    """M3U dosyasını sadece Türkiye kanallarıyla oluşturur"""
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
                tvg_id = ch["tvg_id"]
                proxy_url = PROXY_BASE.format(ch.get("id"))
                country_en = ch.get("country", "Unknown")

                lang = COUNTRY_LANG_MAP.get(country_en, "Bilinmiyor")
                country_tr = COUNTRY_NAME_MAP.get(country_en, country_en)
                group_title = f"{country_tr} ({country_counts.get(country_en, 0)})"

                f.write(
                    f'#EXTINF:-1 tvg-name="{name}" tvg-language="{lang}" '
                    f'tvg-country="{country_tr}" tvg-id="{tvg_id}" tvg-logo="{LOGO_URL}" '
                    f'group-title="{group_title}",{name}\n'
                )
                f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
                f.write(f"{proxy_url}\n")
        
        logger.info(f"{len(channels)} Türkiye kanalı başarıyla kaydedildi → '{OUTPUT_FILE}'")
        return True
    except Exception as e:
        logger.error(f"Dosya yazma hatası: {str(e)}")
        return False

def update_m3u_urls(channels):
    """Mevcut M3U dosyasını güncelleyerek sadece tvg-id eşleşen Türkiye kanallarının URL'lerini günceller"""
    # Türkiye kanallarını tvg-id'ye göre eşle
    turkish_channel_map = {ch["tvg_id"]: ch for ch in channels}
    logger.info(f"Vavoo'dan {len(turkish_channel_map)} Türkiye kanalı alındı")
    
    # Dosyayı satır satır oku ve güncelle
    updated_count = 0
    temp_file = OUTPUT_FILE + ".tmp"
    tvg_id_pattern = re.compile(r'tvg-id="(.*?)"')
    
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as infile, \
             open(temp_file, "w", encoding="utf-8") as outfile:
            
            current_tvg_id = None
            skip_next_line = False  # Bir sonraki satırı atlamak için bayrak
            
            for line in infile:
                stripped_line = line.strip()
                
                # EXTINF satırında tvg-id'yi ara
                if stripped_line.startswith("#EXTINF"):
                    match = tvg_id_pattern.search(stripped_line)
                    current_tvg_id = match.group(1) if match else None
                    outfile.write(line)
                    skip_next_line = False
                    continue
                
                # #EXTVLCOPT satırını kontrol et
                if stripped_line.startswith("#EXTVLCOPT"):
                    outfile.write(line)
                    skip_next_line = False
                    continue
                
                # URL satırını işle (hem http hem https başlangıçları için kontrol)
                if (stripped_line.startswith("http://") or stripped_line.startswith("https://")) and current_tvg_id:
                    # Eğer bu tvg-id Türkiye kanallarında varsa URL'yi güncelle
                    if current_tvg_id in turkish_channel_map:
                        channel_id = turkish_channel_map[current_tvg_id]["id"]
                        new_url = PROXY_BASE.format(channel_id)
                        outfile.write(new_url + "\n")
                        updated_count += 1
                    else:
                        outfile.write(line)
                    current_tvg_id = None
                else:
                    outfile.write(line)
        
        # Geçici dosyayı asıl dosyaya taşı
        os.replace(temp_file, OUTPUT_FILE)
        logger.info(f"{updated_count} Türkiye kanalının URL'si başarıyla güncellendi")
        return True
        
    except Exception as e:
        logger.error(f"Dosya güncelleme hatası: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False

def main_task():
    """Ana görevi yürütür"""
    logger.info("\n" + "="*50)
    logger.info(f"Güncelleme başlatıldı: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*50)
    
    channels = fetch_turkish_channels()
    
    if not channels:
        logger.error("Türkiye kanal listesi alınamadı. İşlem iptal edildi.")
        return False
        
    # Dosya yoksa yeni oluştur, varsa güncelle
    if not os.path.exists(OUTPUT_FILE):
        logger.warning(f"{OUTPUT_FILE} dosyası bulunamadı, yeni dosya oluşturuluyor...")
        result = generate_m3u(channels)
    else:
        logger.info(f"{OUTPUT_FILE} dosyası bulundu, Türkiye kanallarının URL'leri güncelleniyor...")
        result = update_m3u_urls(channels)
    
    logger.info("="*50)
    return result

if __name__ == "__main__":
    # GitHub Actions için tek seferlik çalıştırma
    logger.info("GitHub Actions için başlatılıyor...")
    start_time = time.time()
    
    main_task()
    
    duration = time.time() - start_time
    logger.info(f"İşlem tamamlandı! Süre: {duration:.2f} saniye")

# Description: Utility functions for Python projects.
# Version: 2.0

import os
import sys
import json
import time
import datetime
from pathlib import Path
from loguru import logger


class Utility:

    def __init__(self, log_file_name="utility.log"):
        self.configure_loguru(log_file_name)  # Logger'ı belirtilen dosya adıyla yapılandır
        self.directory = Utility.get_working_directory()
        self.config_path = self.directory / "config.json"
        self.config = Utility.load_config(self.config_path)
        logger.debug(f"Çalışma dizini: {self.directory}")
        logger.debug(f"Yapılandırma: {self.config}")

    @staticmethod
    def get_working_directory() -> Path:
        """Uygulamanın çalıştığı yolu Path objesi olarak döndürür."""
        logger.debug("Çalışma dizini belirleniyor.")
        if getattr(sys, 'frozen', False):
            path = Path(sys.executable).parent
            logger.debug(f"Uygulama .exe olarak çalıştırılıyor. Çalışma dizini: {path}")
        else:
            try:
                path = Path(__file__).parent.resolve()
                logger.debug(f"Uygulama Python betiği olarak çalıştırılıyor. Çalışma dizini: {path}")
            except NameError:
                path = Path.cwd()
                logger.debug(f"Uygulama interaktif ortamda çalışıyor. Çalışma dizini: {path}")
        return path

    @staticmethod
    def configure_logging_old(file_name, log_level="INFO"):
        """ Loglama yapılandırmasını başlatır.
        Dökümantasyon:
        https://docs.python.org/3/library/logger.html#logger.Formatter.formatTime
        """
        import logging as logger
        # log_format = "%(asctime)s [%(levelname)s] [%(filename)s.%(funcName)s] - %(message)s"
        # 2024-07-25 18:53:33,758 [INFO] [api_manager.py.login] - Kullanıcı giriş yaptı.
        log_format = "%(asctime)s [%(levelname)s] [%(filename)s.%(funcName)-30s] - %(message)s"

        file_path = Utility.get_working_directory() / file_name
        logger.basicConfig(filename=file_path, level=log_level, format=log_format, force=True)


    @staticmethod
    def configure_loguru(file_name):
        """ Loglama yapılandırmasını başlatır."""
        file_path = Utility.get_working_directory() / file_name
        
        # Tüm mevcut handler'ları kaldır
        logger.remove()
        # Terminalde logları göstermek için
        logger.add(sys.stderr, level="WARNING")
        # Aynı zamanda logları bir dosyaya yazmak için
        logger.add(file_path, backtrace=True, rotation="10 MB", compression="zip", level="INFO")


    @staticmethod
    def load_config(config_path):
        """Yapılandırma dosyasını yükler."""
        default_config = {
                "USERNAME": None,
                "PASSWORD": None,
                "TELEGRAM_ID": None,
                "TELEGRAM_TOKEN": None,
                "STATION_ID": "61a23dd5572db",
                "ENTRY_TIME": "11:00",
                "EXIT_TIME": "23:00",
                "SEATS": [34, 32, 37, 38, 32, 1]
            }
        logger.info(f"Yapılandırma dosyası yükleniyor: {config_path}")

        try:
            with open(config_path, "r") as file:
                config_data = json.load(file)
                logger.info("Yapılandırma dosyası başarıyla yüklendi.")
                return config_data
        except FileNotFoundError:
            logger.error(f"Yapılandırma dosyası bulunamadı: {config_path}. Varsayılan yapılandırma yükleniyor.")
        except json.JSONDecodeError:
            logger.error("Yapılandırma dosyasında JSON format hatası. Varsayılan yapılandırma yükleniyor.")

        return default_config


    @staticmethod
    def clear_screen():
        """Terminal ekranını temizler"""
        print("\033c", end="")

    @staticmethod
    def _now(gmt=3):
        """Şu anki UTC+X zamanı döndürür."""
        delta = datetime.timedelta(hours=gmt) # 3:00:00
        utc3 = datetime.timezone(delta) # UTC+03:00
        return datetime.datetime.now(utc3) # 2024-08-08 20:40:57.115676+03:00

    @staticmethod
    def get_upcoming_dates(days=7) -> list:
        """Gelecek gün listesi oluşturur."""
        return [(Utility._now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in reversed(range(days))]

    @staticmethod
    def format_seconds_to_hms2(seconds: int) -> str:
        """Formats seconds into HH:MM:SS format."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_seconds_to_hms(seconds) -> str:
        """Formats seconds into HH:MM:SS format."""
        return str(datetime.timedelta(seconds=int(seconds)))

    @staticmethod
    def wait_until_target_time_colab(target_time):
        """Belirtilen zamana kadar bekler ve sürekli olarak kalan süreyi günceller."""
        from IPython.display import clear_output

        while True:
            now = Utility._now()
            if now.hour == target_time.hour and now.minute == target_time.minute:
                logger.info(f"Hedef saate {now.strftime('%H:%M:%S')} ulaşıldı.")
                break

            time_remaining = (target_time - now).total_seconds()
            formatted_time = Utility.format_seconds_to_hms(time_remaining)
            clear_output(wait=True)
            print(f"Kalan süre: {formatted_time}")
            time.sleep(1)

    @staticmethod
    def wait_until_target_time(target_time):
        """Belirtilen saat ve dakikaya kadar bekler"""
        logger.info("Zaman kontrolü başlatıldı.")

        while True:
            now = Utility._now()

            if now.hour == target_time.hour and now.minute == target_time.minute:
                logger.info(f"Hedef saate {now.strftime('%H:%M:%S')} ulaşıldı.")
                break

            if now.second % 30 == 0:
                time_remaining = (target_time - now).total_seconds() + 1
                # 1 saniye ekledim çünkü 59'dan 0'a geçerken 1 saniye kayboluyor.
                formatted_time = Utility.format_seconds_to_hms(time_remaining)
                print(f"Kalan süre: {formatted_time}", end="\r", flush=True)

            time.sleep(1)

    @staticmethod
    def schedule(run_at_midnight=True, hour=0, minute=0):
        """Programın gece yarısı veya belirli bir saatte çalışmasını sağlar."""
        now = Utility._now()
        # target_time = now.replace(hour=0 if run_at_midnight else hour, minute=0 if run_at_midnight else minute, second=0, microsecond=0)

        if run_at_midnight:
            target_time = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time <= now:
                target_time += datetime.timedelta(days=1)

        target_time_hm = target_time.strftime('%Y-%m-%d %H:%M')
        print(f"Program {target_time_hm} zamanında çalıştırılacak.")
        logger.info(f"Program {target_time_hm} zamanında çalıştırılacak.")
        Utility.wait_until_target_time(target_time)



    @staticmethod
    def configure_schedule(choice):
        """Kullanıcı seçimine göre zamanlama yapılandırması."""
        if choice == "1":
            logger.info("Program hemen çalıştırılıyor.")
        elif choice == "2":
            logger.info("Çalışma zamanı 00:00 olarak ayarlandı.")
            Utility.schedule(True)
        elif choice == "3":
            hour = Utility.get_valid_input("Saat girin (0-23): ", range(24))
            minute = Utility.get_valid_input("Dakika girin (0-59): ", range(60))
            logger.info(f"Çalışma zamanı {hour:02}:{minute:02} olarak ayarlandı.")
            Utility.schedule(False, hour, minute)
        else:
            logger.error("Geçersiz seçim yapıldı.")


    @staticmethod
    def display_menu() -> str:
        menu_options = {
            "0": "Çıkış",
            "1": "Şimdi çalıştır",
            "2": "Gece yarısı çalıştır",
            "3": "Belirli bir saatte çalıştır",
        }

        while True:
            for key, value in menu_options.items():
                print(f"{key}. {value}")
            choice = input("Seçiminiz: ").strip()
            if choice in menu_options:
                return choice
            Utility.clear_screen()
            print("Geçersiz seçim yaptınız! Tekrar deneyin.")


    @staticmethod
    def load_credentials():
        """Çevre değişkenlerini yükler, zorunlu olanları kontrol eder ve isteğe bağlı olanlar için uyarı verir."""
        # Çevre değişkenlerini güvenli bir şekilde yükle
        credentials = {
            "USERNAME": os.getenv("USERNAME"),
            "PASSWORD": os.getenv("PASSWORD"),
            "TELEGRAM_ID": os.getenv("TELEGRAM_ID"),
            "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
        }

        # Zorunlu çevre değişkenlerini kontrol et
        if not credentials["USERNAME"] or not credentials["PASSWORD"]:
            logger.error("Zorunlu çevre değişkenleri eksik: USERNAME veya PASSWORD")
            raise EnvironmentError("Missing critical environment variables: USERNAME or PASSWORD")

        # İsteğe bağlı çevre değişkenlerini kontrol et
        if not credentials["TELEGRAM_ID"] or not credentials["TELEGRAM_TOKEN"]:
            logger.warning("Telegram bildirimleri için gerekli çevre değişkenleri eksik: TELEGRAM_ID veya TELEGRAM_TOKEN")

        return credentials


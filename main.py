import os
from loguru import logger
from utility import Utility
from reservation import ReservationManager


def schedule_immediate():
    logger.info("Program hemen çalıştırılıyor.")


def schedule_midnight():
    logger.info("Çalışma zamanı 00:00 olarak ayarlandı.")
    Utility.schedule(True)


def schedule_custom_time():
    hour = Utility.get_valid_input("Saat girin (0-23): ", range(24))
    minute = Utility.get_valid_input("Dakika girin (0-59): ", range(60))
    logger.info(f"Çalışma zamanı {hour:02}:{minute:02} olarak ayarlandı.")
    Utility.schedule(False, hour, minute)


def configure_schedule(choice):
    schedule_actions = {
        "1": schedule_immediate,
        "2": schedule_midnight,
        "3": schedule_custom_time,
    }
    schedule_actions[choice]()


def get_user_choice() -> str:
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




def main(midnight=True):
    utils = Utility()
    utils.configure_loguru(file_name="biruni.log")
    logger.info("------------ PROGRAM BAŞLADI ------------")


    # Çevre değişkenlerini güvenli bir şekilde yükle
    username = os.getenv("USERNAME", None)
    password = os.getenv("PASSWORD", None)
    telegram_id = os.getenv("TELEGRAM_ID", None)
    telegram_token = os.getenv("TELEGRAM_TOKEN", None)

    # Çevre değişkenlerinin doğru yüklenip yüklenmediğini kontrol et
    if not all([username, password, telegram_id, telegram_token]):
        logger.error("Çevre değişkenleri eksik veya yanlış tanımlanmış!")
        return

    utils.config.update({
        "USERNAME": username,
        "PASSWORD": password,
        "TELEGRAM_ID": telegram_id,
        "TELEGRAM_TOKEN": telegram_token
    })

    try:
        choice = "2" if midnight else get_user_choice()
        if choice == "0":
            logger.info("Kullanıcı 0 seçti, programdan çıkılıyor.")
            return

        configure_schedule(choice)
        reservation_manager = ReservationManager(utils.config)
        reservation_manager.manage_reservations()

    except KeyboardInterrupt:
        logger.info("Program kullanıcı tarafından sonlandırıldı.")
    except FileNotFoundError as e:
        logger.error(f"Dosya bulunamadı: {e}")
    except Exception as e:
        logger.error(f"Ana programda hata oluştu: {e}")
    finally:
        logger.info("------------ PROGRAM SONLANDI ------------")


if __name__ == "__main__":
    logger.remove()  # Tüm mevcut handler'ları kaldır
    main(midnight=True)

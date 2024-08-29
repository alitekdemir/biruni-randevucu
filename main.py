from loguru import logger
from utility import Utility
from reservation import ReservationManager


def main(run_midnight=True):
    utils = Utility()
    utils.configure_loguru(file_name="biruni.log")
    logger.info("------------ PROGRAM BAŞLADI ------------")

    # USERNAME veya PASSWORD bilgileri False (boş, None, vb.) ise çevre değişkenlerini kullan
    if not all([utils.config.get("USERNAME"), utils.config.get("PASSWORD")]):
        logger.warning("Yapılandırma dosyası kullanılmayacak, çevre değişkenleri tercih edilecek.")

        credentials = utils.load_credentials()
        if credentials is None:
            return
        utils.config.update(credentials)

    try:
        choice = "2" if run_midnight else utils.display_menu()
        if choice == "0":
            logger.info("Kullanıcı 0 seçti, programdan çıkılıyor.")
            return

        utils.configure_schedule(choice)
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
    main(run_midnight=True)

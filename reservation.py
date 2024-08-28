from loguru import logger
import requests
from utility import Utility



class APIHelper:
    @staticmethod
    def make_request(url, method="get", **kwargs):
        """API isteği yapar ve yanıtı döndürür. Hataları loglar ve yönetir."""
        logger.info(f"Request: {method.upper()}") # at {url}
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Tüm requests ile ilgili hataları yakala ve işle
            logger.error(f"Network error during API request: {e}")
            raise RuntimeError(f"Network error: {e}") from e
        except Exception as e:
            # Diğer beklenmeyen hatalar için genel bir log
            logger.error(f"Unexpected error during API request: {e}")
            raise RuntimeError(f"Unexpected error: {e}") from e


class TelegramBot:
    """
    Telegram'a mesaj veya doküman gönderir.

    More info: https://core.telegram.org/bots/api#sendmessage
    More info: https://core.telegram.org/bots/api#sendDocument
    """

    def __init__(self, token, chat_id):
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.chat_id = chat_id

    def send_message(self, message):
        """Telegram'a mesaj gönderir."""
        url = f"{self.base_url}sendMessage"
        params = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'Markdown'}
        try:
            response = APIHelper.make_request(url, 'get', params=params)
            if response.get('ok', False):
                logger.info(f"Telegram'a mesaj gönderildi.")
                return response
            else:
                raise RuntimeError(f"Telegram'a mesaj gönderilemedi: {response}")
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP error occurred: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error occurred: {e}")


    def send_document(self, document_path):
        """Telegram'a doküman gönder"""
        url = f"{self.base_url}sendDocument"
        data = {'chat_id': self.chat_id}
        with open(document_path, 'rb') as file:
            try:
                response = APIHelper.make_request(url, 'post', data=data, files={'document': file})
                if response.get('ok', False):
                    logger.info(f"Telegram'a dosya başarıyla gönderildi.")
                    return response
                else:
                    raise RuntimeError(f"Telegram'a dosya gönderilemedi: {response}")
            except requests.RequestException as e:
                raise RuntimeError(f"HTTP error occurred: {e}") from e
            except Exception as e:
                raise RuntimeError(f"Unexpected error occurred: {e}") from e


class ReservationManager:

    def __init__(self, config):
        self.config = config
        self.headers = None
        self.telegram_bot = TelegramBot(token=config["TELEGRAM_TOKEN"],
                                        chat_id=config["TELEGRAM_ID"])

    def _get_api_url2(self, endpoint_name):
        """API endpoint URL'sini döndürür."""
        base_url = "https://api.istasyon.gungoren.bel.tr/v1/app"
        endpoints = {
            "login": "/authorize",
            "reservations": "/registration",
            "profile": "/profile",
            "cancel": "/registration",
        }
        return f"{base_url}{endpoints.get(endpoint_name)}"

    def _get_api_url(self, endpoint_name):
        """API endpoint URL'sini döndürür."""
        BASE_URL = "https://api.istasyon.gungoren.bel.tr/v1/app"
        ENDPOINTS = {
            "login": BASE_URL + "/authorize",
            "reservations": BASE_URL + "/registration",
            "profile": BASE_URL + "/profile",
            "cancel": BASE_URL + "/registration",
            }
        return ENDPOINTS.get(endpoint_name)


    def login(self) -> None:
        """API üzerinden kullanıcı girişi yapar ve token header döndürür."""
        url = self._get_api_url("login")
        data = {"username": self.config["USERNAME"], "password": self.config["PASSWORD"], "grant_type": "basic"}
        try:
            response = APIHelper.make_request(url, 'post', json={"data": data})
            token = response.get("data", {}).get("token")
            if not token:
                logger.error("Giriş başarısız, token alınamadı.")
                raise ValueError("Giriş başarısız, token alınamadı.")
            self.headers = {'Authorization': f'Bearer {token}'}
            logger.info("Logged in successfully.")
        except ValueError as e:
            logger.error(f"Login error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise RuntimeError(f"Login failed: {e}") from e


    def get_user_profile(self):
        """Profil bilgilerini ve molaları getirir."""
        url = self._get_api_url("profile")
        params = {'include': 'remaining_breaks,break_status'}
        try:
            response = APIHelper.make_request(url, 'get', headers=self.headers, params=params)
            return response.get('data', {})
        except requests.RequestException as e:
            logger.error(f"Profil bilgileri alınamadı: {e}")
            raise RuntimeError(f"Profil bilgileri alınamadı: {e}") from e


    def cancel_reservation(self, reservation_id):
        """Belirtilen rezervasyon ID'sine sahip rezervasyonu iptal eder."""
        logger.info(f"Rezervasyon {reservation_id} iptal ediliyor...")
        url = f"{self._get_api_url('cancel')}/{reservation_id}"
        APIHelper.make_request(url, 'delete', headers=self.headers)
        logger.info(f"Rezervasyon {reservation_id} başarıyla iptal edildi.")

    def cancel_all_reservations(self):
        """Tüm rezervasyonları iptal eder."""
        reservations = self.get_active_reservations()
        for reservation in reservations:
            self.cancel_reservation(reservation['id'])
        logger.info("Tüm rezervasyonlar başarıyla iptal edildi.")


    def get_active_reservations(self):
        """Aktif rezervasyonları alın."""
        logger.info("Aktif rezervasyonlar alınıyor...")
        url = self._get_api_url("reservations")
        params = {
            'type': '[Activeregistration] Load Activeregistrations',
            'filter[status][eq][0]': '1',
            'filter[status][eq][1]': '3',
            'filter[status][eq][2]': '7',
            'sort': 'date',
            'include': 'station'
        }
        response = APIHelper.make_request(url, headers=self.headers, params=params)
        return self.parse_active_reservations_data(response)

    def parse_active_reservations_data(self, response):
        """API yanıtından rezervasyon verilerini çıkarır."""
        return [
            {
                'id': item['id'],
                'date': attributes["date"][:10],
                'entry': attributes["entry_time"][11:16],
                'exit': attributes["exit_time"][11:16],
                'seat': attributes["seat"]
            }
            for item in response.get('data', [])
            if (attributes := item['attributes'])
        ]


    def print_active_reservations_table(self, reservations, log_func=print):
        """Rezervasyonları tablo formatında loglar."""
        if not reservations:
            log_func("❌ Aktif rezervasyon bulunmuyor.")
            return

        log_func("📅 Aktif Rezervasyonlar:")
        log_func(f"{'🔖 ID':<37} {'📆 Tarih':<11} {'Giriş':<6} {'Çıkış':<6} {'🪑':<3}")
        log_func("-" * 70)
        for r in reservations:
            log_func(f"{r['id']:<38} {r['date']:<12} {r['entry'][:5]:<6} {r['exit'][:5]:<6} {r['seat']:<4}")


    def wrap_active_reservations_table(self, reservations: list) -> str:
        """Listeleri satır satır birleştirir.""" # 🕘🕐⌛⏳📆🗓⧖⧗#💺🪑
        message_lines = ["Aktif Rezervasyonlar:"]
        for r in reservations:
            message_lines.append(f"{r['date']} ⏳{r['entry'][:5]}-{r['exit'][:5]} →{r['seat']}🪑")
        message_lines.append(Utility._now().strftime("%Y-%m-%d %H:%M:%S"))
        return "\n".join(message_lines)


    def log_reservation(self, reservation):
        """Log the details of a successful reservation."""
        if reservation:
            date = reservation['date'][:10]
            entry = reservation['entry_time'][11:16]
            exit = reservation['exit_time'][11:16]
            seat = reservation['seat']
            logger.info(f"Rezervasyon başarılı. {date}, {entry}-{exit}, Koltuk:{seat}")
        else:
            logger.warning("Loglanacak rezervasyon detayı yok.")


    def create_reservation(self, date, seat):
        """Belirli bir koltuk için rezervasyon yapar."""
        message = f"Rezervasyon kaydı deneniyor: Tarih:{date}, Koltuk:{seat}"
        print(message)
        logger.info(message)

        url = self._get_api_url("reservations")
        payload = {
            "data": {
                "attributes": {
                    "date": date,
                    "seat": seat,
                    "station_id": self.config['STATION_ID'],
                    "entry_time": self.config['ENTRY_TIME'],
                    "exit_time": self.config['EXIT_TIME']
                }
            }
        }
        try:
            response = APIHelper.make_request(url, 'post', headers=self.headers, json=payload)
            if response.get('data'):
                self.log_reservation(response['data']['attributes'])
                return True
            raise RuntimeError("No data returned in response")
        except requests.RequestException as e:
            logger.error(f"Rezervasyon oluşturulamadı: {e}")
            raise RuntimeError(f"Rezervasyon oluşturulamadı: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while creating reservation: {e}")
            raise RuntimeError(f"Reservation creation failed: {e}") from e


    def create_reservation_for_seats(self, date):
        """Belirli bir tarih için koltuk rezervasyonu dener ve sonucu kaydeder."""
        logger.info(f"{date} tarihi için rezervasyon denemesi başlıyor...")
        token = self.config.get('TELEGRAM_TOKEN')
        chat_id = self.config.get('TELEGRAM_ID')
        for seat in self.config['SEATS']:
            try:
                # logger.info(f"{date} tarihi için {seat}. koltuk denetleniyor")
                if self.create_reservation(date, seat):
                    message = f"Rezervasyon başarılı: Tarih:{date}, Koltuk:{seat}"
                    logger.info(message)
                    print(message)
                    self.telegram_bot.send_message(chat_id, token, str(message))
                    return True  # Başarılı rezervasyon sonrası döngüyü durdur
                # logger.warning(f"{date} tarihi için {seat}. koltuk uygun değil.")
            except Exception as e:
                logger.warning(f"{date} tarihi için {seat}. koltuk rezervasyonu başarısız: {e}")
        logger.warning(f"{date} tarihinde uygun koltuk bulunamadı.")
        return False


    def create_reservations_for_dates(self, reserved):
        """Gelecek günler için rezervasyon işlemleri yapar."""
        print("Rezervasyon işlemi başlatılıyor...")
        reserved_dates = set(r['date'] for r in reserved)
        upcoming_dates = set(Utility.get_upcoming_dates()) - reserved_dates

        if not upcoming_dates:
            logger.info("Tüm tarihler için rezervasyonlar zaten dolu.")
            return False

        logger.info(f"Rezervasyon yapılacak tarihler: {upcoming_dates}")
        for date in upcoming_dates:
            if not self.create_reservation_for_seats(date):
                logger.warning(f"{date} tarihinde rezervasyon oluşturulamadı.")
        return True


    def manage_reservations(self):
        logger.info("Rezervasyon yönetimi başlatılıyor...")
        self.login()
        reserved = self.get_active_reservations()
        status = self.create_reservations_for_dates(reserved)

        # Eğer rezervasyonlar oluşturulduysa, tekrar kontrol et
        reserved_after = self.get_active_reservations() if status else reserved

        print("Bitiş", Utility._now().strftime("%Y-%m-%d %H:%M:%S"))
        self.print_active_reservations_table(reserved_after, print)
        message = self.wrap_active_reservations_table(reserved_after)
        self.telegram_bot.send_message(message)
        return status

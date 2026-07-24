Opis

Układ automatycznie ustawia panel solarny w kierunku najjaśniejszego źródła światła:

oś pionowa - sterowana serwomechanizmem
oś pozioma - sterowana silnikiem DC przez sterownik L298N

Odczyty z czujników są co 10 sekund wysyłane przez WiFi na serwer i zapisywane w bazie danych MySQL, co umożliwia monitorowanie pracy trackera przez przeglądarkę.


Hardware
Komponent	Opis
ESP32	Mikrokontroler z WiFi
4x LDR	Fotorezystory w układzie kwadratowym
Serwomechanizm	Oś pionowa (góra/dół), pin 18
Silnik DC + L298N	Oś pozioma (lewo/prawo), piny 25/26/27

Piny ESP32
Pin	Funkcja
18	Serwo (PWM)
25	L298N ENA (PWM silnika)
26	L298N IN1
27	L298N IN2
32	LDR góra-lewo
33	LDR góra-prawo
34	LDR dół-lewo
35	LDR dół-prawo

Wymagane biblioteki (Arduino IDE):

ESP32Servo
WiFi 
HTTPClient 
ArduinoJson

Przed wgraniem uzupełnij dane WiFi:

cpp
const char* ssid     = "NazwaTwojejSieci";
const char* password = "HasloDoWiFi";
Serwer (flask_app.py)

Backend w Pythonie hostowany na PythonAnywhere.

Wymagane pakiety:

flask
flask-sqlalchemy
flask-marshmallow
marshmallow-sqlalchemy
pymysql

Instalacja:

bash
pip install flask flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy pymysql

Utworzenie tabel w bazie:

bash
cd /home/<user>/mysite
python3 -c "from flask_app import app, db; app.app_context().push(); db.create_all(); print('OK')"
API – endpointy
Metoda	URL	Opis
GET	/	Status serwera
POST	/user	Dodaj użytkownika
GET	/users	Lista użytkowników
POST	/device	Dodaj urządzenie
GET	/devices	Lista urządzeń
GET	/device/<id>	Dane urządzenia
PATCH	/device/<id>	Aktualizuj urządzenie
POST	/device/<id>/mes1	ESP wysyła pomiary
GET	/device/<id>/mes1	Ostatnie 100 pomiarów
GET	/device/<id>/mes1/last	Ostatni pomiar

Przykładowy JSON wysyłany przez ESP
json
{
  "foto1": 1234,
  "foto2": 2345,
  "foto3": 1500,
  "foto4": 1800,
  "serwo1": 95,
  "serwo2": 0
}
Pole	Opis
foto1-4	Odczyty LDR (0–4095, 12-bit ADC)
serwo1	Aktualny kąt serwa (0–180°)
serwo2	Stan silnika (1 = obraca się, 0 = stop)

Wyłącza się gdy spadnie poniżej 80

Oś pionowa i pozioma są sterowane niezależnie.

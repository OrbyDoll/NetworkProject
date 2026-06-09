# Traceroute as a Service

Полноценный веб-сервис для выполнения `traceroute` из браузера.
Разработан с использованием Python (FastAPI), SQLite, HTML/CSS/JS (Leaflet.js) и упакован в Docker.

## Особенности
- Выполнение traceroute из веб-интерфейса
- Валидация IP и доменов, защита от command injection
- DNS resolving
- Геолокация (определение города и страны с помощью GeoLite2)
- Карта маршрута с использованием Leaflet.js
- Сохранение истории в SQLite
- Статистика по запросам

## Архитектура проекта
- `app/api/endpoints.py` - обработчики API (FastAPI)
- `app/services/traceroute.py` - вызов системного traceroute ("traceroute") и парсинг
- `app/services/geolocation.py` - работа с БД mmdb (GeoIP2)
- `app/models.py` - SQLAlchemy модели (SQLite)
- Frontend: `app/templates` и `app/static`

## Развёртывание на Linux VPS (Ubuntu / Debian)

1. Клонируйте репозиторий:
   ```bash
   git clone <repo_url> traceroute-web
   cd traceroute-web
   ```

2. Скачайте GeoLite2 City Database:
   Для работы геолокации создайте папку `data` и скачайте базу `GeoLite2-City.mmdb`.
   
   ```bash
   mkdir -p data
   # (Пример) Вы должны зарегистрироваться на MaxMind и скачать базу:
   # wget -O data/GeoLite2-City.mmdb "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_KEY&suffix=tar.gz"
   ```
   > **Примечание**: Без базы `GeoLite2-City.mmdb` приложение продолжит работу, но не будет показывать страны/города на карте.

3. Запустите проект в Docker:
   Убедитесь, что установлены `docker` и `docker-compose`.
   
   ```bash
   docker compose up -d --build
   ```

4. Откройте в браузере:
   `http://<IP-вашего-сервера>`

## Безопасность
- Использование регулярных выражений для проверки доменов и IP адресов, что делает невозможным внедрение shell-команд (command injection).
- Команда `traceroute` вызывается строго через список аргументов в `subprocess.Popen` (флаг `shell=True` отсутствует).
- Валидация ввода при помощи Pydantic (максимальная длина).
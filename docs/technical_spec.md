# Техническое задание (ТЗ)

## Задача
Реализовать на Python приложение «ИИ‑подсказчик предметов для Dota 2», которое использует:
1. Game State Integration (GSI) для получения данных о герое игрока.
2. Захват экрана и распознавание иконок героев/предметов для получения информации о врагах.

## Общие требования
- **Язык:** Python 3.10+
- **Структура проекта:**
  ```
  dota_assistant/
    main.py
    gsi_server.py
    screen_capture.py
    ocr_recognition.py
    recommender.py
    ui.py
    config/
      gsi_config_example.cfg
      regions.json
    assets/
      heroes/
      items/
  ```
- **Библиотеки:** Flask/FastAPI, mss/pyautogui, opencv-python, numpy, PyQt5/Tkinter (по выбору), logging.
- Целевая платформа — Windows.

## Модуль GSI (`gsi_server.py`)
- HTTP‑сервер на `http://localhost:4000` (порт можно вынести в настройки).
- Единственный POST endpoint `/gsi` принимает JSON от Dota 2.
- Извлекает имя героя игрока и его предметы, сохраняет актуальное состояние.
- Интерфейс доступа:
  ```python
  def get_my_state() -> dict:
      return {"hero": "juggernaut", "items": ["phase_boots", "battle_fury"]}
  ```
- Пример файла `config/gsi_config_example.cfg` для настройки GSI.

## Модуль захвата экрана (`screen_capture.py`)
- Функция `capture_region(region_name: str) -> np.ndarray` возвращает снимок заданной области (BGR для OpenCV).
- Координаты областей задаются в `config/regions.json`, например:
  ```json
  {
    "top_bar_enemies": {"left": 100, "top": 50, "width": 800, "height": 100},
    "scoreboard_items": {"left": 200, "top": 200, "width": 1000, "height": 400}
  }
  ```
- Реализация на `mss` или `pyautogui`.

## Модуль распознавания (`ocr_recognition.py`)
- Определяет врагов и их предметы по скриншотам.
- Упрощения: фиксированные слоты в верхней панели и на scoreboard; координаты заданы в конфигурации или константах.
- Интерфейсы:
  ```python
  def detect_enemy_heroes(image: np.ndarray) -> list[str]
  def detect_enemy_items(image: np.ndarray, enemy_heroes: list[str]) -> dict
  ```
- Реализация через template matching (`cv2.matchTemplate`) по иконкам из `assets/heroes/` и `assets/items/`.
- Допустимо поддерживать ограниченный набор героев и предметов (10–20).

## Модуль рекомендаций (`recommender.py`)
- Возвращает рекомендации и пояснения на основе героя игрока, его предметов, списка врагов и их предметов.
- Интерфейс:
  ```python
  def get_recommendations(my_hero: str, my_items: list[str], enemy_heroes: list[str], enemy_items: dict) -> dict:
      return {
          "recommended_items": ["black_king_bar", "manta_style", "silver_edge"],
          "explanations": [
              "Black King Bar — против сильного магического урона Lion и Shadow Fiend.",
              "Manta Style — помогает снять Hex и другие дизейблы.",
              "Silver Edge — хорошо работает против танков типа Axe."
          ]
      }
  ```
- Rule-based логика: теги героев (`HERO_TAGS`) и контр‑предметы (`TAG_COUNTER_ITEMS`), объединение тегов врагов и фильтрация предметов, которые уже есть у игрока.
- Пояснения формируются автоматически по шаблонам.

## UI‑модуль (`ui.py`)
- Отображает состояние: герой игрока и его предметы, враги и их предметы, блок рекомендаций.
- Реализация на PyQt5 или Tkinter; обновление каждые 1–2 секунды через таймер.

## Главный модуль (`main.py`)
- Запускает GSI‑сервер (в отдельном потоке), инициализирует UI.
- Периодически: получает `my_state`, делает захват экрана, распознаёт героев и предметы, строит рекомендации, обновляет UI.
- Логгирование: вывод распознанных героев, предметов и рекомендаций.

## Ограничения и допущения
- Не требуется идеальная точность распознавания; достаточно учебного качества.
- Поддержка ограниченного набора героев/предметов допустима.
- Взаимодействие только через GSI и снимки экрана; без вмешательства в память игры.

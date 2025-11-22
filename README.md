# dota2helper

Прототип «ИИ-подсказчика предметов для Dota 2» на Python.

- [Архитектура (GSI + OCR)](docs/architecture.md)
- [Техническое задание](docs/technical_spec.md)

## Соответствие чек-листу

* **GSI-сервер** — реализован на Flask, принимает POST `/gsi`, хранит героя и предметы в памяти (`gsi_server.py`).
* **Захват экрана** — делает снимки по именованным регионам из `config/regions.json` с помощью `mss` (`screen_capture.py`).
* **OCR/распознавание иконок** — template matching для врагов и их предметов, сетка слотов фиксированная (`ocr_recognition.py`, папки `assets/heroes`, `assets/items`).
* **Рекомендации** — rule-based логика по тегам героев и контр-предметам (`recommender.py`).
* **UI** — окно на Tkinter, выводит героя, предметы, врагов, рекомендации с автообновлением (`ui.py`).
* **Главный цикл** — поднимает GSI, оркестрирует захват, распознавание, рекомендации и UI (`main.py`).

## Пошаговый запуск (Windows)

1. **Установите Python 3.10+** и добавьте его в `PATH`.
2. **Склонируйте проект** или скачайте архив с кодом, затем откройте папку с `README.md` в терминале.
3. **Установите зависимости** (включая Tkinter, если он не входит в вашу сборку Python):
   ```bash
   pip install flask mss opencv-python numpy
   ```
4. **Скачайте полные ассеты героев и предметов** (поддержка всех 123 героев и 250+ предметов):
   * Поместите портреты героев (Hero Mini Icons) в `assets/heroes/` с именами из Valve API, например `antimage.png`, `crystal_maiden.png`, `winter_wyvern.png`.
   * Поместите иконки предметов в `assets/items/` с внутренними id из `items.json`, например `blink_dagger.png`, `black_king_bar.png`.
   * Формат файлов: `.png` (допускаются `.jpg/.jpeg`). Названия — строго в нижнем регистре, без пробелов.
5. **Обновите теги героев при необходимости**:
   * В `config/hero_tags.json` уже лежит полный список героев с тегами (сгенерирован по данным OpenDota). Если нужно обновить, запустите скрипт:
   ```bash
   python - <<"PY"
import json, urllib.request, pathlib
url='https://api.opendota.com/api/heroes'
with urllib.request.urlopen(url) as resp:
    data=json.load(resp)
hero_tags={}
for hero in data:
    name=hero['name'].replace('npc_dota_hero_','')
    tags=set(hero.get('roles', []))
    attr=hero.get('primary_attr')
    if attr:
        tags.add({'str':'strength','agi':'agility','int':'intelligence','all':'universal'}.get(attr, attr))
    hero_tags[name]=sorted(t.lower().replace(' ','_') for t in tags)
path=pathlib.Path('config/hero_tags.json')
path.write_text(json.dumps(hero_tags, ensure_ascii=False, indent=2), encoding='utf-8')
print('hero tags refreshed in', path)
PY
   ```
6. **Проверьте словарь контр-предметов**:
   * `config/tag_counter_items.json` содержит правила под разные теги (иллюзионисты, маг-урон, мобильные и т.д.). При желании расширьте список предметов.
7. **Настройте координаты захвата экрана**:
   * Откройте `config/regions.json` и подберите значения `left`, `top`, `width`, `height` под ваш монитор и расположение HUD (верхняя панель врагов и окно TAB).
8. **Включите GSI в Dota 2**:
   * Скопируйте `config/gsi_config_example.cfg` в каталог `Steam\\steamapps\\common\\dota 2 beta\\game\\dota\\cfg\\gamestate_integration`.
   * Перезапустите Dota 2, чтобы игра начала слать данные на `http://localhost:4000/gsi`.
9. **Запустите приложение** из папки проекта:
   ```bash
   python main.py
   ```
   Что произойдёт:
   * запустится GSI-сервер на `0.0.0.0:4000`;
   * загрузятся все шаблоны героев и предметов;
   * стартует фоновый поток с захватом экрана, OCR и рекомендациями каждые ~0.75 с;
   * откроется окно Tkinter с подсказками.
10. **В игре откройте таблицу счёта (TAB)**, чтобы на экране отображались портреты врагов и их слоты. Держите окно приложения поверх или на втором мониторе.
11. **Смотрите рекомендации** в окне: герой, ваши предметы, распознанные враги и их сборки, предложенные предметы с пояснениями.
12. **Логи**:
   * консоль + файл `logs/app.log` (ротация 5×1 МБ);
   * INFO по умолчанию, детальная диагностика по OCR/захвату — в уровне DEBUG.

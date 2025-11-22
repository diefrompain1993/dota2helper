# dota2helper

Прототип «ИИ-подсказчика предметов для Dota 2» на Python.

- [Архитектура (GSI + OCR)](docs/architecture.md)
- [Техническое задание](docs/technical_spec.md)

## Быстрый старт

1. Установите зависимости: `pip install flask mss opencv-python numpy`.
2. Скопируйте `config/gsi_config_example.cfg` в папку `Steam\steamapps\common\dota 2 beta\game\dota\cfg\gamestate_integration`.
3. Запустите приложение: `python main.py`.
4. В игре откройте таблицу счета (TAB), чтобы приложение смогло распознавать героев и предметы.

Структура модулей повторяет требования из ТЗ: GSI-сервер, захват экрана, распознавание иконок, правило-ориентированный рекомендационный движок и простое окно на Tkinter.

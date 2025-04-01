#!/bin/bash

# Скрипт для запуска бота TUKTUK

echo "=== Запуск бота TUKTUK ==="
echo

# Проверяем наличие файла конфигурации
if [ ! -f "config.py" ]; then
    echo "Ошибка: Файл config.py не найден."
    echo "Пожалуйста, скопируйте config.example.py в config.py и настройте его."
    exit 1
fi

# Создаем необходимые директории
mkdir -p storage
mkdir -p reports

# Проверяем, запущен ли уже бот
if pgrep -f "python main.py" > /dev/null; then
    echo "Бот уже запущен. Если вы хотите перезапустить бота, сначала остановите его."
    echo "Для остановки бота используйте: pkill -f 'python main.py'"
    exit 1
fi

# Проверяем, существует ли виртуальное окружение
if [ -d "venv" ]; then
    echo "Активируем виртуальное окружение..."
    source venv/bin/activate
fi

# Запускаем бота
echo "Запускаем бота..."
python main.py

# Обработка выхода
echo
echo "Бот остановлен."
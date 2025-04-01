#!/bin/bash

# Скрипт для установки необходимых зависимостей для бота TUKTUK

echo "=== Установка зависимостей для бота TUKTUK ==="
echo

# Проверяем, установлен ли pip
if ! command -v pip &> /dev/null; then
    echo "Ошибка: pip не найден. Установите Python и pip."
    exit 1
fi

# Устанавливаем зависимости
echo "Устанавливаем необходимые пакеты..."
pip install aiogram>=3.2.0 pandas openpyxl

# Проверяем успешность установки
if [ $? -eq 0 ]; then
    echo
    echo "=== Установка завершена успешно ==="
    echo "Теперь вы можете запустить бота с помощью команды:"
    echo "python main.py"
else
    echo
    echo "=== Ошибка при установке зависимостей ==="
    echo "Пожалуйста, попробуйте установить пакеты вручную:"
    echo "pip install aiogram>=3.2.0 pandas openpyxl"
fi
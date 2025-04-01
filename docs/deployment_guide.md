# Руководство по деплою бота TUKTUK

В этом руководстве описаны шаги по развертыванию Telegram-бота TUKTUK на различных платформах.

## Содержание

1. [Требования](#требования)
2. [Локальный запуск (разработка)](#локальный-запуск-разработка)
3. [Деплой на VPS/сервер](#деплой-на-vpsсервер)
4. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)
5. [Что делать в случае проблем](#что-делать-в-случае-проблем)

## Требования

Для работы бота требуется:

- Python 3.10 или выше
- Установленные зависимости: aiogram 3.2.0, pandas, openpyxl
- Токен Telegram бота (получается у @BotFather)
- ID администраторов бота в Telegram

## Локальный запуск (разработка)

### Настройка окружения в VS Code

1. Клонируйте репозиторий:
   ```
   git clone <URL-репозитория>
   cd tuktuk-bot
   ```

2. Создайте виртуальное окружение Python:
   ```
   python -m venv venv
   ```

3. Активируйте виртуальное окружение:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Установите зависимости:
   ```
   pip install aiogram>=3.2.0 pandas openpyxl
   ```

5. Настройте конфигурацию бота:
   - Скопируйте `config.example.py` в `config.py`
   - Отредактируйте `config.py`, указав токен бота и ID администраторов

6. Выполните настройку бота:
   ```
   python setup_new_bot.py
   ```

7. Запустите бота:
   ```
   python main.py
   ```

## Деплой на VPS/сервер

### Настройка на Ubuntu/Debian

1. Подключитесь к VPS по SSH и обновите систему:
   ```
   ssh user@your_server_ip
   sudo apt update && sudo apt upgrade -y
   ```

2. Установите необходимые пакеты:
   ```
   sudo apt install -y python3 python3-pip python3-venv git
   ```

3. Клонируйте репозиторий:
   ```
   git clone <URL-репозитория>
   cd tuktuk-bot
   ```

4. Создайте виртуальное окружение:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

5. Установите зависимости:
   ```
   pip install aiogram>=3.2.0 pandas openpyxl
   ```

6. Настройте конфигурацию бота:
   ```
   cp config.example.py config.py
   nano config.py  # Отредактируйте, указав токен и ID администраторов
   ```

7. Выполните настройку бота:
   ```
   python setup_new_bot.py
   ```

8. Создайте systemd-сервис для автоматического запуска:
   ```
   sudo nano /etc/systemd/system/tuktuk-bot.service
   ```

9. Добавьте следующее содержимое в файл сервиса (замените пути и пользователя):
   ```
   [Unit]
   Description=TUKTUK Telegram Bot
   After=network.target

   [Service]
   User=<ваш_пользователь>
   WorkingDirectory=/home/<ваш_пользователь>/tuktuk-bot
   ExecStart=/home/<ваш_пользователь>/tuktuk-bot/venv/bin/python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

10. Включите и запустите сервис:
    ```
    sudo systemctl enable tuktuk-bot
    sudo systemctl start tuktuk-bot
    ```

11. Проверьте статус сервиса:
    ```
    sudo systemctl status tuktuk-bot
    ```

## Мониторинг и обслуживание

### Просмотр логов

```
sudo journalctl -u tuktuk-bot -f
```

### Перезапуск бота

```
sudo systemctl restart tuktuk-bot
```

### Обновление бота

1. Остановите бота:
   ```
   sudo systemctl stop tuktuk-bot
   ```

2. Перейдите в директорию бота и обновите код:
   ```
   cd ~/tuktuk-bot
   git pull
   ```

3. Активируйте виртуальное окружение и обновите зависимости:
   ```
   source venv/bin/activate
   pip install -U aiogram pandas openpyxl
   ```

4. Запустите бота:
   ```
   sudo systemctl start tuktuk-bot
   ```

## Что делать в случае проблем

### Бот не отвечает

1. Проверьте статус сервиса:
   ```
   sudo systemctl status tuktuk-bot
   ```

2. Проверьте логи:
   ```
   sudo journalctl -u tuktuk-bot -n 100
   ```

3. Убедитесь, что токен бота правильный и бот не заблокирован.

### Сброс данных

Если нужно сбросить данные бота и начать с чистого листа:

1. Остановите бота:
   ```
   sudo systemctl stop tuktuk-bot
   ```

2. Запустите скрипт очистки данных:
   ```
   cd ~/tuktuk-bot
   source venv/bin/activate
   python clear_data.py
   ```

3. Запустите бота:
   ```
   sudo systemctl start tuktuk-bot
   ```

### Ошибка доступа к файлам

Если возникают ошибки доступа к файлам:

```
sudo chown -R <ваш_пользователь>:<ваш_пользователь> ~/tuktuk-bot
chmod +x ~/tuktuk-bot/*.py
```

### Дополнительная помощь

При возникновении сложных проблем, обратитесь к разработчику бота или создайте issue в репозитории проекта.
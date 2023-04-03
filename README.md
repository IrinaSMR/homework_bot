# homework_bot

Telegram-бот на Python использующий API Яндекс.Домашка для отслеживания статусов выполненных самостоятельно работ:

- бот раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

### Установка и запуск проекта:

Клонируйте репозиторий и перейдите в него в командной строке:
```
git clone https://github.com/alferius/homework_bot.git 
cd homework_bot
```

Cоздайте и активируйте виртуальное окружение:
```
python3 -m venv env source env/bin/activate
```

Обновите pip и установите зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip pip install -r requirements.txt
```

Запустите проект:
```
python3 manage.py runserver
```

### Автор:
IrinaSMR

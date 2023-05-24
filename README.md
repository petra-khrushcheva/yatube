# Блог-платформа yatube

### Описание
Социальная сеть Yatube. Дает пользователям возможность создать учетную запись, публиковать записи, подписываться на любимых авторов и отмечать понравившиеся записи.
***
### Технологии
Python 3.7  
Django 2.2.16
***

### Как запустить проект в dev-режиме:

Клонируйте репозиторий и перейдите в него в командной строке:

```
git clone git@github.com:petra-khrushcheva/yatube.git
```

```
cd yatube
```

Cоздайте и активируйте виртуальное окружение.

Установите зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Перейдите в папку yatube/yatube:

```
cd yatube/yatube
```

Примените миграции:

```
python3 manage.py makemigrations
python manage.py migrate
```

Запустите проект:

```
python3 manage.py runserver
```
# Социальная сеть для публикации постов.
## Описание
Проект разработан на MVT- архитектуре.
Реализована пагинация постов, кэширование, авторизация через JWT токены.
Стек технологий : Python3, Django REST Framework, SQLite3,Simple-JWT, GIT, pytest.


## Установка
```
git clone https://github.com/Markello93/hw05_final.git
```
```
cd hw05_final
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
```
source env/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Выполнить миграции:
```
python3 manage.py migrate
```
Запустить проект:
```
python3 manage.py runserver
```

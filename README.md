# LiveJournalAnalogue

Проект сайта для публикации постов. Реализована регистрация пользователей, подписка на любимых авторов, пагинация постов.

<details>
<summary>Стек</summary>

- [![Python](https://img.shields.io/badge/Python-3.9-blue?style=flat-square&logo=Python&logoColor=3776AB&labelColor=d0d0d0)](https://www.python.org/)
- [![Django](https://img.shields.io/badge/Django-2.2.16-blue?style=flat-square&logo=Django&logoColor=3776AB&labelColor=d0d0d0)](https://docs.djangoproject.com/en/4.2/releases/2.2.16/)
</details>

<details>
<summary>Запуск проекта</summary>

1) Клонировать репозиторий и перейти в папку c проектом;
2) Создать и активировать виртуальное окружение:
    ```
        python3 -m venv venv
        source venv/scripts/activate
    ```
3) Установить зависимости из файла requirements.txt:

    ```
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt
    ```
4) Перейти в папку "yatube"
    ```
    cd yatube
    ```
5) Выполнить команду 
    ```
    python manage.py runserver
    ```
После выполнения всех пунктов проект будет доступен по адресу http://127.0.0.1:8000/
</details>
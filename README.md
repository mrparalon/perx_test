## Установка

Python 3.6

```bash
pip install -r requiremets.txt
```

Для тестов

```bash
pip install -r requiremets.txt
```

## Запуск сервера

```bash
python run.py
```

# Методы

`GET /tasks` - возвращает список задач
`POST /tasks` - создает задачу, принимает json вида

```json
{"n": 1,
"d": 1.0,
"n1": 2.0,
"interval": 1.0}
```

# Переменные среды

NUM_WORKERS - количество одновременно обрабатываемых задач


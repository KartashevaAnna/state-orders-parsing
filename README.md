# state-orders-parsing
- Run celery with:
```celery -A run worker -l INFO```

- Run python with:
```
poetry shell
poetry run python run.py
```

The best practice is to use custom task classes only for overriding general behavior, and then using the task decorator to realize the task. However, I use classes differently, as I believe is requested by the reviewer.
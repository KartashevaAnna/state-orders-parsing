# state-orders-parsing
- Clone the project:
```git clone```
- Activate virtual environment:
```poetry shell```
- Install dependencies:
```poetry install```
- Run Rabbitmq:
```sudo systemctl start rabbitmq-server```
- Make sure that Rabbit is running:
```sudo systemctl status rabbitmq-server```
- Run celery with:
```celery -A run worker -l INFO```
- Run python with:
```poetry run python run.py```

The best practice is to use custom task classes only for overriding general behavior, and then using the task decorator to realize the task. However, I use classes differently, as requested by the reviewer.
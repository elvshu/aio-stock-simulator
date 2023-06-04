from celery import shared_task
from domain import operations

app = Celery("tasks", broker="pyamqp://guest@localhost//")


@shared_task
def update_price(trading_code: str) -> None:
    operations.update_price(trading_code)

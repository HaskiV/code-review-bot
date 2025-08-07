from celery import Celery
from backend.config.env import get_redis_url

celery = Celery(
    __name__,
    broker=get_redis_url(),
    backend=get_redis_url(),
    include=['backend.services.model_service']
)

celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

if __name__ == '__main__':
    celery.start()

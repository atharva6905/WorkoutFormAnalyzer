import multiprocessing
import sys

if sys.platform == "win32":
    _original_get_context = multiprocessing.get_context
    multiprocessing.get_context = lambda method=None: _original_get_context("spawn" if method == "fork" else method)

from redis import Redis
from rq import Worker, Queue

from app.core.config import settings


if __name__ == "__main__":
    redis_conn = Redis.from_url(settings.REDIS_URL)
    queue = Queue("analysis", connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)
    worker.work()

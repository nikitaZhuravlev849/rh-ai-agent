import logging

logger = logging.getLogger(__name__)


class _FakeTask:
    def delay(self, *args, **kwargs):
        logger.info("Celery не запущен — задача пропущена")
        return type("FakeResult", (), {"id": "no-celery"})()

    def __call__(self, *args, **kwargs):
        pass


class _FakeCelery:
    def task(self, *args, **kwargs):
        def decorator(fn):
            fn.delay = lambda *a, **kw: type("FakeResult", (), {"id": "no-celery"})()
            return fn
        return decorator


celery_app = _FakeCelery()

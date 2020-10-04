import asyncio
import os
from datetime import datetime
# Убедится, что количество консьюмеров 1.
# В реальном проекте я бы вынес это в CI
os.environ['NUM_WORKERS'] = '1'


from run import build_app, Status


async def test_create_task(aiohttp_client):
    app = build_app()
    client = await aiohttp_client(app)
    res = await client.post('/tasks',
                            json={'n': 1,
                                  'd': 1,
                                  'n1': -2,
                                  'interval': 10})
    data = await res.json()
    assert data['success'] is True
    queue = app['queue']._queue
    assert len(queue) == 0  # task get by consumer
    consumer_tasks = [c.task for c in app['consumers']
                      if c.task is not None]
    assert len(consumer_tasks) == 1


async def test_create_multiple_task(aiohttp_client):
    app = build_app()
    client = await aiohttp_client(app)
    queue_tasks = 2
    for i in range(queue_tasks + 1):  # 1 will go to consumer
        res = await client.post('/tasks',
                                json={'n': 1,
                                      'd': 1,
                                      'n1': -2,
                                      'interval': 10})
        data = await res.json()
    queue = app['queue']._queue
    assert len(queue) == queue_tasks
    consumer_tasks = [c.task for c in app['consumers']
                      if c.task is not None]
    assert len(consumer_tasks) == 1


async def test_task_run_in_consumer(aiohttp_client):
    app = build_app()
    client = await aiohttp_client(app)
    res = await client.post('/tasks',
                            json={'n': 1,
                                  'd': 1,
                                  'n1': -2,
                                  'interval': 1})
    consumer_tasks = [c.task for c in app['consumers']
                      if c.task is not None]
    assert len(consumer_tasks) == 1
    await asyncio.sleep(1.5)
    consumer_tasks = [c.task for c in app['consumers']
                      if c.task is not None]
    assert len(consumer_tasks) == 0


async def test_get_tasks(aiohttp_client):
    app = build_app()
    client = await aiohttp_client(app)
    n = 1
    d = 1
    n1 = -2
    interval = 1
    for i in range(2):
        res = await client.post('/tasks',
                                json={'n': n,
                                      'd': d,
                                      'n1': n1,
                                      'interval': interval})
    res = await client.get('/tasks')
    data = await res.json()
    assert data[0]['status'] == Status.ongoing.value
    assert data[1]['status'] == Status.queue.value

    assert data[0]['start_date'] == str(datetime.now().date())
    assert data[1]['start_date'] is None

    assert data[0]['queue_position'] == 0
    assert data[1]['queue_position'] == 1

    for task in data:
        assert task['n'] == n
        assert task['d'] == d
        assert task['n1'] == n1
        assert task['interval'] == interval

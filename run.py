#! python
import asyncio
import os
import json
from enum import Enum
from datetime import datetime, date
from typing import Optional
from aiohttp import web
from pydantic import BaseModel, ValidationError

# Количество одновременно обрабатывемых задач
NUM_WORKERS = int(os.environ.get('NUM_WORKERS', 1))
HOST = os.environ.get('HOST', '127.0.0.1')


# Models
class Status(Enum):
    """
    Avaliable values for task status.
    """
    ongoing = 'ongoing'
    queue = 'queue'


class Task(BaseModel):
    """
    Model for tasks.
    """
    n1: float
    n: int
    d: float
    value: Optional[float] = None
    interval: float
    queue_position: int = 0
    start_date: Optional[date] = None
    status: Status = Status.queue.value

    class Config:
        validate_assignment = True
        use_enum_values = True


# Async consumers and queue
class Consumer:
    """
    Consume data from queue and make arithmetic progression.
    Store current state of task.
    """
    def __init__(self):
        self.task: Task = None

    async def start(self, queue: asyncio.Queue):
        while True:
            self.task = await queue.get()
            self.task.start_date = datetime.now().date()
            self.task.status = Status.ongoing.value
            self.task.value = self.task.n1
            for i in range(self.task.n):
                await asyncio.sleep(self.task.interval)
                self.task.value += self.task.d
                print(f'Value: {self.task.value}')
            self.task = None


async def start_queue(app):
    queue = asyncio.Queue()
    app['queue'] = queue
    app['consumers'] = []
    loop = asyncio.get_event_loop()
    for i in range(NUM_WORKERS):
        consumer = Consumer()
        loop.create_task(consumer.start(queue)) # создаются таски, которые берут из очереди данные и обрабатывают их
        app['consumers'].append(consumer)


# Handlers
class TasksHandler:
    def __init__(self, app):
        self.app = app

    async def get_tasks(self, request):
        tasks = self.app['queue']._queue.copy()
        for i, task in enumerate(reversed(tasks)):
            task.queue_position = i + 1
        tasks += [consumer.task for consumer in self.app['consumers']]
        tasks_dicts = [task.dict() for task in tasks if task is not None]
        tasks_dicts.sort(key=lambda x: x['queue_position'])
        serialized_tasks = json.dumps(tasks_dicts, default=str)  # web.json_response не умеет сериалзовать date
        return web.Response(text=serialized_tasks,
                            content_type='application/json')

    async def create_task(self, request):
        data = await request.json()
        try:
            task = Task(**data)
        except ValidationError as exc:
            return web.json_response(
                {'success': False,
                 'error': exc.errors()}
                 )
        await self.app['queue'].put(task)
        return web.json_response(
            {'success': True,
             'queue_position': len(self.app['queue']._queue)}
        )

# Utils

def setup_routes(app, handler):
    router = app.router
    h = handler
    router.add_get('/tasks', h.get_tasks, name='get_tasks')
    router.add_post('/tasks', h.create_task, name='create_task')


def build_app(startup=start_queue, handler=TasksHandler):
    routes = web.RouteTableDef()
    app = web.Application()
    setup_routes(app, handler(app))
    app.on_startup.append(startup)
    app.add_routes(routes)
    return app


if __name__ == '__main__':
    app = build_app()
    web.run_app(app, host=HOST)

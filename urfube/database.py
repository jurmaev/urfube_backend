from contextvars import ContextVar

import peewee

from urfube.config import settings

db_state_default = {'closed': None, 'conn': None, 'ctx': None, 'transactions': None}
db_state = ContextVar('db_state', default=db_state_default.copy())


class PeeweeConnectionState(peewee._ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__('_state', db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]

db = peewee.PostgresqlDatabase(settings.database_name, host=settings.host, port=settings.port, user=settings.user,
                           password=settings.password)
db._state = PeeweeConnectionState()

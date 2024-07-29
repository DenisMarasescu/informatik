import asyncio
import logging
from collections import deque
from contextvars import ContextVar
from datetime import datetime
from enum import Enum
from functools import wraps
from inspect import isfunction, ismethod
from typing import List, Union
from uuid import uuid4

log = logging.getLogger(__name__)

TRAIL_LOGGER_HISTORY_SIZE = 5


class LoggerState(Enum):
    INACTIVE = 0
    ACTIVE = 1
    COMPLETED = 2


class TrailLogger:
    def __init__(self):
        self._trail_log = []
        self._is_active = LoggerState.INACTIVE
        self._id = uuid4()

    def begin(self):
        """
        Moves the logger state to ACTIVE, accepting new events or a finalize() call.
        """
        if self._is_active is not LoggerState.INACTIVE:
            raise RuntimeError(
                f"TrailLogger begin called with incompatible state, {self._is_active}"
            )
        self._is_active = LoggerState.ACTIVE

    def add_event(self, event: str):
        """
        Adds an event to the trail log.  The logger must be in an ACTIVE state.
        """
        if self._is_active is not LoggerState.ACTIVE:
            raise RuntimeError(
                f"TrailLogger add_event called with incompatible state, {self._is_active}"
            )
        self._trail_log.append(event)

    def finalize(self):
        """
        Finalizes the logger, moving the state to COMPLETED.  No further events can be added
        to this logger.
        """
        if self._is_active is not LoggerState.ACTIVE:
            raise RuntimeError(
                f"TrailLogger finalize called with incompatible state, {self._is_active}"
            )
        self._is_active = LoggerState.COMPLETED

    @property
    def id(self):
        """
        Returns the self generated UUID for this logger.
        """
        return self._id

    @property
    def trail(self) -> List[str]:
        """
        Returns a copy of the trail of events in this logger.
        """
        return self._trail_log.copy()

    def __repr__(self) -> str:
        output = f"TrailLogger {self.id}:\n"
        for event in self.trail:
            output += f"    {event}\n"
        return output


TRAIL_LOGGER_CVAR: ContextVar[Union[TrailLogger, None]] = ContextVar(
    "TrailLoggerCVar", default=None
)


class TrailLoggerStore:
    _trail_loggers = deque(maxlen=TRAIL_LOGGER_HISTORY_SIZE)

    @classmethod
    def add_logger(cls, logger):
        """
        Adds a logger to this TrailLoggerStore.  TrailLoggerStore holds a limited history
        of TrailLoggers.
        """
        cls._trail_loggers.append(logger)

    @classmethod
    def get_loggers(cls) -> List[TrailLogger]:
        """
        Returns all TrailLoggers in the TrailLoggerStore.
        """
        return list(cls._trail_loggers)


def init():
    """
    Initializes a TrailLogger for the current context.  Only one TrailLogger can be created
    for a given context.
    """
    if TRAIL_LOGGER_CVAR.get():
        raise RuntimeError("Context already has an active trail logger")
    TRAIL_LOGGER_CVAR.set(TrailLogger())
    TRAIL_LOGGER_CVAR.get().begin()  # type: ignore


def add_event(event: str):
    """
    Adds an event to the current context's TrialLogger, if it exists.
    """
    if TRAIL_LOGGER_CVAR.get(None):
        TRAIL_LOGGER_CVAR.get().add_event(f"{datetime.now()}:{event}")  # type: ignore


def finalize():
    """
    Completes the context's TrailLogger, moving it into the TrailLoggerStore.
    """
    if TRAIL_LOGGER_CVAR.get(None):
        logger = TRAIL_LOGGER_CVAR.get()
        logger.finalize()  # type: ignore
        TrailLoggerStore.add_logger(logger)


def spy_on_object(obj):
    """
    Attempts to spy on all public attrs of an object.  Very spooky.
    """
    for method in dir(obj):
        if method.startswith("_"):
            # Don't spy on private things, that's weird.
            continue
        try:
            spy_on_method(obj, method)
        except AttributeError:
            # Some attrs are properties, and we can't spy on them.
            continue


def spy_on_method(obj, method_name):
    """
    Replaces a single method on an object with a spy method that logs to the TrailLogger when the
    method is called.
    """
    orig_method = getattr(obj, method_name)
    if not isfunction(orig_method) and not ismethod(orig_method):
        return

    @wraps(orig_method)
    def spy_method_sync(*args, **kwargs):
        add_event(f"Called [#{method_name}] on {obj} with {args} and {kwargs}")
        result = orig_method(*args, **kwargs)
        add_event(f"Completed [#{method_name}] on {obj} with {args} and {kwargs}")
        return result

    @wraps(orig_method)
    async def spy_method_async(*args, **kwargs):
        add_event(f"Called [#{method_name}] on {obj} with {args} and {kwargs}")
        result = await orig_method(*args, **kwargs)
        add_event(f"Completed [#{method_name}] on {obj} with {args} and {kwargs}")
        return result

    if asyncio.iscoroutinefunction(orig_method):
        setattr(obj, method_name, spy_method_async)
    else:
        setattr(obj, method_name, spy_method_sync)

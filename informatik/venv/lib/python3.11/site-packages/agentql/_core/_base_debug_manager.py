import importlib.metadata
import logging
import os
import platform
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

from agentql import trail_logger
from agentql._core._utils import get_debug_files_path, save_json_file, save_text_file

log = logging.getLogger("agentql")

MAX_DEBUG_FOLDERS_NUM = 50


class BaseDebugManager:
    debug_mode_enabled = False
    debug_files_path = None
    agentql_session = None

    @classmethod
    def set_agentql_session(cls, agentql_session):
        cls.agentql_session = agentql_session

    @classmethod
    def create_debug_files_dir(cls):
        """
        Create the debug files directory.
        """
        cls.debug_files_path = Path(get_debug_files_path()) / datetime.now().strftime(
            "%Y-%m-%d_%H_%M_%S"
        )
        os.makedirs(cls.debug_files_path, exist_ok=True)
        cls._enforce_folder_number_limit()

    @staticmethod
    def _enforce_folder_number_limit():
        """
        Ensure the number of debug folders does not exceed the maximum limit.
        """
        debug_folder_path = Path(get_debug_files_path())
        folders = [f for f in debug_folder_path.iterdir() if f.is_dir()]
        folders.sort(key=lambda f: f.stat().st_ctime)

        while len(folders) > MAX_DEBUG_FOLDERS_NUM:
            shutil.rmtree(folders.pop(0))

    @classmethod
    def save_last_accessibility_tree(cls):
        """
        Save the last accessibility tree used from AgentQL session to a file.
        """
        if cls.agentql_session:
            accessibility_tree = cls.agentql_session.last_accessibility_tree
            if accessibility_tree and cls.debug_files_path:
                save_json_file(cls.debug_files_path / "accessibility_tree.json", accessibility_tree)

    @classmethod
    def save_traceback(cls, exception: Exception):
        """
        Save the traceback information to a file.

        Parameters:
        ----------
        exception (Exception): The exception that was raised.
        """
        if cls.debug_files_path:
            save_text_file(
                cls.debug_files_path / "traceback.log",
                "".join(traceback.format_exception(None, exception, exception.__traceback__)),
            )

    @classmethod
    def save_logging_file(cls):
        """
        Save the logging information to a file.
        """
        logger_store = trail_logger.TrailLoggerStore.get_loggers()
        if logger_store and cls.debug_files_path:
            save_text_file(cls.debug_files_path / "logging.log", str(logger_store[-1]))

    @classmethod
    def save_meta_data(cls):
        """
        Save the meta data (OS, Python version, AgentQL Library version) to a file.
        """
        meta_data = {
            "OS": platform.platform(),
            "Python version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "AgentQL version": importlib.metadata.version("agentql"),
        }
        if cls.debug_files_path:
            save_json_file(cls.debug_files_path / "meta_data.json", meta_data)

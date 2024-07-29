import logging
from contextlib import contextmanager

from agentql._core._base_debug_manager import BaseDebugManager

log = logging.getLogger("agentql")


class DebugManager(BaseDebugManager):
    @classmethod
    @contextmanager
    def debug_mode(cls):
        cls.debug_mode_enabled = True
        cls.create_debug_files_dir()
        try:
            yield
        except Exception as e:
            cls.save_traceback(e)
            raise
        finally:
            cls.debug_mode_enabled = False
            cls.save_logging_file()
            cls.save_last_accessibility_tree()
            cls.save_meta_data()
            log.debug(f"Debug files saved to {cls.debug_files_path}")

from typing import TypeVar

InteractiveItemTypeT = TypeVar("InteractiveItemTypeT")
"""
A type variable representing the type of interactive items in a web driver session.
Used in type hints where the exact type depends on the specific web driver library used.
"""

PageTypeT = TypeVar("PageTypeT", covariant=False, contravariant=False)
"""
A type variable representing the type of a page in a web driver session.
Used in type hints where the exact type depends on the specific web driver library used.
"""

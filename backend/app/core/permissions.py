from typing import Protocol


class Owned(Protocol):
    author_id: int


def is_moderator(role: str) -> bool:
    return role in {"admin", "moderator"}


def can_manage(user_role: str, user_id: int, owner_id: int) -> bool:
    return user_id == owner_id or is_moderator(user_role)

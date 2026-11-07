from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.topic import Topic
    from app.models.user import User


class Post(TimestampMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("topic_id", "floor", name="uq_posts_topic_floor"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    is_op: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    topic: Mapped[Topic] = relationship(back_populates="posts")
    author: Mapped[User] = relationship(back_populates="posts")

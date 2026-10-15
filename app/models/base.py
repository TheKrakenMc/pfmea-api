from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}
    """Base class for all ORM models.

    All models inherit from this so that ``Base.metadata`` contains
    the full schema — required by Alembic and ``create_all``.
    """

    pass

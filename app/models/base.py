from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(DeclarativeBase):
    """Base class for all ORM models.

    All models inherit from this so that ``Base.metadata`` contains
    the full schema — required by Alembic and ``create_all``.
    """

    pass

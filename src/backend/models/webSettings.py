import json

from sqlalchemy import Column, Integer, VARCHAR, TypeDecorator
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JSONEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""

    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, str):
                return value

            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class SwipeArrSeenRadarr(Base):
    __tablename__ = "swipeArrSeenRadarr"

    id = Column(Integer, primary_key=True)
    itemId = Column(Integer, nullable=False)


class SwipeArrSeenSonarr(Base):
    __tablename__ = "swipeArrSeenSonarr"

    id = Column(Integer, primary_key=True)
    itemId = Column(Integer, nullable=False)

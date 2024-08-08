import json

from sqlalchemy import Column, Integer, String, VARCHAR, TypeDecorator
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


class FavoriteMovies(Base):
    __tablename__ = 'favoriteMovies'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(Integer, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class FavoriteSeries(Base):
    __tablename__ = 'favoriteSeries'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(Integer, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class OnResumeMovies(Base):
    __tablename__ = 'onResumeMovies'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(Integer, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class OnResumeSeries(Base):
    __tablename__ = 'onResumeSeries'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(Integer, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class PlayedMovies(Base):
    __tablename__ = 'PlayedMovies'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(Integer, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class PlayedSeries(Base):
    __tablename__ = 'PlayedSeries'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(Integer, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class PlayedEpisodes(Base):
    __tablename__ = 'PlayedEpisodes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    mediaId = Column(String, nullable=False)

    userIds = Column(JSONEncodedDict)
    date = Column(Integer, nullable=False)


class musicVideoCache(Base):
    __tablename__ = 'musicVideoCache'

    id = Column(Integer, primary_key=True)
    youtubeId = Column(String)
    downloadError = Column(Integer, default=0)
    title = Column(String, nullable=False)
    artists = Column(JSONEncodedDict, nullable=False)
    album = Column(String)
    dateAdded = Column(Integer, nullable=False)
    additionalInfo = Column(JSONEncodedDict)

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import logging
from collections import namedtuple
from typing import List, Optional

from sqlalchemy import ForeignKey, String, func, create_engine, select, or_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.orm import Session

from youtube_audio_provider.appinfo import AppInfo

logger = logging.getLogger(__name__)

Item = namedtuple('Item', ['phrase', 'filename', 'title', 'artist'])


class Base(DeclarativeBase):
    pass


class Entry(Base):
    __tablename__ = "entry"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[Optional[str]]
    artist: Mapped[Optional[str]]
    filename: Mapped[Optional[str]]

    phrases: Mapped[List["SearchPhrase"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )


class SearchPhrase(Base):
    __tablename__ = "phrase"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phrase: Mapped[str]

    entry_id: Mapped[str] = mapped_column(ForeignKey(Entry.__tablename__ + ".id"))
    entry: Mapped["Entry"] = relationship(back_populates="phrases")


class Cache(object):

    def __init__(self, exporter, info: AppInfo, audio_file_directory):
        # db setup
        self.databasefile = "cache.db"
        db_uri = f"sqlite:///{self.databasefile}"
        self.engine = create_engine(db_uri, echo=True)
        Base.metadata.create_all(self.engine)

        self.appinfo = info
        self.audio_file_directory = audio_file_directory

        self.exporter = exporter

        with Session(self.engine) as session:
            self._update_cache_size(session)

    def _entry_to_dict(self, e: Entry):
        res = {}
        res['title'] = e.title
        res['artist'] = e.artist
        res['filename'] = e.filename
        return res

    def _dict_to_entry(self, d):
        return Entry(id=d.get('id'),
                     title=d.get('title'),
                     artist=d.get('artist'),
                     filename=d.get('filename'))

    def _simplify_quoted_search(self, quoted_search: str):
        return quoted_search.casefold()

    def _check_file_exists(self, filename: str):
        path = os.path.join(self.audio_file_directory, filename)
        logger.debug(f"looking for file '{path}'")
        if (os.path.exists(path)):
            return True
        return False

    def _find_entry_with_searchphrase(self, session: Session, search_phrase: str):
        stmt = (
                 select(Entry)
                 .join(SearchPhrase.entry)
                 .where(SearchPhrase.phrase == search_phrase)
            )
        return session.scalars(stmt).first()

    def retrieve_by_search(self, quoted_search: str) -> dict | None:
        ''' get value from cache,
        checks whether file is available, otherwise invalidates cache '''

        simplified_string = self._simplify_quoted_search(quoted_search)

        with Session(self.engine) as session:
            e = self._find_entry_with_searchphrase(session, simplified_string)
            if (e is not None):
                if (self._check_file_exists(e.filename)):
                    logger.debug(f"entries file exists {e.filename} for phrase {quoted_search}")
                    return self._entry_to_dict(e)

        return None

    def retrieve_by_id(self, id: str) -> dict | None:
        with Session(self.engine) as session:
            stmt = (
                 select(Entry)
                 .where(Entry.id == id)
            )
            e = session.scalars(stmt).first()
            if (e is not None):
                if (self._check_file_exists(e.filename)):
                    logger.debug(f"entries file exists {e.filename} for id {id}")
                else:
                    logger.error(f"entries file does not exist {e.filename} for id {id}")
                return self._entry_to_dict(e)
        return None

    def _cache_updated(self, session):
        self._export(session)
        self._update_cache_size(session)

    def _update_cache_size(self, session):
        statement = select(func.count()).select_from(Entry)
        count: int = session.execute(statement).scalar()
        self.appinfo.register('cache_size', count)

    def _export(self, session):
        data = {}
        stmt = (
            select(Entry, SearchPhrase)
            .join(SearchPhrase.entry)
        )
        # compact / create a (legacy) dict phrase -> filename
        for (e, p) in session.execute(stmt).all():
            data[p.phrase] = e.filename
        self.exporter.export(data)

    def put_to_cache(self, quoted_search: str, **kwargs):
        ''' put into cache the quoted_search string together with the filename '''

        simplified_string = self._simplify_quoted_search(quoted_search)

        # put value to cache
        with Session(self.engine) as session:
            stmt = (
                 select(Entry)
                 .where(Entry.filename == kwargs.get('filename'))
            )
            e = session.scalars(stmt).first()
            # get or create entry
            if (e is None):
                e = self._dict_to_entry(kwargs)
                session.add(e)

            # create phrase
            phrase = SearchPhrase(phrase=simplified_string, entry=e)
            session.add(phrase)

            session.commit()
            self._cache_updated(session)

    def add_searchphrase_to_id(self, id, quoted_search):
        simplified_string = self._simplify_quoted_search(quoted_search)

        with Session(self.engine) as session:
            stmt = (
                 select(Entry)
                 .where(Entry.id == id)
            )
            e = session.scalars(stmt).first()
            if (e is None):
                raise ValueError(f'entry with id {id} cold not be found, to add a phrase')

            phrase = SearchPhrase(phrase=simplified_string, entry=e)
            session.add(phrase)

            session.commit()
            self._cache_updated(session)

    def remove_from_cache_by_search(self, quoted_search):
        simplified_string = self._simplify_quoted_search(quoted_search)

        with Session(self.engine) as session:
            e = self._find_entry_with_searchphrase(session, simplified_string)
            if (e is not None):
                filename = e.filename
                session.delete(e)  # should automagically delete the phrases
                session.commit()
                self._cache_updated(session)
                return filename

            return False

    def fulltext_search(self, quoted_search: str):
        simplified_string = self._simplify_quoted_search(quoted_search)

        result_list: List[Item] = []

        with Session(self.engine) as session:
            stmt = (
                 select(Entry, SearchPhrase)
                 .join(SearchPhrase.entry)
                 .where(
                     or_(SearchPhrase.phrase == simplified_string, Entry.filename.contains(simplified_string))
                 )
            )
        results = session.execute(stmt).all()
        for (e, p) in results:
            result_list.append(Item(p.phrase, e.filename, e.title, e.artist))

        return result_list

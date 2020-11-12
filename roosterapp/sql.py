from contextlib import contextmanager

from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("staffs.person_id"))
    client_id = Column(Integer, ForeignKey("clients.person_id"))
    hours = Column(Float, default=1)

class Presence(Base):
    __tablename__ = 'presences'
    person_id = Column(Integer, ForeignKey("persons.id"), primary_key=True)
    dole_id =  Column(Integer, ForeignKey("doles.id"), primary_key=True)
    present = Column(Integer)

class Dole(Base):
    __tablename__ = 'doles'
    id = Column(Integer, primary_key = True)
    name = Column(String(127))
    hours = Column(Float, default=1)
    occupation = relationship("Presence", backref="dole", cascade="delete, delete-orphan")

class Person(Base):
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    name = Column(String(127))
    active = Column(Boolean, default=True)
    atttendance = relationship("Presence", backref="person", cascade="delete, delete-orphan")

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    name = Column(String(127))
    ratio = Column(Float)
    clients = relationship("Client", backref="profile")

class Client(Base):
    __tablename__ = 'clients'
    person_id = Column(Integer, ForeignKey("persons.id"), primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    hours = Column(Float, default=0)
    person = relationship("Person")
    sessions = relationship("Session", backref="client", cascade="delete, delete-orphan")

class Staff(Base):
    __tablename__ = 'staffs'
    person_id = Column(Integer, ForeignKey("persons.id"), primary_key=True)
    min_hours = Column(Float, default=0)
    max_hours = Column(Float, default=0)
    person = relationship("Person")
    sessions = relationship("Session", backref="staff", cascade="delete, delete-orphan")

@contextmanager
def scoped_session(db):
    """ Creates a SQLAlchemy database transaction """

    session = db.create_scoped_session()
    try:
        yield session
        session.commit()
    except DatabaseError as err:
        print(f"Error in scoped session: {err}")
        session.rollback()
    finally:
        session.close()


def with_scoped_session(func):
    """ Decorator to add a scoped session 
    
    The decorated function must be a class method of a class with access
    to an SQLAlchemy database object, as well as take a session parameter.
    """

    def wrapper(self, *args, **kwargs):
        with scoped_session(self.db) as session:
            return func(self, *args, **dict(kwargs, session=session))
    return wrapper

# class SqlUrls(UrlAPI):
#     """ SQLAlchemy backed implementation or the URL API """
    
#     def __init__(self, sqldb):
#         super().__init__(sqldb)
#         self.db = sqldb
#         Base.metadata.create_all(bind=self.db.engine)

#     @with_scoped_session
#     def insert_url(self, key: str, long_url: str, session=None) -> None:
#         new_url = Url(key=key, long_url=long_url)
#         session.add(new_url)

#     @with_scoped_session
#     def read_url(self, key: str, session=None) -> Optional[str]:
#         if url := session.query(Url).get(key):
#             return url.long_url
#         return None

#     @with_scoped_session
#     def read_all_urls(self, session=None):
#         return [KeyUrl(url.key, url.long_url)
#                 for url in session.query(Url).all()]

#     @with_scoped_session
#     def update_url(self, key: str, long_url: str, session=None) -> None:
#         if url := session.query(Url).get(key):
#             url.long_url = long_url

#     @with_scoped_session
#     def delete_url(self, key: str, session=None) -> None:
#         if url := session.query(Url).get(key):
#             session.delete(url)

#     @with_scoped_session
#     def count(self, session=None) -> int:
#         return session.query(Url).count()

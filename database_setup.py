import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False)
    picture = Column(String(80))


class InstrumentType(Base):
    __tablename__ = 'instrumenttype'

    id = Column(Integer, primary_key=True)
    name_type = Column(String(250), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name_type': self.name_type,
            'id': self.id,
            'created_date': self.created_date,
            'user_id': self.user_id,
        }


class Instrument(Base):
    __tablename__ = 'instrument'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    instrumenttype_id = Column(Integer, ForeignKey('instrumenttype.id'))
    instrumenttype = relationship(InstrumentType)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'created_date': self.created_date,
            'instrumenttype_id': self.instrumenttype_id,
            'user_id': self.user_id,
        }


engine = create_engine('sqlite:///instruments.db')


Base.metadata.create_all(engine)
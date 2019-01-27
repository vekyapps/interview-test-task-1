import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import validates, relationship
from database import Base

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    description = Column(Text)
    code = Column(String(30), unique=True, nullable=False)
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    date_updated = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = Column(Enum('enabled', 'disabled', 'deleted'), nullable=False)

    @validates('name')
    def validate_username(self, key, name):
        if not name:
            raise AssertionError('No name provided')
        if len(name) > 32:
            raise AssertionError('Name can contain max. 32 chars.')

        return name

    @validates('code')
    def validate_code(self, key, code):
        if not code:
            raise AssertionError('No code provided')
        if len(code) > 30:
            raise AssertionError('Code can contain max. 32 chars.')

        return code

class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    device = Column(Integer, ForeignKey("devices.id"))
    device_relationship = relationship('Device', backref='contents')

    date_created = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    date_updated = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    expire_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = Column(Enum('enabled', 'disabled', 'deleted'), nullable=False)

    @validates('name')
    def validate_username(self, key, name):
        if not name:
            raise AssertionError('No name provided')
        if len(name) > 100:
            raise AssertionError('Name can contain max. 100 chars.')

        return name
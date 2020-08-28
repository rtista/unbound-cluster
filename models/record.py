# Batteries
import time

# Third Party Imports
from sqlalchemy import Column, Integer, String, Enum

# Own Imports
from . import Base
from config import Config


def unixtime():
    """
    Helper class for integer unix timestamp generation.

    Returns:
        int: Unix timestamp as integer.
    """
    return int(time.time())


class Record(Base):

    __tablename__ = 'records'

    zone = Column('zone', String(255), primary_key=True, nullable=False)
    resource = Column('resource', String(255), primary_key=True, nullable=False)
    rtype = Column('type', Enum(*Config.VALID_RECORD_TYPES), primary_key=True, nullable=False)
    ttl = Column('ttl', Integer, default=3600, nullable=False)
    rdata = Column('rdata', String(255), primary_key=True, nullable=False)
    created = Column('created', Integer, default=unixtime)
    updated = Column('updated', Integer, default=unixtime, onupdate=unixtime)

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

    rname = Column('rname', String(255), primary_key=True, nullable=False)
    rtype = Column('rtype', Enum(*Config.SUPPORTED_RECORD_TYPES), primary_key=True, nullable=False)
    rdata = Column('rdata', String(255), primary_key=True, nullable=False)
    ttl = Column('ttl', Integer, default=3600, nullable=False)
    created = Column('created', Integer, default=unixtime)
    updated = Column('updated', Integer, default=unixtime, onupdate=unixtime)

    def todict(self) -> dict:
        """
        Dict-like representation of the model.
        """
        return {
            'rname': self.rname,
            'rtype': self.rtype,
            'rdata': self.rdata,
            'ttl': self.ttl,
            'created': self.created,
            'updated': self.updated,
        }

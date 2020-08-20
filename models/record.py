# Batteries
import time

# Third Party Imports
from sqlalchemy import Column, Integer, String, Enum

# Own Imports
from . import Base


def unixtime():
    """
    Helper class for integer unix timestamp generation.

    Returns:
        int: Unix timestamp as integer.
    """
    return int(time.time())


class Record(Base):

    __tablename__ = 'records'

    record_id = Column('record_id', Integer, primary_key=True, nullable=False)
    zone = Column('zone', String(255), nullable=False, index=True)
    resource = Column('resource', String(255), nullable=False)
    rtype = Column('type', Enum('A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', 'CERT', 'SRV', 'TXT', 'SOA'), nullable=False)
    ttl = Column('ttl', Integer, default=3600, nullable=False)
    rdata = Column('rdata', String(255), nullable=False)
    created = Column('created', Integer, default=unixtime)
    updated = Column('updated', Integer, default=unixtime, onupdate=unixtime)

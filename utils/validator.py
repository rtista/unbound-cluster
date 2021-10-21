# Third-party Imports
import validators
import tldextract

# Batteries
import ipaddress

# Local Imports
from config import Config


class InvalidDNSRecordType(Exception):
    """
    Raised when an invalid DNS record type is provided.
    """
    ...


class InvalidDNSRecord(Exception):
    """
    Raised when an invalid DNS record is provided.
    """
    ...


class RecordValidator:
    """
    Static class which validates received DNS records.
    """
    @classmethod
    def validate(cls, rname: str, rtype: str, rdata: str) -> None:
        """
        Validates a DNS record parameters.
        """
        # Check record type
        if rtype not in Config.SUPPORTED_RECORD_TYPES:
            raise InvalidDNSRecordType(f'Unsupported DNS record type "{rtype}".')

        # Extract zone from record and raise if invalid
        if not tldextract.extract(rname).registered_domain:
            raise InvalidDNSRecord(f'Invalid zone for domain name "{rname}"')

        # Validate RDATA by RTYPE
        try:

            if rtype == 'A' and not isinstance(ipaddress.ip_address(rdata), ipaddress.IPv4Address):
                raise InvalidDNSRecord(f'RDATA \'{rdata}\' is not a valid IPv4 address.')

            elif rtype == 'AAAA' and not isinstance(ipaddress.ip_address(rdata), ipaddress.IPv6Address):
                raise InvalidDNSRecord(f'RDATA \'{rdata}\' is not a valid IPv6 address.')

            elif rtype in ('CNAME', 'MX'):

                # Don't forget to validate MX priority
                priority, rdata = rdata.split(' ')[0:2] if ' ' in rdata else (None, rdata)

                if rtype == 'MX' and priority and int(priority) < 0:
                    raise InvalidDNSRecord(f'Invalid DNS {rtype} record priority: {priority}')

                # Validate domain-name RDATA
                if isinstance(validators.domain(rdata), validators.ValidationFailure):
                    raise ValueError

        except ValueError:
            raise InvalidDNSRecord(f'Invalid DNS {rtype} record RDATA: \'{rdata}\'')

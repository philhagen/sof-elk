# SOF-ELK® Library: Dictionaries
# (C)2025 Lewes Technology Consulting, LLC

import os
import warnings
from typing import Any

import yaml


class DictionaryManager:
    """
    Manages loading and querying of various dictionary files (YAML format) used for lookups.

    This class employs a singleton-like pattern via `get_instance` and lazy-loading of
    dictionary files to optimize performance.
    """

    _instances: dict[str | None, "DictionaryManager"] = {}

    # Defaults relative to this file
    # ../../../core/lib/dictionaries from sofelk/source/sof_elk/lib
    DEFAULT_DICT_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "core",
        "lib",
        "dictionaries",
    )

    def __init__(self, dict_path: str | None = None) -> None:
        self.dict_path = dict_path if dict_path else self.DEFAULT_DICT_PATH
        self._cache: dict[str, Any] = {}

    @classmethod
    def get_instance(cls, dict_path: str | None = None) -> "DictionaryManager":
        if dict_path not in cls._instances:
            cls._instances[dict_path] = cls(dict_path)
        return cls._instances[dict_path]

    def _load(self, filename: str) -> Any:
        """Lazy load a dictionary file."""
        if filename not in self._cache:
            full_path = os.path.join(self.dict_path, filename)
            if not os.path.exists(full_path):
                # Fallback or error?
                return {}
            try:
                with open(full_path) as f:
                    # Use safe_load for security
                    self._cache[filename] = yaml.safe_load(f)
            except Exception as e:
                warnings.warn(f"Failed to load dictionary {filename}: {e}", stacklevel=2)
                self._cache[filename] = {}
        return self._cache[filename]

    def lookup_syslog_facility(self, facility_name: str) -> int | None:
        """
        Looks up the integer code for a given syslog facility name.

        Args:
            facility_name: The name of the syslog facility (e.g., "auth", "cron").

        Returns:
            The integer code associated with the facility, or None if not found.
        """
        d = self._load("syslog_facility2int.yaml")
        # Direct lookup (file is name: int)
        return d.get(facility_name)

    def lookup_dns_type(self, code: int | str) -> str | None:
        """
        Looks up the DNS record type name for a given integer code.

        Args:
            code: The DNS record type code (e.g., 1).

        Returns:
            The string representation of the DNS record type (e.g., "A"), or None.
        """
        d = self._load("dns_type_code2name.yaml")
        # Keys in yaml are strings "1": "A"
        return d.get(str(code))

    def lookup_ip_proto(self, proto: int | str, reverse: bool = False) -> str | int | None:
        """
        Looks up IP protocol mappings.

        Args:
            proto: The protocol identifier (integer or string name).
            reverse: If True, looks up integer from name (e.g., "tcp" -> 6).
                     If False (default), looks up name from integer (e.g., 6 -> "tcp").

        Returns:
            The mapped value (string name or integer code), or None if not found.
        """
        if reverse:
            d = self._load("ip_proto_name2int.yaml")
            return d.get(str(proto))
        else:
            d = self._load("ip_proto_int2name.yaml")
            return d.get(str(proto))

    def lookup_port(self, port: int | str, proto: str = "tcp") -> str | None:
        """
        Looks up the IANA service name for a given port.

        Args:
            port: The port number.
            proto: The protocol (currently unused, kept for API compatibility/future use).

        Returns:
            The service name associated with the port, or None if not found.
        """
        d = self._load("port_proto_int2iana.yaml")
        # Since the file seemed to just have number keys, we try that.
        # Ideally this file would handle tcp/udp distinction but if it's flat...
        return d.get(str(port))

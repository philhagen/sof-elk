# SOF-ELK® Processor: Community ID
# (C)2025 Lewes Technology Consulting, LLC
#
# Ported from community-id.rb

import base64
import hashlib
import socket
import struct


class CommunityID:
    VERSION = "1:"

    # ICMP mapping constants
    ICMP4_MAP = {
        8: 0,  # Echo -> Reply
        0: 8,  # Reply -> Echo
        13: 14,  # Timestamp -> TS reply
        14: 13,  # TS reply -> timestamp
        15: 16,  # Info request -> Info Reply
        16: 15,  # Info Reply -> Info Req
        10: 9,  # Rtr solicitation -> Rtr Adverstisement
        17: 18,  # Mask -> Mask reply
        18: 17,  # Mask reply -> Mask
    }

    ICMP6_MAP = {
        128: 129,  # Echo Request -> Reply
        129: 128,  # Echo Reply -> Request
        133: 134,  # Router Solicit -> Advert
        134: 133,  # Router Advert -> Solicit
        135: 136,  # Neighbor Solicit -> Advert
        136: 135,  # Neighbor Advert -> Solicit
        130: 131,  # Multicast Listener Query -> Report
        131: 130,  # Multicast Report -> Listener Query
        139: 140,  # Node Information Query -> Response
        140: 139,  # Node Information Response -> Query
        144: 145,  # Home Agent Address Discovery Request -> Reply
        145: 144,  # Home Agent Address Discovery Reply -> Request
    }

    @staticmethod
    def compute(
        source_ip: str,
        dest_ip: str,
        source_port: int | str,
        dest_port: int | str,
        protocol: int | str,
        seed: int | str = 0,
    ) -> str | None:
        """
        Compute the Community ID flow hash.

        Args:
            source_ip (str): Source IP address (IPv4 or IPv6)
            dest_ip (str): Destination IP address (IPv4 or IPv6)
            source_port (Union[int, str]): Source port
            dest_port (Union[int, str]): Destination port
            protocol (Union[int, str]): IANA protocol number
            seed (Union[int, str]): Seed for the hash (default 0)

        Returns:
            Optional[str]: The Community ID string (e.g., '1:HashValue') or None on error
        """
        try:
            # Convert inputs to correct types
            src_p = int(source_port)
            dst_p = int(dest_port)
            proto = int(protocol)
            seed_val = int(seed)

            # Parse IP addresses to packed binary
            try:
                src_packed = socket.inet_pton(socket.AF_INET, source_ip)
                src_is_v6 = False
            except OSError:
                try:
                    src_packed = socket.inet_pton(socket.AF_INET6, source_ip)
                    src_is_v6 = True
                except OSError:
                    return None  # Invalid Source IP

            try:
                dst_packed = socket.inet_pton(socket.AF_INET, dest_ip)
                dst_is_v6 = False
            except OSError:
                try:
                    dst_packed = socket.inet_pton(socket.AF_INET6, dest_ip)
                    dst_is_v6 = True
                except OSError:
                    return None  # Invalid Dest IP

            if src_is_v6 != dst_is_v6:
                return None  # IP version mismatch

            # Handle ICMP special cases for one-way flows
            is_one_way = False
            if proto == 1 or proto == 58:
                if not src_is_v6:  # IPv4 ICMP
                    if src_p not in CommunityID.ICMP4_MAP:
                        is_one_way = True
                else:  # IPv6 ICMPv6
                    if src_p not in CommunityID.ICMP6_MAP:
                        is_one_way = True
                    proto = 58  # Ensure proto is 58 for IPv6 ICMP

            # Order the tuple
            # Logic: if not one-way, sort by (IP, Port) to ensure direction independence
            # Compare IPs as bytes
            # direction_independent = True

            # Comparison logic from Ruby:
            # if !( is_one_way || ((sip <=> dip) == -1) || ((sip == dip) && ((sport <=> dport) < 1)) )
            #   flip

            should_flip = False
            if not is_one_way:
                # Compare IPs
                if src_packed < dst_packed:
                    should_flip = False
                elif src_packed > dst_packed:
                    should_flip = True
                else:
                    # IPs equal, compare ports
                    if src_p < dst_p:
                        should_flip = False
                    else:
                        should_flip = True

            if should_flip:
                sip = dst_packed
                sport = dst_p
                dip = src_packed
                dport = src_p
            else:
                sip = src_packed
                sport = src_p
                dip = dst_packed
                dport = dst_p

            # Hash calculation
            # ruby: hash.update([@comm_id_seed].pack('n')) # 2-byte seed
            # ruby: hash.update(sip)
            # ruby: hash.update(dip)
            # ruby: hash.update([protocol].pack('C')) # 1 byte
            # ruby: hash.update([0].pack('C')) # 1 byte padding
            # ruby: hash.update(sport) # 2 bytes
            # ruby: hash.update(dport) # 2 bytes

            ctx = hashlib.sha1()

            # Seed (2 bytes, network order)
            ctx.update(struct.pack("!H", seed_val))

            # IPs
            ctx.update(sip)
            ctx.update(dip)

            # Protocol (1 byte) + Padding (1 byte)
            ctx.update(struct.pack("!BB", proto, 0))

            # Ports (2 bytes each, network order)
            ctx.update(struct.pack("!HH", sport, dport))

            digest = ctx.digest()
            b64 = base64.b64encode(digest).decode("ascii")

            return CommunityID.VERSION + b64

        except Exception:
            return None

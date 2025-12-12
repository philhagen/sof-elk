# SOF-ELK® Processor: Transport Flags
# (C)2025 Lewes Technology Consulting, LLC
#
# Ported from tcp_flags_expand.rb and tcp_flags_to_array.rb

class Transport:
    TCP_FLAGS_MAP = [
        ("fin", 0x01),
        ("syn", 0x02),
        ("rst", 0x04),
        ("psh", 0x08),
        ("ack", 0x10),
        ("urg", 0x20),
        ("ece", 0x40),
        ("cwr", 0x80)
    ]
    
    @staticmethod
    def expand_tcp_flags(value, source_type='int'):
        """
        Expand TCP flags into Integer, Hex, and Array formats.
        
        Args:
            value: The flag value (int, string, or list[string])
            source_type (str): 'int', 'str', or 'arr'
            
        Returns:
            dict: {
                "tcp_control_bits": int,
                "tcp_flags": list[str],
                "tcp_flags_hex": str
            }
        """
        int_val = 0
        
        if source_type == 'int':
            try:
                int_val = int(value)
            except (ValueError, TypeError):
                int_val = 0
                
        elif source_type == 'arr':
            # Arrays like ["S", "A"] or ["Syn", "Ack"] -> extract first char
            # Ruby: tcp_flags.each { |flag| tcp_flags_str += "#{flag[0].upcase}" }
            if value and isinstance(value, list):
                temp_str = ""
                for flag in value:
                    if flag:
                        temp_str += str(flag)[0].upper()
                # Use string logic
                int_val = Transport._str_to_int(temp_str)
                
        elif source_type == 'str':
            if value:
                int_val = Transport._str_to_int(str(value).upper())
                
        # Construct output
        flags_arr = []
        for name, mask in Transport.TCP_FLAGS_MAP:
             if (int_val & mask) != 0:
                 flags_arr.append(name)
        
        flags_hex = "0x" + hex(int_val)[2:].upper()
        
        return {
            "tcp_control_bits": int_val,
            "tcp_flags": flags_arr,
            "tcp_flags_hex": flags_hex
        }
        
    @staticmethod
    def _str_to_int(flag_str):
        # Ruby logic:
        # tcp_flags_int += 1 if tcp_flags_str.include?("F")
        # ...
        
        val = 0
        if "F" in flag_str: val += 1
        if "S" in flag_str: val += 2
        if "R" in flag_str: val += 4
        if "P" in flag_str: val += 8
        if "A" in flag_str: val += 16
        if "U" in flag_str: val += 32
        if "E" in flag_str: val += 64
        if "C" in flag_str: val += 128
        return val

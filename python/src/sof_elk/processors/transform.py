# SOF-ELK® Processor: Data Transformations
# (C)2025 Lewes Technology Consulting, LLC
#
# Ported from hex_to_integer.rb, split_gcp_authinfo_fields.rb, 
# split_kv_to_fields.rb, split_kv_multi_to_fields.rb

class Transform:

    @staticmethod
    def hex_to_int(value):
        """
        Convert hex string (0xXX or XX) to integer.
        
        Args:
            value (str): Hex string
            
        Returns:
            int: Integer value, or None if failed
        """
        if value is None:
            return None
        
        if isinstance(value, int):
            return value
            
        try:
            val_str = str(value).strip()
            # Ruby script handles bare hex "ff" and "0xff"
            # Python int(x, 16) handles both "A" and "0xA"
            return int(val_str, 16)
        except ValueError:
            return None

    @staticmethod
    def restructure_gcp_authinfo(authinfo_list, key_field="permission"):
        """
        Restructure GCP authorizationInfo.
        
        Args:
            authinfo_list (list): List of dicts from GCP log
            key_field (str): Field to group by (default 'permission')
            
        Returns:
            dict: { permission_name: [ {resource: ..., granted: ...} ] }
        """
        if not authinfo_list or not isinstance(authinfo_list, list):
            return {}
            
        output = {}
        
        for item in authinfo_list:
            if not isinstance(item, dict): continue
            
            if key_field in item:
                new_key = item[key_field]
                if new_key not in output:
                    output[new_key] = []
                
                new_value = {
                    "resource": item.get("resource"),
                    "granted": item.get("granted")
                }
                
                output[new_key].append(new_value)
                
        return output

    @staticmethod
    def split_kv_to_dict(source_data, key_field="name", val_field="value"):
        """
        Transform [{name:k, value:v}] or {name:k, value:v} to {k:v}.
        
        Args:
            source_data (list or dict): Input data
            key_field (str): Key field name
            val_field (str): Value field name
            
        Returns:
            dict: Flattened dictionary
        """
        output = {}
        
        if isinstance(source_data, list):
            for item in source_data:
                if isinstance(item, dict):
                    k = item.get(key_field)
                    v = item.get(val_field)
                    if k and v is not None and v != "":
                        output[k] = v
                        
        elif isinstance(source_data, dict):
            k = source_data.get(key_field)
            v = source_data.get(val_field)
            if k and v is not None and v != "":
                output[k] = v
                
        return output

    @staticmethod
    def split_kv_multi_to_nested(source_data, key_field="name"):
        """
        Transform [{name:k, val1:v1, val2:v2}] to {k: {val1:v1, val2:v2}}.
        
        Args:
            source_data (list): List of dicts
            key_field (str): Field to use as the top-level key
            
        Returns:
            dict: Nested dictionary
        """
        output = {}
        
        if not isinstance(source_data, list):
            return {}
            
        for item in source_data:
            if not isinstance(item, dict): continue
            
            # Make a copy to avoid mutating input
            new_value = item.copy()
            
            if key_field in new_value:
                key = new_value.pop(key_field)
                output[key] = new_value
                
        return output

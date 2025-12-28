def xor_data(data):
    """XOR encrypt/decrypt data with key"""
    key = "NYONYOmmm"
    if isinstance(data, str):
        data = data.encode('utf-8')
    key_bytes = key.encode() if isinstance(key, str) else key
    
    xored_bytes = bytearray(len(data))
    for i in range(len(data)):
        xored_bytes[i] = data[i] ^ key_bytes[i % len(key_bytes)]
    
    return bytes(xored_bytes)
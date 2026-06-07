import zlib
import base64

class Compressor:
    @staticmethod
    def compress(input_string: str) -> str:
        """Compresses the input string using zlib and encodes it in base64."""
        # Convert string to bytes, since zlib works with bytes
        input_bytes = input_string.encode('utf-8') # Convert string to bytes
        compressed_data = zlib.compress(input_bytes) # Compress the bytes
        encoded_detail = base64.b64encode(compressed_data).decode('utf-8')  # Encode and convert to string
        return encoded_detail

    @staticmethod
    def decompress(input_encoded: str) -> str:
        """Decompresses the input string using zlib and decodes it from base64."""
        # Decode the Base64 string to bytes
        detail_compressed = base64.b64decode(input_encoded) # Decode the Base64 string to bytes
        decompressed_data = zlib.decompress(detail_compressed) # Decompress the bytes
        # Convert bytes back to string
        return decompressed_data.decode('utf-8')

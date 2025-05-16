import ecdsa
import hashlib
import base58


class CryptoWallet:
    def __init__(self):
        self.private_key, self.public_key = self.generate_keys()
        self.wallet_address = self.generate_wallet_address(self.public_key)

    def generate_keys(self):
        private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        public_key = private_key.get_verifying_key()
        return private_key, public_key

    def generate_wallet_address(self, public_key):
        """Generate a Bitcoin-like address from the public key."""
        # Get the public key in compressed format (33 bytes)
        public_key_bytes = public_key.to_string("compressed")

        # Perform SHA-256 hashing on the public key
        sha256_hash = hashlib.sha256(public_key_bytes).digest()

        # Perform RIPEMD-160 hashing on the result
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

        # Add version byte (0x00 for Bitcoin mainnet)
        versioned_payload = b'\x00' + ripemd160_hash

        # Perform double SHA-256 hash to get the checksum
        checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]

        # Append the checksum to the versioned payload
        address_bytes = versioned_payload + checksum

        # Convert the result into a Base58Check-encoded string
        address = base58.b58encode(address_bytes)

        return address.decode()



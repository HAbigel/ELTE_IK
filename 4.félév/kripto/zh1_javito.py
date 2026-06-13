# flake8: noqa
from functools import reduce
from operator import xor

################################
###   1. Feladat (8 pont)    ###
################################

LFSR_COEFFS = [1, 0, 0, 0, 1, 1, 0, 1]
CIPHERTEXT  = bytes([7, 50, 106, 6, 93, 207, 200, 128,
                     153, 192, 3, 119, 66, 234, 4, 124,
                     180, 40, 248, 0, 16, 22, 253, 104])
KNOWN_PREFIX = b"lfsr tit"

def lfsr(seed: list[int], coeffs: list[int]) -> int:
    state = seed
    while True:
        yield state[-1]
        t = reduce(xor, [i*j for i, j in zip(state, coeffs)])
        state = [t] + state[:-1]

def generate_keystream(seed: list[int], coeffs: list[int], n_bytes: int) -> bytes:
    state = seed
    kulcs = []
    stream = lfsr(state, coeffs)

    for i in range(n_bytes):
        byte = 0

        for position in range(8):
            bit = next(stream)
            byte |= (bit << position)

        kulcs.append(byte)
    return bytes(kulcs)


def find_seed(ct: bytes, known_prefix: bytes, coeffs: list[int]) -> list[int]:
    lenCoeffs = len(coeffs)

    for i in range(2**lenCoeffs):
        seed = [(i >> j) & 1 for j in range(lenCoeffs)]

        keystream = generate_keystream(seed, coeffs, len(known_prefix))
        plainText = bytes(c ^ k for c, k in zip(ct[:len(known_prefix)], keystream))

        if plainText == known_prefix:
            return seed      
    # raise ValueError("no seed ?")

def decrypt(ct: bytes, seed: list[int], coeffs: list[int]) -> bytes:
    keystream = generate_keystream(seed, coeffs, len(ct))
    plainText = [c ^ k for c, k in zip(ct, keystream)]
    return bytes(plainText)



seed = find_seed(CIPHERTEXT, KNOWN_PREFIX, LFSR_COEFFS)
pt   = decrypt(CIPHERTEXT, seed, LFSR_COEFFS)
#print(pt[:len(KNOWN_PREFIX)])
#print(KNOWN_PREFIX)

assert pt[:len(KNOWN_PREFIX)] == KNOWN_PREFIX
assert pt == b"lfsr titkositas torhetok"
print("1. feladat: OK")


################################
###   2. Feladat (15 pont)   ###
################################
import hashlib

TOY_BLOCK_SIZE = 8
TOY_IV         = b'Kriptogr'
KNOWN_HASH = bytes([14, 173, 14, 194, 38, 102, 233, 253])
COMMAND    = b"muvelet=olvas"
EXTENSION  = b";muvelet=iras"

def toy_compress(block: bytes, state: bytes) -> bytes:
    assert len(block) == TOY_BLOCK_SIZE and len(state) == TOY_BLOCK_SIZE
    return hashlib.sha256(bytes(a ^ b for a, b in zip(state, block))).digest()[:TOY_BLOCK_SIZE]

def md_pad(message: bytes, block_size: int) -> bytes:
    hossz = len(message)
    padded = message + b'\x80'
    while (len(padded) + 4) % block_size != 0:
        padded += b'\x00'
    b1 = (hossz >> 24) & 0xFF
    b2 = (hossz >> 16) & 0xFF
    b3 = (hossz >> 8) & 0xFF
    b4 = hossz & 0xFF
    padded += bytes([b1, b2, b3, b4])

    return padded

def merkle_damgard(message: bytes, iv: bytes, compress_fn) -> bytes:
    padded = md_pad(message, TOY_BLOCK_SIZE)
    h = iv
    for i in range(0, len(padded), TOY_BLOCK_SIZE):
        block = padded[i:i + TOY_BLOCK_SIZE]
        h = compress_fn(block, h)
    return h

def length_extension(known_hash: bytes, known_padded_len: int, extension: bytes, compress_fn) -> bytes:
    paddedExtension = md_pad(extension, TOY_BLOCK_SIZE)
    teljesHossz = known_padded_len + len(extension)
    
    b1 = (teljesHossz >> 24) & 0xFF
    b2 = (teljesHossz >> 16) & 0xFF
    b3 = (teljesHossz >> 8) & 0xFF
    b4 = teljesHossz & 0xFF
    hossz = bytes([b1, b2, b3, b4])
    paddedExtension = paddedExtension[:-4] + hossz
    state = known_hash
    
    for i in range(0, len(paddedExtension), TOY_BLOCK_SIZE):
        block = paddedExtension[i:i + TOY_BLOCK_SIZE]
        state = compress_fn(block, state)
        
    return state

known_padded_len = len(md_pad(b'?' * 5 + COMMAND, TOY_BLOCK_SIZE))
forged_hash = length_extension(KNOWN_HASH, known_padded_len, EXTENSION, toy_compress)

assert md_pad(b"hello", 8) == b"hello\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05"
assert forged_hash == bytes.fromhex("d3dfe374ec1d8fae")
print("2. feladat: OK")


################################
###   3. Feladat (7 pont)    ###
################################
from math import gcd
from functools import reduce

class SecretSharing:
    def __init__(self, moduli: list[int]) -> None:
        n = len(moduli)
        for i in range(n):
            for j in range(i + 1, n):
                if gcd(moduli[i], moduli[j]) != 1:
                    raise ValueError("A moduli lista elemei nem páronként relatív prímek!")
        self.moduli = moduli

    def share(self, secret: int) -> list[int]:
        return [secret % m for m in self.moduli]

    def bovitett_euklideszi(self, a, b):
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = self.bovitett_euklideszi(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

    def mod_inverse(self, a, m):
        gcd, x, y = self.bovitett_euklideszi(a, m)
        if gcd != 1:
            raise ValueError("nincs inverz")
        return (x % m + m) % m

    def reconstruct(self, shares: list[int], indices: list[int]) -> int:
        kivalasztott = [self.moduli[i] for i in indices]
        m = reduce(lambda x, y: x * y, kivalasztott, 1)
        secret = 0
        for s, k in zip(shares, kivalasztott):
            mi = m // k
            modinv = self.mod_inverse(mi, k)
            secret += s * mi * modinv
            
        return secret % m


ss = SecretSharing([1009, 1013, 1019])
shares = ss.share(1_500_000)
assert shares == [626, 760, 32]
assert ss.reconstruct(shares, [0, 1, 2]) == 1_500_000
assert ss.reconstruct([shares[0], shares[1]], [0, 1]) != 1_500_000
assert ss.reconstruct([shares[0], shares[2]], [0, 2]) != 1_500_000
assert ss.reconstruct([shares[1], shares[2]], [1, 2]) != 1_500_000
try:
    SecretSharing([6, 10, 7])   # 6 és 10 nem relatív prím
    assert False, "Nem dobott ValueError-t"
except ValueError:
    pass
print("3. feladat: OK")

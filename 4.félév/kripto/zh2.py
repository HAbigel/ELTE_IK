# flake8: noqa
################################
###   1. Feladat (12 pont)   ###
################################
import hashlib
# SHA-256: (0x)30 31 30 0d 06 09 60 86 48 01 65 03 04 02 01 05 00 04 20 || H.
DIGEST_INFO_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")

def encode_to_sign(message: bytes, em_length: int) -> bytes:
    h = hashlib.sha256(message).digest()
    T = DIGEST_INFO_SHA256 + h
    PS = em_length - len(T) - 3

    if PS < 8:
        raise ValueError("<8")
    else:
        PS = b"\xff" * PS
        EM = b"\x00\x01" + PS + b"\x00" + T
        return EM


def rsa_sign(message: bytes, n: int, d: int) -> bytes:
    if n.bit_length() % 8 == 0:
        hossz = n.bit_length() // 8
    else:
        hossz = n.bit_length() // 8 + 1

    elkodolt = encode_to_sign(message, hossz)
    konvertalt = int.from_bytes(elkodolt, byteorder='big')
    rsaval = pow(konvertalt, d, n)
    return rsaval.to_bytes(hossz, byteorder='big')


def rsa_verify(message: bytes, signature: bytes, n: int, e: int) -> bool:
    if n.bit_length() % 8 == 0:
        hossz = n.bit_length() // 8
    else:
        hossz = n.bit_length() // 8 + 1
    
    if len(signature) != hossz:
        return False
    
    rsaval = int.from_bytes(signature, byteorder='big')
    visszafejtett = pow(rsaval, e, n)    
    visszakonvertalt = visszafejtett.to_bytes(hossz, byteorder='big')
    ujra = encode_to_sign(message, hossz)
    return ujra == visszakonvertalt



N_TEST = 8108715195442214102569438559004844179109019971411540425443623246846679958955617240930640452187115284631299329407019867698669334065746843976732615876735399
E_TEST = 65537
D_TEST = 6704657944761251506845527046918740577410297743729800938620390010579897467016130113543788742970949373121558932501338387270279692011016096698835955757039465
SIG_TEST = bytes.fromhex(
        '15b375af10beb7ba23949f8b27bc3ecf24d4cb2996b44b1ee56827d7bed500ad'
        '5ce6dae6f1d1d520bf8c519df6aeb7aef6c30ff952403b780acaa3b18c78c51a'
)
msg = b"kriptografia-zh-2026"
sig = rsa_sign(msg, N_TEST, D_TEST)
assert sig == SIG_TEST
assert rsa_verify(msg, sig, N_TEST, E_TEST)
assert not rsa_verify(b"hamis uzenet", sig, N_TEST, E_TEST)
print("1. feladat: OK")


################################
###   2. Feladat (15 pont)   ###
################################
import random

class DSA:
    def __init__(self, p: int, q: int, g: int):
        self.p = p
        self.q = q
        self.g = g
        self.v = None # g ** s mod p

    def sign(self, message: bytes) -> tuple[int, int]:
        s = random.randrange(1, self.q-1)
        self.v = pow(self.g, s, self.p)
        D = int.from_bytes(message, byteorder='big')
        e = random.randrange(1, self.q-1)
        S1 = pow(self.g, e, self.p) % self.q # ((self.g ** e) % self.p) % self.q 
        S2 = (D + s*S1) * pow(e, -1, self.q) % self.q
        return (int(S1), int(S2))


    def verify(self, message: bytes, signature: tuple[int, int]) -> bool:
        D = int.from_bytes(message, byteorder='big')
        S1 = signature[0]
        S2 = signature[1]
        V1 = D * pow(S2, -1, self.q) % self.q # D*S2^-1 mod q
        V2 = S1 * pow(S2, -1, self.q) % self.q # S1 * S2^-1 mod q
        # S1 == (g**V1 * v**V2 mod p) mod q
        return S1 == ((pow(self.g, V1, self.p) * pow(self.v, V2, self.p)) % self.p) % self.q


p = 101604377558152947553994940253514368908626973115702234247578783730068690629096077880853696709782510748991342441305937136733989624405049168980544338771394475348707011512865933931385208483047927854708076482598405028667779554640025313181163154565853864944818752329033924696314371331273351864349464462489411622763
q = 841986204697838195664210718264389234098340758111
g = 41697148679934580195631739602284670768097042194078348701407648538717615232181359621842053829692001884137642722905057203928238950064338617740953666593799002909406224260052088761574232390111035280670981291261285512325267872895303291624627247596187317921006000689636350388611567699604053861756867540036203220963
msg = b"Kriptografia ZH 2026"
dsa = DSA(p, q, g)
signature = dsa.sign(msg)
assert dsa.verify(msg, signature)
assert not dsa.verify(b"Rossz uzenet", signature)
print("2. feladat: OK")


###############################
###   3. Feladat (6 pont)   ###
###############################
import math

def dh_decrypt(k: int, p: int, ct: bytes) -> bytes:
    if p.bit_length() % 8 == 0:
        lenP = p.bit_length() // 8
    else:
        lenP = (p.bit_length() // 8) + 1
    
    konvertalt = k.to_bytes(lenP, byteorder='big')
    
    #session_key = SHA-256(k)[:|ct|]
    hashelt = hashlib.sha256(konvertalt).digest()
    session_key = hashelt[:len(ct)]
    
    pt = bytes(c ^ sk for c, sk in zip(ct, session_key))
    return pt


def dh_attack(g: int, p: int, A: int, B: int, ct: bytes) -> bytes:
    # diszkeret log: g^a kongruens A (mod p)
    m = math.ceil(math.sqrt(p))
    lookup = {}
    aktual = 1
    for j in range(m):
        lookup[aktual] = j
        aktual = (aktual * g) % p
    inv = pow(g, -m, p)
    gamma = A
    a = None
    for i in range(m):
        if gamma in lookup:
            a = i * m + lookup[gamma]
            break
        gamma = (gamma * inv) % p
        
    key = pow(B, a, p)
    return dh_decrypt(key, p, ct)


p = 4185373
ct = bytes.fromhex('1879645c9180a893b38b0f0c69f29bae2d')
assert dh_decrypt(1052393, p, ct) == b"DH nem hitelesit!"
assert dh_attack(2, p, 85804, 2283340, ct) == b"DH nem hitelesit!"
print(f"3. feladat: OK")


###############################
###   4. Feladat (7 pont)   ###
###############################

def icbrt(n: int) -> int:
    """Megkeresi az `n` nemnegatív szám egész köbgyökét: azt a legnagyobb `x`-et, amire x^3 <= n."""
    if n == 0:
        return 0
        
    xnm1 = n
    while True:
        xn = (2 * xnm1 + n // (xnm1 ** 2)) // 3
        if xn >= xnm1:
            break
        xnm1 = xn
        
    while xnm1 > 0 and (xnm1 ** 3) > n:
        xnm1 -= 1
    while ((xnm1 + 1) ** 3) <= n:
        xnm1 += 1
        
    return xnm1


def cube_attack(ct_list: list[int], n_list: list[int]) -> bytes:
    szorzat = 1
    for n in n_list:
        szorzat *= n
        
    mkob = 0
    for c, n in zip(ct_list, n_list):
        tobbiSzorzata = szorzat // n
        modinv = pow(tobbiSzorzata, -1, n)
        mkob = (mkob + c * tobbiSzorzata * modinv) % szorzat
        
    m = icbrt(mkob)
    
    return m.to_bytes(4, byteorder='big')


RSA_E  = 3
RSA_N  = [16231793829986840849, 14829442329739479713, 13368367467644882687]
RSA_CT  = [15738650466343245644,  5784448726824874702,  3618203670095455692]
assert cube_attack(RSA_CT, RSA_N) == b"ZH02"
print("4. feladat: OK")

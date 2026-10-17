import hashlib
import secrets
import base58
import bech32
import hmac
from typing import Tuple, List, Optional

# secp256k1椭圆曲线参数
P = 2 ** 256 - 2 ** 32 - 2 ** 9 - 2 ** 8 - 2 ** 7 - 2 ** 6 - 2 ** 4 - 1
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


class BitcoinKeyGenerator:
    """比特币密钥和地址生成器"""

    def __init__(self, testnet: bool = False):
        """
        初始化比特币密钥生成器
        testnet: 是否使用测试网络
        """
        self.testnet = testnet
        self.private_key = None
        self.public_key = None
        self.compressed_public_key = None

    def generate_private_key(self) -> int:
        """生成随机的secp256k1私钥"""
        # 私钥必须是1到N-1之间的整数
        while True:
            private_key = secrets.randbelow(N - 1) + 1
            # 确保私钥有足够的熵
            if private_key.bit_length() >= 256:
                self.private_key = private_key
                return private_key

    def mod_inverse(self, a: int, n: int = P) -> int:
        """模逆运算，使用扩展欧几里得算法"""
        if a == 0:
            return 0
        lm, hm = 1, 0
        low, high = a % n, n
        while low > 1:
            ratio = high // low
            nm, new = hm - lm * ratio, high - low * ratio
            lm, low, hm, high = nm, new, lm, low
        return lm % n

    def elliptic_curve_add(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> Tuple[int, int]:
        """椭圆曲线点加法"""
        if point1 is None:
            return point2
        if point2 is None:
            return point1

        x1, y1 = point1
        x2, y2 = point2

        if x1 == x2:
            if y1 != y2:
                return None  # 点互为逆元，结果为无穷远点
            # 点加倍
            s = (3 * x1 * x1) * self.mod_inverse(2 * y1, P) % P
        else:
            # 点相加
            s = (y2 - y1) * self.mod_inverse(x2 - x1, P) % P

        x3 = (s * s - x1 - x2) % P
        y3 = (s * (x1 - x3) - y1) % P

        return (x3, y3)

    def elliptic_curve_multiply(self, k: int, point: Tuple[int, int]) -> Tuple[int, int]:
        """椭圆曲线标量乘法"""
        result = None
        addend = point

        while k:
            if k & 1:
                result = self.elliptic_curve_add(result, addend)
            addend = self.elliptic_curve_add(addend, addend)
            k >>= 1

        return result

    def generate_public_key(self, compressed: bool = True) -> bytes:
        """从私钥生成公钥"""
        if self.private_key is None:
            raise ValueError("请先生成私钥")

        # 计算公钥点 K = k * G
        public_key_point = self.elliptic_curve_multiply(self.private_key, (Gx, Gy))

        if public_key_point is None:
            raise ValueError("公钥生成失败")

        x, y = public_key_point

        if compressed:
            # 压缩公钥格式：前缀(02/03) + x坐标(32字节)
            prefix = b'\x02' if y % 2 == 0 else b'\x03'
            public_key = prefix + x.to_bytes(32, 'big')
        else:
            # 非压缩公钥格式：前缀04 + x坐标 + y坐标
            prefix = b'\x04'
            public_key = prefix + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')

        self.public_key = public_key
        self.compressed_public_key = compressed
        return public_key

    def hash160(self, data: bytes) -> bytes:
        """计算RIPEMD160(SHA256(data))"""
        sha256_hash = hashlib.sha256(data).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
        return ripemd160_hash

    def double_sha256(self, data: bytes) -> bytes:
        """计算双重SHA256哈希"""
        return hashlib.sha256(hashlib.sha256(data).digest()).digest()

    def create_p2pkh_address(self) -> str:
        """生成P2PKH地址（Base58Check编码）"""
        if self.public_key is None:
            raise ValueError("请先生成公钥")

        # 1. 计算公钥哈希
        pubkey_hash = self.hash160(self.public_key)

        # 2. 添加版本字节（主网：0x00，测试网：0x6F）
        version_byte = b'\x6f' if self.testnet else b'\x00'
        payload = version_byte + pubkey_hash

        # 3. 计算校验和（前4字节）
        checksum = self.double_sha256(payload)[:4]

        # 4. Base58编码
        address_bytes = payload + checksum
        address = base58.b58encode(address_bytes).decode('ascii')

        return address

    def create_p2wpkh_address(self) -> str:
        """生成P2WPKH地址（Bech32编码）"""
        if self.public_key is None:
            raise ValueError("请先生成公钥")

        # 1. 计算见证程序（公钥哈希）
        witness_program = self.hash160(self.public_key)

        # 2. Bech32编码
        hrp = "tb" if self.testnet else "bc"  # 人类可读部分
        version = 0  # P2WPKH版本号为0

        # 将见证程序转换为5位数组
        data = bech32.convertbits(witness_program, 8, 5)
        if data is None:
            raise ValueError("数据转换失败")

        # 生成Bech32地址
        address = bech32.bech32_encode(hrp, [version] + data)

        return address

    def create_p2tr_address(self) -> str:
        """生成P2TR地址（Bech32m编码）- 简化版"""
        if self.public_key is None:
            raise ValueError("请先生成公钥")

        # 注意：完整的P2TR需要更复杂的密钥调整，这里是简化实现
        # 实际中应该使用BIP340的Schnorr签名和密钥调整

        # 1. 计算公钥的x坐标哈希作为见证程序
        x_coord = int.from_bytes(self.public_key[1:33], 'big')
        witness_program = hashlib.sha256(x_coord.to_bytes(32, 'big')).digest()

        # 2. Bech32m编码（版本1）
        hrp = "tb" if self.testnet else "bc"
        version = 1

        # 转换为5位数组
        data = bech32.convertbits(witness_program, 8, 5)
        if data is None:
            raise ValueError("数据转换失败")

        # 生成Bech32m地址（简化实现）
        address = bech32.bech32_encode(hrp, [version] + data)

        return address

    def wif_private_key(self, compressed: bool = True) -> str:
        """生成WIF格式的私钥"""
        if self.private_key is None:
            raise ValueError("请先生成私钥")

        # 1. 添加版本字节（主网：0x80，测试网：0xEF）
        version_byte = b'\xef' if self.testnet else b'\x80'
        private_key_bytes = self.private_key.to_bytes(32, 'big')
        payload = version_byte + private_key_bytes

        # 2. 如果使用压缩公钥，添加压缩标志
        if compressed:
            payload += b'\x01'

        # 3. 计算校验和
        checksum = self.double_sha256(payload)[:4]

        # 4. Base58编码
        wif_bytes = payload + checksum
        wif = base58.b58encode(wif_bytes).decode('ascii')

        return wif

    def validate_address(self, address: str, address_type: str) -> bool:
        """验证地址的有效性"""
        try:
            if address_type == "p2pkh":
                # Base58Check验证
                decoded = base58.b58decode(address)
                if len(decoded) != 25:  # 版本(1) + 哈希(20) + 校验和(4)
                    return False

                payload, checksum = decoded[:-4], decoded[-4:]
                calculated_checksum = self.double_sha256(payload)[:4]
                return checksum == calculated_checksum

            elif address_type in ["p2wpkh", "p2tr"]:
                # Bech32验证
                hrp, data = bech32.bech32_decode(address)
                if hrp is None or data is None:
                    return False

                # 检查人类可读部分
                expected_hrp = "tb" if self.testnet else "bc"
                return hrp == expected_hrp

            else:
                return False

        except Exception:
            return False

    def get_key_info(self) -> dict:
        """获取完整的密钥信息"""
        if self.private_key is None or self.public_key is None:
            raise ValueError("请先生成密钥对")

        return {
            'private_key_hex': hex(self.private_key),
            'private_key_wif': self.wif_private_key(compressed=True),
            'public_key_hex': self.public_key.hex(),
            'public_key_compressed': self.compressed_public_key,
            'p2pkh_address': self.create_p2pkh_address(),
            'p2wpkh_address': self.create_p2wpkh_address(),
            'p2tr_address': self.create_p2tr_address(),
            'network': 'testnet' if self.testnet else 'mainnet'
        }


def demonstrate_bitcoin_address_generation():
    """演示比特币地址生成过程"""
    print("=" * 70)
    print("比特币密钥和地址生成实验")
    print("=" * 70)

    # 1. 生成测试网地址
    print("\n1. 测试网地址生成")
    testnet_gen = BitcoinKeyGenerator(testnet=True)

    # 生成私钥
    private_key = testnet_gen.generate_private_key()
    print(f"生成私钥: {hex(private_key)[:20]}...")

    # 生成公钥（压缩格式）
    public_key = testnet_gen.generate_public_key(compressed=True)
    print(f"生成压缩公钥: {public_key.hex()[:20]}...")

    # 生成各种地址格式
    p2pkh_addr = testnet_gen.create_p2pkh_address()
    p2wpkh_addr = testnet_gen.create_p2wpkh_address()
    p2tr_addr = testnet_gen.create_p2tr_address()
    wif = testnet_gen.wif_private_key()

    print(f"P2PKH地址 (Base58Check): {p2pkh_addr}")
    print(f"P2WPKH地址 (Bech32):    {p2wpkh_addr}")
    print(f"P2TR地址 (Bech32m):     {p2tr_addr}")
    print(f"WIF私钥:                {wif}")

    # 验证地址
    p2pkh_valid = testnet_gen.validate_address(p2pkh_addr, "p2pkh")
    p2wpkh_valid = testnet_gen.validate_address(p2wpkh_addr, "p2wpkh")

    print(f"P2PKH地址验证: {'有效' if p2pkh_valid else '无效'}")
    print(f"P2WPKH地址验证: {'有效' if p2wpkh_valid else '无效'}")

    # 2. 生成主网地址
    print("\n2. 主网地址生成")
    mainnet_gen = BitcoinKeyGenerator(testnet=False)

    mainnet_gen.generate_private_key()
    mainnet_gen.generate_public_key(compressed=True)

    mainnet_p2pkh = mainnet_gen.create_p2pkh_address()
    mainnet_p2wpkh = mainnet_gen.create_p2wpkh_address()
    mainnet_wif = mainnet_gen.wif_private_key()

    print(f"P2PKH地址: {mainnet_p2pkh}")
    print(f"P2WPKH地址: {mainnet_p2wpkh}")
    print(f"WIF私钥:   {mainnet_wif}")

    # 3. 地址格式对比
    print("\n3. 地址格式对比")
    formats_info = [
        ("P2PKH", "1开头", "Base58Check", "传统地址", "支持广泛"),
        ("P2WPKH", "bc1/tb1开头", "Bech32", "原生隔离见证", "手续费低"),
        ("P2TR", "bc1p/tb1p开头", "Bech32m", "Taproot", "隐私性好")
    ]

    for name, prefix, encoding, features, advantages in formats_info:
        print(f"   {name:8} {prefix:12} {encoding:12} {features:15} {advantages}")

    # 4. 安全性验证
    print("\n4. 安全性验证")

    # 测试无效地址验证
    invalid_address = "1InvalidBitcoinAddress123456789"
    is_valid = testnet_gen.validate_address(invalid_address, "p2pkh")
    print(f"无效地址验证: {' 拒绝' if not is_valid else '通过（异常）'}")

    # 测试修改校验和
    try:
        modified_addr = p2pkh_addr[:-1] + 'X'  # 修改最后一个字符
        is_valid = testnet_gen.validate_address(modified_addr, "p2pkh")
        print(f"篡改地址验证: {'拒绝' if not is_valid else '通过（异常）'}")
    except:
        print(f"篡改地址验证: 拒绝（解码失败）")

    # 5. 批量生成示例
    print("\n5. 批量地址生成示例")
    print("生成3个测试网地址:")

    for i in range(3):
        gen = BitcoinKeyGenerator(testnet=True)
        gen.generate_private_key()
        gen.generate_public_key()

        info = gen.get_key_info()
        print(f"地址{i + 1}: {info['p2pkh_address']}")

    # 7. 技术细节
    print("\n6. 技术细节")
    print("secp256k1曲线参数:")
    print(f"质数P: 2²⁵⁶ - 2³² - 2⁹ - 2⁸ - 2⁷ - 2⁶ - 2⁴ - 1")
    print(f"阶N: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141")
    print(f"生成点G: (0x{Gx:064x}, 0x{Gy:064x})")


def advanced_crypto_demo():
    """高级密码学演示"""
    print("\n\n" + "=" * 70)
    print("高级密码学演示")
    print("=" * 70)

    # 密钥派生演示
    print("\n1. 密钥派生演示")
    seed = secrets.token_bytes(32)
    print(f"随机种子: {seed.hex()}")

    # 简单密钥派生函数
    def simple_kdf(seed: bytes, index: int) -> int:
        """简单的密钥派生函数"""
        data = seed + index.to_bytes(4, 'big')
        derived = hashlib.sha256(data).digest()
        return int.from_bytes(derived, 'big') % (N - 1) + 1

    # 派生多个密钥
    print("派生密钥:")
    for i in range(3):
        derived_key = simple_kdf(seed, i)
        gen = BitcoinKeyGenerator(testnet=True)
        gen.private_key = derived_key
        gen.generate_public_key()
        addr = gen.create_p2pkh_address()
        print(f"索引{i}: {addr}")

    # 压缩vs非压缩公钥
    print("\n2. 压缩vs非压缩公钥")
    gen = BitcoinKeyGenerator(testnet=True)
    gen.generate_private_key()

    # 压缩公钥
    compressed_pubkey = gen.generate_public_key(compressed=True)
    compressed_addr = gen.create_p2pkh_address()

    # 非压缩公钥
    uncompressed_pubkey = gen.generate_public_key(compressed=False)
    uncompressed_addr = gen.create_p2pkh_address()

    print(f"压缩公钥长度: {len(compressed_pubkey)} 字节")
    print(f"非压缩公钥长度: {len(uncompressed_pubkey)} 字节")
    print(f"压缩地址: {compressed_addr}")
    print(f"非压缩地址: {uncompressed_addr}")
    print(f"地址相同: {compressed_addr == uncompressed_addr}")


if __name__ == "__main__":
    # 运行主要演示
    demonstrate_bitcoin_address_generation()

    # 运行高级演示
    advanced_crypto_demo()

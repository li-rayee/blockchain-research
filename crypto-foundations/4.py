import hashlib
import secrets
import struct
import time
from typing import List, Dict, Tuple, Optional
import bech32
import base58

# secp256k1参数
P = 2 ** 256 - 2 ** 32 - 2 ** 9 - 2 ** 8 - 2 ** 7 - 2 ** 6 - 2 ** 4 - 1
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

class BitcoinTransaction:
    """比特币交易构建和签名类"""

    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.version = 1
        self.locktime = 0
        self.inputs = []
        self.outputs = []

    def mod_inverse(self, a: int, n: int = P) -> int:
        """计算模逆运算，用于椭圆曲线签名中的点乘法"""
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
        """执行椭圆曲线上的点加法"""
        if point1 is None:
            return point2
        if point2 is None:
            return point1

        x1, y1 = point1
        x2, y2 = point2

        if x1 == x2:
            if y1 != y2:
                return None
            s = (3 * x1 * x1) * self.mod_inverse(2 * y1, P) % P
        else:
            s = (y2 - y1) * self.mod_inverse(x2 - x1, P) % P

        x3 = (s * s - x1 - x2) % P
        y3 = (s * (x1 - x3) - y1) % P

        return (x3, y3)

    def elliptic_curve_multiply(self, k: int, point: Tuple[int, int]) -> Tuple[int, int]:
        """执行椭圆曲线上的标量乘法"""
        result = None
        addend = point

        while k:
            if k & 1:
                result = self.elliptic_curve_add(result, addend)
            addend = self.elliptic_curve_add(addend, addend)
            k >>= 1

        return result

    def hash160(self, data: bytes) -> bytes:
        """计算RIPEMD160(SHA256(data))哈希，用于生成公钥哈希"""
        sha256_hash = hashlib.sha256(data).digest()
        return hashlib.new('ripemd160', sha256_hash).digest()

    def double_sha256(self, data: bytes) -> bytes:
        """计算双重SHA256哈希，用于生成签名哈希和交易ID"""
        return hashlib.sha256(hashlib.sha256(data).digest()).digest()

    def create_p2wpkh_script(self, pubkey_hash: bytes) -> bytes:
        """创建P2WPKH锁定脚本"""
        # P2WPKH: 0 <20字节公钥哈希>
        return bytes([0x00, 0x14]) + pubkey_hash

    def create_p2pkh_script(self, pubkey_hash: bytes) -> bytes:
        """创建P2PKH锁定脚本"""
        # P2PKH: OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
        return bytes([0x76, 0xA9, 0x14]) + pubkey_hash + bytes([0x88, 0xAC])

    def encode_varint(self, n: int) -> bytes:
        """编码变长整数，用于序列化交易中的输入和输出数量"""
        if n < 0xfd:
            return bytes([n])
        elif n <= 0xffff:
            return b'\xfd' + struct.pack('<H', n)
        elif n <= 0xffffffff:
            return b'\xfe' + struct.pack('<I', n)
        else:
            return b'\xff' + struct.pack('<Q', n)

    def add_input(self, prev_txid: str, prev_index: int, amount: int, script_pubkey: bytes, sequence: int = 0xffffffff):
        """添加交易输入"""
        # 反转TXID（小端序）
        prev_txid_bytes = bytes.fromhex(prev_txid)[::-1]

        self.inputs.append({
            'prev_txid': prev_txid_bytes,
            'prev_index': prev_index,
            'script_sig': b'',  # 初始为空，签名时填充
            'sequence': sequence,
            'amount': amount,
            'script_pubkey': script_pubkey,
            'witness': []  # 见证数据（用于隔离见证）
        })

    def add_output(self, address: str, amount: int):
        """添加交易输出"""
        # 解码地址获取脚本公钥
        if address.startswith('tb1') or address.startswith('bc1'):
            # Bech32地址 (P2WPKH)
            hrp, data = bech32.bech32_decode(address)
            if hrp and data:
                witness_version = data[0]
                witness_program = bech32.convertbits(data[1:], 5, 8, False)
                if witness_program and len(witness_program) == 20:
                    script_pubkey = self.create_p2wpkh_script(bytes(witness_program))
                else:
                    raise ValueError("无效的P2WPKH地址")
            else:
                raise ValueError("无效的Bech32地址")
        else:
            # Base58Check地址 (P2PKH)
            try:
                decoded = base58.b58decode(address)
                # 去掉版本字节和校验和
                if len(decoded) != 25:
                    raise ValueError("Base58Check地址长度无效")
                pubkey_hash = decoded[1:21]  # 版本(1) + 公钥哈希(20)
                script_pubkey = self.create_p2pkh_script(pubkey_hash)
            except Exception as e:
                raise ValueError(f"无效的Base58Check地址: {e}")

        self.outputs.append({
            'amount': amount,
            'script_pubkey': script_pubkey
        })

    def create_signature_hash(self, input_index: int, script_pubkey: bytes, sighash_type: int = 0x01) -> bytes:
        """创建签名哈希，用于隔离见证签名"""
        # 版本
        data = struct.pack('<I', self.version)

        # 输入哈希序列
        hash_prevouts = hashlib.sha256(b''.join(
            inp['prev_txid'] + struct.pack('<I', inp['prev_index'])
            for inp in self.inputs
        )).digest()
        hash_sequence = hashlib.sha256(b''.join(
            struct.pack('<I', inp['sequence']) for inp in self.inputs
        )).digest()

        data += hash_prevouts
        data += hash_sequence

        # 当前输入
        input_data = self.inputs[input_index]
        data += input_data['prev_txid']
        data += struct.pack('<I', input_data['prev_index'])
        data += self.encode_varint(len(script_pubkey)) + script_pubkey
        data += struct.pack('<Q', input_data['amount'])
        data += struct.pack('<I', input_data['sequence'])

        # 输出哈希序列
        hash_outputs = hashlib.sha256(b''.join(
            struct.pack('<Q', out['amount']) + self.encode_varint(len(out['script_pubkey'])) + out['script_pubkey']
            for out in self.outputs
        )).digest()

        data += hash_outputs

        # 锁定时间和哈希类型
        data += struct.pack('<I', self.locktime)
        data += struct.pack('<I', sighash_type)

        # 双重SHA256
        return self.double_sha256(data)

    def ecdsa_sign(self, private_key: int, message_hash: bytes) -> Tuple[int, int]:
        """使用ECDSA算法对消息哈希进行签名"""
        z = int.from_bytes(message_hash, 'big')
        k = secrets.randbelow(N - 1) + 1  # 临时密钥

        # 计算临时公钥点
        r_point = self.elliptic_curve_multiply(k, (Gx, Gy))
        r = r_point[0] % N

        # 计算s值
        s = (self.mod_inverse(k, N) * (z + r * private_key)) % N

        # 低S值规范化（BIP62）
        if s > N // 2:
            s = N - s

        return (r, s)

    def der_encode_signature(self, r: int, s: int) -> bytes:
        """将ECDSA签名编码为DER格式"""
        # 编码r
        r_bytes = r.to_bytes(32, 'big').lstrip(b'\x00')
        if r_bytes[0] & 0x80:
            r_bytes = b'\x00' + r_bytes

        # 编码s
        s_bytes = s.to_bytes(32, 'big').lstrip(b'\x00')
        if s_bytes[0] & 0x80:
            s_bytes = b'\x00' + s_bytes

        # DER编码
        der = bytes([0x30])  # SEQUENCE
        der += bytes([4 + len(r_bytes) + len(s_bytes)])  # 长度

        der += bytes([0x02, len(r_bytes)]) + r_bytes  # INTEGER r
        der += bytes([0x02, len(s_bytes)]) + s_bytes  # INTEGER s

        return der

    def sign_input(self, input_index: int, private_key: int, public_key: bytes, sighash_type: int = 0x01):
        """对交易输入进行签名"""
        # 对于P2WPKH，使用P2PKH脚本进行签名
        pubkey_hash = self.hash160(public_key)
        script_code = self.create_p2pkh_script(pubkey_hash)

        # 创建签名哈希
        sighash = self.create_signature_hash(input_index, script_code, sighash_type)

        # ECDSA签名
        r, s = self.ecdsa_sign(private_key, sighash)

        # DER编码签名并添加哈希类型
        der_sig = self.der_encode_signature(r, s) + bytes([sighash_type])

        # 构建见证数据
        self.inputs[input_index]['witness'] = [
            der_sig,  # 签名
            public_key  # 公钥
        ]

        # 对于隔离见证，script_sig为空
        self.inputs[input_index]['script_sig'] = b''

    def serialize_transaction(self) -> bytes:
        """序列化交易，生成原始交易数据"""
        # 版本
        data = struct.pack('<I', self.version)

        # 标记和标志（隔离见证）
        data += b'\x00\x01'  # 标记: 0x00, 标志: 0x01

        # 输入数量
        data += self.encode_varint(len(self.inputs))

        # 输入
        for inp in self.inputs:
            data += inp['prev_txid']  # 小端序
            data += struct.pack('<I', inp['prev_index'])
            data += self.encode_varint(len(inp['script_sig'])) + inp['script_sig']
            data += struct.pack('<I', inp['sequence'])

        # 输出数量
        data += self.encode_varint(len(self.outputs))

        # 输出
        for out in self.outputs:
            data += struct.pack('<Q', out['amount'])
            data += self.encode_varint(len(out['script_pubkey'])) + out['script_pubkey']

        # 见证数据
        for inp in self.inputs:
            data += self.encode_varint(len(inp['witness']))
            for item in inp['witness']:
                data += self.encode_varint(len(item)) + item

        # 锁定时间
        data += struct.pack('<I', self.locktime)

        return data

    def calculate_txid(self) -> str:
        """计算交易ID（不含见证数据），用于标识交易"""
        # 版本
        data = struct.pack('<I', self.version)

        # 输入数量
        data += self.encode_varint(len(self.inputs))

        # 输入（不含见证）
        for inp in self.inputs:
            data += inp['prev_txid']
            data += struct.pack('<I', inp['prev_index'])
            data += self.encode_varint(len(inp['script_sig'])) + inp['script_sig']
            data += struct.pack('<I', inp['sequence'])

        # 输出数量
        data += self.encode_varint(len(self.outputs))

        # 输出
        for out in self.outputs:
            data += struct.pack('<Q', out['amount'])
            data += self.encode_varint(len(out['script_pubkey'])) + out['script_pubkey']

        # 锁定时间
        data += struct.pack('<I', self.locktime)

        # 交易ID是双重SHA256的逆序
        tx_hash = self.double_sha256(data)
        return tx_hash[::-1].hex()

    def calculate_vsize(self) -> int:
        """计算虚拟大小（vsize），用于估算交易费用"""
        # 基础交易大小（不含见证）
        base_size = len(self.serialize_transaction())

        # 总大小（含见证）
        total_size = base_size
        for inp in self.inputs:
            for item in inp['witness']:
                total_size += len(self.encode_varint(len(item))) + len(item)

        # 虚拟大小 = (基础大小 * 3 + 总大小) / 4
        vsize = (base_size * 3 + total_size) // 4
        return vsize

    def calculate_fee(self) -> int:
        """计算手续费（聪），即输入总额减去输出总额"""
        input_total = sum(inp['amount'] for inp in self.inputs)
        output_total = sum(out['amount'] for out in self.outputs)
        return input_total - output_total

    def get_transaction_info(self) -> Dict:
        """获取交易详细信息，包括交易ID、原始交易数据、虚拟大小、手续费等"""
        raw_tx = self.serialize_transaction()
        txid = self.calculate_txid()
        vsize = self.calculate_vsize()
        fee = self.calculate_fee()
        fee_rate = fee / vsize  # 聪/虚拟字节

        return {
            'txid': txid,
            'raw_transaction': raw_tx.hex(),
            'virtual_size': vsize,
            'fee_satoshis': fee,
            'fee_btc': fee / 100000000,
            'fee_rate': fee_rate,
            'input_total': sum(inp['amount'] for inp in self.inputs),
            'output_total': sum(out['amount'] for out in self.outputs)
        }

def generate_valid_bech32_address(testnet=True) -> str:
    """生成有效的Bech32地址"""
    # 生成随机私钥
    private_key = secrets.randbelow(N - 1) + 1

    # 计算公钥
    tx_gen = BitcoinTransaction()
    pub_point = tx_gen.elliptic_curve_multiply(private_key, (Gx, Gy))
    public_key = bytes([0x02 if pub_point[1] % 2 == 0 else 0x03]) + pub_point[0].to_bytes(32, 'big')

    # 计算公钥哈希
    pubkey_hash = tx_gen.hash160(public_key)

    # 转换为Bech32格式
    hrp = "tb" if testnet else "bc"
    witness_version = 0
    data_5bit = bech32.convertbits(pubkey_hash, 8, 5)

    if data_5bit is None:
        raise ValueError("数据转换失败")

    address = bech32.bech32_encode(hrp, [witness_version] + data_5bit)
    return address

def demonstrate_bitcoin_transaction():
    """演示比特币交易构建和签名"""
    print("=" * 70)
    print("比特币交易构建和签名模拟")
    print("=" * 70)

    # 1. 生成账户A和账户B的密钥对
    print("1. 生成测试账户")

    # 账户A（发送方）
    private_key_a = secrets.randbelow(N - 1) + 1
    public_key_point_a = BitcoinTransaction().elliptic_curve_multiply(private_key_a, (Gx, Gy))
    public_key_a = bytes([0x02 if public_key_point_a[1] % 2 == 0 else 0x03]) + public_key_point_a[0].to_bytes(32, 'big')
    pubkey_hash_a = BitcoinTransaction().hash160(public_key_a)

    # 账户B（接收方）
    private_key_b = secrets.randbelow(N - 1) + 1
    public_key_point_b = BitcoinTransaction().elliptic_curve_multiply(private_key_b, (Gx, Gy))
    public_key_b = bytes([0x02]) + public_key_point_b[0].to_bytes(32, 'big')
    pubkey_hash_b = BitcoinTransaction().hash160(public_key_b)

    # 生成P2WPKH地址
    hrp = "tb"  # 测试网
    address_a = bech32.bech32_encode(hrp, [0] + list(bech32.convertbits(pubkey_hash_a, 8, 5)))
    address_b = bech32.bech32_encode(hrp, [0] + list(bech32.convertbits(pubkey_hash_b, 8, 5)))

    print(f"账户A地址: {address_a}")
    print(f"账户B地址: {address_b}")
    print(f"账户A私钥: 0x{private_key_a:064x}")
    print(f"账户B私钥: 0x{private_key_b:064x}")

    # 2. 构建交易
    print("\n2. 构建交易")

    tx = BitcoinTransaction(testnet=True)

    # 假设账户A有一个UTXO：0.2 BTC
    utxo_txid = "a" * 64  # 模拟前一个交易ID
    utxo_index = 0
    utxo_amount = 20000000  # 0.2 BTC in satoshis

    # 添加输入（来自账户A的UTXO）
    script_pubkey_a = tx.create_p2wpkh_script(pubkey_hash_a)
    tx.add_input(utxo_txid, utxo_index, utxo_amount, script_pubkey_a)

    # 添加输出：0.1 BTC给账户B，0.0999 BTC找零给账户A（手续费0.0001 BTC）
    amount_to_b = 10000000  # 0.1 BTC
    change_amount = 9990000  # 0.0999 BTC
    fee = 10000  # 0.0001 BTC

    tx.add_output(address_b, amount_to_b)
    tx.add_output(address_a, change_amount)

    print(f"输入: 1个UTXO，金额: {utxo_amount / 100000000:.8f} BTC")
    print(f"输出1（给B）: {amount_to_b / 100000000:.8f} BTC")
    print(f"输出2（找零）: {change_amount / 100000000:.8f} BTC")
    print(f"手续费: {fee / 100000000:.8f} BTC")

    # 3. 签名交易
    print("\n3. 签名交易")

    # 对输入进行签名（SIGHASH_ALL）
    tx.sign_input(0, private_key_a, public_key_a, sighash_type=0x01)

    print("使用账户A的私钥对输入进行签名")
    print("签名类型: SIGHASH_ALL (0x01)")
    print("见证数据包含签名和公钥")

    # 4. 获取交易信息
    print("\n4. 交易信息")

    tx_info = tx.get_transaction_info()

    print(f"交易ID: {tx_info['txid']}")
    print(f"虚拟大小: {tx_info['virtual_size']} vbytes")
    print(f"手续费: {tx_info['fee_satoshis']} 聪 ({tx_info['fee_btc']:.8f} BTC)")
    print(f"费率: {tx_info['fee_rate']:.2f} 聪/vbyte")
    print(f"输入总额: {tx_info['input_total'] / 100000000:.8f} BTC")
    print(f"输出总额: {tx_info['output_total'] / 100000000:.8f} BTC")

    # 5. 验证交易结构
    print("\n5. 交易结构验证")

    raw_tx = tx.serialize_transaction()
    print(f"原始交易长度: {len(raw_tx)} 字节")
    print(f"输入数量: {len(tx.inputs)}")
    print(f"输出数量: {len(tx.outputs)}")
    print(f"见证数据: {len(tx.inputs[0]['witness'])} 个元素")

    # 6. 费用优化建议
    print("\n6. 费用优化")
    print(f"当前费率: {tx_info['fee_rate']:.2f} 聪/vbyte")

    # 不同费率下的手续费估算
    fee_rates = [1, 5, 10, 20, 50]
    print("不同费率下的手续费:")
    for rate in fee_rates:
        estimated_fee = rate * tx_info['virtual_size']
        print(f"{rate:2d} 聪/vbyte: {estimated_fee:6d} 聪 ({estimated_fee / 100000000:.8f} BTC)")

    # 7. 交易广播模拟
    print("\n7. 交易广播模拟")
    print("将原始交易广播到比特币网络:")
    print(f"bitcoin-cli sendrawtransaction {tx_info['raw_transaction']}")
    print("交易构建完成 - 成功模拟0.1 BTC从账户A转移到账户B")

    return tx_info

def advanced_transaction_demo():
    """高级交易演示"""
    print("\n\n" + "=" * 70)
    print("高级交易特性演示")
    print("=" * 70)

    # 1. 复杂交易示例（多输入多输出）
    print("\n1. 复杂交易示例（多输入多输出）")

    tx = BitcoinTransaction(testnet=True)

    # 添加多个输入
    utxos = [
        ("b" * 64, 0, 5000000),  # 0.05 BTC
        ("c" * 64, 1, 8000000),  # 0.08 BTC
    ]

    for i, (txid, index, amount) in enumerate(utxos):
        # 生成有效的密钥对
        priv_key = secrets.randbelow(N - 1) + 1
        pub_point = BitcoinTransaction().elliptic_curve_multiply(priv_key, (Gx, Gy))
        pub_key = bytes([0x02]) + pub_point[0].to_bytes(32, 'big')
        pubkey_hash = BitcoinTransaction().hash160(pub_key)
        script_pubkey = tx.create_p2wpkh_script(pubkey_hash)

        tx.add_input(txid, index, amount, script_pubkey)
        print(f"添加输入 {i + 1}: {amount / 100000000:.8f} BTC")

    # 生成有效的Bech32地址
    valid_addresses = [generate_valid_bech32_address(testnet=True) for _ in range(3)]

    outputs = [
        (valid_addresses[0], 10000000),  # 0.1 BTC
        (valid_addresses[1], 2000000),   # 0.02 BTC
        (valid_addresses[2], 900000),    # 0.009 BTC (找零)
    ]

    for i, (address, amount) in enumerate(outputs):
        try:
            tx.add_output(address, amount)
            print(f"添加输出 {i + 1}: {address} -> {amount / 100000000:.8f} BTC")
        except ValueError as e:
            print(f"添加输出失败: {e}")
            # 如果地址无效，使用回退方案
            fallback_address = generate_valid_bech32_address(testnet=True)
            tx.add_output(fallback_address, amount)
            print(f"使用回退地址: {fallback_address}")

    tx_info = tx.get_transaction_info()
    print(f"\n输入数量: {len(tx.inputs)}")
    print(f"输出数量: {len(tx.outputs)}")
    print(f"虚拟大小: {tx_info['virtual_size']} vbytes")
    print(f"估算手续费: {tx_info['fee_satoshis']} 聪")

    # 2. 交易大小分析
    print("\n2. 交易大小分析")

    # 不同输入输出组合的大小比较
    configurations = [
        (1, 1, "标准P2WPKH"),
        (1, 2, "P2WPKH带找零"),
        (2, 2, "多输入交易"),
    ]

    print(" 配置比较:")
    for inputs, outputs, desc in configurations:
        test_tx = BitcoinTransaction(testnet=True)

        # 添加模拟输入
        for i in range(inputs):
            # 使用有效的脚本公钥
            pubkey_hash = hashlib.sha256(f"test{i}".encode()).digest()[:20]
            script_pubkey = test_tx.create_p2wpkh_script(pubkey_hash)
            test_tx.add_input("d" * 64, i, 10000000, script_pubkey)

        # 添加模拟输出
        for i in range(outputs):
            address = generate_valid_bech32_address(testnet=True)
            test_tx.add_output(address, 1000000)

        vsize = test_tx.calculate_vsize()
        print(f"    {desc:15} | {inputs}输入 {outputs}输出 | {vsize:4d} vbytes")

    # 3. 手续费优化策略
    print("\n3. 手续费优化策略")
    strategies = [
        ("实时确认", 20, "高优先级交易"),
        ("1-2块确认", 10, "标准交易"),
        ("不紧急", 5, "经济模式"),
    ]

    base_vsize = 140  # 典型P2WPKH交易大小
    print("确认策略建议:")
    for strategy, rate, desc in strategies:
        fee = base_vsize * rate
        print(f"    {strategy:10} | {rate:2d} 聪/vbyte | {fee:5d} 聪 | {desc}")

if __name__ == "__main__":
    # 运行主要演示
    try:
        tx_info = demonstrate_bitcoin_transaction()
    except Exception as e:
        print(f"主要演示出错: {e}")

    # 运行修复后的高级演示
    try:
        advanced_transaction_demo()
    except Exception as e:
        print(f"高级演示出错: {e}")

import hashlib
import secrets
from typing import Tuple, List


class CustomLamportOTS:
    def __init__(self, n: int = 256):
        """
        初始化 Lamport OTS
        n: 消息摘要长度（位）
        """
        self.n = n
        self.modulus = 2 ** n

    def custom_operator(self, a: int, b: int) -> int:
        """
        实现自定义运算: a +⊕⊙ b = a + b + (a ⊕ b) - (a ⊙ b) mod 2^n
        其中 ⊕ 为异或，⊙ 为按位与
        """
        xor_result = a ^ b
        and_result = a & b
        result = a + b + xor_result - and_result
        return result % self.modulus

    def one_way_function(self, x: int, b: int) -> int:
        """
        单向函数: f_b(x) = x +⊕⊙ b
        """
        return self.custom_operator(x, b)

    def generate_keys(self) -> Tuple[List[int], List[int], int]:
        """
        生成 Lamport OTS 密钥对
        返回: (私钥列表, 公钥列表, 参数b)
        """
        # 生成随机参数b
        b = secrets.randbits(self.n)

        # 生成私钥: 2n个随机数
        private_key_0 = [secrets.randbits(self.n) for _ in range(self.n)]  # 对应消息位0
        private_key_1 = [secrets.randbits(self.n) for _ in range(self.n)]  # 对应消息位1

        # 生成公钥: 对每个私钥应用单向函数
        public_key_0 = [self.one_way_function(x, b) for x in private_key_0]
        public_key_1 = [self.one_way_function(x, b) for x in private_key_1]

        # 合并私钥和公钥
        private_key = private_key_0 + private_key_1
        public_key = public_key_0 + public_key_1

        return private_key, public_key, b

    def hash_message(self, message: str) -> List[int]:
        """
        对消息进行SHA256哈希，并转换为位列表
        """
        # 计算SHA256哈希
        hash_obj = hashlib.sha256(message.encode())
        hash_bytes = hash_obj.digest()

        # 转换为整数
        hash_int = int.from_bytes(hash_bytes, byteorder='big')

        # 转换为256位列表（高位在前）
        bits = [(hash_int >> i) & 1 for i in range(self.n - 1, -1, -1)]

        return bits

    def sign(self, message: str, private_key: List[int], b: int) -> List[int]:
        """
        对消息进行签名
        """
        # 计算消息哈希的位表示
        message_bits = self.hash_message(message)

        # 根据消息位选择对应的私钥元素
        signature = []
        for i, bit in enumerate(message_bits):
            if bit == 0:
                signature.append(private_key[i])  # 使用前n个私钥元素
            else:
                signature.append(private_key[i + self.n])  # 使用后n个私钥元素

        return signature

    def verify(self, message: str, signature: List[int],
               public_key: List[int], b: int) -> bool:
        """
        验证签名
        """
        # 计算消息哈希的位表示
        message_bits = self.hash_message(message)

        # 验证每个签名元素
        for i, bit in enumerate(message_bits):
            if bit == 0:
                expected_public_key = public_key[i]  # 对应前n个公钥元素
            else:
                expected_public_key = public_key[i + self.n]  # 对应后n个公钥元素

            # 计算签名元素通过单向函数的结果
            computed_public_key = self.one_way_function(signature[i], b)

            # 验证是否匹配
            if computed_public_key != expected_public_key:
                return False

        return True


def demonstrate_lamport_ots():
    """
    演示完整的 Lamport OTS 流程
    """
    print("=" * 60)
    print("基于自定义单向函数的 Lamport OTS 数字签名实验")
    print("=" * 60)

    # 初始化 Lamport OTS
    ots = CustomLamportOTS(n=256)

    # 1. 密钥生成
    print("1. 密钥生成")
    private_key, public_key, b = ots.generate_keys()
    print(f"生成 {ots.n} 位私钥和公钥")
    print(f"单向函数参数 b: 0x{b:064x}")
    print(f"私钥长度: {len(private_key)} 个元素")
    print(f"公钥长度: {len(public_key)} 个元素")

    # 2. 签名消息
    print("\n2. 签名过程")
    original_message = "this is a test message"
    print(f"原始消息: '{original_message}'")

    signature = ots.sign(original_message, private_key, b)
    print(f"生成签名，长度: {len(signature)} 个元素")

    # 3. 验证正确消息
    print("\n3. 验证过程 - 正确消息")
    is_valid = ots.verify(original_message, signature, public_key, b)
    print(f"消息: '{original_message}'")
    print(f"验证结果: {'签名有效' if is_valid else '签名无效'}")

    # 4. 验证错误消息
    print("\n4. 验证过程 - 错误消息")
    tampered_message = "this is a fake message"
    is_valid_tampered = ots.verify(tampered_message, signature, public_key, b)
    print(f"消息: '{tampered_message}'")
    print(f"验证结果: {'签名有效' if is_valid_tampered else '签名无效（预期结果）'}")

    # 5. 性能测试
    print("\n5. 性能测试")
    import time

    test_messages = ["测试消息1", "测试消息2", "测试消息3"]

    # 签名性能
    start_time = time.time()
    for msg in test_messages:
        _ = ots.sign(msg, private_key, b)
    sign_time = (time.time() - start_time) / len(test_messages)

    # 验证性能
    start_time = time.time()
    for msg in test_messages:
        _ = ots.verify(msg, ots.sign(msg, private_key, b), public_key, b)
    verify_time = (time.time() - start_time) / len(test_messages)

    print(f"平均签名时间: {sign_time * 1000:.2f} 毫秒")
    print(f"平均验证时间: {verify_time * 1000:.2f} 毫秒")

    # 6. 定义运算验证
    print("\n6. 定义运算验证")
    test_a = 0x1234567890ABCDEF
    test_b = 0xFEDCBA0987654321

    result = ots.custom_operator(test_a, test_b)
    print(f"测试运算: a +⊕⊙ b, 其中 a=0x{test_a:016x}, b=0x{test_b:016x}")
    print(f"结果: 0x{result:032x} (mod 2^{ots.n})")

    # 验证运算性质
    result_direct = (test_a + test_b + (test_a ^ test_b) - (test_a & test_b)) % ots.modulus
    print(f"直接计算验证: {'一致' if result == result_direct else '不一致'}")


if __name__ == "__main__":
    # 运行演示
    demonstrate_lamport_ots()

import hashlib
import secrets
import numpy as np
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass
import time


# 首先定义 CustomLamportOTS 类
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


@dataclass
class MerkleSignature:
    """Merkle签名数据结构"""
    ots_signature: List[int]  # OTS签名
    ots_public_key: List[int]  # OTS公钥
    ots_b_param: int  # OTS参数b
    auth_path: List[Tuple[int, List[int]]]  # 认证路径 (方向, 兄弟节点)
    index: int  # 签名索引


class MerkleMSS:
    def __init__(self, k: int = 8, n: int = 256):
        """
        初始化Merkle多次签名方案
        k: 树的高度，支持T=2^k次签名
        n: 消息摘要长度
        """
        self.k = k
        self.T = 2 ** k  # 签名次数
        self.n = n
        self.modulus = 2 ** n
        self.used_indices = set()  # 已使用的签名索引

        # 现在 CustomLamportOTS 已经被定义，可以正常初始化
        self.ots = CustomLamportOTS(n)

    def custom_operator(self, a: int, b: int) -> int:
        """自定义运算（与Lamport OTS一致）"""
        return self.ots.custom_operator(a, b)

    def one_way_function(self, x: int, b: int) -> int:
        """单向函数（与Lamport OTS一致）"""
        return self.ots.one_way_function(x, b)

    def hash_public_key(self, public_key: List[int]) -> List[int]:
        """
        对OTS公钥进行哈希压缩
        返回: 压缩后的公钥哈希（作为Merkle树叶子节点）
        """
        # 将公钥序列化为字节
        key_bytes = b''.join([key.to_bytes(32, byteorder='big') for key in public_key])

        # 计算SHA256哈希
        hash_obj = hashlib.sha256(key_bytes)
        hash_bytes = hash_obj.digest()

        # 转换为整数列表（便于后续处理）
        hash_int = int.from_bytes(hash_bytes, byteorder='big')
        return [(hash_int >> i) & 1 for i in range(self.n - 1, -1, -1)]

    def merkle_hash(self, left: List[int], right: List[int]) -> List[int]:
        """
        Merkle树节点哈希函数
        将左右子节点哈希组合并计算新哈希
        """
        # 将左右节点转换为字节
        left_bytes = b''.join([str(bit).encode() for bit in left])
        right_bytes = b''.join([str(bit).encode() for bit in right])

        # 组合并计算哈希
        combined = left_bytes + b'|' + right_bytes
        hash_obj = hashlib.sha256(combined)
        hash_bytes = hash_obj.digest()

        # 转换为位列表
        hash_int = int.from_bytes(hash_bytes, byteorder='big')
        return [(hash_int >> i) & 1 for i in range(self.n - 1, -1, -1)]

    def generate_merkle_tree(self) -> Tuple[List[List[List[int]]], List[Dict]]:
        """
        生成Merkle树和所有OTS密钥对
        返回: (Merkle树, OTS密钥列表)
        """
        print(f"生成Merkle树 (高度k={self.k}, 叶子数T={self.T})...")

        # 生成所有OTS密钥对
        ots_keys = []
        for i in range(self.T):
            private_key, public_key, b_param = self.ots.generate_keys()
            ots_keys.append({
                'index': i,
                'private_key': private_key,
                'public_key': public_key,
                'b_param': b_param,
                'used': False
            })

        # 构建Merkle树叶子节点（OTS公钥的哈希）
        leaves = [self.hash_public_key(key['public_key']) for key in ots_keys]

        # 构建完整的Merkle树
        merkle_tree = [leaves]  # 第0层：叶子节点

        current_level = leaves
        for level in range(self.k):
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    parent_hash = self.merkle_hash(current_level[i], current_level[i + 1])
                else:
                    # 如果节点数为奇数，复制最后一个节点
                    parent_hash = self.merkle_hash(current_level[i], current_level[i])
                next_level.append(parent_hash)

            merkle_tree.append(next_level)
            current_level = next_level

        # Merkle根在树的最高层
        self.merkle_root = merkle_tree[-1][0]

        return merkle_tree, ots_keys

    def get_authentication_path(self, merkle_tree: List[List[List[int]]], index: int) -> List[Tuple[int, List[int]]]:
        """
        获取指定索引的认证路径
        返回: [(方向, 兄弟节点), ...]，方向0=左兄弟，1=右兄弟
        """
        auth_path = []
        current_index = index

        for level in range(self.k):
            # 确定兄弟节点的位置
            if current_index % 2 == 0:  # 当前是左节点
                sibling_index = current_index + 1
                direction = 1  # 兄弟在右边
            else:  # 当前是右节点
                sibling_index = current_index - 1
                direction = 0  # 兄弟在左边

            # 确保兄弟索引不越界
            if sibling_index >= len(merkle_tree[level]):
                sibling_index = current_index  # 如果没有兄弟，使用自己

            sibling_node = merkle_tree[level][sibling_index]
            auth_path.append((direction, sibling_node))

            # 移动到父节点索引
            current_index = current_index // 2

        return auth_path

    def sign(self, message: str, merkle_tree: List[List[List[int]]],
             ots_keys: List[Dict], index: int) -> MerkleSignature:
        """
        对消息进行Merkle签名
        """
        # 检查索引是否有效
        if index < 0 or index >= self.T:
            raise ValueError(f"签名索引必须在0到{self.T - 1}之间")

        # 检查是否已使用
        if index in self.used_indices:
            raise ValueError(f"索引{index}已被使用，每个OTS密钥对只能使用一次")

        # 标记为已使用
        self.used_indices.add(index)
        ots_keys[index]['used'] = True

        # 使用对应的OTS密钥对进行签名
        ots_private_key = ots_keys[index]['private_key']
        ots_public_key = ots_keys[index]['public_key']
        ots_b_param = ots_keys[index]['b_param']

        ots_signature = self.ots.sign(message, ots_private_key, ots_b_param)

        # 获取认证路径
        auth_path = self.get_authentication_path(merkle_tree, index)

        return MerkleSignature(
            ots_signature=ots_signature,
            ots_public_key=ots_public_key,
            ots_b_param=ots_b_param,
            auth_path=auth_path,
            index=index
        )

    def verify_merkle_path(self, leaf_hash: List[int], auth_path: List[Tuple[int, List[int]]],
                           index: int, root_hash: List[int]) -> bool:
        """
        验证Merkle认证路径
        """
        current_hash = leaf_hash
        current_index = index

        for direction, sibling in auth_path:
            if direction == 0:  # 兄弟在左边
                current_hash = self.merkle_hash(sibling, current_hash)
            else:  # 兄弟在右边
                current_hash = self.merkle_hash(current_hash, sibling)

            current_index = current_index // 2

        # 验证最终哈希是否与根匹配
        return current_hash == root_hash

    def verify(self, message: str, signature: MerkleSignature,
               merkle_root: List[int]) -> bool:
        """
        验证Merkle签名
        """
        # 1. 验证OTS签名
        ots_valid = self.ots.verify(message, signature.ots_signature,
                                    signature.ots_public_key, signature.ots_b_param)
        if not ots_valid:
            return False

        # 2. 计算OTS公钥的哈希（叶子节点）
        leaf_hash = self.hash_public_key(signature.ots_public_key)

        # 3. 验证Merkle路径
        merkle_valid = self.verify_merkle_path(leaf_hash, signature.auth_path,
                                               signature.index, merkle_root)

        return merkle_valid


def demonstrate_merkle_mss():
    """
    演示完整的Merkle MSS流程
    """
    print("=" * 70)
    print("Merkle多次签名方案（MSS）实验")
    print("=" * 70)

    # 初始化MSS（k=8，支持256次签名）
    k = 8
    mss = MerkleMSS(k=k, n=256)

    # 1. 生成Merkle树和OTS密钥对
    print(f"1. 生成Merkle树和OTS密钥对")
    start_time = time.time()
    merkle_tree, ots_keys = mss.generate_merkle_tree()
    keygen_time = time.time() - start_time

    print(f"生成Merkle树，高度: {k}, 叶子数: {mss.T}")
    print(f"生成{len(ots_keys)}个OTS密钥对")
    print(f"密钥生成时间: {keygen_time:.2f}秒")
    print(f"Merkle根哈希: {mss.merkle_root}")  # 显示前8位

    # 2. 进行多次签名演示
    test_messages = [
        "this is the first test message",
        "this is the second test message",
        "this is the third test message",
        "this is the fourth test message",
        "this is the fifth test message"
    ]

    signatures = []

    print(f"\n2. 进行{len(test_messages)}次签名演示")
    for i, message in enumerate(test_messages):
        print(f"\n第{i + 1}次签名:")
        print(f"消息: '{message}'")
        print(f"使用索引: {i}")

        # 签名
        start_time = time.time()
        signature = mss.sign(message, merkle_tree, ots_keys, i)
        sign_time = time.time() - start_time

        signatures.append(signature)
        print(f"签名成功，时间: {sign_time * 1000:.2f}毫秒")
        print(f"认证路径长度: {len(signature.auth_path)}")

    # 3. 验证所有签名
    print(f"\n3. 验证所有签名")
    for i, (message, signature) in enumerate(zip(test_messages, signatures)):
        start_time = time.time()
        is_valid = mss.verify(message, signature, mss.merkle_root)
        verify_time = time.time() - start_time

        print(f"签名{i + 1}: {'验证成功' if is_valid else '验证失败'} "
              f"(时间: {verify_time * 1000:.2f}毫秒)")

    # 4. 测试重复使用检测
    print(f"\n4. 测试重复使用检测")
    try:
        # 尝试重复使用索引0
        duplicate_sig = mss.sign("reused message", merkle_tree, ots_keys, 0)
        print("重复使用检测失败")
    except ValueError as e:
        print(f"重复使用检测成功: {e}")

    # 5. 测试错误消息验证
    print(f"\n5. 测试错误消息验证")
    wrong_message = "this is the wrong message"
    print(f"消息: '{wrong_message}'")
    is_valid_wrong = mss.verify(wrong_message, signatures[0], mss.merkle_root)
    print(f"错误消息验证: {'通过（异常）' if is_valid_wrong else '拒绝（正常）'}")

    # 6. 性能统计
    print(f"\n6. 性能统计")
    total_ots_keys = len(ots_keys)
    used_keys = len(mss.used_indices)
    remaining_keys = total_ots_keys - used_keys

    print(f"OTS密钥对总数: {total_ots_keys}")
    print(f"已使用密钥对: {used_keys}")
    print(f"剩余可用次数: {remaining_keys}")


if __name__ == "__main__":
    # 运行主要演示
    demonstrate_merkle_mss()
# 密码学基础实现

区块链课的前置密码学实验，覆盖哈希函数、一次性与多次性数字签名、椭圆曲线密码学，还有比特币交易序列化。全部能直接跑，Python 和 MATLAB 都有。

## Python 实现

| 文件 | 主题 | 关键内容 |
|---|---|---|
| `1.py` | Lamport 一次性签名 (OTS) | 自定义单向运算 `a ⊕⊙ b = a + b + (a⊕b) − (a⊙b) mod 2ⁿ`；`generate_keys / sign / verify` |
| `2.py` | Merkle 多次签名方案 (MSS) | 在 Lamport OTS 之上构建 Merkle 树（`MerkleMSS`），实现认证路径 `get_authentication_path` 与多次签名验证 |
| `3.py` | secp256k1 椭圆曲线 | 曲线参数、点加、倍乘、公钥派生，结合 `base58` 和 `bech32` 做地址编码 |
| `4.py` | 比特币交易序列化 | `BitcoinTransaction` 类：ECDSA 签名、P2PKH/P2WPKH 脚本、varint 编码、`txid`、虚拟大小 `vsize` 与手续费估算 |

直接 `python 4.py` 就能看到演示输出，比如生成合法的 bech32 地址、构造并校验签名的交易。

## MATLAB 实现

| 文件 | 主题 |
|---|---|
| `my_hash.m` / `merkle_damgard_hash_v2.m` | 自实现的 Merkle–Damgård 结构哈希函数 |
| `pad_message.m` / `pad_message_v2.m` | 消息填充（MD Padding） |
| `find_inverse.m` / `find_inverse_brute.m` | 模逆，扩展欧几里得和暴力两种 |
| `oplusodot_v2.m` / `plus_oplus_odot.m` | 有限域自定义运算 `⊕ / ⊙` |
| `compress_v2.m` | 压缩函数 |

在 MATLAB 或 Octave 里跑 `Q1.mlx / Q2.mlx / Q3.mlx` 这几个实验报告脚本，能复现整个实验过程。

## 说明

这些实现是为了弄懂密码学原理，不是生产级安全库，真实密钥千万别用它们。实验 2 还有一套基于 Python 的扩展代码，放在课程 `实验2/Ex*` 目录，本仓库只收了最贴近区块链底层的哈希和签名部分。

*Author: 李瑞宇 · 深圳大学 电子信息工程*

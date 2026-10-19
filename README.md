# Blockchain Research

围绕区块链主题攒下来几个项目，按研究方向分了三块，从代币经济学建模一路做到底层密码学和链上合约。

```
blockchain-research/
├── meme-coin-investment/   # Meme 币投资研究与代币经济学建模（Python）
├── crypto-foundations/     # 哈希、数字签名、椭圆曲线、比特币交易（Python + MATLAB）
└── smart-contracts/        # Solidity 智能合约（ERC20 + 投票）
```

## Meme 币投资研究与代币经济学建模

挑了 Dogecoin、Shiba Inu、Pepe 三种典型 Meme 币，没走炒币笔记那套，而是用可计算的代币经济学模型把它们拆开看：

- `dogecoin_inflation.py` 跑适应性通胀模型，无限供应加上固定年增发
- `shiba_deflation.py` 跑结构性通缩模型，超发加交易销毁
- `pepe_market_simulation.py` 跑固定供应的博弈市场，事件驱动随机游走

三个脚本都实测能跑，各自出四张图加关键指标。`report.pdf` 是三十四页的原报告。

## 密码学基础实现

想弄明白区块链底层的密码学原理，就手写了这几块：

- Lamport 一次性签名，外面再套 Merkle 多次签名方案，都是 Python
- secp256k1 椭圆曲线加地址编码，Python
- 比特币交易序列化，ECDSA、P2PKH、P2WPKH、txid、vsize 都覆盖，Python
- 自实现的 Merkle–Damgård 哈希、模逆、有限域运算，MATLAB

## 智能合约工程

一个 Solidity 工程，在 Remix IDE 里写、编译、部署验证。最小可用的 ERC20 代币 `MyToken`、支持委托的投票合约 `Ballot`、所有权模式和存储合约都在这。

## 技术栈

Python、NumPy、Pandas、Matplotlib、SciPy，MATLAB 或 Octave，Solidity 0.8.20 往上。

## 声明

相关实现是原理演示，不是生产级安全实现。合约没审计、没上主网。报告里对代币的观点只作学术分析，不构成任何投资建议。

---

*Author: 李瑞宇*

# Blockchain Research · 区块链课程项目合集

深圳大学《区块链》课程的相关项目与实验代码合集，按主题分成三个子模块：

```
blockchain-research/
├── meme-coin-investment/   # 大作业：Meme 币投资研究与代币经济学建模（Python）
├── crypto-foundations/     # 实验 1–3：哈希 / 数字签名 / 椭圆曲线 / 比特币交易（Python + MATLAB）
└── smart-contracts/        # 实验 4：Solidity 智能合约（ERC20 + 投票）
```

## 1. Meme 币投资研究与代币经济学建模 [`meme-coin-investment/`](meme-coin-investment/)

课程大作业。用**可计算的代币经济学模型**对比 Dogecoin / Shiba Inu / Pepe 三种
典型 Meme 币的价值逻辑：

- `dogecoin_inflation.py` —— 适应性通胀模型（无限供应 + 固定年增发）
- `shiba_deflation.py` —— 结构性通缩模型（超发 + 交易销毁）
- `pepe_market_simulation.py` —— 固定供应博弈市场（事件驱动随机游走）

三个脚本均**实测可运行**，输出 4 图 + 关键指标；`report.pdf` 为 34 页原报告。

## 2. 密码学基础实现 [`crypto-foundations/`](crypto-foundations/)

理解区块链底层的密码学原理：

- **Lamport 一次性签名** + **Merkle 多次签名方案**（Python）
- **secp256k1 椭圆曲线** 与地址编码（Python）
- **比特币交易序列化**（ECDSA / P2PKH / P2WPKH / txid / vsize）（Python）
- 自实现 **Merkle–Damgård 哈希**、模逆、有限域运算（MATLAB）

## 3. 智能合约实验 [`smart-contracts/`](smart-contracts/)

Solidity 工程（Remix IDE）：最小可用 **ERC20 代币** `MyToken`、支持委托的
**投票合约** `Ballot`、所有权模式与存储合约。

## 技术栈

Python · NumPy / Pandas / Matplotlib / SciPy · MATLAB / Octave · Solidity (^0.8.20)

## 声明

所有代码与报告均用于**课程学习**，相关实现为原理演示、非生产级安全实现，
合约未审计、未上主网；报告中涉及的代币观点仅作学术研究，不构成任何投资建议。

---

*Author: 李瑞宇 · 深圳大学 电子信息工程 · GPA 3.8/4.5*

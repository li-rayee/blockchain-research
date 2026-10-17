# 智能合约实验（Solidity · Remix）

区块链课程 **实验 4** 的 Solidity 工程，使用 Remix IDE 编写、编译并在
Remix VM（含上海/伦敦分叉）上部署验证。

## 合约清单

| 文件 | 说明 |
|---|---|
| `MyToken.sol` | 最小可用的 **ERC20 代币**：含 `name/symbol/decimals/totalSupply`、余额与授权映射、`transfer/approve/transferFrom`，以及 `onlyOwner` 修饰符保护与 `mint` 铸造函数 |
| `3_Ballot.sol` | **投票合约**：支持投票权委托（delegate，含环检测）、提案计票与 `winningProposal()/winnerName()` 胜出判定 |
| `1_Storage.sol` | 最基础的 `set/get` 存储合约，理解状态变量与交易写入 |
| `2_Owner.sol` | **所有权模式**：`onlyOwner` 权限控制的最小实现 |
| `SimpleStorage(Browser Wallet).sol` / `SimpleStorage(Remix VM).sol` | 同一存储合约在浏览器钱包 / Remix VM 两种环境下的部署版本 |

## 实验要点

- 在 Remix 中编译 `^0.8.20` 合约，分别部署到 **Remix VM (Shanghai)** 与
  **Remix VM (London)** 验证 EVM 版本差异
- `MyToken` 部署时传入 `(name, symbol, initialSupply)`，初始供应量按
  `initialSupply * 10**decimals` 铸造给部署者
- 配套 `export-token-0xc75d...xlsx` 记录了代币导出的元数据；`.states/` 下保存了
  两种 VM 的部署后状态快照

## 编译 / 部署

1. 打开 [Remix IDE](https://remix.ethereum.org)
2. 将本目录放入 File Explorer（或用 Hardhat/Foundry 拉取）
3. 在 Solidity Compiler 选择对应 pragma 版本后编译
4. Deploy & Run 选择环境（VM 或注入的浏览器钱包）即可部署

> 合约仅用于教学验证，**未审计、未上主网**，请勿用于真实资产。

*Author: 李瑞宇 · 深圳大学 电子信息工程*

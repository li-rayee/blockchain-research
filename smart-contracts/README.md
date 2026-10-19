# 智能合约工程

一个 Solidity 智能合约工程，在 Remix IDE 里写、编译，再在 Remix VM（含上海和伦敦分叉）上部署验证。

## 合约清单

| 文件 | 说明 |
|---|---|
| `MyToken.sol` | 最小可用的 ERC20 代币：name、symbol、decimals、totalSupply 都有，余额和授权映射、transfer、approve、transferFrom 齐全，外加 onlyOwner 修饰符保护和 mint 铸造函数 |
| `3_Ballot.sol` | 投票合约：支持投票权委托（delegate，含环检测）、提案计票，以及 winningProposal 和 winnerName 胜出判定 |
| `1_Storage.sol` | 最基础的 set/get 存储合约，用来理解状态变量和交易写入 |
| `2_Owner.sol` | 所有权模式：onlyOwner 权限控制的最小实现 |
| `SimpleStorage(Browser Wallet).sol` / `SimpleStorage(Remix VM).sol` | 同一个存储合约在浏览器钱包和 Remix VM 两种环境下的部署版本 |

## 工程要点

在 Remix 里编译 0.8.20 往上的合约，分别部署到 Remix VM 的 Shanghai 和 London 两种分叉，对比 EVM 版本差异。`MyToken` 部署时传 name、symbol、initialSupply，初始供应量按 initialSupply 乘 10 的 decimals 次方铸造给部署者。配套的 `export-token-0xc75d...xlsx` 记了代币导出的元数据，`.states/` 下存着两种 VM 部署后的状态快照。

## 编译与部署

1. 打开 Remix IDE
2. 把本目录放进 File Explorer，或者用 Hardhat、Foundry 拉取
3. 在 Solidity Compiler 选好对应 pragma 版本后编译
4. 在 Deploy & Run 里选环境（VM 或者注入的浏览器钱包）即可部署

合约只用于演示验证，没审计、没上主网，真实资产千万别碰。

*Author: 李瑞宇*

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title 一个最小可用的ERC20代币合约
 * @dev 符合ERC20标准，包含铸造功能和权限控制
 */
contract MyToken {
    // --- 代币元数据 ---
    string public name;
    string public symbol;
    uint8 public constant decimals = 18;
    uint256 public totalSupply;

    // --- 余额和授权映射 ---
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // --- 事件（ERC20标准要求）---
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    // --- 权限控制 ---
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    /**
     * @dev 构造函数，在部署时执行
     * @param _name 代币全称（如 "My First Token"）
     * @param _symbol 代币符号（如 "MFT"）
     * @param _initialSupply 初始供应量（整数形式，如 1000000 表示100万枚）
     */
    constructor(string memory _name, string memory _symbol, uint256 _initialSupply) {
        name = _name;
        symbol = _symbol;
        owner = msg.sender; // 部署者成为合约所有者
        // 将初始供应量铸造给部署者，注意要乘以10^decimals
        _mint(msg.sender, _initialSupply * (10 ** uint256(decimals)));
    }

    /**
     * @dev 转账函数，任何人都可以调用，将自己持有的代币转给他人
     */
    function transfer(address to, uint256 value) external returns (bool) {
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        require(to != address(0), "Cannot transfer to zero address");

        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    /**
     * @dev 授权函数，允许另一个地址（如某个DApp）代表你花费一定数量的代币
     */
    function approve(address spender, uint256 value) external returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    /**
     * @dev 授权转账函数，被授权者调用，从授权人账户向目标账户转账
     */
    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Allowance exceeded");
        require(to != address(0), "Cannot transfer to zero address");

        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value; // 减少授权额度
        emit Transfer(from, to, value);
        return true;
    }

    /**
     * @dev 铸造函数，只有合约所有者可以调用，用于创造新的代币
     */
    function mint(address to, uint256 value) external onlyOwner {
        _mint(to, value);
    }

    /**
     * @dev 内部铸造逻辑
     */
    function _mint(address to, uint256 value) internal {
        require(to != address(0), "Cannot mint to zero address");
        totalSupply += value;
        balanceOf[to] += value;
        emit Transfer(address(0), to, value); // 来自零地址表示新代币产生
    }
}
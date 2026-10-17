// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0; // 使用0.8.x版本，它内置了安全的算术运算

/**
 * @title 增强版简单存储合约
 * @dev 演示状态变量、函数、事件、错误处理
 */
contract SimpleStorage {
    // 1. 状态变量：永久存储在区块链上
    uint256 private _storedNumber;

    // 2. 事件：记录重要的状态改变（可用于前端监听）
    event ValueChanged(uint256 indexed oldValue, uint256 indexed newValue, address indexed setBy);
    
    // 3. 自定义错误（Solidity 0.8.4+）：更省Gas的错误处理方式
    error NumberTooLarge(uint256 maxAllowed, uint256 providedValue);

    // 4. 函数：设置一个数字
    function setNumber(uint256 newNumber) public {
        // 使用 `require` 验证输入条件
        require(newNumber != _storedNumber, "New number must be different from the current one.");
        
        // 使用 `revert` 与自定义错误处理更复杂的业务逻辑
        if (newNumber > 10000) {
            revert NumberTooLarge(10000, newNumber);
        }
        
        // 记录旧值，更新状态，触发事件
        uint256 oldValue = _storedNumber;
        _storedNumber = newNumber;
        emit ValueChanged(oldValue, _storedNumber, msg.sender);
    }

    // 5. 函数：获取当前存储的数字（`view` 表示不修改状态）
    function getNumber() public view returns (uint256) {
        return _storedNumber;
    }

    // 6. 函数：演示 `assert` 的使用，用于检查绝不应为假的条件
    function increment() public {
        uint256 oldValue = _storedNumber;
        _storedNumber += 1;
        
        // 使用 `assert` 检查内部逻辑一致性
        assert(_storedNumber == oldValue + 1); // 这个条件应该永远为真
        
        emit ValueChanged(oldValue, _storedNumber, msg.sender);
    }
}
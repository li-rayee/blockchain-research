// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title SimpleStorage
 * @dev 一个简单的存储合约，演示Solidity基础语法和错误处理
 */
contract SimpleStorage {
    // 状态变量：存储一个无符号整数
    uint private value;
    
    // 事件：当值改变时触发，记录旧值和新值
    event ValueChanged(uint indexed oldValue, uint indexed newValue);
    
    // 错误定义：用于更高效的错误处理（Solidity 0.8.4+）
    error ValueTooHigh(uint providedValue, uint maxAllowed);
    error ValueNotIncreased(uint oldValue, uint newValue);
    
    /**
     * @dev 构造函数，初始化存储值为0
     */
    constructor() {
        value = 0;
    }
    
    /**
     * @dev 设置新值，触发ValueChanged事件
     * @param _newValue 要设置的新值
     * @notice 使用require进行输入验证，使用revert进行复杂条件检查
     */
    function set(uint _newValue) public {
        // 使用require检查基本条件：新值不能与当前值相同
        require(_newValue != value, "New value must be different from current value");
        
        // 使用revert进行更复杂的条件检查
        if (_newValue > 10000) {
            revert ValueTooHigh(_newValue, 10000);
        }
        
        // 检查新值是否大于旧值
        if (_newValue <= value) {
            revert ValueNotIncreased(value, _newValue);
        }
        
        uint oldValue = value;
        value = _newValue;
        
        // 触发事件，记录状态变化
        emit ValueChanged(oldValue, value);
    }
    
    /**
     * @dev 获取当前存储的值
     * @return 当前存储的无符号整数值
     */
    function get() public view returns (uint) {
        return value;
    }
    
    /**
     * @dev 将存储的值增加1，演示assert的使用
     */
    function increment() public {
        uint oldValue = value;
        value += 1;
        
        // 使用assert检查内部逻辑一致性（应永远为真）
        assert(value == oldValue + 1);
        
        emit ValueChanged(oldValue, value);
    }
    
    /**
     * @dev 一个演示失败交易的特殊函数
     * @notice 此函数专门用于展示错误处理机制
     */
    function demonstrateFailedTransaction() public view {
        // 此调用总是会失败，用于演示错误处理
        require(value > 1000, "Current value is not greater than 1000");
    }
}
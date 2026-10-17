function a_list = find_inverse_brute(b, c)
    % 定义4中的运算 +⊕⊙ 和 +⊙⊕
    % 同时假设a的二进制表示中，a1为最高位（MSB），an为最低位（LSB）
    
    n = 32; % 32比特
    a_list = []; % 存储所有满足条件的a
    
    % 遍历所有可能的a值（0 to 2^32-1）
    for a = 0:2^32-1
        % 计算a的二进制表示（MSB first）
        a_bits = bitget(a, n:-1:1, 'uint32'); % 从最高位到最低位
        
        % 根据定义5计算 c_value = a +⊕⊙ b
        current = b;
        for i = 1:n
            if a_bits(i) == 0
                % 使用 +⊕⊙ 操作
                current = mod(current + a + 1 + 2 * bitxor(current, a), 2^n);
            else
                % 使用 +⊙⊕ 逆运算操作
                current = bitcmp(mod(current + a - 1 - 2 * bitxor(current, a), 2^n));
            end
        end
        c_value = current;
        
        % 检查是否匹配
        if c_value == c
            a_list = [a_list; a];
        end
    end
end
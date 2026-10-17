function a = find_inverse(b, c)
    n = 32;
    % 计算 d = c - b - 1 mod 2^32
    d = mod(c - b - 1, 2^n);
    a = 0;
    carry = 0;
    
    % 处理最低位 (i=0)
    a0 = bitget(d, 1);
    a = bitset(a, 1, a0);
    
    % 处理位 1 到 31
    for i = 2:n
        % 获取 a 和 b 的前一位（i-1）
        a_prev = bitget(a, i-1);
        b_prev = bitget(b, i-1);
        xor_prev = bitxor(a_prev, b_prev);
        carry_in = carry;
        bit_d = bitget(d, i);
        
        % 计算当前位 a_i
        a_i = bitxor(bitxor(bit_d, xor_prev), carry_in);
        a = bitset(a, i, a_i);
        
        % 计算进位
        total = a_i + xor_prev + carry_in;
        carry = floor(total / 2);
    end
end

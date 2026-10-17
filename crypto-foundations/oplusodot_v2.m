function output = oplusodot_v2(a, b, type, n)
%   a, b: 整数
%   n: 模运算的位长
%   output: 模2^n的结果

    % 计算按位异或和按位与
    xor_ab = bitxor(a, b);
    and_ab = bitand(a, b);
    
    % 根据类型应用公式
    if strcmp(type, 'oplusodot')
        output = mod(a + b + xor_ab - and_ab, 2^n);
    elseif strcmp(type, 'odotoplus')
        output = mod(a + b + and_ab - xor_ab, 2^n);
    else
        error('无效的操作类型');
    end
end
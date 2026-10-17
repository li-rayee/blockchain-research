function H_new = compress_v2(H, M, n)
% COMPRESS_V2 压缩函数：H_new = H +⊕⊙ M
%   H: 当前哈希值（整数）
%   M: 消息块（整数）
%   n: 位长
%   H_new: 新哈希值（整数）

    % 获取H的二进制表示
    H_bin = dec2bin(H, n) - '0'; % n位二进制向量（高位在前）
    % 初始化当前值为M
    current = M;
    for i = 1:n
        bit = H_bin(i);
        if bit == 0
            current = oplusodot_v2(current, H, 'oplusodot', n);
        else
            current = oplusodot_v2(current, H, 'odotoplus', n);
        end
    end
    H_new = current;
end
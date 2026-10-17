function hash = merkle_damgard_hash_v2(message, n)
% MERKLE_DAMGARD_HASH_V2 使用非零初始向量(IV)的哈希函数
%   message: 输入消息，字符串或字节数组
%   n: 哈希输出位数（默认为32）
%   hash: 输出的哈希值，整数类型

    if nargin < 2
        n = 32; % 默认使用32位哈希
    end

    % 将消息转换为二进制向量（0和1）
    if ischar(message)
        message = uint8(message);
    end
    msg_bin = dec2bin(message, 8) - '0'; % 转换为二进制矩阵
    msg_bin = msg_bin(:)'; % 展平为行向量

    % 消息填充
    padded_msg = pad_message_v2(msg_bin, n);
    
    % 使用非零值初始化初始向量（使用简单常量）
    IV = bin2dec('10101010101010101010101010101010'); % 非零初始向量
    H = IV;
    
    % 处理每个消息块
    num_blocks = length(padded_msg) / n;
    for i = 1:num_blocks
        block_start = (i-1)*n + 1;
        block_end = i*n;
        M_i = padded_msg(block_start:block_end);
        % 将二进制向量转换为整数
        M_i_int = 0;
        for j = 1:n
            M_i_int = M_i_int * 2 + M_i(j);
        end
        H = compress_v2(H, M_i_int, n);
    end
    
    hash = H;
end

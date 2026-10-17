function padded_msg = pad_message_v2(msg_bin, n)
% PAD_MESSAGE_V2 将消息填充至n位的倍数
%   msg_bin: 消息的二进制向量
%   n: 块大小（位）
%   padded_msg: 填充后的二进制向量

    L = length(msg_bin);
    % 添加1位
    padded_msg = [msg_bin, 1];
    % 计算需要添加的0的个数
    len_bits = n; % 使用n位表示长度
    k = mod(- (L + 1 + len_bits), n);
    if k < 0
        k = k + n;
    end
    padded_msg = [padded_msg, zeros(1, k)];
    % 附加长度信息（n位二进制）
    len_bin = dec2bin(L, len_bits) - '0';
    padded_msg = [padded_msg, len_bin];
end
function padded_msg = pad_message(msg_bin, n)
% PAD_MESSAGE_CORRECTED Pad the message to multiple of n bits.
%   msg_bin: binary vector of message
%   n: block size in bits
%   padded_msg: padded binary vector

    L = length(msg_bin);
    % Add 1 bit
    padded_msg = [msg_bin, 1];
    % Determine number of zeros to add
    len_bits = n; % we use n-bit length representation
    k = mod(- (L + 1 + len_bits), n);
    if k < 0
        k = k + n;
    end
    padded_msg = [padded_msg, zeros(1, k)];
    % Append length as n-bit binary
    len_bin = dec2bin(L, len_bits) - '0';
    padded_msg = [padded_msg, len_bin];
end

function hash_val = my_hash(message)
% MY_HASH Compute hash value using Merkle-Damgard structure and +⊕⊙ operation.
%   message: Input string or byte array.
%   hash_val: Output hash value as uint32.

    % Parameters
    n = 32; % Bit length
    block_size = 4; % Bytes per block (32 bits)

    % Convert message to uint8 array if it is a string
    if ischar(message)
        msg_uint8 = uint8(message);
    else
        msg_uint8 = message;
    end

    % Pad the message
    padded_msg = pad_message(msg_uint8, block_size);

    % Split into blocks of size block_size
    num_blocks = length(padded_msg) / block_size;
    blocks = zeros(1, num_blocks, 'uint32'); % Preallocate blocks as uint32

    for i = 1:num_blocks
        start_index = (i-1)*block_size + 1;
        end_index = i*block_size;
        block_bytes = padded_msg(start_index:end_index);
        % Convert 4 bytes to uint32 (little-endian)
        block_uint32 = typecast(block_bytes, 'uint32');
        blocks(i) = block_uint32;
    end

    % Initialize hash value (IV)
    H = uint32(0);

    % Process each block with compression function
    for i = 1:num_blocks
        H = plus_oplus_odot(H, blocks(i));
    end

    hash_val = H;
end

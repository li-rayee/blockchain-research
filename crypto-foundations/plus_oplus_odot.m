function result = plus_oplus_odot(a, b)
% PLUS_OPLUS_ODOT Compute a +⊕⊙ b mod 2^32.
%   a, b: uint32 inputs.
%   result: uint32 output.

    % Definition: a +⊕⊙ b = a + b + 1 + 2*(a XOR b) mod 2^32
    xor_ab = bitxor(a, b);
    result = mod(a + b + 1 + 2 * xor_ab, 2^32);
    % Since a and b are uint32, operations are automatically modulo 2^32
end
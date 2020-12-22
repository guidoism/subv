def u(num, bits):
    """ parse an unsigned integer into a bitfield.

    >>> u(0x08, 8)
    (8, 8)
    >>> u(0xff, 8)
    (255, 8)

    >>> u(0xf0, 7)
    Traceback (most recent call last):
      ...
    ValueError: value 240 (u8) too large for u7 field
    >>> u(-1, 8)
    Traceback (most recent call last):
      ...
    ValueError: negative value not allowed: -1
    """
    if num < 0:
        raise ValueError("negative value not allowed: {}".format(num))

    if num.bit_length() > bits:
        raise ValueError("value {} (u{}) too large for u{} field"
                         .format(num, num.bit_length(), bits))

    return (num, bits)

def i(num, bits):
    """ parse a signed integer into a bitfield.

    >>> i(8, 8)
    (8, 8)
    >>> i(-4, 8)
    (252, 8)
    >>> i(127, 8)
    (127, 8)
    >>> i(-128, 8)
    (128, 8)

    >>> i(128, 8)
    Traceback (most recent call last):
      ...
    ValueError: value 128 (i9) too large for i8 field [-128;127]
    >>> i(-129, 8)
    Traceback (most recent call last):
      ...
    ValueError: value -129 (i9) too large for i8 field [-128;127]
    """
    min = -(1 << (bits - 1))
    max = -1 - min

    if num > max or num < min:
        raise ValueError("value {} (i{}) too large for i{} field [{};{}]"
                         .format(num, num.bit_length()+1, bits, min, max))

    if num < 0:
        num = (1 << bits) + num

    return u(num, bits)

def from_part(part):
    """ parse a size-tagged subv part into a bit.

    >>> from_part((34, 2))
    (34, 2)
    >>> from_part((34, 2, 'extra'))
    (34, 2)
    """
    val = int(part[0])
    size = part[1]
    return (val, int(size))

def concat(*parts):
    """ concatenate multiple bitfields.

    >>> concat((0b10, 2), (0b00, 2))
    (2, 4)
    >>> concat((0b1, 1), (0b0110, 4), (0b110, 3))
    (205, 8)
    """
    val, size = 0, 0
    for (pval, psize) in parts:
        val = val | pval << size
        size += psize
    return (val, size)

def slice(bits, hi, lo):
    """ slice a bitfield given hi and lo bit indices.

    >>> slice((0x7f, 8), 7, 4)
    (7, 4)
    >>> slice((0b100, 3), 2, 2)
    (1, 1)
    >>> slice((0x12345678, 32), 7, 0)
    (120, 8)
    >>> slice((0x12345678, 32), 15, 8)
    (86, 8)
    >>> slice((0x12345678, 32), 23, 16)
    (52, 8)

    >>> slice((0xf, 4), 4, 0)
    Traceback (most recent call last):
      ...
    ValueError: slice [4:0] out of range (4 bit value)
    >>> slice((0xf, 4), 2, 3)
    Traceback (most recent call last):
      ...
    ValueError: cant slice reverse range
    >>> slice((0xf, 4), 3, -1)
    Traceback (most recent call last):
      ...
    ValueError: slice [3:-1] out of range (4 bit value)
    """
    (val, size) = bits

    if hi < lo:
        raise ValueError("cant slice reverse range")
    elif lo < 0 or hi >= size:
        raise ValueError("slice [{}:{}] out of range ({} bit value)".format(hi, lo, size))

    size = hi - lo + 1
    val = (val >> lo) & ((1 << size) - 1)
    return (val, size)

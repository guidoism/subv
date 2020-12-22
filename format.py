#!/usr/bin/env python3
""" format.py
Verifies instruction formats, orders and pre-bit-packs arguments.
Every instruction-line in the code segment needs to start with the opcode,
which has to be correctly tagged. Arguments have to be provided in the correct
order currently, and their first tag is verified also.

Labels can be referenced in the immXX/offXX fields of most instructions. If no
bitslice is given for the labels, the default slice is picked based on the
instruction.

>>> from io import StringIO
>>> # doctest: +REPORT_NDIFF
... print(subv.join_all(format(StringIO('''
... == code 0x80000000
... main:
... # load 0x10010000 (UART0) into t0
... 37/lui 5/rd/t0 0x10010/imm20
... # store 0x48 (H) in UART0+0
... 13/opi 0/subop/add 6/rd/t1 0/rs/x0 48/imm12
... 23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
... # store 0x65 (e) in UART0+0
... 13/opi 0/subop/add 6/rd/t1 0/rs/x0 65/imm12
... 23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
... # store 0x6c (l) in UART0+0
... 13/opi 0/subop/add 6/rd/t1 0/rs/x0 6c/imm12
... 23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
... # store 0x6c (l) in UART0+0
... 13/opi 0/subop/add 6/rd/t1 0/rs/x0 6c/imm12
... 23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
... # store 0x6f (o) in UART0+0
... 13/opi 0/subop/add 6/rd/t1 0/rs/x0 6f/imm12
... 23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
... # store 0x0a (\\\\n) in UART0+0
... 13/opi 0/subop/add 6/rd/t1 0/rs/x0 0a/imm12
... 23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
... # jump back up to the top
... 6f/jal 0/rd/x0 main/off20
... '''[1:-1]))))
== code 0x80000000
main:
# load 0x10010000 (UART0) into t0
37/7 05/5 10010/20
# store 0x48 (H) in UART0+0
13/7 06/5 00/3 00/5 48/12
23/7 00/5 02/3 05/5 06/5 00/7
# store 0x65 (e) in UART0+0
13/7 06/5 00/3 00/5 65/12
23/7 00/5 02/3 05/5 06/5 00/7
# store 0x6c (l) in UART0+0
13/7 06/5 00/3 00/5 6c/12
23/7 00/5 02/3 05/5 06/5 00/7
# store 0x6c (l) in UART0+0
13/7 06/5 00/3 00/5 6c/12
23/7 00/5 02/3 05/5 06/5 00/7
# store 0x6f (o) in UART0+0
13/7 06/5 00/3 00/5 6f/12
23/7 00/5 02/3 05/5 06/5 00/7
# store 0x0a (\\n) in UART0+0
13/7 06/5 00/3 00/5 0a/12
23/7 00/5 02/3 05/5 06/5 00/7
# jump back up to the top
6f/7 00/5 main[19:12]/off8 main[11:11]/off1 main[10:1]/off10 main[20:20]/off1
"""

import subv
import bits

def ref_slice(ref, hi, lo):
    if hi < lo:
        raise ValueError("cant slice reverse range")
    elif hi >= ref['size']:
        raise ValueError("cant slice [{}:{}] from {} bit value".format(hi, lo, ref['size']))

    return {
        **ref,
        'hi': hi,
        'lo': lo,
        'size': hi - lo + 1,
    }

def default_slice(val, hi, lo):
    """ add a default slice spec to labels if missing,

    >>> default_slice(('label', 'imm12'), 12, 1)
    ('label[12:1]', 'imm12')
    >>> default_slice(('label[14:3]', 'imm12'), 12, 1)
    ('label[14:3]', 'imm12')
    >>> default_slice(('label[14:3]', 'imm12', 'extra'), 12, 1)
    ('label[14:3]', 'imm12', 'extra')
    >>> default_slice(('label[31:0]', 'imm12'), 11, 0)
    Traceback (most recent call last):
        ...
    AssertionError: expected 12 bit slice
    """
    parsed = subv.parse_reference(val)
    if 'hi' not in parsed:
      parsed['hi'] = hi
      parsed['lo'] = lo

    p_size = parsed['hi'] - parsed['lo'] + 1
    assert parsed['size'] == p_size, "expected {} bit slice".format(parsed['size'])

    ref = '{label}[{hi}:{lo}]'.format(**parsed)
    return (ref, *val[1:])

def slice_bit_or_ref(val, hi, lo):
    """ bit.slice but for bitfields and label references.

    >>> slice_bit_or_ref(('label[31:0]', 'imm32'), 12, 1)
    ('label[12:1]', 'imm12')
    >>> slice_bit_or_ref(('label[31:0]', 'off32'), 11, 0)
    ('label[11:0]', 'off12')
    >>> slice_bit_or_ref(('label[31:0]', 'off32'), 31, 12)
    ('label[31:12]', 'off20')
    >>> slice_bit_or_ref(('label[11:0]', 'imm12', 'extra'), 15, 4)
    Traceback (most recent call last):
        ...
    AssertionError: cant slice outside of bounds
    >>> slice_bit_or_ref(('label', 'imm12'), 12, 1)
    Traceback (most recent call last):
        ...
    AssertionError: cant slice label w/o bounds
    """
    if not isinstance(val[0], str):
        return bits.slice(val, hi, lo)

    ref = subv.parse_reference(val)
    assert 'hi' in ref, "cant slice label w/o bounds"

    sz = hi - lo
    lo = ref['lo'] + lo
    hi = lo + sz
    assert hi <= ref['hi'], "cant slice outside of bounds"

    ref['hi'] = hi
    ref['lo'] = lo
    ref['size'] = sz + 1
    main = '{label}[{hi}:{lo}]'.format(**ref)
    field = '{mode}{size}'.format(**ref)
    return (main, field, *val[2:])

def pack_u(instr):
    """ verify & pack U-type instructions.

    >>> pack_u([(0x37, 'lui'), (5, 'rd', 't0'), (0x10010, 'imm20')])
    [(55, 7), (5, 5), (65552, 20)]

    >>> pack_u([(0x37, 'lui'), (5, 'rd', 't0'), ('pos', 'imm20')])
    [(55, 7), (5, 5), ('pos[31:12]', 'imm20')]

    >>> pack_u([(0x37, 'lui'), (5, 'rd', 't0'), ('pos[19:0]', 'imm20')])
    [(55, 7), (5, 5), ('pos[19:0]', 'imm20')]

    >>> pack_u([(0x37, 'lui'), (5, 'rd', 't0'), ('pos[31:0]', 'imm20')])
    Traceback (most recent call last):
        ...
    AssertionError: expected 20 bit slice
    """
    (op, rd, imm) = instr
    op = bits.u(subv.untag(op), 7)
    rd = bits.u(subv.untag(rd, 'rd'), 5)
    if subv.is_reference(imm):
        imm = default_slice(imm, 31, 12)
    else:
        imm = bits.i(subv.untag(imm, 'imm20'), 20)

    return [op, rd, imm]

def pack_i(instr):
    """ verify & pack I-type instructions.

    >>> pack_i([(0x13, 'opi'), (0, 'subop', 'add'), (6, 'rd', 't1'), (0, 'rs', 'x0'), (101, 'imm12')])
    [(19, 7), (6, 5), (0, 3), (0, 5), (101, 12)]

    >>> pack_i([(0x13, 'opi'), (0, 'subop', 'add'), (6, 'rd', 't1'), (0, 'rs', 'x0'), ('label', 'imm12')])
    [(19, 7), (6, 5), (0, 3), (0, 5), ('label[11:0]', 'imm12')]
    """
    (op, sub, rd, rs, imm) = instr
    op  = bits.u(subv.untag(op), 7)
    sub = bits.u(subv.untag(sub, 'subop'), 3)
    rd  = bits.u(subv.untag(rd, 'rd'), 5)
    rs  = bits.u(subv.untag(rs, 'rs'), 5)
    if subv.is_reference(imm):
        imm = default_slice(imm, 11, 0)
    else:
        imm = bits.i(subv.untag(imm, 'imm12'), 12)

    return [op, rd, sub, rs, imm]

def pack_s(instr):
    """ verify & pack S-type instructions.

    >>> pack_s([(0x23, 'store'), (2, 'subop', 'word'), (5, 'rs', 't0'), (6, 'rs', 't1'), (0, 'off12')])
    [(35, 7), (0, 5), (2, 3), (5, 5), (6, 5), (0, 7)]

    >>> pack_s([(0x23, 'store'), (2, 'subop', 'word'), (5, 'rs', 't0'), (6, 'rs', 't1'), ('home', 'off12')])
    [(35, 7), ('home[4:0]', 'off5'), (2, 3), (5, 5), (6, 5), ('home[11:5]', 'off7')]
    """
    (op, sub, rs1, rs2, imm) = instr
    op  = bits.u(subv.untag(op), 7)
    sub = bits.u(subv.untag(sub, 'subop'), 3)
    rs1 = bits.u(subv.untag(rs1, 'rs'), 5)
    rs2 = bits.u(subv.untag(rs2, 'rs'), 5)

    if subv.is_reference(imm):
        imm = default_slice(imm, 11, 0)
    else:
        imm = bits.i(subv.untag(imm, 'off12'), 12)

    imm_lo = slice_bit_or_ref(imm, 4, 0)  # + ('off[4:0]',)
    imm_hi = slice_bit_or_ref(imm, 11, 5) # + ('off[11:5]',)
    return [op, imm_lo, sub, rs1, rs2, imm_hi]

def pack_j(instr):
    """ verify & pack J-type instructions.

    >>> pack_j([(0x6f, 'jal'), (0, 'rd', 'x0'), (0, 'off20')])
    [(111, 7), (0, 5), (0, 8), (0, 1), (0, 10), (0, 1)]

    >>> pack_j([(0x6f, 'jal'), (0, 'rd', 'x0'), (-2, 'off20')])
    [(111, 7), (0, 5), (255, 8), (1, 1), (1022, 10), (1, 1)]

    >>> pack_j([(0x6f, 'jal'), (2, 'rd', 'x2'), ('home', 'off20')])
    [(111, 7), (2, 5), ('home[19:12]', 'off8'), ('home[11:11]', 'off1'), ('home[10:1]', 'off10'), ('home[20:20]', 'off1')]
    """
    (op, rd, imm) = instr
    op = bits.u(subv.untag(op), 7)
    rd = bits.u(subv.untag(rd, 'rd'), 5)

    if subv.is_reference(imm):
        imm = default_slice(imm, 20, 1)
    else:
        imm = bits.i(subv.untag(imm, 'off20'), 20)

    imm_lo = slice_bit_or_ref(imm,  9,  0) # + ('off[10:1]',)
    imm_11 = slice_bit_or_ref(imm, 10, 10) # + ('off[11]',)
    imm_hi = slice_bit_or_ref(imm, 18, 11) # + ('off[19:12]',)
    imm_20 = slice_bit_or_ref(imm, 19, 19) # + ('off[20]',)

    return [op, rd, imm_hi, imm_11, imm_lo, imm_20]

def pack_b(instr):
    """ verify & pack B-type instructions.

    >>> pack_b([(0x63, 'branch'), (0, 'subop', '=='), (6, 'rs'), (0, 'rs'), (0, 'off12')])
    [(99, 7), (0, 1), (0, 4), (0, 3), (6, 5), (0, 5), (0, 6), (0, 1)]

    >>> pack_b([(0x63, 'branch'), (0, 'subop', '=='), (6, 'rs'), (0, 'rs'), (-2, 'off12')])
    [(99, 7), (1, 1), (14, 4), (0, 3), (6, 5), (0, 5), (63, 6), (1, 1)]

    >>> pack_b([(0x63, 'branch'), (0, 'subop', '=='), (6, 'rs'), (0, 'rs'), ('home', 'off12')])
    [(99, 7), ('home[11:11]', 'off1'), ('home[4:1]', 'off4'), (0, 3), (6, 5), (0, 5), ('home[10:5]', 'off6'), ('home[12:12]', 'off1')]
    """
    (op, sub, rs1, rs2, imm) = instr
    op  = bits.u(subv.untag(op), 7)
    sub = bits.u(subv.untag(sub, 'subop'), 3)
    rs1 = bits.u(subv.untag(rs1, 'rs'), 5)
    rs2 = bits.u(subv.untag(rs2, 'rs'), 5)

    if subv.is_reference(imm):
        imm = default_slice(imm, 12, 1)
    else:
        imm = bits.i(subv.untag(imm, 'off12'), 12)

    imm_lo = slice_bit_or_ref(imm,  3,  0) # + ('off[4:1]',)
    imm_md = slice_bit_or_ref(imm,  9,  4) # + ('off[10:5]',)
    imm_11 = slice_bit_or_ref(imm, 10, 10) # + ('off[11]',)
    imm_12 = slice_bit_or_ref(imm, 11, 11) # + ('off[12]',)
    return [op, imm_11, imm_lo, sub, rs1, rs2, imm_md, imm_12]

instr_map = {
    # 'opr': (pack_r, 0x33),
    'load': (pack_i, 0x03),
    'opi': (pack_i, 0x13),
    'jalr': (pack_i, 0x67),
    'store': (pack_s, 0x23),
    'branch': (pack_b, 0x63),
    'lui': (pack_u, 0x37),
    'auipc': (pack_u, 0x17),
    'jal': (pack_j, 0x6f),
}

def format(iter):
    segment = None
    for line in iter:
        line = subv.parse(line)

        if segment == 'code' and line['type'] == 'instr':
            op = line['instr'][0]
            assert len(op) == 2, 'instruction without op label: {}'.format(op)

            (op, label) = op
            if label not in instr_map:
                raise ValueError("unknown instruction label: {}".format(label))
            (formatter, expected) = instr_map[label]
            if op != expected:
                raise ValueError("opcode {} doesn't match label {} (expected {})"
                                 .format(op, label, expected))

            line['instr'] = formatter(line['instr'])
            yield subv.format(line)
        else:
            if line['type'] == 'segment':
                segment = line['segment'][0]
            yield line['raw']

if __name__ == '__main__':
    import sys
    for line in format(sys.stdin):
        print(line)

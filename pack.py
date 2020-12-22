#!/usr/bin/env python3
""" pack.py
Packs bitfields tagged with their size into untagged bytes.

>>> from io import StringIO
>>> # doctest: +REPORT_NDIFF
... print(subv.join_all(pack(StringIO('''
... == code 0x80000000
... 37/7 05/5 10010/20
... 13/7 06/5 00/3 00/5 48/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... 13/7 06/5 00/3 00/5 65/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... 13/7 06/5 00/3 00/5 6c/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... 13/7 06/5 00/3 00/5 6c/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... 13/7 06/5 00/3 00/5 6f/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... 13/7 06/5 00/3 00/5 0a/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... 6f/7 00/5 ff/8 01/1 3e6/10 01/1
... '''[1:-1]))))
== code 0x80000000
b7 02 01 10
13 03 80 04
23 a0 62 00
13 03 50 06
23 a0 62 00
13 03 c0 06
23 a0 62 00
13 03 c0 06
23 a0 62 00
13 03 f0 06
23 a0 62 00
13 03 a0 00
23 a0 62 00
6f f0 df fc
"""

import subv
import bits

def byteify(word):
    """ split longer bitfield into bytes.

    >>> byteify((0x12345678, 32))
    [(120,), (86,), (52,), (18,)]
    >>> byteify((0x4801813, 32))
    [(19,), (24,), (128,), (4,)]
    >>> byteify((0x13, 9)),
    Traceback (most recent call last):
        ...
    AssertionError: not byte aligned: 9 bits
    """
    (val, size) = word
    assert size % 8 == 0, "not byte aligned: {} bits".format(size)

    out = []
    for i in range(0, size, 8):
        byte = bits.slice(word,  i+7,  i)
        out.append(byte[:1])
    return out

def pack(iter):
    segment = None
    for line in iter:
        line = subv.parse(line)
        if line['type'] == 'instr':
            fields = [bits.from_part(p) for p in line['instr']]
            total = bits.concat(*fields)

            line['instr'] =  byteify(total)
            yield subv.format(line)
        else:
            if line['type'] == 'segment':
                segment = line['segment'][0]
            yield line['raw']

if __name__ == '__main__':
    import sys
    for line in pack(sys.stdin):
        print(line)

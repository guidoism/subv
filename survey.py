#!/usr/bin/env python3
""" survey.py
Resolves label references and substitutes them with literal values.

>>> from io import StringIO
>>> # doctest: +REPORT_NDIFF
... print(subv.join_all(survey(StringIO('''
... == code 0x80000000
... main:
... # load 0x10010000 (UART0) into t0
... 37/7 05/5 10010/20
... # store 0x48 (H) in UART0+0
... 13/7 06/5 00/3 00/5 48/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... # store 0x65 (e) in UART0+0
... 13/7 06/5 00/3 00/5 65/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... # store 0x6c (l) in UART0+0
... 13/7 06/5 00/3 00/5 6c/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... # store 0x6c (l) in UART0+0
... 13/7 06/5 00/3 00/5 6c/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... # store 0x6f (o) in UART0+0
... 13/7 06/5 00/3 00/5 6f/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... # store 0x0a (\\\\n) in UART0+0
... 13/7 06/5 00/3 00/5 0a/12
... 23/7 00/5 02/3 05/5 06/5 00/7
... # jump back up to the top
... 6f/7 00/5 main[19:12]/off8 main[11:11]/off1 main[10:1]/off10 main[20:20]/off1
... '''[1:-1]))))
== code 0x80000000
37/7 05/5 10010/20
13/7 06/5 00/3 00/5 48/12
23/7 00/5 02/3 05/5 06/5 00/7
13/7 06/5 00/3 00/5 65/12
23/7 00/5 02/3 05/5 06/5 00/7
13/7 06/5 00/3 00/5 6c/12
23/7 00/5 02/3 05/5 06/5 00/7
13/7 06/5 00/3 00/5 6c/12
23/7 00/5 02/3 05/5 06/5 00/7
13/7 06/5 00/3 00/5 6f/12
23/7 00/5 02/3 05/5 06/5 00/7
13/7 06/5 00/3 00/5 0a/12
23/7 00/5 02/3 05/5 06/5 00/7
6f/7 00/5 ff/8 01/1 3e6/10 01/1
"""
import subv
import bits
import re

slice_re = re.compile(r'^([^\[]+)(?:\[(\d+):(\d+)\])?$')
field_re = re.compile(r'^(imm|off)(\d+)$')

def observe(part, rel_addr, map):
    """ resolve a label reference.

    >>> observe((3, '3'), 0, {})
    (3, '3')
    >>> observe(('label[31:0]', 'imm32'), 0, {'label': 1234})
    (1234, 32)
    >>> observe(('label[1:0]', 'imm32'), 0, {'label': 1234})
    (2, 2)
    >>> observe(('label[31:0]', 'off32'), 1000, {'label': 1234})
    (234, 32)
    >>> observe(('label[31:12]', 'off32'), 1000, {'label': 1234})
    (0, 20)
    >>> observe(('label[31:0]', 'off32'), 2000, {'label': 1000})
    (4294966296, 32)

    >>> observe(('label[32:0]', 'imm32'), 0, {})
    Traceback (most recent call last):
        ...
    AssertionError: undefined label 'label'
    """
    if not subv.is_reference(part):
        return part

    ref = subv.parse_reference(part)
    assert ref['label'] in map, "undefined label '{}'".format(ref['label'])
    addr = map[ref['label']]

    # @TODO: the hardcoded 32 here is not right, this is going to blow up
    # in some circumstances (e.g. a backwards branch 2<<18 bytes away)
    if ref['mode'] == 'imm':
        addr = bits.u(addr, 32)
    else:
        addr = bits.i(addr - rel_addr, 32)

    return bits.slice(addr, ref['hi'], ref['lo'])

def survey(iter):
    queue = []
    map = {}
    addr = -1
    for line in iter:
        line = subv.parse(line)
        line['addr'] = addr
        queue.append(line)

        # step forward addr
        if line['type'] == 'segment':
            segment, addr = line['segment']
        elif line['type'] == 'label':
            map[line['label']] = addr
        elif line['type'] == 'instr':
            bits = 0
            for part in line['instr']:
                if subv.is_reference(part):
                  ref = subv.parse_reference(part)
                  bits += ref['size']
                else:
                  bits += int(part[1])

            assert bits % 8 == 0, "line not byte-aligned"
            addr += bits // 8

    for line in queue:
        if line['type'] == 'instr':
            instr = []
            for part in line['instr']:
                observed = observe(part, line['addr'], map)
                instr.append(observed)
            line['instr'] = instr
            yield subv.format(line)
        elif line['type'] == 'segment':
            yield line['raw']

if __name__ == '__main__':
    import sys
    for line in survey(sys.stdin):
        print(line)

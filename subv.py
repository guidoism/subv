import re
white = re.compile(r'[ \t\.\n]+')
hex = re.compile(r'^\-?(0x)?[0-9a-f]+$')
slice_re = re.compile(r'^([^\[]+)(?:\[(\d+):(\d+)\])?$')
field_re = re.compile(r'^(imm|off)(\d+)$')

# parsing
def parse_part(part):
    """ parse a literal with attached metadata.

    >>> parse_part('0')
    (0,)
    >>> parse_part('00')
    (0,)
    >>> parse_part('0x00')
    (0,)

    >>> parse_part('12')
    (18,)
    >>> parse_part('0x12')
    (18,)

    >>> parse_part('-12')
    (-18,)
    >>> parse_part('-0x12')
    (-18,)

    >>> parse_part('00/with/tag')
    (0, 'with', 'tag')
    >>> parse_part('-12/and/tag')
    (-18, 'and', 'tag')

    >>> parse_part('label/tag*')
    ('label', 'tag*')
    >>> parse_part('$label/tag*')
    ('$label', 'tag*')
    >>> parse_part('label:suff/tag*')
    ('label:suff', 'tag*')
    >>> parse_part('$label:suff/tag*')
    ('$label:suff', 'tag*')
    >>> parse_part('label[3:1]/tag*')
    ('label[3:1]', 'tag*')
    >>> parse_part('$label:suff[11:0]/tag*')
    ('$label:suff[11:0]', 'tag*')
    """
    part = part.split('/')
    if hex.match(part[0]):
        part[0] = int(part[0], 16)
    return tuple(part)

def parse_instr(line):
    """ parse an instruction-line.

    >>> parse_instr('ff/op 0/subop/add 1/rd/x1 label[11:0]/imm12')
    [(255, 'op'), (0, 'subop', 'add'), (1, 'rd', 'x1'), ('label[11:0]', 'imm12')]
    """
    parts = white.split(line)
    parts = [parse_part(part) for part in parts if part != '']
    return parts

def parse_segment(line):
    """ parse a segment-line.

    >>> parse_segment('== code 0x8000')
    ('code', 32768)
    >>> parse_segment('== text')
    ('text',)
    """
    parts = white.split(line)
    if len(parts) == 3:
      return (parts[1], int(parts[2], 16))
    elif len(parts) == 2:
      return (parts[1],)
    else:
      raise ValueError("invalid segment line")

def parse_label(line):
    """ parse a label-line.

    >>> parse_label('some_label:')
    'some_label'
    >>> parse_label('$some:label:')
    '$some:label'
    """
    return line[:-1]

def parse_reference(part):
    """ parse a sliced-label part.

    >>> parse_reference(('lbl', 'imm32'))
    {'label': 'lbl', 'mode': 'imm', 'size': 32, 'meta': ()}

    >>> parse_reference(('x[11:0]', 'off12'))
    {'label': 'x', 'mode': 'off', 'size': 12, 'meta': (), 'hi': 11, 'lo': 0}
    """
    ref = part[0]
    field = part[1]

    label, hi, lo = slice_re.match(ref).groups()
    mode, size = field_re.match(field).groups()
    
    ref = {
        'label': label,
        'mode': mode,
        'size': int(size),
        'meta': part[2:],
    }

    if hi is not None:
        ref['hi'] = int(hi)
        ref['lo'] = int(lo)

    return ref

def classify(line):
    """ classify cleaned lines.

    >>> classify('')
    'empty'
    >>> classify('== code')
    'segment'
    >>> classify('== text 0x1000')
    'segment'
    >>> classify('some_label:')
    'label'
    >>> classify('$some:label:')
    'label'
    >>> classify('ff/op 0/subop/add 1/rd/x1 label[11:0]/imm12')
    'instr'
    """
    if line == '':
        return 'empty'
    elif line.startswith('=='): # segment
        return 'segment'
    elif line.endswith(':'): # label
        return 'label'
    else:
        return 'instr'

def parse(line):
    """ clean, classify and parse lines.
    """
    raw = line.strip()
    split = raw.split('#', 1)
    if len(split) == 1:
        clean = raw
        comment = None
    else:
        clean, comment = split

    type = classify(clean)

    if type == 'segment':
        parsed = parse_segment(clean)
    elif type == 'label':
        parsed = parse_label(clean)
    elif type == 'instr':
        parsed = parse_instr(clean)
    else:
        parsed = None

    return {
        'type': type,
        'raw': raw,
        'line': clean,
        'comment': comment,
        type: parsed,
    }

def is_reference(part):
    """ check whether a part is a label reference.

    >>> is_reference(('hello',))
    True
    >>> is_reference(('hello:world',))
    True
    >>> is_reference(('$label',))
    True
    >>> is_reference(('$label:extra',))
    True
    >>> is_reference(('$label:extra', 'off20'))
    True
    >>> is_reference(('plain', 'off20'))
    True

    >>> is_reference((0,))
    False
    >>> is_reference((1,))
    False
    >>> is_reference((1, 'disp20'))
    False
    >>> is_reference((0x13f, 'imm12'))
    False
    """
    return isinstance(part[0], str)

def untag(part, expect=None):
    """ returns the value of a part and optionally verifies the first tag.

    >>> untag((2, 'num'))
    2
    >>> untag(('$label', 'imm20'))
    '$label'
    >>> untag((2, 'hello', 'things'))
    2

    >>> untag((2, 'num'), expect='num')
    2
    >>> untag(('$label', 'imm20'), expect='imm20')
    '$label'

    >>> untag((2, 'imm12'), expect='imm20')
    Traceback (most recent call last):
        ...
    ValueError: expected (2, 'imm12') to be labelled imm20
    >>> untag(('$label', 'imm20'), expect='off12')
    Traceback (most recent call last):
        ...
    ValueError: expected ('$label', 'imm20') to be labelled off12
    """
    if expect and part[1] != expect:
        raise ValueError("expected {} to be labelled {}".format(part, expect))
    return part[0]

def format_part(part):
    """ oppposite of parse_part.

    >>> format_part((0,))
    '00'
    >>> format_part((0x00,))
    '00'

    >>> format_part(('label', 'tag*'))
    'label/tag*'
    >>> format_part(('$label', 'tag*'))
    '$label/tag*'
    >>> format_part(('label:suff', 'tag'))
    'label:suff/tag'
    >>> format_part(('$label:suff', 'tag'))
    '$label:suff/tag'
    """
    if not is_reference(part):
        first = '{:02x}'.format(part[0])
        part = (first, *part[1:])
    return '/'.join([str(p) for p in part])

def format(line):
    """ oppposite of parse.

    >>> format({
    ...     'type': 'instr',
    ...     'instr': [(255, 'op'), (0, 'subop', 'add'), (1, 'rd', 'x1'), ('label[11:0]', 'imm12')],
    ...     'comment': "this does things."
    ... })
    'ff/op 00/subop/add 01/rd/x1 label[11:0]/imm12 # this does things.'
    """
    if line['type'] == 'instr':
      packed = ' '.join(format_part(part) for part in line['instr'])
      if line['comment']:
          packed = packed + ' # ' + line['comment']
      return packed
    else:
      raise NotImplementedError()

def join_all(gen):
    res = '\n'.join(gen)
    return res

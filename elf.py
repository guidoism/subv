#!/usr/bin/env python3
import sys
import subv

"""
Takes a packed & surveyed hex stream (with section headers) and packs it into a
simulatable ELF file that can be run as a kernel:

    qemu-system-riscv32 -nographic -machine sifive_u -nographic -kernel out.elf

sifive-u has lots of memory mapped peripherals, see
https://github.com/qemu/qemu/blob/master/hw/riscv/sifive_u.c#L66-L83

Among them are two memory-mapped virtual UARTs at 0x10010000 and 0x10011000.
Writing to UART0+0x0 writes to qemu's output TTY, and reading from UART0+0x4
reads from it. The MSB in UART0+0x4 is set if there is nothing to read.
See full documentation here:
https://sifive.cdn.prismic.io/sifive/4d063bf8-3ae6-4db6-9843-ee9076ebadf7_fe310-g000.pdf
"""

def w(b):
    sys.stdout.buffer.write(b)
    return len(b)

def wi(num, size=2):
    sys.stdout.buffer.write(num.to_bytes(size, byteorder='little'))
    return size

def padto(offset, cursor):
    missing = offset - cursor
    if missing < 0:
        raise ValueError("cursor {} already past offset {}!".format(cursor, offset))
    w(b'\x00' * missing)
    return offset

def write_elf_header(segments):
    c = 0

    code = next(s for s in segments if s['name'] == 'code')
    entrypoint = code['addr']

    c += w(b"\x7fELF")     # ELF magic
    c += wi(0x010101, 4)   # 32bit, little endian
    c += wi(0, 8)          # reserved
    c += wi(0x02)          # e_type
    c += wi(0xf3)          # e_machine
    c += wi(0x01, 4)       # e_version
    c += wi(entrypoint, 4) # e_entry
    c += wi(0x34, 4)       # e_phoff (Program Header offset)
    c += wi(0x00, 4)       # e_shoff (Section Header offset, unused)
    c += wi(0x0004, 4)     # e_flags
    c += wi(0x34)          # e_ehsize
    c += wi(0x20)          # e_phentsize
    c += wi(len(segments)) # e_phnum
    c += wi(0x28)          # e_shentsize
    c += wi(0x0)           # e_shnum
    c += wi(0x0)           # e_shstrndx
    return c

def write_program_header(segment, c, start):
    align = 0x1000
    offset = (1 + start // align) * align
    segment['offset'] = offset
    start = segment['addr']
    size = len(segment['content'])
    flags = 5 if segment['name'] == "code" else 6

    if offset % align != start % align:
        print("{:02x} {:02x}".format(offset, offset % align))
        print("{:02x} {:02x}".format(start, start % align))
        raise ValueError("improper alignment")

    c += wi(0x1, 4)    # p_type
    c += wi(offset, 4) # p_offset
    c += wi(start, 4)  # p_vaddr
    c += wi(start, 4)  # p_paddr
    c += wi(size, 4)   # p_filesz
    c += wi(size, 4)   # p_memsz
    c += wi(flags, 4)    # p_flags, 0x5=rx, 0x6=rw
    c += wi(align, 4)  # p_align
    return c

if __name__ == "__main__":
    segments = []
    segment = None
    for line in sys.stdin:
        line = subv.parse(line)

        if line['type'] == 'segment':
            (name, addr) = line['segment']
            segment = { 'name': name, 'addr': addr, 'content': [] }
            segments.append(segment)
        elif line['type'] == 'instr':
            if segment == None:
              raise ValueError("label or code outside of segment!")

            segment['content'] += line['instr']
        else:
            raise ValueError("elf input should contain only segments and instructions!")

    cursor = 0

    c = write_elf_header(segments)
    segment_start = 0x1000
    for seg in segments:
        c = write_program_header(seg, c, segment_start)
        segment_start = seg['offset'] + len(seg['content'])

    for seg in segments:
        c = padto(seg['offset'], c)
        for part in seg['content']:
            c += wi(part[0], 1)

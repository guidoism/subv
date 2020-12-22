# SubV

This is a wip clone of [SubX][mu] for the RISC-V RV31I base ISA.

    $ <label_test.subv ./format.py | ./survey.py | ./pack.py | ./elf.py >out.elf
    $ ./qemu.sh out.elf

## Status

Features:

- ELF output: ✔️
- Free arg order: ❌
- SubX cross-asm: ❌

Instruction Groups:

- OP-IMM: ✔️✔️
- OP: ✔️❌
- LUI: ✔️✔️
- AIUPC: ✔️❌
- JAL: ✔️✔️
- JALR: ✔️❌
- BRANCH: ❌❌
- LOAD: ✔️❌
- STORE: ✔️✔️

(✔️❌: implemented but untested)

## Pipeline

back to front:

- `elf.py`: takes hex bytes and segment headers, outputs an ELF file
- `pack.py`: packs bitfields (`3/3 1/1 f/4`) into hex bytes (`fb`)
- `survey.py`: replaces label references by their addresses
- `format.py`: checks op-arguments and chops and orders arguments into ISA formats

and now front to back with a little example:

    $ ./format.py <ex.subv   >ex.format
    $ ./survey.py <ex.format >ex.survey
    $ ./pack.py   <ex.survey >ex.pack
    $ ./elf.py    <ex.pack   >ex.elf
    $ ./qemu.sh ex.elf

`ex.subv`: hand-writable.

    == code 0x80000000
    # repeatedly print "Hi\\n"
    main:
      # load 0x10010000 (UART0) into t0
      37/lui 5/rd/t0 0x10010/imm20
      # store 0x48 (H) in UART0+0
      13/opi 0/subop/add 6/rd/t1 0/rs/x0 48/imm12
      23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
      # store 0x69 (i) in UART0+0
      13/opi 0/subop/add 6/rd/t1 0/rs/x0 69/imm12
      23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
      # store 0x0a (\n) in UART0+0
      13/opi 0/subop/add 6/rd/t1 0/rs/x0 0a/imm12
      23/store 2/subop/word 5/rs/t0 6/rs/t1 0/off12
      # jump back up to the top
      6f/jal 0/rd/x0 main/off21

`ex.format`: arguments sliced and diced and put into the ISA order.

    == code 0x80000000
    # repeatedly print "Hi\n"
    main:
    # load 0x10010000 (UART0) into t0
    37/7 05/5 10010/20
    # store 0x48 (H) in UART0+0
    13/7 06/5 00/3 00/5 48/12
    23/7 00/5 02/3 05/5 06/5 00/7
    # store 0x69 (i) in UART0+0
    13/7 06/5 00/3 00/5 69/12
    23/7 00/5 02/3 05/5 06/5 00/7
    # store 0x0a (\n) in UART0+0
    13/7 06/5 00/3 00/5 0a/12
    23/7 00/5 02/3 05/5 06/5 00/7
    # jump back up to the top
    6f/7 00/5 main/8/off21>>12 main/1/off21>>11 main/10/off21>>1 main/1/off21>>20

`ex.survey`: labels resolved, ready to be packed into hex format

    == code 0x80000000
    37/7 05/5 10010/20
    13/7 06/5 00/3 00/5 48/12
    23/7 00/5 02/3 05/5 06/5 00/7
    13/7 06/5 00/3 00/5 69/12
    23/7 00/5 02/3 05/5 06/5 00/7
    13/7 06/5 00/3 00/5 0a/12
    23/7 00/5 02/3 05/5 06/5 00/7
    6f/7 00/5 ff/8 01/1 3f2/10 01/1

`ex.pack`: fully packed, ready to run bare-metal

    == code 0x80000000
    b7 02 01 10
    13 03 80 04
    23 a0 62 00
    13 03 90 06
    23 a0 62 00
    13 03 a0 00
    23 a0 62 00
    6f f0 5f fe

`ex.elf`: binary file for use with `qemu` (see next section).

## Debugging

You can hook gdb into `qemu` using the `-s` flag, and make it halt on start
using the `-S` flag. `gdb` can be attached using `target remote localhost:1234`:

    $ ./qemu.sh out.elf -S -s
    # in another terminal
    $ riscv32-elf-gdb -iex "target remote localhost:1234"
    layout asm # show assembly trace
    nexti      # step forward one instruction
    c          # free-run forward

[mu]: https://github.com/akkartik/mu

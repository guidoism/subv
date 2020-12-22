#!/bin/sh
# build test.py and show disassembly
# options:
# -M numeric,no-aliases
./test.py | tail -n +2 | ../mu/apps/hex > a.bin
riscv32-elf-objcopy -I binary -O elf32-littleriscv a.bin a.elf
riscv32-elf-objdump -D a.elf "$@"

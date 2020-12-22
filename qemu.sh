#!/bin/sh
qemu-system-riscv32 -nographic -machine sifive_u -nographic -kernel "$@"

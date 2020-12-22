
# RISC-V full size Instructions Formats (32bit):

## R-format: op(rs1, rs2) -> rd
`opcode[7] rd[5] funct3[3] rs1[5] rs2[5] funct7[7]`

register arithmetic/logical
opcode: 0b0110011 / 0x33

| funct7 | funct3 | operation |
|========|========|===========|
| 0x0    | 0x0    | ADD       |
| 0x20   | 0x0    | SUB       |
| 0x0    | 0x1    | SLL       |
| 0x0    | 0x2    | SLT       |
| 0x0    | 0x3    | SLTU      |
| 0x0    | 0x4    | XOR       |
| 0x0    | 0x5    | SRL       |
| 0x20   | 0x5    | SRA       |
| 0x0    | 0x6    | OR        |
| 0x0    | 0x7    | AND       |

## I-Format: op(rs1, imm12) -> rd
`opcode[7] rd[5] funct3[3] rs1[5] imm[12]`

load
opcode: 0b0000011 / 0x03

- rs1: base address
- imm12: offset (scaled/signed by funct3)

| funct3 | operation |     |
|========|===========|=====|
| 0x0    | LB        | i8  |
| 0x1    | LH        | i16 |
| 0x2    | LW        | i32 |
| 0x4    | LBU       | u8  |
| 0x5    | LHU       | u16 |


immediate arhitmetic/logical
opcode: 0b0010011 / 0x13

- rs1: base address
- imm12: offset (scaled/signed by funct3)

| funct3 | operation |                              |
|========|===========|==============================|
| 0x0    | ADDI      |                              |
| 0x2    | SLTI      |                              |
| 0x3    | SLTIU     |                              |
| 0x4    | XORI      |                              |
| 0x6    | ORI       |                              |
| 0x7    | ANDI      |                              |
| 0x1    | SLLI      | imm12 = 0b0000000 , shamt[5] |
| 0x5    | SRLI      | imm12 = 0b0000000 , shamt[5] |
| 0x5    | SRAI      | imm12 = 0b0100000 , shamt[5] |


jalr
opcode = 0b1100111 / 0x67

- rs1: base address
- imm12: offset (bytes)
- save PC+4 in rd
- jump to offset

## S-format: op(rs1, rs2, imm12)
`opcode[7] imm4:0[5] funct3[3] rs1[5] rs2[5] imm11:5[7]`

store
opcode: 0b0100011 / 0x23

- rs1: base address
- rs2: data
- imm12: offset (scaled/signed by funct3)

| funct3 | operation |                          |
|========|===========|==========================|
| 0x0    | SB        | i8,  imm12 in bytes      |
| 0x1    | SH        | i16, imm12 in half-words |
| 0x2    | SW        | i32, imm13 in words      |

## SB-format: op(rs1, rs2, imm12/13)
`opcode[7] imm11[1] imm4:1[4] funct3[3] rs1[5] rs2[5] imm10:5[6] imm12[1]`

branch
opcode = 0b1100011 / 0x63

- rs1, rs2: registers to compare
- imm12/13: PC offset in half-words

| funct3 | operation |
|========|===========|
| 0x0    | BEQ       |
| 0x1    | BNE       |
| 0x4    | BLT       |
| 0x5    | BGE       |
| 0x6    | BLTU      |
| 0x7    | BGEU      |

## U-Format: op(imm20/32) -> rd
`opcode[7] rd[5] imm31:12[20]`
upper-bit immediates (lui, auipc)

lui
opcode: 0b0110111 / 0x37

- imm20: top 20 bits of rd
- clears bottom 12 bits
- combine lui + addi to load 32bit immediate
  NOTE: sign extension requires some trickery.

auipc:
opcode: 0b0010111 / 0x17

- imm20: top 20 bits of offset added to PC
- result stored in rd

## J-Format: op(imm20/21) -> rd
`opcode[7] rd[5] imm31:12[20]`
immediates on a 32bit scale (jal)

jal
opcode = 0b1101111 / 0x6f

- save PC+4 in rd
- imm20/21: PC offset in half-words

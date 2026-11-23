#!/usr/bin/env python3
"""Consulta localmente um ELF ARM64 e o script.json do Il2CppDumper."""

import argparse
from bisect import bisect_right
from collections import defaultdict
import json
import re
import struct

from capstone import CS_ARCH_ARM64, CS_GRP_CALL, CS_MODE_LITTLE_ENDIAN, Cs
from capstone.arm64 import ARM64_INS_ADRP, ARM64_INS_LDR, ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG
from elftools.elf.elffile import ELFFile


def integer(value):
    return int(value, 0)


def file_offset(elf, address, size=1):
    for segment in elf.iter_segments(type="PT_LOAD"):
        begin = segment["p_vaddr"]
        if begin <= address and address + size <= begin + segment["p_filesz"]:
            return address - begin + segment["p_offset"]
    raise ValueError(f"endereço fora dos dados PT_LOAD: 0x{address:x}")


def branch_target(word, address):
    opcode = word >> 26
    if opcode not in (0b000101, 0b100101):
        return None
    displacement = word & 0x03FFFFFF
    if displacement & (1 << 25):
        displacement -= 1 << 26
    return address + displacement * 4


def xrefs(section, names, boundaries, pattern):
    targets = {address for address, aliases in names.items()
               if any(pattern.search(name) for name in aliases)}
    start = section["sh_addr"]
    for index, (word,) in enumerate(struct.iter_unpack("<I", section.data())):
        address = start + index * 4
        target = branch_target(word, address)
        if target not in targets:
            continue
        owner_index = bisect_right(boundaries, address) - 1
        owner = boundaries[owner_index] if owner_index >= 0 else None
        caller = " | ".join(names.get(owner, ())) or (
            f"0x{owner:x}" if owner is not None else "?")
        callee = " | ".join(name for name in names[target] if pattern.search(name))
        opcode = "bl" if word >> 31 else "b"
        print(f"0x{address:08x} {caller} -> {opcode} 0x{target:08x} {callee}")


def disassemble(elf, section, dump, names, address, end):
    start = section["sh_addr"]
    if address % 4 or end % 4 or not start <= address < end <= start + section["sh_size"]:
        raise ValueError("intervalo desalinhado ou fora da seção il2cpp")
    slots = {entry["Address"]: repr(entry["Value"]) for entry in dump["ScriptString"]}
    slots.update((entry["Address"], entry["Name"])
                 for key in ("ScriptMetadata", "ScriptMetadataMethod") for entry in dump[key])
    relocations = {reloc["r_offset"]: reloc["r_addend"]
                   for reloc in elf.get_section_by_name(".rela.dyn").iter_relocations()
                   if reloc["r_info_type"] == 1027}  # R_AARCH64_RELATIVE
    arm = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    arm.detail = True
    pages = {}
    for insn in arm.disasm(section.data()[address - start:end - start], address):
        annotation = ""
        dest = branch_target(int.from_bytes(insn.bytes, "little"), insn.address)
        if dest in names:
            aliases = names[dest]
            annotation = " | ".join(aliases[:4])
            if len(aliases) > 4:
                annotation += f" | +{len(aliases) - 4} aliases"
        operands = insn.operands
        if (insn.id == ARM64_INS_LDR and len(operands) == 2 and
                operands[0].type == ARM64_OP_REG and operands[1].type == ARM64_OP_MEM):
            memory = operands[1].mem
            if memory.base in pages and not memory.index:
                slot = pages[memory.base] + memory.disp
                relocated = relocations.get(slot)
                if relocated in slots:
                    annotation = f"GOT 0x{slot:x} → 0x{relocated:x} {slots[relocated]}"
        if insn.group(CS_GRP_CALL):  # Descarta o estado linear ao atravessar uma chamada.
            pages.clear()
        for register in insn.regs_access()[1]:
            pages.pop(register, None)
        if insn.id == ARM64_INS_ADRP and operands[1].type == ARM64_OP_IMM:
            pages[operands[0].reg] = operands[1].imm
        suffix = f"  # {annotation}" if annotation else ""
        print(f"0x{insn.address:08x} {insn.mnemonic:<7} {insn.op_str}{suffix}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=argparse.FileType("rb"))
    parser.add_argument("dump", type=argparse.FileType())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("methods", "xrefs"):
        commands.add_parser(name).add_argument("pattern")
    asm = commands.add_parser("disasm")
    asm.add_argument("address", type=integer)
    asm.add_argument("--end", type=integer)
    scalars = commands.add_parser("value")
    scalars.add_argument("format", choices=("f32", "i32"))
    scalars.add_argument("address", type=integer, nargs="+")
    args = parser.parse_args()

    with args.elf, args.dump:
        elf = ELFFile(args.elf)
        section = elf.get_section_by_name("il2cpp")
        if elf["e_machine"] != "EM_AARCH64" or not elf.little_endian or section is None:
            parser.exit(1, "Esperado ELF AArch64 little-endian com seção il2cpp.\n")

        dump = json.load(args.dump)
        methods = dump["ScriptMethod"]
        names = defaultdict(list)
        for method in methods:
            if method["Address"]:
                names[method["Address"]].append(method["Name"])
        boundaries = sorted(set(dump["Addresses"]) | names.keys())
        try:
            if args.command == "methods":
                pattern = re.compile(args.pattern)
                for entry in methods:
                    if pattern.search(entry["Name"]):
                        address = entry["Address"]
                        offset = file_offset(elf, address) if address else None
                        print(f"RVA=0x{address:08x} offset={offset:#x} "
                              f"{entry['Name']} | {entry['Signature']}" if offset is not None
                              else f"sem endereço: {entry['Name']} | {entry['Signature']}")
            elif args.command == "xrefs":
                xrefs(section, names, boundaries, re.compile(args.pattern))
            elif args.command == "disasm":
                index = bisect_right(boundaries, args.address)
                end = args.end if args.end is not None else boundaries[index]
                disassemble(elf, section, dump, names, args.address, end)
            else:
                for address in args.address:
                    offset = file_offset(elf, address, 4)
                    args.elf.seek(offset)
                    fmt = "<f" if args.format == "f32" else "<i"
                    value, = struct.unpack(fmt, args.elf.read(4))
                    print(f"VA=0x{address:x} offset=0x{offset:x} {value}")
        except (ValueError, IndexError, re.error) as error:
            parser.exit(1, f"Erro: {error}\n")


if __name__ == "__main__":
    main()

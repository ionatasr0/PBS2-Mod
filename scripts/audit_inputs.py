#!/usr/bin/env python3
"""Identifica as entradas da auditoria PBS2 e verifica seus limites básicos."""

import argparse
import hashlib
import json
from pathlib import Path
import struct


FIXED_NAMES = ("global-metadata.dat", "libunity.so", "AndroidManifest.xml",
               "boot.config", "ScriptingAssemblies.json")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(directory, il2cpp_name):
    for name in (*FIXED_NAMES, il2cpp_name):
        path = directory / name
        print(f"{name}\t{path.stat().st_size}\t{sha256(path)}")

    for name in (il2cpp_name, "libunity.so"):
        with (directory / name).open("rb") as stream:
            header = stream.read(64)
        if len(header) != 64 or header[:7] != b"\x7fELF\x02\x01\x01":
            raise ValueError(f"{name}: esperado ELF64 little-endian")
        if struct.unpack_from("<HH", header, 16) != (3, 183):
            raise ValueError(f"{name}: esperado ET_DYN AArch64")
        print(f"{name}: ELF64 AArch64 ET_DYN")

    metadata = (directory / "global-metadata.dat").read_bytes()
    magic, version, header_size = struct.unpack_from("<III", metadata)
    if (magic, version) != (0xFAB11BAF, 27):
        raise ValueError("esperado magic IL2CPP e versão 27")
    if header_size < 16 or header_size > len(metadata) or (header_size - 8) % 8:
        raise ValueError("tamanho inválido para o cabeçalho v27")
    spans = list(struct.iter_unpack("<II", metadata[8:header_size]))
    for offset, size in spans:
        if size and (offset < header_size or offset + size > len(metadata)):
            raise ValueError(f"tabela IL2CPP fora do arquivo em 0x{offset:x}")
    print(f"IL2CPP: magic=0x{magic:08x}, versão={version}, "
          f"{len(spans)} pares offset/tamanho dentro dos limites")

    manifest = (directory / "AndroidManifest.xml").read_bytes()
    if struct.unpack_from("<HHI", manifest) != (3, 8, len(manifest)):
        raise ValueError("cabeçalho AXML inválido")
    assemblies = json.loads((directory / "ScriptingAssemblies.json").read_text())
    if len(assemblies["names"]) != len(assemblies["types"]):
        raise ValueError("listas names e types de tamanhos diferentes")
    print(f"AXML válido no cabeçalho. ScriptingAssemblies: {len(assemblies['names'])} registros")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--il2cpp-name", default="libil2cpp.so")
    args = parser.parse_args()
    try:
        audit(args.directory, args.il2cpp_name)
    except (OSError, ValueError, KeyError, struct.error) as error:
        parser.exit(1, f"Erro: {error}\n")


if __name__ == "__main__":
    main()

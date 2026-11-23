# Ambiente e reprodução

## Identidade das entradas

| Nome recebido | Bytes | SHA-256 |
| --- | ---: | --- |
| `libil2cpp(1).so` | 47.179.472 | `13198545e048459c5be0e00030963bb28a5c371800217fb332ac6ab90bed4a54` |
| `libunity.so` | 24.673.912 | `2c0b58b33e014db5de856ed83b8671f26b375c5ee12ebd90bb09292b87273f5e` |
| `global-metadata.dat` | 9.139.004 | `4851d0afdde440998bb3c52030d0357ac0ffa990fcee22d4465b0ff4042a2097` |
| `AndroidManifest.xml` | 8.608 | `81e77f3817081371440cbc5cef35dcdedd992e21cc058585d9e4486cf2d2af7e` |
| `boot.config` | 156 | `7f227ea2458b7b216f0338f8ae6e4d10df7fa98c0aebeb5fb899e67780759b70` |
| `ScriptingAssemblies.json` | 4.325 | `5e75d573dc80572aac6bc3995ea4593276a2f5f7ffced3a846ab19bda13775b2` |

A análise usou cópias dos seis anexos desta execução. Ambos os ELF são `ET_DYN`, AArch64, little-endian, stripados e têm notas do NDK r19 para API 21. Os Build IDs são `49e8ff251fec44e8a27303f7efd3460c481f50f6` para IL2CPP e `f5dc651d2ff2d749a773985e5aafffb52cec2251` para Unity. A nota `.note.unity` identifica `2020.3.39f1_fd6670bb8be9`. O AXML informa `aaa.core.mods2`, versionCode/versionName `309`, minSdk 19 e targetSdk 33. `boot.config` confirma HDR desabilitado e contém `gc-max-time-slice=3`, sem declarar o modo gráfico ativo ou uma política de resolução dinâmica.

**Confiança alta** na identidade dos arquivos e no emparelhamento estático IL2CPP/metadados, sustentado por tabelas válidas e chamadas coerentes. O APK assinado seria necessário para provar a origem comum de todos os anexos como unidade de distribuição. Os hashes permitem identificar as amostras e conferir que as cópias ficaram intactas.

## Ferramentas usadas

| Ferramenta | Versão e observação |
| --- | --- |
| Python e binutils | Python 3.12.14, GNU readelf 2.44, file 5.46. O GNU objdump instalado lista alvos x86, então a desmontagem AArch64 usou Capstone. |
| Il2CppDumper | 6.7.46, distribuição .NET 7, executada com .NET Runtime 8.0.0 via `--roll-forward Major`. ZIP SHA-256 `c7f365347ce6bd816cdf774830e44ac46aea59c391c94f388605667394d6aba2`. |
| Biblioteca de análise | Capstone 5.0.7 e pyelftools 0.32. O rastreamento de chamadas diretas verifica instruções `B/BL` na seção `il2cpp`. Chamadas virtuais, delegados e lambdas indiretos exigem inspeção adicional. |
| Android AXML | AAPT2 Linux x64 2.19-eng.000000, extraído do Apktool 2.11.1. O comando `decode --only-manifest` foi rejeitado nessa versão do Apktool. AAPT2 leu o AXML de um ZIP temporário com uma única entrada. |
| Dispositivo | Samsung Galaxy M34 5G com Android 16 é a referência. Esta execução não tinha telefone conectado ou ADB disponível. |

## Reproduzir a inspeção

No diretório do repositório, copie os seis anexos para `inputs/`. Os comandos abaixo mantêm o nome recebido de `libil2cpp(1).so`. Instale as dependências de rastreamento no ambiente Python e coloque a distribuição oficial do Il2CppDumper em `tools/dumper/`.

```sh
mkdir -p out
python3 -m pip install -r scripts/requirements.txt
python3 scripts/audit_inputs.py inputs --il2cpp-name 'libil2cpp(1).so'
readelf -h -lW -n inputs/libunity.so
readelf -h -lW -n 'inputs/libil2cpp(1).so'
script -q -e -c 'dotnet --roll-forward Major tools/dumper/Il2CppDumper.dll "inputs/libil2cpp(1).so" inputs/global-metadata.dat out' out/dumper.log <<<'x'
```

O comando `script` acima usa Bash e `script` do util-linux. A primeira execução redirecionada terminou com código 134 em `Console.ReadKey` após concluir todas as saídas. A repetição com pseudoterminal terminou com código 0. `dump.cs` e `script.json` foram idênticos byte a byte nas duas execuções.

```sh
python3 -m zipfile -c out/manifest-only.zip inputs/AndroidManifest.xml
unzip -jo tools/apktool.jar prebuilt/linux/aapt2_64 -d tools
chmod +x tools/aapt2_64
tools/aapt2_64 dump xmltree --file AndroidManifest.xml out/manifest-only.zip
```

O ZIP temporário é só um contêiner para o AXML e não é instalável. O comando de leitura com AAPT2, a reconstrução na ordem acima, `audit_inputs.py` e os quatro subcomandos de `trace_il2cpp.py` foram executados nas amostras. Entradas, arquivos de saída e ferramentas baixadas ficam fora do Git.

[Il2CppDumper 6.7.46](https://github.com/Perfare/Il2CppDumper/releases/tag/v6.7.46) · [Apktool 2.11.1](https://github.com/iBotPeaches/Apktool/releases/tag/v2.11.1)

# Reconstrução IL2CPP

O cabeçalho contém magic `0xFAB11BAF` e versão inteira `27`. O verificador confirmou que os 31 pares de offset e tamanho cabem no arquivo. O Il2CppDumper 6.7.46 identificou o layout nativo como 27.1, aplicou relocações e recuperou `CodeRegistration` em VA `0x2AF2F38` e `MetadataRegistration` em VA `0x2AF2FB0`.

A mensagem inicial sobre `JNI_OnLoad` e possível proteção é um diagnóstico heurístico da ferramenta. A própria busca encontrou os registros, gerou todas as saídas e permitiu confirmar referências cruzadas coerentes. Os cabeçalhos recuperados descrevem classes e assinaturas. O corpo dos métodos foi investigado por desmontagem ARM64 em pontos selecionados.

| Resultado | Contagem |
| --- | ---: |
| Imagens gerenciadas no dump | 91 |
| Definições de tipos | 10.930 |
| Entradas `ScriptMethod`, incluindo compartilhamento de código genérico | 109.968 |
| Endereços distintos e não nulos em `ScriptMethod` | 103.144 |
| Entradas de literais | 18.480 |
| Entradas do inventário `ScriptingAssemblies.json` | 120 |
| Nomes em comum entre inventário e dump | 79 |

O inventário de scripting e as imagens gerenciadas nativas têm escopos diferentes. Por exemplo, o dump acrescenta `mscorlib` e assemblies `System.*`, enquanto o inventário inclui módulos que não aparecem entre as imagens recuperadas. A diferença de contagem, por si só, não demonstra mistura de versões.

| Imagem ou namespace recuperado | Evidência relevante |
| --- | --- |
| `Assembly-CSharp.dll` | `MepMobileControls`, `FPSDisplayNovo`, `InstalaZipPersistenteHANDLER`, `TrocaItinerario`, `ProtonPaths`, `XFrameEffect`, `VehiclePhysics` e `Mep.MEPControlesBus` |
| `System.IO.Compression.FileSystem.dll` | `ZipFile.ExtractToDirectory` recebe chamada direta da coroutine do instalador |
| `SimpleFileBrowser.Runtime.dll` | `WaitForLoadDialog` recebe chamada direta do fluxo de importação de pastas |
| `ImaginationOverflow.UniversalFileAssociation*` | Callback de ativação de ZIP e ponte de leitura Android |
| `ICSharpCode.SharpZipLib.dll` | Assembly presente. O fluxo de compartilhamento auditado chama `System.IO.Compression`. |
| `Unity.Postprocessing.Runtime.dll` | Chamadas aos getters de escala do `ScalableBufferManager` no pós-processamento |

Nesta amostra a região de código executável pertence a um `PT_LOAD` com `p_offset = p_vaddr = 0`. Os RVAs de código documentados coincidem com os offsets de arquivo. Endereços de dados e registros devem ser convertidos pelo segmento correspondente. O endereço de execução depende da base de carregamento e do ASLR.

Reprodução a partir da raiz, com o dump gerado em `out/` conforme [ambiente](environment.md).

```sh
trace() { python3 scripts/trace_il2cpp.py 'inputs/libil2cpp(1).so' out/script.json "$@"; }
trace methods 'XFrameManager\$\$(LateUpdate|CheckRT|PrepareAdaptativeRenderTexture)$'
trace xrefs 'XFrameManager\$\$set_(method|targetFPS|downsampling|staticCameraDownsampling)$'
trace disasm 0x20d87d4
```

A anotação de literais usa `ADRP/LDR` e `R_AARCH64_RELATIVE`. O rastreador é linear, então uma anotação em código com múltiplos caminhos deve ser conferida com os registradores e o salto correspondente. Para chamadas indiretas, a leitura do slot de metadados e da sequência local complementa a busca de `B/BL`.

**Confiança alta** nos métodos, endereços e chamadas identificadas. O próximo experimento é correlacionar os caminhos estáticos com comportamento no aparelho usando a mesma build.

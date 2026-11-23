# PBS2 Cabransa Edition

Auditoria estática da versão Android ARM64 do Proton Bus Simulator 2, com foco em resolução dinâmica, importação de mods, letreiros e física veicular. A amostra usa Unity **2020.3.39f1** e IL2CPP com cabeçalho **27** e layout nativo **27.1** identificado pelo Il2CppDumper.

O jogo ativa `XFrameEffect.XFrameManager` pelo menu gráfico. O caminho recuperado configura alvo adaptativo de **25 FPS** e escala mínima de **75%** em movimento e com a câmera parada. A textura intermediária usa uma grade de **10 pontos percentuais**, portanto o piso interno e a escala efetivamente rasterizada podem divergir. A cadência e o backend gráficos ativos no Galaxy M34 5G precisam ser medidos.

| Relatório | Conteúdo |
| --- | --- |
| [Ambiente e reprodução](analysis/environment.md) | Identidade das amostras, ferramentas, comandos e verificações |
| [Reconstrução IL2CPP](analysis/il2cpp-report.md) | Assemblies, namespaces e evidências nativas |
| [Resolução dinâmica](analysis/dynamic-resolution.md) | Ativação, escala, cadência e protocolo de desempenho |
| [ZIP e letreiros](analysis/mod-importer.md) | Associações Android, critérios de importação e estrutura efetivamente encontrada |
| [Física veicular](analysis/vehicle-physics.md) | Vehicle Physics, rodas, suspensão, motor, freios e articulação |
| [Viabilidade de patch](analysis/patch-feasibility.md) | Escopo de um experimento futuro e dados adicionais mínimos |

Os scripts operam sobre cópias locais fornecidas pelo pesquisador. `patches/` contém apenas um marcador de diretório.

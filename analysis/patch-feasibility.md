# Viabilidade de um patch experimental

## Parecer

A localização do XFrame torna **viável preparar um experimento estático**, com escopo preso ao SHA-256 do `libil2cpp` auditado. Ainda falta validar no M34 a aplicação real dos limites, a cadência e a coexistência com o controle de qualidade geral.

| Objetivo | Viabilidade e dependência |
| --- | --- |
| Pisos 80% em movimento e câmera parada | Alta confiança na localização das duas entradas em `AtivaXFrameAccelerator`. Os setters já aceitam esse valor. O teto 100% e a inicialização 100% já estão presentes. É preciso conferir a escala global de tela e a escala da textura no mesmo ensaio. |
| Alvo adaptativo 45 ou 40 FPS | Alta confiança na localização do setter. O valor de `Application.targetFrameRate` é estabelecido em outro ponto e pode ser alterado mais tarde por opções e pelo redutor geral. Confirmar os escritores ativos antes de alterar o limite de apresentação. |
| Degrau efetivo de 5 p.p. e janela de 1 s | Viabilidade condicionada a uma alteração coordenada no índice, cache, pré-aquecimento, alocação e limiar de troca das texturas, além do prazo de amostragem e cálculo do FPS. Ajustar apenas constantes de piso e alvo não entrega esse perfil. |
| Importação de letreiros | Requer reconhecimento próprio ou seletor dentro do app. O ZIP compartilhado dispara um instalador que procura marcadores de ônibus/mapa. A compatibilidade do fluxo existente deve ser testada com exemplos válidos antes de ampliar o reconhecimento. |
| Física | O desenho atual permite investigar calibração por veículo e controles existentes. Troca de simulador exigiria integração extensa com prefabs e formatos. O primeiro teste deve variar um parâmetro de uma configuração de mod própria. |

## Reconstrução Unity e empacotamento Android

Um futuro experimento em uma cópia ARM64 pode alterar o componente compilado afetado, preservando o conteúdo de `data.unity3d` e dispensando uma recompilação completa do projeto Unity. Um delta distribuível teria de vincular origem e resultado a hashes exatos e ser aplicado localmente por quem possui a amostra. Essa abordagem ainda exigiria um mecanismo autorizado de instalação ou execução da versão de teste.

Alterar um arquivo dentro de um APK muda o conteúdo coberto pela assinatura Android. Uma variante instalável precisaria ser empacotada e assinada de forma autorizada. Atualizar por cima da instalação oficial depende da assinatura compatível ou do mecanismo oficial de distribuição. Para testes fora do pacote original, a rota preferível é um build de QA do mantenedor ou uma instalação isolada que preserve a instalação e os dados do usuário. O manifesto indica `extractNativeLibs=true`, mas isso por si só não autoriza nem prova ser possível trocar uma biblioteca da instalação existente. Nenhum método de execução de código em tempo de execução foi necessário para a auditoria. [Assinatura de apps Android](https://developer.android.com/studio/publish/app-signing)

## O que pedir somente se necessário

| Dúvida | Menor entrada útil |
| --- | --- |
| Backend, Hz efetivos e quedas de desempenho | Registro de `dumpsys display`, log de inicialização com backend quando disponível e captura Perfetto de uma sessão da build 309 no M34. Backend e timing interno podem exigir log ou build de diagnóstico do mantenedor. |
| Configuração ativa da câmera, API gráfica e assets do pipeline | Exportação apenas das configurações de Player/Graphics e do prefab ou da cena com a câmera representativa, caso os dados de runtime não resolvam a dúvida. |
| Ponte Java para ZIP ou fotos | Apenas o DEX que define a atividade e o plugin Java da URI/seletor, se o teste comportamental deixar a rota em aberto. |
| Física de um ônibus específico | Configuração de um mod próprio e, quando necessário, prefab serializado desse ônibus. Para o caso de articulação, incluir a configuração da junta e dos corpos rígidos do modelo testado. |

Os seis arquivos atuais bastaram para a reconstrução, para o rastreamento estático e para a decisão de viabilidade inicial. O próximo passo experimental é a captura da build original no M34, antes de escolher os parâmetros de um protótipo. A validação deve incluir regressão de ônibus, mapas e letreiros e comparação com uma captura de referência. `patches/` fica reservado para alterações futuras validadas.

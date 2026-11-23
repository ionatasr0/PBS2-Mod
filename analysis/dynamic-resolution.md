# Resolução dinâmica

## Controlador identificado

O acelerador de resolução do jogo é `XFrameEffect.XFrameManager`, acionado por `MepMobileControls` em `Assembly-CSharp.dll`. O caminho foi confirmado em ARM64, desde a leitura da preferência até a atribuição de uma render texture à câmera. A confiança é **alta** para a implementação recuperada e seus valores estáticos. O comportamento em cena e o desempenho no Galaxy M34 5G ainda precisam de medição.

| Método e RVA/offset | Evidência executada |
| --- | --- |
| `MepMobileControls.Awake()` · `0x20D31A8` | Lê `usarXFrameAccelerator`, com padrão zero, e guarda a comparação com 1 no campo estático `+0x8B`. A chamada de ativação ocorre em `0x20D6128`. No arranque, a opção também força o modo 0 de `AcertaResolucaoAgora` em `0x20D5CD4`. |
| `MepMobileControls.AtivaXFrameAccelerator()` · `0x20D87D4` | Quando habilitado, desativa `allowMSAA` na câmera, adiciona `XFrameManager` ao GameObject e passa modo 1 (`AdaptativeDownsampling`), alvo **25 FPS**, pisos **0,75** em movimento e com câmera parada, flags de sombras e luzes por pixel em falso e `antialias = 2` para o XFrame. |
| `XFrameManager.Init()` · `0xB4DEA0` | Escreve escala acumulada inicial **1,0** em `+0xB0` antes de configurar o caminho de renderização. |
| `XFrameManager.Start()` · `0xB4E758` e `LateUpdate()` · `0xB4E794` | Usa `Time.realtimeSinceStartup`, contador de quadros e janela de **0,5 s**. O primeiro prazo é inicializado em `0xB4E770`. A estimativa normal dobra o contador, atualiza o prazo em `0xB4EC20` e compara o resultado ao alvo em `+0x28`. |
| `XFrameManager.LateUpdate()` · `0xB4E794` | Reduz ou recupera a escala utilizando a diferença de FPS e os campos `_fpsChangeSpeedDown` e `_fpsChangeSpeedUp`. Cada chamada de `Mathf.Min` limita o ajuste pelo respectivo campo. Os padrões do construtor são cerca de **0,02** para cada sentido. O clamp de `0xB4ECC4` lê o piso de `+0x38` ou `+0x3C` com teto **1,0**. |
| `XFrameManager.set_downsampling(float)` · `0xB4D1AC`, `set_staticCameraDownsampling(float)` · `0xB4D210`, `rtClamp(float)` · `0xB4D1F4` | Os setters aceitam uma faixa até 1,0 com limite inferior genérico de aproximadamente **0,1**. A configuração móvel escolhe 0,75 dentro dessa faixa. |
| `XFrameManager.set_targetFPS(int)` · `0xB4CFA4` | O clamp em `0xB4CFD0` limita o alvo a **10–120 FPS**. As metas de 40 e 45 estão dentro do intervalo. |
| `XFrameManager.CheckRT()` · `0xB4CB90`, `PrepareAdaptativeRenderTexture()` · `0xB50014` | O modo adaptativo calcula `RoundToInt(escala × 10)`, usa a posição correspondente em `rtArray` e calcula largura e altura a partir dos valores de `Screen` multiplicados por `índice × 0,1`. `CheckRT` pode atribuir a textura em `Camera.targetTexture` na chamada de `0xB4CF28`. |
| `XFrameManager.FetchRT(int, int)` · `0xB4FEFC` | Constrói e cria uma `RenderTexture` em caso de necessidade. `PrepareAdaptativeRenderTexture` confere tamanho e `IsCreated` antes de reutilizar uma textura do cache. |
| `PostFrameCompositor.OnPostRender()` · `0xF43BC4` | Um dos caminhos de composição termina em `Graphics.Blit` em `0xF43D28`. O construtor do XFrame inicia em `SecondCameraBillboardWorldSpace` e o ativador móvel deixa o modo de composição como está. |

A janela usa FPS agregado. O caminho inspecionado não mostrou separação de tempo de CPU e GPU. `libunity.so` contém os nomes nativos `ScalableBufferManager::ResizeBuffers` e `FrameTimingManager::CaptureFrameTimings`, sem método gerenciado correspondente recuperado. Os getters de escala têm chamadas no pós-processamento. `CheckPipeline()` em `0xB4D714` procura a propriedade **`RenderScale`** por reflexão no ramo Lightweight, que depende do nome do pipeline e de configuração específica. Nenhum assembly URP/HDRP foi identificado. A configuração que o ativador móvel de fato escreve usa o caminho das texturas intermediárias. O suporte do Unity 2020.3 à resolução dinâmica nativa no Android é documentado para Vulkan. Isso não identifica o backend usado pela amostra no M34. [Manual do Unity 2020.3](https://docs.unity3d.com/2020.3/Documentation/Manual/DynamicResolution.html) · [FrameTimingManager](https://docs.unity3d.com/2020.3/Documentation/ScriptReference/FrameTimingManager.html)

## A escala e o limite de FPS são controles distintos

`XFrameManager.UpdateSettings()` usa `Application.targetFrameRate = 300` para os modos 1 a 3 e `-1` para o modo 0. A tabela de despacho começa em `0x2129AA0`. As chamadas ocorrem em `0xB4C798` e `0xB4C7BC`. O primeiro valor solicita uma frequência ao Unity, sujeita ao dispositivo. O alvo configurado no XFrame é usado para decidir quando reduzir ou recuperar a escala.

O jogo também tem um caminho de resolução de tela em `MepMobileControls.AcertaResolucaoAgora`, que chama `Screen.SetResolution` em `0x20D7DD8` e `0x20D8254`. `FPSDisplayNovo.VeSeTahBaixosFPSPraLimitarRecursos()` pode, em seus ramos, chamar esse caminho (`0xB1F828`), escrever limite de **30 FPS** (`0xB1F8A4`) e alterar o passo da física (`0xB1F918`). Outros escritores diretos incluem `MobileControl.Awake` e `MEPCanvasStart.SalvaConfig`. A janela, os escritores e a base de resolução devem ser verificados juntos para que 80% da resolução de referência não se torne 80% de uma resolução de tela já reduzida.

O Unity 2020.3 orienta escolher um divisor inteiro da taxa de atualização no Android e documenta que outros valores podem resultar em menos quadros que o solicitado. A Samsung anuncia tela de até 120 Hz no M34. Em **120 Hz**, **40 FPS a cada 3 VBlanks** é o primeiro candidato a cadência uniforme abaixo de 45. Em **60 Hz**, 30 FPS a cada 2 VBlanks é a referência uniforme abaixo de 45. Os **45 FPS** cabem em **90 Hz** se o dispositivo disponibilizar e efetivamente selecionar esse modo. O modo ativo, o comportamento dessa build e os intervalos apresentados precisam ser medidos. [Unity 2020.3](https://docs.unity3d.com/2020.3/Documentation/ScriptReference/Application-targetFrameRate.html) · [Samsung Brasil](https://news.samsung.com/br/samsung-apresenta-o-galaxy-m34-5g-no-brasil)

## Cabransa Adaptive Resolution 1.0

| Parâmetro | Resultado da auditoria e condição para validar |
| --- | --- |
| Meta 45 FPS | Viável como parâmetro de controle. O limitador do Unity e o FPS apresentado precisam de ensaio próprio. Ponto de partida para o M34 em 120 Hz: variante medida a 40 FPS, com alvo do controlador compatível com a cadência. |
| Limites 80–100% | Viável estaticamente para os dois pisos móveis e o teto existente. Medir a base de resolução e a escala efetivamente aplicada a cada eixo. |
| Início em 100% | Presente no `Init`. Conferir a primeira imagem apresentada e o reinício após troca de câmera e retomada. |
| Passo de 5 p.p. | Requer alterar a seleção de resolução efetiva e os consumidores do cache. Hoje o índice usa grade de 10 p.p. e o acumulador muda segundo a diferença de FPS e os coeficientes. |
| Avaliação a cada 1 s | Requer tratar o primeiro prazo, a recorrência e o cálculo de FPS. Trocar apenas o prazo manteria a multiplicação por dois e distorceria o FPS. |

A 80% em cada eixo, a cena tem cerca de **64%** dos pixels de 100%, antes de arredondamento e composição. O orçamento por quadro é de **22,22 ms** a 45 FPS e **25,00 ms** a 40 FPS. Ganho de FPS depende do gargalo do quadro. Sombras, draw calls e simulação merecem medições independentes.

## Ensaio no M34

1. Registrar a build instalada, backend gráfico quando observável, modo efetivo de tela, preset, temperatura inicial e configuração de bateria. Fazer três corridas de 120 s, depois de estabilizar o carregamento, no mesmo mapa, ônibus e trajeto. Incluir um trecho com câmera em movimento, parada, tráfego e terminal.
2. Medir o jogo original com acelerador ligado e desligado, mantendo as demais opções. Com o telefone conectado, registrar `adb shell dumpsys display`, `adb shell dumpsys meminfo aaa.core.mods2` e capturar o FrameTimeline do Perfetto com o processo do jogo e SurfaceFlinger. Registrar mediana e p95/p99 dos intervalos de apresentação, quadros atrasados, modo de tela, RAM e oscilações após aquecimento. FrameTimeline mede apresentação e atrasos. Tempos internos de GPU, draw calls e resolução por câmera dependem de contadores ou instrumentação disponíveis.
3. Em build experimental autorizada, medir perfis fixos 100% e 80% antes do adaptativo. Ganho com a queda do tamanho é evidência de sensibilidade ao custo por pixel. Se o ganho for pequeno, variar separadamente sombras, tráfego e pedestres, e distinguir trabalho das threads de jogo/render da espera por GPU. Capturar início de rota e troca de veículo separadamente para investigar I/O, alocações, GC e carregamento de recursos.
4. Validar a escala de 80/85/90/95/100% nas duas dimensões e os intervalos de 1 s, com HUD, retrovisores e letreiros legíveis. Verificar picos ao criar texturas, troca de câmera, retomada e mudanças de mapa. Congelar configurações de sombras e física durante a comparação de escala.

Observe `FPSDisplayNovo` e o modo de resolução da tela na reprodução de qualquer queda abrupta. Há código que reduz recursos quando o FPS fica baixo, mas nenhum gargalo do M34 foi comprovado nesta auditoria. [Perfetto FrameTimeline](https://perfetto.dev/docs/data-sources/frametimeline)

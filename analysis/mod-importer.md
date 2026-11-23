# Importação de mods e letreiros

## Recepção e classificação de ZIP

O manifesto AXML da versão 309 registra `VIEW` e `SEND` para `application/zip` na atividade `com.unity3d.player.UnityPlayerActivity`. A inspeção de IL2CPP confirmou a rota de instalação de veículos e mapas e o critério que deixa de reconhecer um ZIP contendo apenas letreiros.

| Método e RVA/offset | Evidência |
| --- | --- |
| `InstalaZipPersistenteHANDLER.Start()` · `0xE771E0` | Inicializa um delegado para `FileActivatedHandler(FileInformation)` e se inscreve em `FileAssociationManager.FileActivated` em `0xE77374`. |
| `InstalaZipPersistenteHANDLER.FileActivatedHandler(FileInformation)` · `0xE7779C` | Limpa a área temporária, pede um nome de arquivo, chama `SalvaStreamProArquivo2` em `0xE77814` e abre a coroutine em `0xE77820`. |
| `<TentaExtrairSaporraAgora>d__5.MoveNext()` · `0xB06D60` | Chama `System.IO.Compression.ZipFile.ExtractToDirectory` em `0xB070E0`. Procura `*.map.txt` e `*.ini` no nível atual e nas subpastas enumeradas, classifica pelas ramificações de mapa/ônibus, copia pelo `MepUtils.DirectoryCopy` e atualiza as listas. O caminho de falha seleciona `mod_installNotValidMod`. |
| `VeSeTemArquivoRootNaPasta(string, string)` · `0xE778D8` | Chama `DirectoryInfo.GetFiles` em `0xE77944`. O seletor de tipos vem de `MoveNext`. |
| `ImportaModsDaPasta.<ShowLoadDialogCoroutine>d__20.MoveNext()` · `0xB06104` | Fluxo separado da ativação de ZIP. Chama `SimpleFileBrowser.FileBrowser.WaitForLoadDialog` em `0xB061F0`, consulta helpers de diretório e usa `persistentDataPath` no fluxo `/usermods/`. |

A associação vem dos assemblies `ImaginationOverflow.UniversalFileAssociation*`. Há implementação de `AndroidFileProvider.OnFileReceived` e de `AndroidInputReadOnlyStream.Read`. A fronteira Java da entrega da URI precisa dos DEX ou de observação do aplicativo. A presença de SharpZipLib em `ScriptingAssemblies.json` não identifica a rotina que executa esta extração.

## Pasta e fases do letreiro

A amostra usa **`dest/` no singular**. Em `ProtonPaths.AssociaPastaMods()` (`0x150796C`), o literal `/dest/` em `0x1507CD8` é concatenado à raiz e o resultado é gravado em `pastaModsLetreiros` (`+0x20`) em `0x1507CF4`. O método contém caminhos de associação da raiz, incluindo `Application.persistentDataPath`. Com a raiz padrão de arquivos do pacote, o caminho esperado é `Android/data/aaa.core.mods2/files/dest/533/`. O caminho mostrado pelo editor do jogo é a referência para a raiz ativa na instalação do usuário. `dests/` pode ser uma estrutura usada na distribuição de um mod ou em outra versão e fica como caso de compatibilidade a testar.

| Método e RVA/offset | Evidência |
| --- | --- |
| `MepMobileControls.TrocaLetreiroMod()` · `0x20E4070` | Concatena o número à pasta, consulta/cria o diretório, escreve a preferência `letreiro` e chama `TrocaItinerarioAutomatico()`. |
| `TrocaItinerario.TrocaItinerarioAutomatico()` · `0xC2444C` | Tem uma chamada para `ConfiguraLetreiroPersonalizado()` em `0xC24518`. |
| `TrocaItinerario.ConfiguraLetreiroPersonalizado()` · `0xC21EC0` | Lê `1.png`, `2.png` e `3.png`. Chamadas de `ReadAllBytes` em `0xC22100`, `0xC22170` e `0xC221E0` e de `ImageConversion.LoadImage` em `0xC22140`, `0xC221B0` e `0xC22220`. A classe declara texturas distintas para as três fases e também tem variantes de lona, capelinha, placas e painéis. |
| `cenaModLetreiro.escolheuImagemDaGaleria(string)` · `0x20FB34C` | Encaminha o caminho para `CarregaImagemNaLista`, que decodifica a imagem e atualiza a miniatura. Nessa build, os três handlers `clicouBuscarImagem*` apenas selecionam o slot. Nenhuma chamada de abertura de um seletor foi verificada nesses corpos. |
| `cenaModLetreiro.SalvaImagensNaPasta()` · `0x20FB490` | Usa os nomes das três fases e chama `SalvaImagemAgora`, que chama `EncodeToPNG` e `File.WriteAllBytes`. |

## Experimento para importar pelo Android

A próxima prova no jogo original é abrir a cena de letreiros, registrar a pasta que ela exibe, verificar se o toque abre a galeria e tentar três PNGs numerados no letreiro 533. Comparar com um ZIP de ônibus válido, um de mapa válido e um ZIP contendo apenas os três PNGs. Guardar o texto da falha e confirmar o ponto em que a lista de mods é atualizada.

Uma mudança futura integrada ao próprio jogo pode usar `ACTION_OPEN_DOCUMENT` com `image/png`, seleção múltipla ou três slots individuais. O fluxo pode ler a URI com `ContentResolver`, validar o tamanho e a imagem e salvar no diretório próprio do pacote. Um app auxiliar pode criar o ZIP, mas a seleção padrão do Android 11+ restringe `Android/data` e o acesso a diretórios específicos de outros apps. Se houver importador de ZIP novo, usar staging e tratar nomes repetidos, imagens inválidas e interrupções antes de substituir arquivos do letreiro. [Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files) · [Restrições do Android 11](https://developer.android.com/about/versions/11/privacy/storage)

Confiança **alta** nas rotas recuperadas, critérios de classificação, literal da pasta e três PNGs. Confiança **moderada** no caminho absoluto até confirmação em dispositivo. O funcionamento do seletor no APK de produção requer teste no telefone. Se ainda ficar em aberto, o menor artefato adicional é o DEX que contém a ponte Unity/Android e o plugin de arquivos, junto do DEX de atividade somente se estiver em outro split.

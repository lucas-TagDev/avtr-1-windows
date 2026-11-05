# Instalação no Windows, sem WSL

Esta é uma adaptação comunitária do AVTR-1. O avatar é renderizado neste computador; não é necessário contratar um serviço de avatar. A geração de texto pode usar uma API ou um servidor local compatível. Leia também as [licenças originais](LICENSE.md).

## 1. O que você precisa

- Windows 10/11 de 64 bits, GPU NVIDIA com CUDA e driver atualizado.
- Configuração usada no desenvolvimento: RTX 4060 Ti com **16 GB de VRAM**. Outras GPUs não foram validadas; placas com menos memória podem não conseguir carregar avatar e OmniVoice simultaneamente. Não há garantia de tempo real em toda máquina.
- [Python 3.12 de 64 bits](https://www.python.org/downloads/windows/) com o Python Launcher instalado, e [Git para Windows](https://git-scm.com/download/win).
- [Microsoft Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe).
- Internet para instalar dependências e baixar vários GB de modelos. Reserve espaço adicional para três ambientes Python, caches e compilação TensorRT; o instalador não calcula o espaço livre necessário.
- Conta no Hugging Face com acesso autorizado ao [modelo AVTR-1](https://huggingface.co/avaturn-live/avtr-1). Aceite as condições na página antes do download.

Não instale WSL. Os scripts usam Python, CUDA e TensorRT nativos do Windows. O PyTorch instalado inclui as bibliotecas CUDA necessárias; o driver NVIDIA precisa ser compatível com CUDA 12.8.

## 2. Baixar e instalar

Baixe este repositório pelo botão **Code → Download ZIP** e extraia, ou use `git clone` com a URL deste repositório. Escolha uma pasta local com permissão de escrita, preferencialmente um caminho curto, como `C:\IA\avtr-1-windows`.

Dê dois cliques em **INSTALAR-WINDOWS.cmd**. Aguarde o término. Ele cria:

```text
pasta-escolhida/
├── avtr-1-windows/          # nome da pasta deste repositório pode variar
│   ├── .venv/              # renderizador CUDA/TensorRT
│   └── .venv-streamer/     # interface e WebRTC
└── OmniVoice/              # criado ao lado do repositório
    ├── .venv/              # síntese e reconhecimento de voz
    └── models/OmniVoice/   # baixado na preparação
```

Mantenha as pastas juntas. Não copie ambientes `.venv` de outro computador. Não execute o instalador enquanto a aplicação estiver aberta.

Se ocorrer erro, a janela permanece aberta: corrija a causa indicada e execute novamente. O instalador utiliza os ambientes já existentes. Uma instalação limpa em outra máquina ainda precisa de validação; os testes realizados usam a máquina de desenvolvimento acima.

## 3. Entrar no Hugging Face e preparar os modelos

Abra o PowerShell na pasta deste repositório e execute:

```powershell
$env:HF_HOME = "$PWD\.cache\huggingface"
.\.venv\Scripts\huggingface-cli.exe login
```

Use um token de leitura autorizado para o modelo. Não coloque o token no código e não marque a opção de salvar como credencial Git se não precisar dela. Se o comando não existir, confirme que `INSTALAR-WINDOWS.cmd` terminou sem erros.

Depois abra **PREPARAR-MODELOS.cmd**. Ele baixa os pesos, prepara o warp para Windows, compila os engines TensorRT na sua GPU e baixa Silero VAD, OmniVoice e Whisper. A primeira compilação pode demorar bastante. Aguarde a mensagem de conclusão e não feche a janela.

Os engines TensorRT dependem do ambiente e da GPU: não distribua os arquivos `.engine` de outra instalação. Se você trocar a GPU ou a versão TensorRT, os engines precisam ser reconstruídos; os scripts de warp pulam arquivos existentes. Faça backup e remova apenas os engines gerados que precisam ser refeitos antes de repetir a preparação.

## 4. Iniciar a conversa

1. Abra **CONVERSAR-AO-VIVO.cmd** e mantenha a janela aberta.
2. Aguarde carregar a voz e o renderizador. Abra **http://localhost:7860** em Chrome ou Edge.
3. Escolha avatar, fundo e microfone. Autorize o microfone no navegador.
4. Escolha o modo e os provedores, informe suas próprias chaves quando necessário e selecione um modelo disponível na sua conta ou servidor.
5. Clique em **Start session**. Fale normalmente; o Silero VAD detecta a pausa para encerrar o turno.

O fluxo com OmniVoice usa reconhecimento de fala → modelo de texto → voz local → animação local do avatar. Gemini, OpenAI, DeepSeek e Grok são serviços externos quando escolhidos. Para texto local, inicie um servidor como LM Studio, carregue um modelo e use o endereço/modelo fornecidos por ele. O projeto não instala nem configura o LM Studio.

OpenAI Realtime é outro modo, com voz e conversa fornecidas pela API. Cartesia é uma integração alternativa herdada do projeto original. Nenhum deles é obrigatório para usar a opção com voz local.

Voz de referência é opcional. Para clonar, envie uma gravação limpa da voz que você tem autorização para usar; a transcrição pode ficar vazia para reconhecimento local. Fotos de avatares personalizados podem ser cadastradas em **Meus avatares**. O diálogo pode ser aberto ou escondido e o vídeo pode ser destacado pelo botão **Abrir avatar em janela separada**.

## 5. Arquivos e configurações

| Arquivo/pasta | Conteúdo |
| --- | --- |
| `settings.sqlite3` | Chaves e configurações, salvas automaticamente em texto sem criptografia no banco SQLite |
| `artifacts/custom_avatars/` | Fotos, miniaturas e nomes dos avatares personalizados |
| `artifacts/voices/` | Áudios de referência e informações das vozes |
| `artifacts/main/` | Modelos e engines do renderizador |
| `artifacts/silero-vad/` | Modelo VAD e licença |
| `../OmniVoice/models/` | Modelo de síntese de voz |
| `.cache/` e `../.cache/` | Caches de download |

Esses dados locais não são publicados no GitHub. Faça backup do banco, das vozes e dos avatares para migrar suas configurações, sem compartilhar suas chaves. O banco não contém os próprios arquivos de áudio ou imagem. A importação das configurações antigas do navegador ocorre uma única vez na primeira abertura com o banco novo.

**Excluir avatar** e **Excluir voz e áudio** apagam os arquivos correspondentes após confirmação. Encerre a chamada antes de excluir. **Usar voz automática** apenas desassocia a voz atual, sem apagar seu arquivo.

## 6. Qual iniciador usar?

| Arquivo | Finalidade |
| --- | --- |
| **INSTALAR-WINDOWS.cmd** | Instalar dependências, antes do primeiro uso |
| **PREPARAR-MODELOS.cmd** | Baixar modelos e compilar para sua GPU |
| **CONVERSAR-AO-VIVO.cmd** | Uso diário: conversa com avatar e voz local |
| `INICIAR.cmd` | Iniciador legado do renderizador/interface, sem serviço OmniVoice |
| `CONVERSAR-GEMINI.cmd` | Interface alternativa/legada de geração por etapas |
| `GERAR-VIDEO.cmd` | Exemplo de geração de arquivo de vídeo |
| `ambiente-windows.cmd` | Auxiliar dos outros scripts; não abre a aplicação sozinho |

## 7. Problemas comuns

- **Python não encontrado:** instale Python 3.12 com o Launcher; confira `py -3.12 --version`.
- **401/403 no download:** verifique login, acesso ao AVTR-1 e condições aceitas na conta usada pelo token.
- **Erro CUDA / memória insuficiente:** feche outros aplicativos que usam GPU, confirme o driver e a VRAM disponível. Não há caminho de tempo real em CPU validado nesta adaptação.
- **DLL ausente:** instale o Visual C++ Redistributable x64 e confirme que iniciou pelo `.cmd`, que configura os caminhos das bibliotecas.
- **Timeout / tela preta:** leia o erro na janela do iniciador. Verifique os serviços em `http://localhost:8000/health` e `http://localhost:7863/health`. Evite iniciar duas cópias. Portas padrão: 7860, 7863 e 8000.
- **Configuração ou botão antigo:** reinicie o iniciador e atualize a página com Ctrl+F5.
- **API sem modelos:** confirme chave, endereço e acesso da sua conta; no LM Studio, o servidor e um modelo precisam estar carregados. A lista depende do provedor e não é garantida para todo servidor compatível.
- **Microfone sem permissão:** libere o acesso a localhost nas configurações do navegador e selecione o dispositivo correto.
- **Download ou compilação interrompidos:** leia o primeiro erro e repita a preparação após corrigi-lo. Os caches e alguns builds existentes são reaproveitados.

Não exponha os serviços à internet: esta aplicação foi preparada para uso pessoal local, sem autenticação de usuários. A chave da API continua sendo enviada ao respectivo provedor quando você usa o serviço.

## Verificação e limitações

Os testes locais cobrem VAD, biblioteca de avatares, persistência de configurações e renderização/WebRTC. O benchmark local do renderizador chegou a aproximadamente 25 fps na RTX 4060 Ti 16 GB após aquecimento, usando `AVTR1_ODE_STEPS=3`; isso não representa a latência completa da conversa. O OmniVoice e o avatar compartilham a GPU, e as APIs acrescentam latência. Não há garantia de conversa sem pausas nem de funcionamento de todo modelo de terceiros.

Os instaladores e o guia precisam de teste de ponta a ponta em uma instalação limpa. Por enquanto, a configuração Windows existente é a referência de validação.

## Créditos

[AVTR-1](https://github.com/avaturn-live/avtr-1), [OmniVoice](https://github.com/k2-fsa/OmniVoice), [Silero VAD](https://github.com/snakers4/silero-vad) e os modelos de terceiros citados no projeto. As licenças originais, avisos e atribuições foram preservados. Consulte `LICENSE.md`, `LICENSE-MODEL.md`, `LICENSE-RENDERER.md`, `LICENSE-STREAMER.md`, `PATENTS.md` e `THIRD-PARTY-NOTICES.md`.

### Executar verificações locais

Após a instalação e o download do Silero:

```powershell
.\.venv-streamer\Scripts\python.exe scripts/test_local_settings.py
.\.venv-streamer\Scripts\python.exe scripts/test_silero_turns.py
.\.venv\Scripts\python.exe scripts/test_custom_avatars_local.py
```

Esses testes usam arquivos temporários e não apagam os seus avatares ou configurações.

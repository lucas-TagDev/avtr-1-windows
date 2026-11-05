# AVTR-1 para Windows — avatar e voz locais

Adaptação comunitária do [AVTR-1 original](https://github.com/avaturn-live/avtr-1), para Windows nativo, sem WSL. Não é uma distribuição oficial da Avaturn.

**Comece pelo [guia de instalação para Windows](WINDOWS.md).**

- Avatar local com AVTR-1, TensorRT e CUDA.
- Voz local OmniVoice com clonagem opcional e transcrição Whisper local ou API.
- Texto por Gemini, OpenAI, DeepSeek, Grok ou servidor compatível, como LM Studio.
- Silero VAD, diálogos laterais, janela flutuante, fotos como avatares personalizados.
- Configurações persistidas em SQLite na pasta do projeto.

Instalação: baixe o ZIP, extraia e abra **`INSTALAR-WINDOWS.cmd`**. Coloque a pasta extraída no disco desejado e execute o instalador nela. A aplicação, o OmniVoice e os caches ficam dentro dessa mesma pasta, sem seleção de destino.

Depois, entre no Hugging Face e execute `PREPARAR-MODELOS.cmd`, conforme o [guia Windows](WINDOWS.md).
Uso diário: **`CONVERSAR-AO-VIVO.cmd`** → http://localhost:7860.

Modelos, chaves, banco de configurações, vozes e fotos pessoais não estão incluídos neste repositório. Cada pessoa precisa obter o próprio acesso aos modelos e às APIs que escolher. O modo local não exige serviço externo de avatar.

Os arquivos de licença originais foram preservados: [mapa de licenças](LICENSE.md). Este fork não altera as permissões de uso dos componentes originais.


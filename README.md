# OffTube

> Downloader de vídeos e áudios para desktop, com interface gráfica simples e moderna.

O **OffTube** é uma aplicação desktop desenvolvida em Python para facilitar o download de conteúdos através de links, usando **yt-dlp** como mecanismo principal e **FFmpeg** para processamento e conversão de mídia.

## ✨ Recursos

- 🎬 Download de vídeos por URL
- 🎵 Extração de áudio em MP3
- 📺 Suporte a diferentes formatos:
  - MP4
  - MP3
  - MKV
  - WebM
- 🎚️ Seleção de qualidade de vídeo:
  - 360p
  - 480p
  - 720p
  - 1080p
  - 4K
  - Melhor qualidade disponível
- 🎧 Qualidade de MP3 configurável
- 📝 Download de legendas em português e inglês
- 🖼️ Download e conversão de thumbnails
- 📋 Detecção de playlists
- 📊 Barra de progresso e velocidade de download
- 👀 Pré-visualização das informações do conteúdo
- 📁 Escolha da pasta de destino
- 📜 Histórico de downloads
- 🔄 Verificação automática de atualizações
- ⚙️ Instalação automática das dependências durante o modo de desenvolvimento
- 🧩 FFmpeg integrado através do `imageio-ffmpeg`
- 🖥️ Interface construída com CustomTkinter

## 🛠️ Tecnologias

| Tecnologia | Utilização |
|---|---|
| Python | Linguagem principal |
| CustomTkinter | Interface gráfica |
| yt-dlp | Download e obtenção de informações |
| FFmpeg | Conversão e processamento de mídia |
| Pillow | Manipulação de imagens |
| imageio-ffmpeg | Distribuição do FFmpeg |
| Requests | Requisições HTTP |

## 📁 Estrutura do projeto

```text
OffTube_source/
├── OffTube.py
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── discord.py
│   ├── downloader.py
│   ├── history.py
│   ├── setup.py
│   └── updater.py
│
└── ui/
    ├── __init__.py
    ├── app.py
    ├── history_window.py
    ├── playlist_window.py
    ├── preview.py
    ├── progress_hooks.py
    └── theme.py
```

## 🚀 Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/KaueFSS/OffTube_source.git
cd OffTube_source
```

### 2. Execute o projeto

```bash
python OffTube.py
```

O projeto possui um sistema de configuração que verifica e instala automaticamente algumas dependências ausentes quando executado em modo de desenvolvimento.

As principais dependências utilizadas são:

```text
customtkinter
Pillow
imageio-ffmpeg
yt-dlp
requests
```

Caso prefira instalar manualmente:

```bash
pip install customtkinter Pillow imageio-ffmpeg yt-dlp requests
```

## ▶️ Uso

1. Abra o OffTube.
2. Cole a URL do conteúdo.
3. Escolha o formato desejado.
4. Selecione a qualidade.
5. Escolha a pasta de destino.
6. Opcionalmente, habilite legendas ou thumbnail.
7. Inicie o download.

O aplicativo mostra o progresso do download diretamente na interface.

## 🎞️ Formatos

### Vídeo

O OffTube permite selecionar:

- `MP4`
- `MKV`
- `WebM`

A qualidade pode ser configurada entre 360p e 4K, dependendo das opções disponíveis para o conteúdo.

### Áudio

Ao selecionar `MP3`, o áudio é extraído usando FFmpeg.

Qualidades disponíveis:

- `320k`
- `256k`
- `192k`
- `128k`
- `96k`

## 📝 Legendas

É possível solicitar legendas em:

- Português (`pt`)
- Inglês (`en`)

Quando disponíveis, o OffTube também pode utilizar legendas automáticas.

## 🖼️ Thumbnails

O aplicativo pode salvar a thumbnail do conteúdo.

Formatos disponíveis:

- JPG
- PNG
- WebP

## 📋 Playlists

Quando uma playlist é detectada, o aplicativo apresenta uma opção específica para selecionar os vídeos que serão baixados.

Isso permite escolher individualmente quais itens da playlist devem ser processados.

## 🔄 Atualizações

O projeto possui um sistema de atualização integrado.

A versão atual definida no código é:

```text
v2.0.1
```

A configuração da versão fica em:

```text
core/config.py
```

O aplicativo também possui lógica para verificar novas versões e atualizar a aplicação distribuída.

## 📦 Gerando o executável

O projeto possui comandos preparados para utilizar **PyInstaller**.

Exemplo:

```bash
python -m PyInstaller --onefile --windowed --name OffTube OffTube.py
```

Também existe suporte para utilizar um arquivo `.spec`:

```bash
py -m PyInstaller --clean OffTube.spec
```

## 🧠 Arquitetura

O projeto é dividido principalmente em duas camadas:

### `core/`

Responsável pela lógica da aplicação.

- `downloader.py` → download e processamento dos arquivos
- `config.py` → configurações gerais
- `setup.py` → dependências e FFmpeg
- `history.py` → histórico
- `updater.py` → atualizações
- `discord.py` → integração relacionada ao Discord

### `ui/`

Responsável pela interface gráfica.

- `app.py` → aplicação principal
- `preview.py` → pré-visualização
- `playlist_window.py` → seleção de playlists
- `history_window.py` → histórico
- `progress_hooks.py` → atualização do progresso
- `theme.py` → tema visual

## 🔐 Segurança

**Importante:** nunca coloque tokens, webhooks, chaves de API ou outras credenciais diretamente no código-fonte de um repositório público.

Antes de publicar ou redistribuir o projeto, utilize variáveis de ambiente ou um arquivo de configuração local para informações sensíveis.

Se uma credencial já foi publicada acidentalmente, ela deve ser considerada comprometida e revogada/rotacionada.

## ⚖️ Aviso legal

O OffTube é uma ferramenta de software.

O usuário é responsável por utilizar o aplicativo de acordo com as leis aplicáveis e com os termos de serviço das plataformas acessadas.

Baixe somente conteúdos para os quais você possui autorização ou direito de uso.

## 👨‍💻 Autor

Desenvolvido por **KaueFSS**.

- GitHub: https://github.com/KaueFSS
- Projeto: https://github.com/KaueFSS/OffTube_source

## 📄 Licença

Nenhuma licença de código aberto foi identificada no repositório no momento.

Se você pretende permitir que outras pessoas utilizem, modifiquem ou redistribuam o projeto, considere adicionar uma licença, como MIT, Apache-2.0 ou GPL-3.0.

---

⭐ Se o projeto foi útil para você, considere deixar uma estrela no repositório.

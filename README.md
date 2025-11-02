# 🎵 MP3 Player Offline

Player MP3 estático e offline, desenvolvido em HTML/JavaScript com atualização automática via Python. Interface moderna e minimalista, totalmente funcional sem necessidade de servidor.

## 📋 Características

- ✅ **Totalmente Offline** - Funciona sem internet ou servidor
- ✅ **Interface Moderna** - Design minimalista e responsivo
- ✅ **Metadados ID3** - Extrai título, artista e capa dos álbuns
- ✅ **Controles Completos** - Play, pause, seek, volume e navegação
- ✅ **Atualização Automática** - Script Python regenera o HTML facilmente

## 🚀 Instalação

### Pré-requisitos

- Python 3.6 ou superior
- Navegador moderno (Chrome, Firefox, Edge - últimas 2 versões)

### 1. Instalar Dependências Python

```bash
pip install mutagen
```

Ou se utilizar pip3:

```bash
pip3 install mutagen
```

### 2. Estrutura de Pastas

O projeto deve ter a seguinte estrutura:

```
DJMIXPLYR/
├── index.html          # Player HTML (será atualizado automaticamente)
├── update_player.py    # Script de atualização
├── README.md          # Este ficheiro
└── mp3/               # Pasta com os ficheiros MP3
    ├── musica1.mp3
    ├── musica2.mp3
    └── ...
```

### 3. Adicionar Ficheiros MP3

Coloque os seus ficheiros MP3 na pasta `mp3/`. Se a pasta não existir, o script criá-la-á automaticamente.

## 📖 Utilização

### Atualizar o Player

Sempre que adicionar, remover ou modificar ficheiros MP3 na pasta `mp3/`, execute:

```bash
python update_player.py
```

Ou:

```bash
python3 update_player.py
```

O script irá:
1. Escanear a pasta `mp3/` em busca de ficheiros MP3
2. Extrair metadados ID3 (título, artista, capa)
3. Atualizar o `index.html` com as novas faixas

### Abrir o Player

Abra o ficheiro `index.html` no seu navegador. Pode fazê-lo de várias formas:

- **Duplo clique** no `index.html`
- **Arrastar e largar** o ficheiro para o navegador
- **Clicar com botão direito** → "Abrir com" → Navegador

## 🎮 Controlos

- **▶/⏸** - Play/Pause
- **⏮** - Faixa anterior
- **⏭** - Faixa seguinte
- **Barra de progresso** - Clique para saltar para uma posição
- **Slider de volume** - Ajustar volume
- **Lista de faixas** - Clique numa faixa para a tocar

## 🔧 Funcionalidades Técnicas

### Metadados Suportados

O script extrai automaticamente:
- **Título** (TIT2, TITLE, ©nam)
- **Artista** (TPE1, ARTIST, ©ART)
- **Álbum** (TALB, ALBUM, ©alb)
- **Capa do Álbum** (APIC, PIC, covr)

Se os metadados não estiverem disponíveis, o player mostra o nome do ficheiro.

### Capas de Álbum

As capas são extraídas dos ficheiros MP3 e incorporadas no HTML como imagens base64, permitindo que funcionem totalmente offline.

### Fallbacks

- Se não houver metadados: mostra o nome do ficheiro
- Se não houver capa: mostra ícone 🎵
- Se não houver ficheiros: mostra mensagem informativa

## 📝 Notas

- O player funciona apenas com ficheiros locais (caminhos relativos `mp3/...`)
- Para funcionar completamente offline, todos os ficheiros MP3 devem estar na pasta `mp3/`
- O HTML é regenerado sempre que executar `update_player.py`
- Alterações manuais no HTML podem ser perdidas ao executar o script

## 🐛 Resolução de Problemas

### "Nenhum ficheiro MP3 encontrado"

Certifique-se de que:
- Os ficheiros têm extensão `.mp3` ou `.MP3`
- Os ficheiros estão na pasta `mp3/` (no mesmo diretório do script)

### Metadados não aparecem

Alguns ficheiros MP3 podem não ter metadados ID3. O player mostrará o nome do ficheiro nestes casos.

### Capas não aparecem

Nem todos os ficheiros MP3 contêm capas incorporadas. O player mostrará um ícone padrão (🎵) quando não houver capa.

### Erro ao importar mutagen

Certifique-se de que instalou o mutagen:
```bash
pip install mutagen
```

## 📄 Licença

Projeto livre para uso pessoal.

---

**Desenvolvido com ❤️ para música offline**


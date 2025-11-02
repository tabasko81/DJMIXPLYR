#!/usr/bin/env python3
"""
Script para atualizar o player MP3 offline.
Escanha a pasta mp3/, extrai metadados ID3 e regenera o index.html.
"""

import json
import base64
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

# Configurações
MP3_FOLDER = Path('mp3')
HTML_FILE = Path('index.html')


def extract_cover_art(mp3_file):
    """
    Extrai a capa do álbum do ficheiro MP3 e retorna como base64 data URI.
    Retorna None se não houver capa.
    """
    try:
        audio_file = File(str(mp3_file))
        if audio_file is None:
            return None

        # Tentar extrair imagem de diferentes tags
        if hasattr(audio_file, 'tags') and audio_file.tags:
            for tag in ['APIC:', 'APIC', 'PIC', 'covr']:
                if tag in audio_file.tags:
                    artwork = audio_file.tags[tag]
                    if isinstance(artwork, list) and len(artwork) > 0:
                        artwork = artwork[0]
                    if hasattr(artwork, 'data'):
                        image_data = artwork.data
                        # Detectar tipo MIME
                        mime_type = 'image/jpeg'
                        if image_data[:2] == b'\xff\xd8':
                            mime_type = 'image/jpeg'
                        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
                            mime_type = 'image/png'
                        elif image_data[:4] == b'GIF8':
                            mime_type = 'image/gif'
                        # Converter para base64 data URI
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        return f"data:{mime_type};base64,{b64_data}"
                    elif isinstance(artwork, bytes):
                        mime_type = 'image/jpeg'
                        b64_data = base64.b64encode(artwork).decode('utf-8')
                        return f"data:image/jpeg;base64,{b64_data}"

        # Tentar com mutagen ID3
        try:
            from mutagen.id3 import ID3
            id3 = ID3(str(mp3_file))
            for tag_name in id3.keys():
                if tag_name.startswith('APIC'):
                    apic = id3[tag_name]
                    if hasattr(apic, 'data'):
                        image_data = apic.data
                        mime_type = apic.mime if hasattr(apic, 'mime') else 'image/jpeg'
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        return f"data:{mime_type};base64,{b64_data}"
        except (ID3NoHeaderError, ImportError):
            pass

    except Exception as e:
        print(f"Erro ao extrair capa de {mp3_file.name}: {e}")
    
    return None


def extract_metadata(mp3_file):
    """
    Extrai metadados do ficheiro MP3.
    Retorna dicionário com título, artista, capa e caminho.
    """
    try:
        audio_file = File(str(mp3_file))
        if audio_file is None:
            return None

        metadata = {
            'filename': mp3_file.stem,
            'title': None,
            'artist': None,
            'album': None,
            'cover': None,
            'path': f"mp3/{mp3_file.name}"
        }

        # Extrair título, artista e álbum
        if hasattr(audio_file, 'tags') and audio_file.tags:
            tags = audio_file.tags
            
            # Título
            for key in ['TIT2', 'TITLE', '©nam']:
                if key in tags:
                    value = tags[key]
                    if isinstance(value, list) and len(value) > 0:
                        metadata['title'] = str(value[0]).strip()
                    else:
                        metadata['title'] = str(value).strip()
                    break

            # Artista
            for key in ['TPE1', 'ARTIST', '©ART']:
                if key in tags:
                    value = tags[key]
                    if isinstance(value, list) and len(value) > 0:
                        metadata['artist'] = str(value[0]).strip()
                    else:
                        metadata['artist'] = str(value).strip()
                    break

            # Álbum
            for key in ['TALB', 'ALBUM', '©alb']:
                if key in tags:
                    value = tags[key]
                    if isinstance(value, list) and len(value) > 0:
                        metadata['album'] = str(value[0]).strip()
                    else:
                        metadata['album'] = str(value).strip()
                    break

        # Extrair capa
        cover = extract_cover_art(mp3_file)
        if cover:
            metadata['cover'] = cover

        return metadata

    except Exception as e:
        print(f"Erro ao processar {mp3_file.name}: {e}")
        return {
            'filename': mp3_file.stem,
            'title': None,
            'artist': None,
            'album': None,
            'cover': None,
            'path': f"mp3/{mp3_file.name}"
        }


def get_existing_tracks():
    """
    Lê as faixas existentes do HTML e retorna como lista.
    """
    if not HTML_FILE.exists():
        return []
    
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procurar pela constante PLAYLIST_DATA
        start_idx = content.find('const PLAYLIST_DATA')
        if start_idx == -1:
            return []
        
        # Encontrar o início do array JSON
        array_start = content.find('[', start_idx)
        if array_start == -1:
            return []
        
        # Encontrar o fim do array
        array_end = content.find('];', array_start)
        if array_end == -1:
            return []
        
        # Extrair o JSON
        json_str = content[array_start:array_end + 1]
        
        # Tentar fazer parse do JSON
        try:
            existing_tracks = json.loads(json_str)
            return existing_tracks if isinstance(existing_tracks, list) else []
        except json.JSONDecodeError:
            return []
    except Exception as e:
        print(f"Aviso: Erro ao ler faixas existentes: {e}")
        return []


def get_existing_playlist():
    """
    Lê a playlist atual do HTML e retorna um conjunto de paths normalizados.
    """
    existing_tracks = get_existing_tracks()
    existing_paths = set()
    for track in existing_tracks:
        if 'path' in track:
            # Normalizar path para comparação (lowercase)
            existing_paths.add(track['path'].lower().replace('\\', '/'))
    return existing_paths


def scan_mp3_files(existing_paths=None):
    """
    Escaneia a pasta mp3/ e retorna lista de metadados.
    Evita duplicados (importante no Windows que é case-insensitive).
    Se existing_paths for fornecido, apenas processa ficheiros novos.
    """
    if existing_paths is None:
        existing_paths = set()
    
    if not MP3_FOLDER.exists():
        print(f"Pasta {MP3_FOLDER} não encontrada. A criá-la...")
        MP3_FOLDER.mkdir(exist_ok=True)
        print(f"Pasta {MP3_FOLDER} criada. Adicione ficheiros MP3 e execute novamente.")
        return []

    # Coletar todos os ficheiros MP3 e evitar duplicados
    mp3_files_dict = {}  # {lowercase_name: Path}
    
    # Procurar por todos os ficheiros .mp3 (case-insensitive)
    for mp3_file in MP3_FOLDER.glob('*.mp3'):
        name_lower = mp3_file.name.lower()
        if name_lower not in mp3_files_dict:
            mp3_files_dict[name_lower] = mp3_file
    
    # Também procurar por .MP3 (caso haja extensões em maiúsculas)
    for mp3_file in MP3_FOLDER.glob('*.MP3'):
        name_lower = mp3_file.name.lower()
        if name_lower not in mp3_files_dict:
            mp3_files_dict[name_lower] = mp3_file
    
    mp3_files = sorted(mp3_files_dict.values(), key=lambda x: x.name.lower())
    
    if not mp3_files:
        print(f"Nenhum ficheiro MP3 encontrado em {MP3_FOLDER}")
        return []

    print(f"Encontrados {len(mp3_files)} ficheiro(s) MP3")
    
    new_tracks = []
    skipped_count = 0
    
    for mp3_file in mp3_files:
        # Verificar se já existe na playlist
        track_path = f"mp3/{mp3_file.name}"
        track_path_normalized = track_path.lower().replace('\\', '/')
        
        if track_path_normalized in existing_paths:
            print(f"Já existe na playlist: {mp3_file.name} (ignorado)")
            skipped_count += 1
            continue
        
        print(f"Novo ficheiro encontrado: {mp3_file.name}")
        metadata = extract_metadata(mp3_file)
        if metadata:
            new_tracks.append(metadata)
    
    if skipped_count > 0:
        print(f"\n{skipped_count} ficheiro(s) já existem na playlist (ignorados)")
    
    return new_tracks


def get_current_mp3_files():
    """
    Retorna um conjunto de paths normalizados dos ficheiros MP3 atualmente na pasta.
    """
    if not MP3_FOLDER.exists():
        return set()
    
    current_files = set()
    
    # Procurar por todos os ficheiros .mp3
    for mp3_file in MP3_FOLDER.glob('*.mp3'):
        path_normalized = f"mp3/{mp3_file.name}".lower().replace('\\', '/')
        current_files.add(path_normalized)
    
    # Procurar por .MP3 também
    for mp3_file in MP3_FOLDER.glob('*.MP3'):
        path_normalized = f"mp3/{mp3_file.name}".lower().replace('\\', '/')
        current_files.add(path_normalized)
    
    return current_files


def update_html(new_tracks):
    """
    Atualiza o index.html adicionando novas faixas no topo da playlist
    e removendo faixas cujos ficheiros já não existem.
    Substitui o conteúdo de PLAYLIST_DATA de forma robusta.
    """
    if not HTML_FILE.exists():
        print(f"Erro: {HTML_FILE} não encontrado!")
        return False

    # Ler faixas existentes
    existing_tracks = get_existing_tracks()
    
    # Obter ficheiros MP3 que existem atualmente na pasta
    current_files = get_current_mp3_files()
    
    # Filtrar faixas existentes: manter apenas as que ainda têm ficheiros
    valid_existing_tracks = []
    removed_count = 0
    
    for track in existing_tracks:
        if 'path' in track:
            track_path_normalized = track['path'].lower().replace('\\', '/')
            if track_path_normalized in current_files:
                valid_existing_tracks.append(track)
            else:
                removed_count += 1
                print(f"Ficheiro removido: {track.get('filename', track['path'])}")
        else:
            # Se não tiver path, manter (não deveria acontecer, mas por segurança)
            valid_existing_tracks.append(track)
    
    if removed_count > 0:
        print(f"\n{removed_count} faixa(s) removida(s) da playlist (ficheiros não encontrados)")
    
    # Combinar: novas faixas no topo, depois as existentes válidas
    all_tracks = new_tracks + valid_existing_tracks

    # Ler HTML existente
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Criar JSON dos dados das faixas
    tracks_json = json.dumps(all_tracks, ensure_ascii=False, indent=2)
    
    # Encontrar a linha que contém "const PLAYLIST_DATA ="
    start_line_idx = None
    for i, line in enumerate(lines):
        if 'const PLAYLIST_DATA' in line and '=' in line:
            start_line_idx = i
            break
    
    if start_line_idx is None:
        print("Erro: Não foi possível encontrar 'const PLAYLIST_DATA =' no HTML")
        return False
    
    # Encontrar a linha que contém "];" após a linha de início
    # Procurar pela primeira linha após start_line_idx que contém apenas "];"
    end_line_idx = None
    for i in range(start_line_idx + 1, len(lines)):
        line_stripped = lines[i].strip()
        if line_stripped == '];':
            end_line_idx = i
            break
    
    if end_line_idx is None:
        print("Erro: Não foi possível encontrar '];' após PLAYLIST_DATA no HTML")
        return False
    
    # Obter a indentação da linha original
    start_line = lines[start_line_idx]
    indent = ''
    for char in start_line:
        if char in [' ', '\t']:
            indent += char
        else:
            break
    
    # Construir o novo conteúdo
    # Substituir tudo entre start_line_idx e end_line_idx
    new_lines = lines[:start_line_idx]
    
    # Criar JSON com indentação apropriada
    # O json.dumps já tem indent=2
    json_lines = tracks_json.split('\n')
    
    if json_lines:
        # Verificar se a primeira linha é apenas '[' (array vazio ou início)
        if json_lines[0].strip() == '[':
            # Primeira linha: const PLAYLIST_DATA = [
            new_lines.append(f'{indent}const PLAYLIST_DATA = [\n')
            # Começar da segunda linha do JSON
            start_idx = 1
        else:
            # JSON numa linha só ou formato diferente
            new_lines.append(f'{indent}const PLAYLIST_DATA = {json_lines[0]}\n')
            start_idx = 1
        
        # Adicionar linhas do JSON com indentação base
        # Verificar se a última linha é ']' para fechar corretamente
        for i, json_line in enumerate(json_lines[start_idx:], start=start_idx):
            line_stripped = json_line.strip()
            
            # Se for a última linha e for ']', fechar com '];'
            if i == len(json_lines) - 1 and line_stripped == ']':
                new_lines.append(f'{indent}];\n')
            elif line_stripped:  # Linhas não vazias
                new_lines.append(f'{indent}{json_line}\n')
            else:
                new_lines.append('\n')
    else:
        # Se não houver dados, apenas o array vazio
        new_lines.append(f'{indent}const PLAYLIST_DATA = [];\n')
    
    # Adicionar o restante após a linha com ];
    new_lines.extend(lines[end_line_idx + 1:])
    
    # Escrever HTML atualizado
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"HTML atualizado com {len(all_tracks)} faixa(s)")
    return True


def main():
    """
    Função principal.
    """
    print("=== Atualizador do Player MP3 ===\n")
    
    # Ler playlist existente para identificar novos ficheiros
    existing_paths = get_existing_playlist()
    existing_count = len(existing_paths)
    
    if existing_count > 0:
        print(f"Playlist atual contém {existing_count} faixa(s)\n")
    
    # Escanear ficheiros MP3 (apenas novos)
    new_tracks = scan_mp3_files(existing_paths)
    
    if new_tracks:
        print(f"\n{len(new_tracks)} nova(s) faixa(s) encontrada(s)")
    else:
        if existing_count == 0:
            print("\nNenhuma faixa encontrada. Verifique se há ficheiros MP3 na pasta mp3/")
            return
        else:
            print("\nVerificando ficheiros removidos...")

    # Atualizar HTML (adiciona novas no topo e remove ficheiros ausentes)
    # Sempre atualizar para verificar ficheiros removidos
    if update_html(new_tracks):
        # Obter contagem final após atualização
        final_tracks = get_existing_tracks()
        final_count = len(final_tracks)
        
        print("\n✅ Player atualizado com sucesso!")
        if new_tracks:
            print(f"Novas faixas adicionadas: {len(new_tracks)}")
        if final_count != existing_count:
            removed = existing_count - (final_count - len(new_tracks))
            if removed > 0:
                print(f"Faixas removidas: {removed}")
        print(f"Total de faixas na playlist: {final_count}")
    else:
        print("\n❌ Erro ao atualizar o player")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo utilizador")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

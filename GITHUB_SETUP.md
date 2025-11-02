# 📤 Guia para Publicar no GitHub

## Nome Sugerido do Projeto
**DJMIXPLYR** ou **OfflineMP3Player**

## Passos para Publicar

### 1. Criar Repositório no GitHub

1. Aceda a https://github.com/new
2. **Repository name**: `DJMIXPLYR` (ou o nome que preferir)
3. **Description**: `🎵 MP3 Player Offline - Player MP3 estático com interface minimalista e atualização automática via Python`
4. Escolha **Public** ou **Private**
5. **NÃO** marque "Initialize this repository with a README" (já temos um)
6. Clique em **Create repository**

### 2. Conectar e Fazer Push

Depois de criar o repositório, execute estes comandos no terminal:

```bash
# Adicionar o remote (substitua USERNAME pelo seu username do GitHub)
git remote add origin https://github.com/USERNAME/DJMIXPLYR.git

# Ou se preferir usar SSH:
# git remote add origin git@github.com:USERNAME/DJMIXPLYR.git

# Fazer push
git branch -M main
git push -u origin main
```

### 3. Verificar Configuração Git (Opcional)

Se quiser alterar o nome/email do Git para este projeto:

```bash
git config user.name "Seu Nome"
git config user.email "seu@email.com"
```

Para configurar globalmente (todos os projetos):

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"
```

## ✅ Pronto!

Depois do push, o projeto estará disponível em:
`https://github.com/USERNAME/DJMIXPLYR`


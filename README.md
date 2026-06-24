# 🎮 KioThumb 2 — Gerador de Thumbnails para Longplay

**Gera automaticamente thumbnails numeradas em lote para canais de longplay no YouTube.** Adicione imagens ou extraia frames diretamente dos seus vídeos, posicione o número do episódio e logos onde quiser, e exporte tudo de uma vez em 1280×720 (padrão YouTube).

---

## Por que esse programa existe?

Tenho um canal de longplay no YouTube e criar thumbnail por thumbnail manualmente era uma perda de tempo enorme. O **KioThumb 2** resolve isso: você configura uma vez e gera 10, 20, 50 thumbnails em segundos — cada uma com o número certo e a imagem certa.

---

## ✨ Funcionalidades

- Gera thumbnails numeradas em lote (`#1`, `#2`, `#3`... ou o prefixo que você quiser)
- **Assistente de vídeo** — jogue seus vídeos e o programa extrai 10 frames para você escolher o melhor momento. Não gostou? Clique em *Outras 10 imagens*
- **Ordem automática** — lê o `#número` no nome do arquivo e organiza tudo na sequência certa
- **Sobreposições** — adicione quantos PNGs quiser em cima da thumbnail (logos, selos...), cada um com posição e tamanho independentes
- Preview em tempo real: o que você vê é exatamente o que vai sair
- Arraste o número e as sobreposições direto na tela para posicionar
- Zoom e pan na imagem de fundo para enquadrar como quiser
- 1 imagem + quantidade 20 → gera 20 thumbnails com a mesma imagem
- 5 imagens + quantidade 5 → cada thumbnail com uma imagem diferente
- Se faltar imagens, a última é repetida (o programa avisa antes)
- Sombra com controle de opacidade no número do episódio
- Suporte a fontes personalizadas (.ttf / .otf)
- Salvar e reabrir projetos (arquivo `.json`)
- Histórico de projetos recentes
- Prévia em grade antes de gerar
- Ctrl+V para colar prints direto da área de transferência
- Ctrl+Z para desfazer movimentos
- Exporta em PNG ou JPEG em 1280×720

---

## 📥 Download

Vá em [Releases](../../releases) e baixe o arquivo `KioThumb2.exe`.

Não precisa instalar nada. Basta colocar o `KioThumb2.exe` e o `icone2.png` na mesma pasta e executar.

> **Sistema operacional:** Windows 10 ou superior

---

## 🛠️ Rodar pelo código-fonte

**Requisitos:**
- Python 3.10 ou superior
- Pillow
- psutil
- opencv-python

**Instalação:**
```bash
py -m pip install pillow psutil opencv-python
```

**Executar:**
```bash
py kiothumb2.py
```

> O arquivo `icone2.png` precisa estar na mesma pasta que o `kiothumb2.py`.

---

## 🖥️ Como usar

**Com imagens:**
1. Clique em **+ Adicionar imagem** → selecione uma ou mais imagens
2. No painel central, arraste a imagem para enquadrar, scroll para zoom
3. Clique no número `#1` para selecionar (contorno vermelho) e arraste para posicionar
4. Configure fonte, tamanho, cor e efeitos no painel direito
5. No rodapé, defina o número inicial e a quantidade
6. Clique em **▶ GERAR THUMBNAILS**

**Com vídeos:**
1. Clique em **+ Adicionar imagem** → **Do vídeo**
2. Selecione um ou mais vídeos (nomeie com `#1`, `#2`... para ordenação automática)
3. O assistente mostra 10 frames de cada vídeo — clique no que preferir
4. Não gostou de nenhum? Clique em **🔄 Outras 10 imagens**
5. Confirme e passe para o próximo vídeo automaticamente

---

## 📌 Dicas

- Nomeie seus vídeos com `#número` (ex: `Sekiro #1.mp4`) para o programa ordenar automaticamente
- Use **Salvar projeto** para guardar todas as configurações e retomar depois
- Clique no `?` no canto superior direito para abrir o tutorial a qualquer momento
- Scroll do mouse em cima de uma sobreposição redimensiona ela
- Arraste itens na lista da esquerda para reordenar

---

## 📋 Histórico de versões

**v1.1**
- Correção do bug do PNG (tamanho da sobreposição agora é igual no preview e no arquivo final)
- Tutorial substituído por botão `?` discreto — só abre quando você quiser
- Assistente de vídeo: *Outras 10 imagens* substitui as anteriores com animação suave
- Botões com animação de hover e clique

**v1.0**
- Lançamento inicial

---

## 👤 Autor

Feito por **KioHype**

---

## 📄 Licença

MIT — use, modifique e distribua à vontade.

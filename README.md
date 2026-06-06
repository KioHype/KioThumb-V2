# 🎮 KioThumb 2 — Gerador de Thumbnails para Longplay

**Gera automaticamente thumbnails numeradas em lote para canais de longplay no YouTube.** Adicione imagens ou extraia frames diretamente dos seus vídeos, posicione o número do episódio e as logos onde quiser, e exporte tudo de uma vez em 1280×720 (padrão YouTube).

---

## Por que esse programa existe?

Tenho um canal de longplay no YouTube e criar thumbnail por thumbnail manualmente era uma perda de tempo enorme. O **KioThumb 2** resolve isso: você configura uma vez e gera 10, 20, 50 thumbnails em segundos — cada uma com o número certo e a imagem certa.

---

## ✨ O que há de novo no v2

- **Assistente de vídeo** — jogue seus vídeos no programa e ele extrai 10 frames para você escolher o melhor momento. Não gostou de nenhum? Clique em "Gerar mais 10"
- **Ordem automática** — o programa lê o `#número` no nome do arquivo e organiza tudo na sequência certa automaticamente
- **Sobreposições** — adicione quantos PNGs quiser em cima da thumbnail (logos, selos, qualquer coisa), cada um com posição e tamanho independentes
- **Salvar e reabrir projetos** — todas as configurações ficam salvas num arquivo `.json` para você retomar de onde parou
- **Histórico de projetos recentes** — acesso rápido aos últimos projetos no menu do topo
- **Prévia em grade** — veja todas as thumbnails de uma vez antes de gerar
- **Sombra com opacidade** — controle fino sobre o efeito de sombra no número
- **Undo** — desfaça o último movimento com Ctrl+Z
- **Aviso de sobrescrita** — o programa avisa antes de substituir arquivos existentes

---

## ✨ Funcionalidades principais

- Gera thumbnails numeradas em lote (`#1`, `#2`, `#3`... ou o prefixo que você quiser)
- Preview em tempo real: o que você vê é exatamente o que vai sair
- Arraste o número e as sobreposições direto na tela para posicionar
- Zoom e pan na imagem de fundo para enquadrar como quiser
- 1 imagem + quantidade 20 → gera 20 thumbnails com a mesma imagem
- 5 imagens + quantidade 5 → cada thumbnail com uma imagem diferente
- Se faltar imagens, a última é repetida (o programa avisa antes)
- Suporte a fontes personalizadas (.ttf / .otf)
- Exporta em PNG ou JPEG em 1280×720 (padrão YouTube)
- Ctrl+V para colar prints direto da área de transferência

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
3. Clique no número `#1` para selecionar e arraste para posicionar
4. Configure fonte, tamanho, cor e efeitos no painel direito
5. No rodapé, defina o número inicial e a quantidade
6. Clique em **▶ GERAR THUMBNAILS**

**Com vídeos:**
1. Clique em **+ Adicionar imagem** → **Do vídeo**
2. Selecione um ou mais vídeos (nomeados com `#1`, `#2`...)
3. O assistente mostra 10 frames de cada vídeo — clique no que mais gostar
4. Se não gostar de nenhum, clique em **🔄 Gerar mais 10**
5. Confirme e passe para o próximo vídeo automaticamente

---

## 📌 Dicas

- Nomeie seus vídeos com `#número` (ex: `Sekiro #1.mp4`) para o programa ordenar automaticamente
- Use **Salvar projeto** para guardar todas as configurações e retomar depois
- Adicione logos e selos em **Sobreposições** — cada um tem posição e tamanho independentes
- Scroll do mouse em cima de uma sobreposição redimensiona ela

---

## 👤 Autor

Feito por **KioHype**
Canal: [link do seu canal aqui]

---

## 📄 Licença

MIT — use, modifique e distribua à vontade.

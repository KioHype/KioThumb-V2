import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageGrab
import os, sys, threading, json, re, shutil, tempfile, time
import cv2

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════
YT_W, YT_H  = 1280, 720
PV_W, PV_H  = 854, 480
APP_DIR      = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(APP_DIR, "projetos")
os.makedirs(PROJECTS_DIR, exist_ok=True)

BG        = "#13131a"
SURFACE   = "#1e1e28"
SURFACE2  = "#28283a"
ACCENT    = "#9b6dff"
ACCENT2   = "#7b4ddf"
ACCENT_DIM= "#2a1e4a"
TEXT      = "#eeeef5"
MUTED     = "#666688"
BORDER    = "#3a3a5a"
DANGER    = "#ff4466"
SUCCESS   = "#44ffaa"
WARNING   = "#ffaa44"
SEL       = "#ff3355"
CHECK_BG  = "#2a2a3a"
HOVER_BG  = "#3a3a5a"

SUPPORTED_VIDEO = (".mp4",".mkv",".avi",".mov",".webm",".flv")
SUPPORTED_IMAGE = (".png",".jpg",".jpeg",".bmp",".webp")

def resource_path(rel):
    try:    base = sys._MEIPASS
    except: base = APP_DIR
    return os.path.join(base, rel)

def get_windows_fonts():
    fd = os.path.join(os.environ.get("WINDIR","C:\\Windows"),"Fonts")
    out = []
    if os.path.isdir(fd):
        for f in os.listdir(fd):
            if f.lower().endswith((".ttf",".otf")):
                out.append(f)
    return sorted(out)

def find_font(name):
    fd = os.path.join(os.environ.get("WINDIR","C:\\Windows"),"Fonts")
    p  = os.path.join(fd, name)
    return p if os.path.exists(p) else None

def ep_num_from_path(path):
    name = os.path.splitext(os.path.basename(path))[0]
    m = re.search(r'#\s*(\d+)', name)
    if m: return int(m.group(1))
    for mm in re.finditer(r'\b(\d{1,3})\b', name):
        v = int(mm.group(1))
        if v < 1000: return v
    return 9999

# ══════════════════════════════════════════════════════════════════════════════
# BOTÃO ANIMADO
# ══════════════════════════════════════════════════════════════════════════════
class AnimBtn(tk.Button):
    def __init__(self, parent, text, cmd, fg=ACCENT, bg=SURFACE2,
                 hover_bg=HOVER_BG, active_bg=ACCENT2, active_fg=BG,
                 size=9, pady=6, padx=10, **kwargs):
        super().__init__(parent, text=text, command=cmd,
                         bg=bg, fg=fg,
                         activebackground=active_bg, activeforeground=active_fg,
                         relief="flat", bd=0, cursor="hand2",
                         font=("Segoe UI", size, "bold"),
                         padx=padx, pady=pady,
                         highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT, **kwargs)
        self._bg       = bg
        self._fg       = fg
        self._hover_bg = hover_bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, e):
        self.config(bg=self._hover_bg, highlightbackground=ACCENT)

    def _on_leave(self, e):
        self.config(bg=self._bg, highlightbackground=BORDER)

    def _on_press(self, e):
        self.config(bg=ACCENT2, fg=BG)

    def _on_release(self, e):
        self.config(bg=self._hover_bg, fg=self._fg)

def mkbtn(parent, text, cmd, fg=ACCENT, bg=SURFACE2, size=9, pady=6, padx=10):
    return AnimBtn(parent, text, cmd, fg=fg, bg=bg, size=size, pady=pady, padx=padx)

def mksep(parent):
    return tk.Frame(parent, bg=BORDER, height=1)

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO
# ══════════════════════════════════════════════════════════════════════════════
class BgImage:
    def __init__(self, path):
        self.path  = path
        self.ox    = 0.0
        self.oy    = 0.0
        self.scale = 1.0

    def to_dict(self):
        return {"path":self.path,"ox":self.ox,"oy":self.oy,"scale":self.scale}

    @staticmethod
    def from_dict(d):
        b = BgImage(d["path"])
        b.ox=d.get("ox",0.0); b.oy=d.get("oy",0.0); b.scale=d.get("scale",1.0)
        return b

class Overlay:
    def __init__(self, path, name=""):
        self.path = path
        self.name = name or os.path.basename(path)
        self.fx   = 0.72
        self.fy   = 0.04
        self.size = 180
        self.pil  = Image.open(path).convert("RGBA")

    def to_dict(self):
        return {"path":self.path,"name":self.name,
                "fx":self.fx,"fy":self.fy,"size":self.size}

    @staticmethod
    def from_dict(d):
        try:
            ov = Overlay(d["path"], d.get("name",""))
            ov.fx=d.get("fx",0.72); ov.fy=d.get("fy",0.04); ov.size=d.get("size",180)
            return ov
        except:
            return None

# ══════════════════════════════════════════════════════════════════════════════
# ASSISTENTE DE VÍDEO
# ══════════════════════════════════════════════════════════════════════════════
class VideoWizard(tk.Toplevel):
    def __init__(self, parent, video_files, callback):
        super().__init__(parent)
        self.callback = callback
        self.videos   = sorted(video_files, key=ep_num_from_path)
        self.current  = 0
        self.results  = []
        self.frames   = []
        self.selected_path = None
        self._zoomed_win   = None
        self._animating    = False

        self.title("KioThumb 2 — Assistente de Vídeo")
        self.geometry("920x640")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        self._load_video(self.current)

    def _build(self):
        hdr = tk.Frame(self, bg=BG, height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        self._title_lbl = tk.Label(hdr, text="", bg=BG, fg=ACCENT,
                                    font=("Times New Roman",16,"bold"))
        self._title_lbl.pack(side="left", padx=16, pady=12)
        self._prog_lbl = tk.Label(hdr, text="", bg=BG, fg=MUTED,
                                   font=("Segoe UI",9))
        self._prog_lbl.pack(side="right", padx=16)
        mksep(self).pack(fill="x")

        self._grid_fr = tk.Frame(self, bg=BG)
        self._grid_fr.pack(fill="both", expand=True, padx=16, pady=12)

        nav = tk.Frame(self, bg=SURFACE, height=56)
        nav.pack(fill="x"); nav.pack_propagate(False)
        tk.Label(nav, text="Navegar no vídeo:", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI",8)).pack(side="left", padx=12, pady=10)
        self._nav_var = tk.DoubleVar(value=0.0)
        tk.Scale(nav, from_=0, to=100, orient="horizontal",
                 variable=self._nav_var, showvalue=False,
                 bg=SURFACE, troughcolor=SURFACE2,
                 activebackground=ACCENT, highlightthickness=0,
                 length=260).pack(side="left", padx=8, pady=10)
        mkbtn(nav, "📷 Capturar momento", self._capture_custom,
              pady=4).pack(side="left", padx=6, pady=10)

        mksep(self).pack(fill="x")
        ft = tk.Frame(self, bg=SURFACE, height=56)
        ft.pack(fill="x"); ft.pack_propagate(False)

        mkbtn(ft, "⟵ Anterior", self._prev,
              fg=MUTED, bg=BG, pady=8).pack(side="left", padx=12, pady=10)
        mkbtn(ft, "Pular →", self._skip,
              fg=WARNING, bg=BG, pady=8).pack(side="left", padx=4, pady=10)
        mkbtn(ft, "🔄 Outras 10 imagens", self._more_frames,
              fg=ACCENT, bg=SURFACE2, pady=8).pack(side="left", padx=4, pady=10)

        self._confirm_btn = mkbtn(ft, "Confirmar escolha →", self._confirm,
                                   fg=BG, bg=ACCENT, pady=8)
        self._confirm_btn.pack(side="right", padx=12, pady=10)
        self._sel_lbl = tk.Label(ft, text="Nenhuma selecionada",
                                  bg=SURFACE, fg=MUTED, font=("Segoe UI",8))
        self._sel_lbl.pack(side="right", padx=8)

    def _load_video(self, idx):
        if idx >= len(self.videos):
            self._finish(); return
        video = self.videos[idx]
        name  = os.path.basename(video)
        self._title_lbl.config(text=f"Vídeo {idx+1}: {name[:48]}")
        self._prog_lbl.config(text=f"{idx+1} de {len(self.videos)}")
        self.selected_path = None
        self._sel_lbl.config(text="Nenhuma selecionada")
        for p in self.frames:
            try: os.remove(p)
            except: pass
        self.frames = []
        for w in self._grid_fr.winfo_children(): w.destroy()
        tk.Label(self._grid_fr, text="Extraindo frames do vídeo...",
                 bg=BG, fg=MUTED, font=("Segoe UI",12)).pack(expand=True)
        self.update()
        threading.Thread(target=self._extract_frames,
                         args=(video, False), daemon=True).start()

    def _extract_frames(self, video_path, random_mode=False):
        frames = []
        try:
            cap   = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if random_mode:
                import random
                positions = sorted(random.sample(range(max(1,total)), min(10,total)))
            else:
                step = max(1, total//11)
                positions = [step*(i+1) for i in range(10)]
            for pos in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                ret, frame = cap.read()
                if ret:
                    tmp = tempfile.mktemp(suffix=".jpg")
                    cv2.imwrite(tmp, frame)
                    frames.append(tmp)
            cap.release()
        except Exception as ex:
            self.after(0, lambda: messagebox.showerror("KioThumb 2",
                f"Erro ao extrair frames:\n{ex}"))
            return
        self.after(0, lambda: self._animate_in(frames))

    def _animate_in(self, new_frames):
        """Anima a entrada dos novos frames."""
        if self._animating: return
        self._animating = True

        # Fade out dos cards antigos
        old_widgets = list(self._grid_fr.winfo_children())

        def fade_out(step=0):
            if step < 5:
                alpha = 1.0 - step*0.2
                for w in old_widgets:
                    try:
                        # Escurece progressivamente
                        w.config(bg=self._lerp_color(SURFACE2, BG, step/5))
                    except: pass
                self.after(40, lambda: fade_out(step+1))
            else:
                for w in old_widgets: w.destroy()
                for p in self.frames:
                    try: os.remove(p)
                    except: pass
                self.frames = new_frames
                self.selected_path = None
                self._sel_lbl.config(text="Nenhuma selecionada")
                self._show_grid(animate=True)
                self._animating = False

        if old_widgets:
            fade_out()
        else:
            self.frames = new_frames
            self._show_grid(animate=True)
            self._animating = False

    def _lerp_color(self, c1, c2, t):
        r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
        r = int(r1+(r2-r1)*t); g = int(g1+(g2-g1)*t); b = int(b1+(b2-b1)*t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _show_grid(self, animate=False):
        for w in self._grid_fr.winfo_children(): w.destroy()
        cols = 5
        for i, path in enumerate(self.frames):
            self._make_card(i, path, i//cols, i%cols, animate=animate, delay=i*40)

    def _make_card(self, idx, path, row, col, animate=False, delay=0):
        start_bg = BG if animate else SURFACE2

        fr = tk.Frame(self._grid_fr, bg=start_bg, cursor="hand2",
                      highlightthickness=2, highlightbackground=BORDER)
        fr.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        self._grid_fr.grid_columnconfigure(col, weight=1)

        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((155, 90))
            ph  = ImageTk.PhotoImage(img)
            lbl = tk.Label(fr, image=ph, bg=start_bg, cursor="hand2")
            lbl.image = ph
            lbl.pack(padx=2, pady=2)
        except:
            lbl = tk.Label(fr, text="?", bg=start_bg, fg=MUTED,
                           font=("Segoe UI",20))
            lbl.pack(padx=20, pady=20)

        num_lbl = tk.Label(fr, text=f"Frame {idx+1}", bg=start_bg,
                           fg=MUTED, font=("Segoe UI",7))
        num_lbl.pack(pady=(0,2))

        all_w = [fr, lbl, num_lbl]

        # Animação de fade-in
        if animate:
            def fade_in(step=0, widgets=all_w):
                if step <= 5:
                    c = self._lerp_color(BG, SURFACE2, step/5)
                    for w in widgets:
                        try: w.config(bg=c)
                        except: pass
                    self.after(40, lambda: fade_in(step+1, widgets))
            self.after(delay, fade_in)

        def select(f=fr, p=path, i=idx, ws=all_w):
            self.selected_path = p
            self._sel_lbl.config(text=f"Frame {i+1} selecionado ✔",
                                  fg=SUCCESS)
            for w in self._grid_fr.winfo_children():
                w.config(highlightbackground=BORDER)
            f.config(highlightbackground=ACCENT)

        def zoom(p=path):
            if self._zoomed_win and self._zoomed_win.winfo_exists():
                self._zoomed_win.destroy()
            win = tk.Toplevel(self); win.configure(bg=BG)
            win.title("Ampliar frame"); win.grab_set()
            self._zoomed_win = win
            try:
                im = Image.open(p).convert("RGB"); im.thumbnail((800,450))
                ph2 = ImageTk.PhotoImage(im)
                lb  = tk.Label(win, image=ph2, bg=BG)
                lb.image = ph2; lb.pack(padx=16, pady=16)
            except: pass
            mkbtn(win, "Fechar", win.destroy).pack(pady=(0,12))

        for w in all_w:
            w.bind("<Button-1>",        lambda e,f=fr,p=path,i=idx,ws=all_w: select(f,p,i,ws))
            w.bind("<Double-Button-1>", lambda e,p=path: zoom(p))

        def on_enter(e, f=fr, p=path):
            if self.selected_path != p:
                f.config(highlightbackground=ACCENT2)
        def on_leave(e, f=fr, p=path):
            if self.selected_path != p:
                f.config(highlightbackground=BORDER)

        for w in all_w:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _more_frames(self):
        """Substitui os 10 frames por outros 10 aleatórios."""
        if self.current >= len(self.videos) or self._animating: return
        video = self.videos[self.current]
        self.selected_path = None
        self._sel_lbl.config(text="Carregando...", fg=MUTED)
        threading.Thread(target=self._extract_frames,
                         args=(video, True), daemon=True).start()

    def _capture_custom(self):
        if self.current >= len(self.videos): return
        pct = self._nav_var.get()/100.0
        try:
            cap   = cv2.VideoCapture(self.videos[self.current])
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total*pct))
            ret, frame = cap.read(); cap.release()
            if ret:
                tmp = tempfile.mktemp(suffix=".jpg")
                cv2.imwrite(tmp, frame)
                self.frames.append(tmp)
                idx = len(self.frames)-1
                self._make_card(idx, tmp, idx//5, idx%5, animate=True, delay=0)
                self._grid_fr.grid_columnconfigure(idx%5, weight=1)
        except Exception as ex:
            messagebox.showerror("KioThumb 2", f"Erro:\n{ex}")

    def _confirm(self):
        if not self.selected_path:
            messagebox.showwarning("KioThumb 2", "Selecione uma imagem antes de confirmar!")
            return
        dest = os.path.join(PROJECTS_DIR, f"frame_{self.current}.jpg")
        shutil.copy2(self.selected_path, dest)
        self.results.append(dest)
        self.current += 1
        self._load_video(self.current)

    def _skip(self):
        self.results.append(None)
        self.current += 1
        self._load_video(self.current)

    def _prev(self):
        if self.current > 0:
            self.current -= 1
            if self.results: self.results.pop()
            self._load_video(self.current)

    def _finish(self):
        for p in self.frames:
            try: os.remove(p)
            except: pass
        self.destroy()
        self.callback([r for r in self.results if r])

    def _on_close(self):
        if messagebox.askyesno("KioThumb 2",
                               "Cancelar o assistente?\nAs escolhas feitas serão perdidas."):
            self.destroy()

# ══════════════════════════════════════════════════════════════════════════════
# PRÉVIA EM GRADE
# ══════════════════════════════════════════════════════════════════════════════
class GridPreview(tk.Toplevel):
    def __init__(self, parent, bg_images, qty, start, composer):
        super().__init__(parent)
        self.title("KioThumb 2 — Prévia completa")
        self.configure(bg=BG)
        self.geometry("980x620")
        self.grab_set()
        self.bg_images = bg_images
        self.qty       = qty
        self.start     = start
        self.composer  = composer
        self._build()
        self._render()

    def _build(self):
        hdr = tk.Frame(self,bg=BG,height=44); hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="Prévia — todas as thumbnails",bg=BG,fg=ACCENT,
                 font=("Times New Roman",14,"bold")).pack(side="left",padx=14,pady=8)
        mkbtn(hdr,"↺ Atualizar",self._render,pady=4).pack(side="right",padx=12,pady=8)
        mksep(self).pack(fill="x")
        c = tk.Canvas(self,bg=BG,highlightthickness=0)
        sb= tk.Scrollbar(self,orient="vertical",command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); c.pack(fill="both",expand=True)
        self._inner = tk.Frame(c,bg=BG)
        win = c.create_window((0,0),window=self._inner,anchor="nw")
        self._inner.bind("<Configure>",lambda e: c.configure(scrollregion=c.bbox("all")))
        c.bind("<Configure>",lambda e: c.itemconfig(win,width=e.width))
        mksep(self).pack(fill="x")
        ft = tk.Frame(self,bg=SURFACE,height=44); ft.pack(fill="x"); ft.pack_propagate(False)
        mkbtn(ft,"Fechar",self.destroy,pady=6).pack(side="right",padx=12,pady=6)

    def _render(self):
        for w in self._inner.winfo_children(): w.destroy()
        tk.Label(self._inner,text="Gerando prévia...",bg=BG,fg=MUTED,
                 font=("Segoe UI",10)).pack(pady=20)
        self.update()
        for w in self._inner.winfo_children(): w.destroy()
        n=len(self.bg_images); cols=4
        for i in range(self.qty):
            bg  = self.bg_images[i] if i<n else (self.bg_images[n-1] if n else None)
            num = self.start+i
            fr  = tk.Frame(self._inner,bg=SURFACE2,highlightthickness=1,
                           highlightbackground=BORDER)
            fr.grid(row=i//cols,column=i%cols,padx=5,pady=5,sticky="nsew")
            self._inner.grid_columnconfigure(i%cols,weight=1)
            try:
                img = self.composer(bg,num,320,180)
                ph  = ImageTk.PhotoImage(img)
                lb  = tk.Label(fr,image=ph,bg=SURFACE2); lb.image=ph; lb.pack(padx=3,pady=3)
            except: pass
            tk.Label(fr,text=f"#{num}",bg=SURFACE2,fg=TEXT,
                     font=("Segoe UI",8,"bold")).pack(pady=(0,4))

# ══════════════════════════════════════════════════════════════════════════════
# JANELA DE TUTORIAL
# ══════════════════════════════════════════════════════════════════════════════
class TutorialWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KioThumb 2 — Ajuda")
        self.configure(bg=BG)
        self.geometry("520x360")
        self.resizable(False, False)
        self.grab_set()

        slides = [
            ("👋  Bem-vindo ao KioThumb 2!",
             "Gera thumbnails numeradas em lote para o seu canal de longplay.\n\nUse  + Adicionar imagem  para começar — você pode adicionar fotos ou extrair frames de vídeos."),
            ("🖱️  Editando no preview",
             "Clique em qualquer elemento para selecioná-lo (contorno vermelho) e arraste para mover.\n\nScroll do mouse na imagem = zoom.\nScroll em cima de uma sobreposição = redimensiona ela.\n\nCtrl+Z para desfazer."),
            ("▶  Gerando as thumbnails",
             "No rodapé, defina o número inicial e a quantidade.\n\n• 1 imagem + quantidade 20 → 20 thumbs com a mesma imagem\n• 5 imagens + quantidade 5 → cada uma com imagem diferente\n• Se faltar imagens, a última é repetida"),
            ("🎬  Assistente de vídeo",
             "Ao adicionar vídeos, o programa extrai 10 frames para você escolher.\n\nNão gostou de nenhum? Clique em  🔄 Outras 10 imagens.\n\nNomeie seus vídeos com  #número  (ex: Sekiro #1.mp4) para ordenação automática."),
        ]

        self._idx = 0
        self._slides = slides

        tl = tk.Label(self, text="", bg=BG, fg=ACCENT,
                      font=("Times New Roman",15,"bold"),
                      wraplength=470, justify="left")
        tl.pack(padx=24, pady=(24,8), anchor="w")
        bl = tk.Label(self, text="", bg=BG, fg=TEXT,
                      font=("Segoe UI",10), wraplength=470, justify="left")
        bl.pack(padx=24, pady=4, anchor="w", fill="both", expand=True)
        pl = tk.Label(self, text="", bg=BG, fg=MUTED, font=("Segoe UI",8))
        pl.pack(pady=(0,4))

        ft = tk.Frame(self, bg=BG); ft.pack(fill="x", padx=24, pady=(0,16))
        mkbtn(ft, "Fechar", self.destroy, fg=MUTED, bg=BG, pady=6).pack(side="left")
        nb = mkbtn(ft, "Próximo →", None, fg=BG, bg=ACCENT, pady=6)
        nb.pack(side="right")
        pb = mkbtn(ft, "⟵ Anterior", None, fg=MUTED, bg=BG, pady=6)
        pb.pack(side="right", padx=6)

        def show(i):
            self._idx = i
            tl.config(text=slides[i][0])
            bl.config(text=slides[i][1])
            pl.config(text=f"{i+1} de {len(slides)}")
            nb.config(text="Próximo →" if i<len(slides)-1 else "Fechar")
            nb.config(command=(lambda: show(i+1)) if i<len(slides)-1 else self.destroy)
            pb.config(state="normal" if i>0 else "disabled")
            pb.config(command=lambda: show(i-1))

        show(0)

# ══════════════════════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class KioThumb2(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KioThumb 2")
        self.geometry("1200x740")
        self.minsize(1000, 640)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            ip = resource_path("icone2.png")
            self._ico = tk.PhotoImage(file=ip)
            self.iconphoto(True, self._ico)
        except: pass

        # Estado
        self.bg_images    = []
        self.overlays     = []
        self.current_idx  = 0
        self.selected_ov  = None
        self.custom_fonts = {}
        self.project_name = tk.StringVar(value="Novo Projeto")
        self.project_path = None
        self._unsaved     = False
        self.selected     = None
        self._hover       = None
        self._drag_sx=0; self._drag_sy=0; self._drag_ref={}
        self._undo_stack  = []
        self._list_drag_start = None

        # Vars
        self.prefix_var     = tk.StringVar(value="#")
        self.start_var      = tk.IntVar(value=1)
        self.qty_var        = tk.IntVar(value=1)
        self.font_var       = tk.StringVar(value="arialbd.ttf")
        self.font_size_var  = tk.IntVar(value=72)
        self.text_color     = "#ffffff"
        self.outline_on     = tk.BooleanVar(value=True)
        self.outline_color  = "#000000"
        self.outline_sz_var = tk.IntVar(value=3)
        self.shadow_on      = tk.BooleanVar(value=False)
        self.shadow_color   = "#000000"
        self.shadow_opacity = tk.IntVar(value=80)
        self.export_fmt     = tk.StringVar(value="PNG")
        self.jpeg_quality   = tk.IntVar(value=92)

        self.text_fx = 0.05; self.text_fy = 0.78

        self._build()
        self._refresh_preview()
        self._load_recent_projects()

        self.bind("<Control-v>", self._paste)
        self.bind("<Control-V>", self._paste)
        self.bind("<Control-z>", self._undo)
        self.bind("<Control-Z>", self._undo)

    # ══════════════════════════════════════════════════════════════════════════
    # BUILD UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build(self):
        hdr = tk.Frame(self, bg=BG, height=54)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        try:
            ic = Image.open(resource_path("icone2.png")).convert("RGBA")
            ic.thumbnail((44,44))
            self._hico = ImageTk.PhotoImage(ic)
            tk.Label(hdr, image=self._hico, bg=BG).pack(side="left",padx=(14,8),pady=5)
        except: pass
        tk.Label(hdr, text="KioThumb 2", bg=BG, fg=ACCENT,
                 font=("Times New Roman",22,"bold")).pack(side="left",pady=6)
        tk.Label(hdr, text="Gerador de Thumbnails para Longplay",
                 bg=BG, fg=MUTED, font=("Segoe UI",8)).pack(side="left",padx=10)

        # Botão de ajuda ? discreto
        help_btn = tk.Button(hdr, text="?", bg=BG, fg=MUTED,
                             relief="flat", bd=0, cursor="hand2",
                             font=("Segoe UI",11,"bold"),
                             command=self._show_tutorial)
        help_btn.pack(side="right", padx=6, pady=10)
        help_btn.bind("<Enter>", lambda e: help_btn.config(fg=ACCENT))
        help_btn.bind("<Leave>", lambda e: help_btn.config(fg=MUTED))

        # Projetos recentes
        self._recent_menu_btn = tk.Menubutton(hdr, text="📁 Projetos recentes",
                                               bg=SURFACE2, fg=TEXT, relief="flat",
                                               cursor="hand2", font=("Segoe UI",8),
                                               highlightthickness=1,
                                               highlightbackground=BORDER)
        self._recent_menu = tk.Menu(self._recent_menu_btn, tearoff=0,
                                     bg=SURFACE2, fg=TEXT,
                                     activebackground=ACCENT, activeforeground=BG)
        self._recent_menu_btn["menu"] = self._recent_menu
        self._recent_menu_btn.pack(side="right", padx=8, pady=10)
        mksep(self).pack(fill="x")

        body = tk.Frame(self, bg=BG); body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=SURFACE, width=190)
        left.pack(side="left", fill="y"); left.pack_propagate(False)
        self._build_left(left)

        right = tk.Frame(body, bg=SURFACE, width=245)
        right.pack(side="right", fill="y"); right.pack_propagate(False)
        self._build_right(right)

        mid = tk.Frame(body, bg=BG)
        mid.pack(side="left", fill="both", expand=True)
        self._build_center(mid)

        mksep(self).pack(fill="x")
        self._build_footer()

    # ── Esquerda ──────────────────────────────────────────────────────────────
    def _build_left(self, p):
        tk.Label(p, text="IMAGENS DE FUNDO", bg=SURFACE, fg=MUTED,
                 font=("Segoe UI",8,"bold")).pack(pady=(10,4),padx=8,anchor="w")
        mkbtn(p, "+ Adicionar imagem", self._show_add_menu).pack(fill="x",padx=8,pady=(0,2))
        tk.Label(p, text="ou Ctrl+V para colar print",
                 bg=SURFACE, fg="#333355", font=("Segoe UI",7)).pack(padx=8,anchor="w")
        mksep(p).pack(fill="x", pady=6)

        c = tk.Canvas(p, bg=SURFACE, highlightthickness=0)
        sb= tk.Scrollbar(p, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); c.pack(side="left", fill="both", expand=True)
        self._list_inner = tk.Frame(c, bg=SURFACE)
        win = c.create_window((0,0), window=self._list_inner, anchor="nw")
        self._list_inner.bind("<Configure>",
            lambda e: c.configure(scrollregion=c.bbox("all")))
        c.bind("<Configure>", lambda e: c.itemconfig(win, width=e.width))

    def _show_add_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=SURFACE2, fg=TEXT,
                       activebackground=ACCENT, activeforeground=BG,
                       font=("Segoe UI",9))
        menu.add_command(label="🎬  Do vídeo (extrair frames)", command=self._add_from_video)
        menu.add_command(label="🖼️  Da imagem (arquivo)",       command=self._add_from_image)
        try:
            x=self.winfo_rootx()+8; y=self.winfo_rooty()+90
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _refresh_list(self):
        for w in self._list_inner.winfo_children(): w.destroy()
        for i, bg in enumerate(self.bg_images):
            self._make_bg_card(i, bg)

    def _make_bg_card(self, i, bg):
        is_cur = (i == self.current_idx)
        bg2    = ACCENT_DIM if is_cur else SURFACE2
        border = ACCENT if is_cur else BORDER

        fr = tk.Frame(self._list_inner, bg=bg2, cursor="hand2",
                      highlightthickness=2, highlightbackground=border)
        fr.pack(fill="x", padx=6, pady=3)

        if bg.path and os.path.exists(bg.path):
            try:
                im = Image.open(bg.path).convert("RGB"); im.thumbnail((52,36))
                ph = ImageTk.PhotoImage(im)
                ll = tk.Label(fr, image=ph, bg=bg2); ll.image=ph
                ll.pack(side="left", padx=3, pady=3)
            except:
                tk.Label(fr, text="?", bg=bg2, fg=MUTED,
                         font=("Segoe UI",10)).pack(side="left",padx=4)
        else:
            tk.Label(fr, text="?", bg=bg2, fg=MUTED,
                     font=("Segoe UI",10)).pack(side="left",padx=4)

        name = os.path.basename(bg.path) if bg.path else "?"
        if len(name)>14: name=name[:12]+"…"
        info = tk.Frame(fr, bg=bg2); info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=f"#{i+1}", bg=bg2, fg=ACCENT,
                 font=("Segoe UI",11,"bold")).pack(anchor="w",padx=4,pady=(4,0))
        tk.Label(info, text=name, bg=bg2, fg=TEXT,
                 font=("Segoe UI",7)).pack(anchor="w",padx=4)

        tk.Button(fr, text="✕", bg=bg2, fg=DANGER, relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI",8),
                  command=lambda i=i: self._remove_bg(i)).pack(side="right",padx=3,pady=3)

        def enter(e, f=fr): f.config(highlightbackground=ACCENT)
        def leave(e, f=fr): f.config(highlightbackground=ACCENT if i==self.current_idx else BORDER)

        for w in fr.winfo_children():
            if not isinstance(w, tk.Button):
                w.bind("<ButtonPress-1>",   lambda e,idx=i: self._lpress(e,idx))
                w.bind("<B1-Motion>",       lambda e,idx=i: self._lmotion(e,idx))
                w.bind("<ButtonRelease-1>", lambda e,idx=i: self._lrelease(e,idx))
                w.bind("<Enter>", enter); w.bind("<Leave>", leave)
        fr.bind("<ButtonPress-1>",   lambda e,idx=i: self._lpress(e,idx))
        fr.bind("<B1-Motion>",       lambda e,idx=i: self._lmotion(e,idx))
        fr.bind("<ButtonRelease-1>", lambda e,idx=i: self._lrelease(e,idx))
        fr.bind("<Enter>", enter); fr.bind("<Leave>", leave)

    def _lpress(self,e,idx): self._list_drag_start=(idx,e.y_root)
    def _lmotion(self,e,idx): pass
    def _lrelease(self,e,idx):
        if self._list_drag_start is None: return
        orig,y0=self._list_drag_start; dy=e.y_root-y0; new=orig
        if   dy<-25 and orig>0:                        new=orig-1
        elif dy> 25 and orig<len(self.bg_images)-1:    new=orig+1
        if new!=orig:
            self.bg_images.insert(new,self.bg_images.pop(orig))
            if self.current_idx==orig:  self.current_idx=new
            elif self.current_idx==new: self.current_idx=orig
        else:
            self.current_idx=idx
        self._list_drag_start=None
        self._refresh_list(); self._refresh_preview(); self._mark_unsaved()

    # ── Centro ────────────────────────────────────────────────────────────────
    def _build_center(self, p):
        tb = tk.Frame(p, bg=BG, height=34); tb.pack(fill="x"); tb.pack_propagate(False)
        mkbtn(tb,"↩ Desfazer",self._undo,fg=MUTED,bg=BG,size=8,pady=3,padx=8).pack(side="left",padx=8,pady=4)
        tk.Label(tb,text="1280 × 720 px — YouTube",bg=BG,fg="#2a2a44",
                 font=("Segoe UI",7)).pack(side="right",padx=12)

        fr = tk.Frame(p, bg=BG); fr.pack(expand=True)
        self.cv = tk.Canvas(fr, width=PV_W, height=PV_H, bg="#0d0d14",
                            cursor="crosshair", highlightthickness=2,
                            highlightbackground=ACCENT)
        self.cv.pack(pady=10)
        self.cv.bind("<ButtonPress-1>",   self._cvpress)
        self.cv.bind("<B1-Motion>",       self._cvdrag)
        self.cv.bind("<ButtonRelease-1>", self._cvrelease)
        self.cv.bind("<MouseWheel>",      self._cvscroll)
        self.cv.bind("<Motion>",          self._cvhover)
        self.cv.bind("<Leave>",           self._cvleave)

    # ── Direita ───────────────────────────────────────────────────────────────
    def _build_right(self, p):
        c = tk.Canvas(p, bg=SURFACE, highlightthickness=0)
        sb= tk.Scrollbar(p, orient="vertical", command=c.yview)
        c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); c.pack(fill="both", expand=True)
        inn = tk.Frame(c, bg=SURFACE)
        win = c.create_window((0,0), window=inn, anchor="nw")
        inn.bind("<Configure>",lambda e: c.configure(scrollregion=c.bbox("all")))
        c.bind("<Configure>",  lambda e: c.itemconfig(win,width=e.width))

        pad=dict(padx=10,pady=2)

        def sec(icon,txt):
            mksep(inn).pack(fill="x",pady=(12,4))
            tk.Label(inn,text=f"{icon}  {txt}",bg=SURFACE,fg=MUTED,
                     font=("Segoe UI",7,"bold")).pack(anchor="w",padx=10)

        tk.Label(inn,text="✏️  TEXTO",bg=SURFACE,fg=MUTED,
                 font=("Segoe UI",7,"bold")).pack(anchor="w",padx=10,pady=(12,4))
        r=tk.Frame(inn,bg=SURFACE); r.pack(fill="x",**pad)
        tk.Label(r,text="Prefixo:",bg=SURFACE,fg=TEXT,font=("Segoe UI",9)).pack(side="left")
        e=self._mkentry(r,self.prefix_var,8); e.pack(side="left",padx=4)
        e.bind("<KeyRelease>",lambda e:self._rp())

        tk.Label(inn,text="Fonte:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(6,0))
        self.font_combo=ttk.Combobox(inn,textvariable=self.font_var,
                                      font=("Segoe UI",8),state="readonly")
        self.font_combo["values"]=get_windows_fonts()
        self.font_combo.pack(fill="x",padx=10,pady=2)
        self.font_combo.bind("<<ComboboxSelected>>",lambda e:self._rp())
        mkbtn(inn,"⊕ Importar fonte (.ttf/.otf)",self._import_font).pack(fill="x",padx=10,pady=3)
        self._imp_lbl=tk.Label(inn,text="",bg=SURFACE,fg=SUCCESS,font=("Segoe UI",7))
        self._imp_lbl.pack(anchor="w",padx=10)

        tk.Label(inn,text="Tamanho:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(6,0))
        self._mkslider(inn,self.font_size_var,8,300)

        sec("🎨","COR E EFEITOS")
        cr=tk.Frame(inn,bg=SURFACE); cr.pack(fill="x",padx=10,pady=3)
        tk.Label(cr,text="Cor do texto:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left")
        self._tcol=tk.Button(cr,bg=self.text_color,width=3,relief="flat",cursor="hand2",
                              highlightthickness=1,highlightbackground=BORDER,
                              command=self._pick_text)
        self._tcol.pack(side="left",padx=6)

        tk.Checkbutton(inn,text="Contorno",variable=self.outline_on,
                       bg=SURFACE,fg=TEXT,selectcolor=CHECK_BG,
                       activebackground=SURFACE,font=("Segoe UI",8),
                       command=self._rp).pack(anchor="w",padx=10)
        ocr=tk.Frame(inn,bg=SURFACE); ocr.pack(fill="x",padx=10,pady=2)
        tk.Label(ocr,text="Cor:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left")
        self._ocol=tk.Button(ocr,bg=self.outline_color,width=3,relief="flat",cursor="hand2",
                              highlightthickness=1,highlightbackground=BORDER,
                              command=self._pick_outline)
        self._ocol.pack(side="left",padx=4)
        tk.Label(ocr,text="Esp.:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left",padx=(8,0))
        self._mkslider(inn,self.outline_sz_var,1,20)

        tk.Checkbutton(inn,text="Sombra",variable=self.shadow_on,
                       bg=SURFACE,fg=TEXT,selectcolor=CHECK_BG,
                       activebackground=SURFACE,font=("Segoe UI",8),
                       command=self._rp).pack(anchor="w",padx=10)
        scr=tk.Frame(inn,bg=SURFACE); scr.pack(fill="x",padx=10,pady=2)
        tk.Label(scr,text="Cor:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left")
        self._scol=tk.Button(scr,bg=self.shadow_color,width=3,relief="flat",cursor="hand2",
                              highlightthickness=1,highlightbackground=BORDER,
                              command=self._pick_shadow)
        self._scol.pack(side="left",padx=6)
        tk.Label(inn,text="Opacidade da sombra:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(4,0))
        self._mkslider(inn,self.shadow_opacity,0,100)

        sec("🖼️","SOBREPOSIÇÕES (logos, selos...)")
        mkbtn(inn,"+ Adicionar PNG",self._add_overlay).pack(fill="x",padx=10,pady=3)
        tk.Label(inn,text="Clique numa sobreposição no preview\npara selecionar e arrastar.\nScroll = redimensionar.",
                 bg=SURFACE,fg="#444466",font=("Segoe UI",7),justify="left").pack(anchor="w",padx=10)
        self._ov_list_fr=tk.Frame(inn,bg=SURFACE)
        self._ov_list_fr.pack(fill="x",padx=10,pady=4)

        sec("💾","EXPORTAR")
        er=tk.Frame(inn,bg=SURFACE); er.pack(fill="x",padx=10,pady=4)
        tk.Label(er,text="Formato:",bg=SURFACE,fg=TEXT,font=("Segoe UI",8)).pack(side="left")
        for fmt in ("PNG","JPEG"):
            tk.Radiobutton(er,text=fmt,variable=self.export_fmt,value=fmt,
                           bg=SURFACE,fg=TEXT,selectcolor=CHECK_BG,
                           activebackground=SURFACE,font=("Segoe UI",8),
                           command=self._rp).pack(side="left",padx=4)
        tk.Label(inn,text="Qualidade JPEG:",bg=SURFACE,fg=TEXT,
                 font=("Segoe UI",8)).pack(anchor="w",padx=10,pady=(4,0))
        self._mkslider(inn,self.jpeg_quality,50,100)

        sec("📁","PROJETO")
        mkbtn(inn,"💾 Salvar projeto",self._save_project).pack(fill="x",padx=10,pady=2)
        mkbtn(inn,"📂 Abrir projeto",  self._open_project).pack(fill="x",padx=10,pady=2)

    def _mkentry(self,parent,var,width):
        return tk.Entry(parent,textvariable=var,width=width,
                        bg=SURFACE2,fg=TEXT,insertbackground=TEXT,relief="flat",
                        highlightthickness=1,highlightbackground=BORDER,
                        highlightcolor=ACCENT,font=("Segoe UI",9))

    def _mkslider(self,parent,var,lo,hi):
        fr=tk.Frame(parent,bg=SURFACE); fr.pack(fill="x",padx=10,pady=2)
        vl=tk.Label(fr,text=str(var.get()),bg=SURFACE,fg=ACCENT,
                    font=("Segoe UI",9,"bold"),width=5); vl.pack(side="right")
        tk.Scale(fr,from_=lo,to=hi,orient="horizontal",variable=var,showvalue=False,
                 bg=SURFACE,troughcolor=SURFACE2,activebackground=ACCENT,
                 highlightthickness=0,
                 command=lambda v,l=vl:(l.config(text=v),self._rp())
                 ).pack(side="left",fill="x",expand=True)

    def _refresh_ov_list(self):
        for w in self._ov_list_fr.winfo_children(): w.destroy()
        for i,ov in enumerate(self.overlays):
            fr=tk.Frame(self._ov_list_fr,bg=SURFACE2,highlightthickness=1,
                        highlightbackground=ACCENT if i==self.selected_ov else BORDER)
            fr.pack(fill="x",pady=2)
            tk.Label(fr,text=ov.name[:20],bg=SURFACE2,fg=TEXT,
                     font=("Segoe UI",8)).pack(side="left",padx=6,pady=4)
            tk.Button(fr,text="✕",bg=SURFACE2,fg=DANGER,relief="flat",bd=0,
                      cursor="hand2",font=("Segoe UI",8),
                      command=lambda i=i: self._remove_overlay(i)).pack(side="right",padx=4)

    # ── Rodapé ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        ft=tk.Frame(self,bg=SURFACE,height=52); ft.pack(fill="x"); ft.pack_propagate(False)

        lf=tk.Frame(ft,bg=SURFACE); lf.pack(side="left",padx=12,pady=8)
        tk.Label(lf,text="Projeto:",bg=SURFACE,fg=MUTED,font=("Segoe UI",8)).pack(side="left")
        e=self._mkentry(lf,self.project_name,14); e.config(bg=SURFACE); e.pack(side="left",padx=4)
        tk.Label(lf,text="  Início #",bg=SURFACE,fg=MUTED,font=("Segoe UI",8)).pack(side="left")
        tk.Spinbox(lf,from_=1,to=9999,textvariable=self.start_var,width=4,
                   bg=SURFACE2,fg=TEXT,relief="flat",buttonbackground=SURFACE2,
                   font=("Segoe UI",8),command=self._rp).pack(side="left",padx=2)
        tk.Label(lf,text="  Qtd:",bg=SURFACE,fg=MUTED,font=("Segoe UI",8)).pack(side="left")
        tk.Spinbox(lf,from_=1,to=999,textvariable=self.qty_var,width=4,
                   bg=SURFACE2,fg=TEXT,relief="flat",buttonbackground=SURFACE2,
                   font=("Segoe UI",8)).pack(side="left",padx=2)

        cf=tk.Frame(ft,bg=SURFACE); cf.pack(side="left",expand=True)
        mkbtn(cf,"👁  Ver prévia",self._show_grid_preview,size=9,pady=6,padx=12).pack(side="left",padx=4)
        self._gen_btn=mkbtn(cf,"▶  GERAR THUMBNAILS",self._generate,
                             fg=BG,bg=ACCENT,size=10,pady=8,padx=20)
        self._gen_btn.pack(side="left",padx=4)

        rf2=tk.Frame(ft,bg=SURFACE); rf2.pack(side="left",padx=6)
        for fmt in ("PNG","JPEG"):
            tk.Radiobutton(rf2,text=fmt,variable=self.export_fmt,value=fmt,
                           bg=SURFACE,fg=TEXT,selectcolor=CHECK_BG,
                           activebackground=SURFACE,font=("Segoe UI",8),
                           command=self._rp).pack(side="left",padx=2)

        rf=tk.Frame(ft,bg=SURFACE); rf.pack(side="right",padx=14)
        self._res_lbl=tk.Label(rf,text="",bg=SURFACE,fg="#1a1a30",font=("Segoe UI",7))
        self._res_lbl.pack()
        self._update_res()

    # ══════════════════════════════════════════════════════════════════════════
    # PREVIEW E COMPOSIÇÃO
    # ══════════════════════════════════════════════════════════════════════════
    def _rp(self,*_):
        self._refresh_preview(); self._mark_unsaved()

    def _refresh_preview(self,*_):
        try:
            bg  = self.bg_images[self.current_idx] if self.bg_images else None
            num = self.start_var.get()
            img = self._compose(bg, num, PV_W, PV_H)
            self._pvphoto = ImageTk.PhotoImage(img)
            self.cv.delete("all")
            self.cv.create_image(0,0,anchor="nw",image=self._pvphoto)
            self._draw_sel()
            self._draw_hover()
        except Exception as ex:
            self.cv.delete("all")
            self.cv.create_text(PV_W//2,PV_H//2,
                                text=f"Preview indisponível\n{ex}",
                                fill=MUTED,font=("Segoe UI",10),justify="center")

    def _compose(self, bg, number, W, H):
        base = Image.new("RGB",(W,H),"#0d0d14")

        # Imagem de fundo
        if bg and bg.path and os.path.exists(bg.path):
            try:
                src=Image.open(bg.path).convert("RGB")
                sw,sh=src.size
                bs=max(W/sw,H/sh)*bg.scale
                nw=max(1,int(sw*bs)); nh=max(1,int(sh*bs))
                scaled=src.resize((nw,nh),Image.LANCZOS)
                cx=nw//2+int(bg.ox*W); cy=nh//2+int(bg.oy*H)
                l=cx-W//2; t=cy-H//2; r=l+W; b=t+H
                if l<0:  l,r=0,W
                if t<0:  t,b=0,H
                if r>nw: l,r=nw-W,nw
                if b>nh: t,b=nh-H,nh
                l=max(0,min(l,nw-1)); t=max(0,min(t,nh-1))
                r=max(1,min(r,nw));   b=max(1,min(b,nh))
                crop=scaled.crop((l,t,r,b))
                if crop.size!=(W,H): crop=crop.resize((W,H),Image.LANCZOS)
                base.paste(crop,(0,0))
            except: pass

        draw  = ImageDraw.Draw(base)
        label = f"{self.prefix_var.get()}{number}"
        fsize = max(8,int(self.font_size_var.get()*W/YT_W))
        font  = self._load_font(fsize)
        tx=int(self.text_fx*W); ty=int(self.text_fy*H)

        # Sombra com opacidade
        if self.shadow_on.get():
            off     = max(2,int(fsize*0.06))
            opacity = int(self.shadow_opacity.get()*2.55)
            try:
                sr=int(self.shadow_color[1:3],16)
                sg=int(self.shadow_color[3:5],16)
                sb_=int(self.shadow_color[5:7],16)
                sh_layer=Image.new("RGBA",base.size,(0,0,0,0))
                sd=ImageDraw.Draw(sh_layer)
                sd.text((tx+off,ty+off),label,font=font,fill=(sr,sg,sb_,opacity))
                base_rgba=base.convert("RGBA")
                base_rgba=Image.alpha_composite(base_rgba,sh_layer)
                base=base_rgba.convert("RGB")
                draw=ImageDraw.Draw(base)
            except:
                draw.text((tx+off,ty+off),label,font=font,fill=self.shadow_color)

        # Contorno
        if self.outline_on.get():
            osz=max(1,int(self.outline_sz_var.get()*W/YT_W))
            for dx in range(-osz,osz+1):
                for dy in range(-osz,osz+1):
                    if dx or dy:
                        draw.text((tx+dx,ty+dy),label,font=font,fill=self.outline_color)
        draw.text((tx,ty),label,font=font,fill=self.text_color)

        # ── CORREÇÃO DO BUG DO PNG ──
        # Sobreposições: escala corretamente para qualquer resolução de saída
        for ov in self.overlays:
            try:
                # Calcula tamanho proporcional ao canvas de saída
                lsz = max(10, int(ov.size * W / YT_W))
                lg  = ov.pil.copy()
                lg.thumbnail((lsz, lsz), Image.LANCZOS)
                lx  = int(ov.fx * W)
                ly  = int(ov.fy * H)
                # Garante que não vai sair dos limites
                lx  = max(0, min(lx, W - lg.width))
                ly  = max(0, min(ly, H - lg.height))
                if lg.mode == "RGBA":
                    base.paste(lg, (lx,ly), lg)
                else:
                    base.paste(lg, (lx,ly))
            except: pass

        return base

    def _load_font(self,size):
        sel=self.font_var.get()
        path=self.custom_fonts.get(sel) or find_font(sel)
        try:
            if path and os.path.exists(path):
                return ImageFont.truetype(path,size)
        except: pass
        try:    return ImageFont.truetype("arial.ttf",size)
        except: return ImageFont.load_default()

    # ══════════════════════════════════════════════════════════════════════════
    # HIT TEST
    # ══════════════════════════════════════════════════════════════════════════
    def _hit(self,x,y):
        for i in range(len(self.overlays)-1,-1,-1):
            ov=self.overlays[i]
            lsz=max(10,int(ov.size*PV_W/YT_W))
            lx=int(ov.fx*PV_W); ly=int(ov.fy*PV_H)
            if lx-8<=x<=lx+lsz+8 and ly-8<=y<=ly+lsz+8:
                return f"ov_{i}"
        tx=int(self.text_fx*PV_W); ty=int(self.text_fy*PV_H)
        fsize=max(8,int(self.font_size_var.get()*PV_W/YT_W))
        if tx-8<=x<=tx+fsize*5 and ty-8<=y<=ty+fsize+12:
            return "text"
        return "image"

    def _draw_sel(self):
        if self.selected: self._draw_handle(self.selected,SEL,2,(4,3))

    def _draw_hover(self):
        if self._hover and self._hover!=self.selected:
            self._draw_handle(self._hover,ACCENT2,1,(3,4))

    def _draw_handle(self,target,color,width,dash):
        if target=="text":
            tx=int(self.text_fx*PV_W); ty=int(self.text_fy*PV_H)
            fsize=max(8,int(self.font_size_var.get()*PV_W/YT_W))
            self.cv.create_rectangle(tx-8,ty-8,tx+fsize*5,ty+fsize+12,
                                     outline=color,width=width,dash=dash)
        elif target=="image":
            self.cv.create_rectangle(4,4,PV_W-4,PV_H-4,
                                     outline=color,width=width,dash=dash)
        elif target and target.startswith("ov_"):
            idx=int(target[3:])
            if idx<len(self.overlays):
                ov=self.overlays[idx]
                lsz=max(10,int(ov.size*PV_W/YT_W))
                lx=int(ov.fx*PV_W); ly=int(ov.fy*PV_H)
                self.cv.create_rectangle(lx-8,ly-8,lx+lsz+8,ly+lsz+8,
                                         outline=color,width=width,dash=dash)

    # ══════════════════════════════════════════════════════════════════════════
    # CANVAS EVENTOS
    # ══════════════════════════════════════════════════════════════════════════
    def _cvpress(self,e):
        self._push_undo()
        self.selected=self._hit(e.x,e.y)
        if self.selected and self.selected.startswith("ov_"):
            self.selected_ov=int(self.selected[3:]); self._refresh_ov_list()
        self._drag_sx=e.x; self._drag_sy=e.y
        bg=self.bg_images[self.current_idx] if self.bg_images else None
        ref={"tx":self.text_fx,"ty":self.text_fy,
             "ox":bg.ox if bg else 0,"oy":bg.oy if bg else 0}
        for i,ov in enumerate(self.overlays):
            ref[f"ov_{i}_fx"]=ov.fx; ref[f"ov_{i}_fy"]=ov.fy
        self._drag_ref=ref
        self._refresh_preview()

    def _cvdrag(self,e):
        if not self.selected: return
        dx=(e.x-self._drag_sx)/PV_W; dy=(e.y-self._drag_sy)/PV_H
        if self.selected=="text":
            self.text_fx=max(0,min(0.95,self._drag_ref["tx"]+dx))
            self.text_fy=max(0,min(0.95,self._drag_ref["ty"]+dy))
        elif self.selected=="image" and self.bg_images:
            bg=self.bg_images[self.current_idx]
            bg.ox=self._drag_ref["ox"]-dx; bg.oy=self._drag_ref["oy"]-dy
        elif self.selected and self.selected.startswith("ov_"):
            idx=int(self.selected[3:])
            if idx<len(self.overlays):
                ov=self.overlays[idx]
                ov.fx=max(0,min(0.95,self._drag_ref[f"ov_{idx}_fx"]+dx))
                ov.fy=max(0,min(0.95,self._drag_ref[f"ov_{idx}_fy"]+dy))
        self._refresh_preview()

    def _cvrelease(self,e): self._mark_unsaved()

    def _cvscroll(self,e):
        delta=1 if e.delta>0 else -1
        hit=self._hit(e.x,e.y)
        if hit and hit.startswith("ov_"):
            idx=int(hit[3:])
            if idx<len(self.overlays):
                self.overlays[idx].size=max(20,min(1000,self.overlays[idx].size+delta*15))
        elif self.bg_images:
            bg=self.bg_images[self.current_idx]
            bg.scale=max(0.1,min(10.0,bg.scale+delta*0.05))
        self._rp()

    def _cvhover(self,e):
        h=self._hit(e.x,e.y)
        if h!=self._hover:
            self._hover=h
            self.cv.config(cursor="fleur" if h!="image" else "crosshair")
            self._refresh_preview()

    def _cvleave(self,e):
        self._hover=None; self._refresh_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # UNDO
    # ══════════════════════════════════════════════════════════════════════════
    def _push_undo(self):
        bg=self.bg_images[self.current_idx] if self.bg_images else None
        s={"tx":self.text_fx,"ty":self.text_fy,
           "ox":bg.ox if bg else 0,"oy":bg.oy if bg else 0,
           "scale":bg.scale if bg else 1}
        for i,ov in enumerate(self.overlays):
            s[f"ov_{i}"]={"fx":ov.fx,"fy":ov.fy,"size":ov.size}
        self._undo_stack.append(s)
        if len(self._undo_stack)>30: self._undo_stack.pop(0)

    def _undo(self,event=None):
        if not self._undo_stack: return
        s=self._undo_stack.pop()
        self.text_fx=s["tx"]; self.text_fy=s["ty"]
        if self.bg_images:
            bg=self.bg_images[self.current_idx]
            bg.ox=s["ox"]; bg.oy=s["oy"]; bg.scale=s["scale"]
        for i,ov in enumerate(self.overlays):
            key=f"ov_{i}"
            if key in s: ov.fx=s[key]["fx"]; ov.fy=s[key]["fy"]; ov.size=s[key]["size"]
        self._refresh_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # ADICIONAR IMAGENS
    # ══════════════════════════════════════════════════════════════════════════
    def _add_from_video(self):
        files=filedialog.askopenfilenames(title="Selecionar vídeos",
            filetypes=[("Vídeos","*.mp4 *.mkv *.avi *.mov *.webm *.flv"),("Todos","*.*")])
        if not files: return
        valid=[f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_VIDEO]
        invalid=len(files)-len(valid)
        if invalid:
            messagebox.showwarning("KioThumb 2",
                f"{invalid} arquivo(s) ignorado(s).\nFormatos suportados: {', '.join(SUPPORTED_VIDEO)}")
        if valid: VideoWizard(self,list(valid),self._wizard_done)

    def _wizard_done(self,paths):
        for p in paths:
            if p: self.bg_images.append(BgImage(p))
        self._refresh_list(); self._refresh_preview(); self._mark_unsaved()

    def _add_from_image(self):
        files=filedialog.askopenfilenames(title="Selecionar imagens",
            filetypes=[("Imagens","*.png *.jpg *.jpeg *.bmp *.webp"),("Todos","*.*")])
        for f in files: self.bg_images.append(BgImage(f))
        if files:
            self._refresh_list(); self._refresh_preview(); self._mark_unsaved()

    def _remove_bg(self,idx):
        self.bg_images.pop(idx)
        if self.current_idx>=len(self.bg_images):
            self.current_idx=max(0,len(self.bg_images)-1)
        self._refresh_list(); self._refresh_preview(); self._mark_unsaved()

    def _paste(self,event=None):
        try:
            img=ImageGrab.grabclipboard()
            if img is None:
                messagebox.showinfo("KioThumb 2","Nenhuma imagem na área de transferência.\nPressione Print Screen antes.")
                return
            if isinstance(img,Image.Image):
                tmp=tempfile.mktemp(suffix=".png"); img.save(tmp)
                self.bg_images.append(BgImage(tmp))
                self._refresh_list(); self._refresh_preview(); self._mark_unsaved()
        except Exception as ex:
            messagebox.showerror("KioThumb 2",f"Erro ao colar:\n{ex}")

    # ══════════════════════════════════════════════════════════════════════════
    # SOBREPOSIÇÕES
    # ══════════════════════════════════════════════════════════════════════════
    def _add_overlay(self):
        p=filedialog.askopenfilename(title="Adicionar sobreposição",
            filetypes=[("PNG","*.png"),("Imagens","*.png *.jpg *.jpeg"),("Todos","*.*")])
        if not p: return
        try:
            self.overlays.append(Overlay(p))
            self._refresh_ov_list(); self._rp()
        except Exception as ex:
            messagebox.showerror("KioThumb 2",f"Erro:\n{ex}")

    def _remove_overlay(self,idx):
        self.overlays.pop(idx)
        if self.selected_ov==idx: self.selected_ov=None
        self._refresh_ov_list(); self._rp()

    # ══════════════════════════════════════════════════════════════════════════
    # CORES E FONTE
    # ══════════════════════════════════════════════════════════════════════════
    def _pick_text(self):
        c=colorchooser.askcolor(color=self.text_color,title="Cor do texto")
        if c and c[1]: self.text_color=c[1]; self._tcol.config(bg=c[1]); self._rp()

    def _pick_outline(self):
        c=colorchooser.askcolor(color=self.outline_color,title="Cor do contorno")
        if c and c[1]: self.outline_color=c[1]; self._ocol.config(bg=c[1]); self._rp()

    def _pick_shadow(self):
        c=colorchooser.askcolor(color=self.shadow_color,title="Cor da sombra")
        if c and c[1]: self.shadow_color=c[1]; self._scol.config(bg=c[1]); self._rp()

    def _import_font(self):
        p=filedialog.askopenfilename(title="Importar fonte",
                                     filetypes=[("Fontes","*.ttf *.otf")])
        if not p: return
        name=os.path.basename(p)
        self.custom_fonts[name]=p
        self.font_combo["values"]=list(self.font_combo["values"])+[name]
        self.font_var.set(name)
        self._imp_lbl.config(text=f"✔ {name}")
        self._rp()

    # ══════════════════════════════════════════════════════════════════════════
    # TUTORIAL
    # ══════════════════════════════════════════════════════════════════════════
    def _show_tutorial(self):
        TutorialWindow(self)

    # ══════════════════════════════════════════════════════════════════════════
    # PRÉVIA EM GRADE
    # ══════════════════════════════════════════════════════════════════════════
    def _show_grid_preview(self):
        if not self.bg_images:
            messagebox.showinfo("KioThumb 2","Adicione pelo menos uma imagem!"); return
        GridPreview(self,self.bg_images,self.qty_var.get(),
                    self.start_var.get(),self._compose)

    # ══════════════════════════════════════════════════════════════════════════
    # GERAÇÃO
    # ══════════════════════════════════════════════════════════════════════════
    def _generate(self):
        qty=self.qty_var.get(); n=len(self.bg_images)
        if n==0:
            messagebox.showwarning("KioThumb 2","Adicione pelo menos uma imagem!"); return
        if n>1 and n<qty:
            ok=messagebox.askyesno("KioThumb 2 — Atenção",
                f"Você pediu {qty} thumbnail(s) mas adicionou {n} imagem(ns).\n"
                f"A imagem #{n} será repetida nas restantes.\n\nContinuar?")
            if not ok: return

        folder=filedialog.askdirectory(title="Onde salvar as thumbnails?")
        if not folder: return

        fmt=self.export_fmt.get(); ext=".png" if fmt=="PNG" else ".jpg"
        pref="".join(c for c in self.prefix_var.get().strip()
                     if c.isalnum() or c in "-_") or "thumb"
        start=self.start_var.get()

        existing=[i for i in range(qty)
                  if os.path.exists(os.path.join(folder,f"{pref}{start+i}{ext}"))]
        if existing:
            ok=messagebox.askyesno("KioThumb 2 — Atenção",
                f"{len(existing)} arquivo(s) já existem na pasta.\nDeseja substituir?")
            if not ok: return

        self._gen_btn.config(state="disabled",text="Gerando…")
        self.update_idletasks()

        def worker():
            try:
                for i in range(qty):
                    num=start+i
                    bg=self.bg_images[i] if i<n else self.bg_images[n-1]
                    img=self._compose(bg,num,YT_W,YT_H)
                    path=os.path.join(folder,f"{pref}{num}{ext}")
                    if fmt=="PNG": img.save(path,"PNG")
                    else:          img.convert("RGB").save(path,"JPEG",
                                       quality=self.jpeg_quality.get(),optimize=True)
                self.after(0,lambda: messagebox.showinfo("KioThumb 2",
                    f"✔ {qty} thumbnail(s) salva(s) em:\n{folder}"))
            except Exception as ex:
                self.after(0,lambda: messagebox.showerror("KioThumb 2",f"Erro:\n{ex}"))
            finally:
                self.after(0,lambda: self._gen_btn.config(
                    state="normal",text="▶  GERAR THUMBNAILS"))

        threading.Thread(target=worker,daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # SALVAR / ABRIR PROJETO
    # ══════════════════════════════════════════════════════════════════════════
    def _save_project(self):
        if not self.project_path:
            path=filedialog.asksaveasfilename(title="Salvar projeto",
                defaultextension=".json",
                initialfile=self.project_name.get()+".json",
                filetypes=[("Projeto KioThumb","*.json")])
            if not path: return
            self.project_path=path
        data={
            "project_name":self.project_name.get(),
            "prefix":self.prefix_var.get(),
            "start":self.start_var.get(),
            "qty":self.qty_var.get(),
            "font":self.font_var.get(),
            "font_size":self.font_size_var.get(),
            "text_color":self.text_color,
            "outline_on":self.outline_on.get(),
            "outline_color":self.outline_color,
            "outline_sz":self.outline_sz_var.get(),
            "shadow_on":self.shadow_on.get(),
            "shadow_color":self.shadow_color,
            "shadow_opacity":self.shadow_opacity.get(),
            "export_fmt":self.export_fmt.get(),
            "jpeg_quality":self.jpeg_quality.get(),
            "text_fx":self.text_fx,"text_fy":self.text_fy,
            "bg_images":[b.to_dict() for b in self.bg_images],
            "overlays":[o.to_dict() for o in self.overlays]
        }
        with open(self.project_path,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,ensure_ascii=False)
        self._unsaved=False
        self._save_to_recent(self.project_path,self.project_name.get())
        messagebox.showinfo("KioThumb 2",f"Projeto salvo!\n{self.project_path}")

    def _open_project(self):
        if self._unsaved:
            resp=messagebox.askyesnocancel("KioThumb 2","Alterações não salvas. Salvar antes?")
            if resp is None: return
            if resp: self._save_project()
        path=filedialog.askopenfilename(title="Abrir projeto",
            filetypes=[("Projeto KioThumb","*.json")])
        if path: self._load_project(path)

    def _load_project(self,path):
        try:
            with open(path,"r",encoding="utf-8") as f: data=json.load(f)
            self.project_name.set(data.get("project_name","Projeto"))
            self.prefix_var.set(data.get("prefix","#"))
            self.start_var.set(data.get("start",1))
            self.qty_var.set(data.get("qty",1))
            self.font_var.set(data.get("font","arialbd.ttf"))
            self.font_size_var.set(data.get("font_size",72))
            self.text_color=data.get("text_color","#ffffff"); self._tcol.config(bg=self.text_color)
            self.outline_on.set(data.get("outline_on",True))
            self.outline_color=data.get("outline_color","#000000"); self._ocol.config(bg=self.outline_color)
            self.outline_sz_var.set(data.get("outline_sz",3))
            self.shadow_on.set(data.get("shadow_on",False))
            self.shadow_color=data.get("shadow_color","#000000"); self._scol.config(bg=self.shadow_color)
            self.shadow_opacity.set(data.get("shadow_opacity",80))
            self.export_fmt.set(data.get("export_fmt","PNG"))
            self.jpeg_quality.set(data.get("jpeg_quality",92))
            self.text_fx=data.get("text_fx",0.05); self.text_fy=data.get("text_fy",0.78)
            self.bg_images=[BgImage.from_dict(d) for d in data.get("bg_images",[])]
            self.overlays=[o for o in (Overlay.from_dict(d) for d in data.get("overlays",[])) if o]
            self.current_idx=0; self.project_path=path; self._unsaved=False
            self._refresh_list(); self._refresh_ov_list(); self._refresh_preview()
            self._save_to_recent(path,data.get("project_name","Projeto"))
        except Exception as ex:
            messagebox.showerror("KioThumb 2",f"Erro ao abrir projeto:\n{ex}")

    def _save_to_recent(self,path,name):
        rec=os.path.join(APP_DIR,"recent.json")
        try:
            recents=[]
            if os.path.exists(rec):
                with open(rec) as f: recents=json.load(f)
            recents=[r for r in recents if r["path"]!=path]
            recents.insert(0,{"path":path,"name":name})
            with open(rec,"w") as f: json.dump(recents[:8],f)
            self._load_recent_projects()
        except: pass

    def _load_recent_projects(self):
        rec=os.path.join(APP_DIR,"recent.json")
        self._recent_menu.delete(0,"end")
        try:
            if os.path.exists(rec):
                with open(rec) as f: recents=json.load(f)
                for r in recents:
                    self._recent_menu.add_command(
                        label=f"{r['name']}  —  {os.path.basename(r['path'])}",
                        command=lambda p=r["path"]: self._load_project(p))
        except: pass

    # ══════════════════════════════════════════════════════════════════════════
    # FECHAR / RECURSOS
    # ══════════════════════════════════════════════════════════════════════════
    def _mark_unsaved(self): self._unsaved=True

    def _on_close(self):
        if self._unsaved:
            resp=messagebox.askyesnocancel("KioThumb 2",
                "Alterações não salvas. Salvar antes de sair?")
            if resp is None: return
            if resp: self._save_project()
        self.destroy()

    def _update_res(self):
        try:
            import psutil
            proc=psutil.Process(os.getpid())
            cpu=proc.cpu_percent(interval=None)
            ram=proc.memory_info().rss/1024/1024
            self._res_lbl.config(text=f"cpu {cpu:.0f}%  ram {ram:.0f}mb")
            if ram>800:
                messagebox.showwarning("KioThumb 2","Memória muito alta. Encerrando.")
                self.destroy(); return
        except: pass
        self.after(4000,self._update_res)

# ══════════════════════════════════════════════════════════════════════════════
if __name__=="__main__":
    try:    import psutil
    except: import subprocess; subprocess.check_call([sys.executable,"-m","pip","install","psutil"]); import psutil
    try:    import cv2
    except: import subprocess; subprocess.check_call([sys.executable,"-m","pip","install","opencv-python"]); import cv2
    KioThumb2().mainloop()

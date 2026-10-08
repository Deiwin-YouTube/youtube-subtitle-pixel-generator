import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from tkinter import font as tkfont
from PIL import Image, ImageSequence, ImageTk
import html, os, xml.etree.ElementTree as ET

DEFAULT_CHARS='`"+1nuLdoq0$8pb'

# ---------- Theme ----------
BG = '#0F1115'
PANEL = '#171A21'
PANEL_2 = '#1C2028'
BORDER = '#292E38'
TEXT = '#F1F3F5'
SECONDARY = '#9AA3B2'
MUTED = '#687180'
ACCENT = '#7C5CFF'
ACCENT_HOVER = '#8D70FF'
DANGER = '#E05252'
DANGER_HOVER = '#EF6868'
BLACK = '#000000'

class Item:
    def __init__(self,path,kind,duration=None):
        self.path=path; self.kind=kind; self.duration=duration or 5.0
        self.start=0.0; self.end=self.duration

class App:
    def __init__(self,root):
        self.root=root
        root.title('Subtitle Pixel Generator')
        root.geometry('1200x760')
        root.minsize(980,650)
        root.configure(bg=BG)

        self.items=[]; self.selected=None
        self.w=tk.IntVar(value=32); self.h=tk.IntVar(value=12); self.fps=tk.DoubleVar(value=5)
        self.mode=tk.StringVar(value='blocks'); self.chars=tk.StringVar(value=DEFAULT_CHARS); self.bg=tk.StringVar(value='#000000')
        self.fit=tk.StringVar(value='stretch'); self.only_changed=tk.BooleanVar(value=False)
        self.tkimg=None
        self.font_family='Segoe UI Variable' if 'Segoe UI Variable' in tkfont.families() else 'Segoe UI'

        self.style()
        self.ui()
        self.bind_keys()
        self.refresh()

    # ---------- UI helpers ----------
    def style(self):
        s=ttk.Style()
        try:s.theme_use('clam')
        except Exception:pass
        s.configure('.',font=(self.font_family,10),background=BG,foreground=TEXT)
        s.configure('Dark.TFrame',background=BG)
        s.configure('Panel.TFrame',background=PANEL)
        s.configure('Panel2.TFrame',background=PANEL_2)
        s.configure('Dark.TLabel',background=BG,foreground=TEXT,font=(self.font_family,10))
        s.configure('Panel.TLabel',background=PANEL,foreground=TEXT,font=(self.font_family,10))
        s.configure('Muted.TLabel',background=BG,foreground=SECONDARY,font=(self.font_family,9))
        s.configure('PanelMuted.TLabel',background=PANEL,foreground=SECONDARY,font=(self.font_family,9))
        s.configure('Section.TLabel',background=PANEL,foreground=SECONDARY,font=(self.font_family,9,'bold'))
        s.configure('TEntry',fieldbackground=PANEL_2,foreground=TEXT,insertcolor=TEXT,borderwidth=0,padding=(8,6))
        s.map('TEntry',fieldbackground=[('focus','#222733')])
        s.configure('TSpinbox',fieldbackground=PANEL_2,foreground=TEXT,insertcolor=TEXT,arrowcolor=SECONDARY,borderwidth=0,padding=(7,5))
        s.configure('TCombobox',fieldbackground=PANEL_2,foreground=TEXT,arrowcolor=SECONDARY,borderwidth=0,padding=(7,5))
        s.map('TCombobox',fieldbackground=[('readonly',PANEL_2)],foreground=[('readonly',TEXT)])
        s.configure('Vertical.TScrollbar',background=PANEL_2,troughcolor=PANEL,bordercolor=PANEL,arrowcolor=MUTED,width=8)
        s.map('Vertical.TScrollbar',background=[('active','#333947')])

    def flat_button(self,parent,text,command,primary=False,danger=False,width=None):
        bg = ACCENT if primary else (PANEL_2 if not danger else PANEL_2)
        fg = '#FFFFFF' if primary else (DANGER if danger else TEXT)
        active = ACCENT_HOVER if primary else ('#252B35' if not danger else '#2A2023')
        b=tk.Button(parent,text=text,command=command,bg=bg,fg=fg,activebackground=active,activeforeground='#FFFFFF' if primary else fg,
                     relief='flat',bd=0,highlightthickness=0,font=(self.font_family,9,'bold' if primary else 'normal'),cursor='hand2',padx=12,pady=7)
        if width is not None:b.config(width=width)
        return b

    def card(self,parent,padx=14,pady=14):
        f=tk.Frame(parent,bg=PANEL,highlightbackground=BORDER,highlightcolor=BORDER,highlightthickness=1,bd=0)
        f.pack(fill='x',padx=0,pady=0)
        inner=tk.Frame(f,bg=PANEL); inner.pack(fill='both',expand=True,padx=padx,pady=pady)
        return inner

    def section_title(self,parent,text):
        tk.Label(parent,text=text.upper(),bg=PANEL,fg=SECONDARY,font=(self.font_family,9,'bold')).pack(anchor='w',pady=(0,9))

    def divider(self,parent):
        tk.Frame(parent,bg=BORDER,height=1).pack(fill='x',pady=(13,13))

    # ---------- Main UI ----------
    def ui(self):
        # Header
        header=tk.Frame(self.root,bg=BG,height=72)
        header.pack(fill='x',padx=22,pady=(18,10))
        titlebox=tk.Frame(header,bg=BG); titlebox.pack(side='left')
        tk.Label(titlebox,text='Subtitle Pixel Generator',bg=BG,fg=TEXT,font=(self.font_family,17,'bold')).pack(anchor='w')
        tk.Label(titlebox,text='Image / GIF → YouTube subtitle pixel art',bg=BG,fg=MUTED,font=(self.font_family,9)).pack(anchor='w',pady=(2,0))
        self.flat_button(header,'Save XML',self.save,primary=True).pack(side='right',anchor='n')

        # Main split
        main=tk.Frame(self.root,bg=BG)
        main.pack(fill='both',expand=True,padx=22,pady=(0,12))
        main.grid_columnconfigure(0,weight=7,minsize=620)
        main.grid_columnconfigure(1,weight=3,minsize=320)
        main.grid_rowconfigure(0,weight=1)

        left=tk.Frame(main,bg=BG)
        left.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        right=tk.Frame(main,bg=BG)
        right.grid(row=0,column=1,sticky='nsew',padx=(8,0))
        right.grid_rowconfigure(1,weight=1)

        # Timeline card
        timeline=tk.Frame(left,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,bd=0)
        timeline.pack(fill='both',expand=True)
        top=tk.Frame(timeline,bg=PANEL); top.pack(fill='x',padx=14,pady=(14,10))
        tk.Label(top,text='TIMELINE',bg=PANEL,fg=TEXT,font=(self.font_family,10,'bold')).pack(side='left')
        self.flat_button(top,'+ Add files',self.add).pack(side='right')

        tablewrap=tk.Frame(timeline,bg=PANEL)
        tablewrap.pack(fill='both',expand=True,padx=12)
        self.table_canvas=tk.Canvas(tablewrap,bg=PANEL,highlightthickness=0,bd=0)
        self.table_canvas.pack(side='left',fill='both',expand=True)
        self.table_scroll=ttk.Scrollbar(tablewrap,orient='vertical',command=self.table_canvas.yview,style='Vertical.TScrollbar')
        self.table_scroll.pack(side='right',fill='y')
        self.table_canvas.configure(yscrollcommand=self.table_scroll.set)
        self.table_canvas.bind('<Configure>',lambda e:self.draw_table())
        self.table_canvas.bind('<MouseWheel>',self._table_wheel)
        self.table_canvas.bind('<Button-4>',self._table_wheel)
        self.table_canvas.bind('<Button-5>',self._table_wheel)

        # Toolbar
        toolbar=tk.Frame(timeline,bg=PANEL); toolbar.pack(fill='x',padx=12,pady=(10,10))
        self.flat_button(toolbar,'+ Add',self.add).pack(side='left',padx=(0,5))
        self.flat_button(toolbar,'Edit',self.edit_end).pack(side='left',padx=5)
        self.flat_button(toolbar,'↑',lambda:self.move(-1),width=3).pack(side='left',padx=5)
        self.flat_button(toolbar,'↓',lambda:self.move(1),width=3).pack(side='left',padx=5)
        self.flat_button(toolbar,'Delete',self.remove,danger=True).pack(side='right')

        # Timeline footer
        foot=tk.Frame(timeline,bg=PANEL_2,height=32); foot.pack(fill='x',side='bottom')
        self.timeline_info=tk.Label(foot,text='Files: 0    Duration: 0.000 s',bg=PANEL_2,fg=MUTED,font=(self.font_family,9))
        self.timeline_info.pack(anchor='w',padx=12,pady=7)

        # Right settings
        settings_frame=tk.Frame(right,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,bd=0)
        settings_frame.pack(fill='x')
        st=tk.Frame(settings_frame,bg=PANEL); st.pack(fill='x',padx=14,pady=14)
        tk.Label(st,text='PROJECT SETTINGS',bg=PANEL,fg=TEXT,font=(self.font_family,10,'bold')).pack(anchor='w')
        self.divider(st)

        self.section_title(st,'Canvas')
        grid=tk.Frame(st,bg=PANEL); grid.pack(fill='x')
        self.spin(grid,'Width',self.w,1,512,1,0)
        self.spin(grid,'Height',self.h,1,512,1,1)
        self.spin(grid,'FPS',self.fps,.1,60,.1,2)
        self.divider(st)

        self.section_title(st,'Render mode')
        modes=tk.Frame(st,bg=PANEL); modes.pack(fill='x')
        self.mode_buttons={}
        self.make_mode_button(modes,'Blocks  █','blocks').pack(side='left',fill='x',expand=True,padx=(0,4))
        self.make_mode_button(modes,'Characters','symbols').pack(side='left',fill='x',expand=True,padx=(4,0))

        chars_box=tk.Frame(st,bg=PANEL); chars_box.pack(fill='x',pady=(10,0))
        tk.Label(chars_box,text='Characters',bg=PANEL,fg=SECONDARY,font=(self.font_family,9)).pack(anchor='w',pady=(0,4))
        e=tk.Entry(chars_box,textvariable=self.chars,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,highlightcolor=ACCENT,font=(self.font_family,10))
        e.pack(fill='x',ipady=7,padx=1); e.bind('<KeyRelease>',lambda _:self.preview())
        tk.Label(chars_box,text='Light → Dense',bg=PANEL,fg=MUTED,font=(self.font_family,8)).pack(anchor='w',pady=(3,0))
        self.chars_entry=e
        self.divider(st)

        self.section_title(st,'Background')
        bgrow=tk.Frame(st,bg=PANEL); bgrow.pack(fill='x')
        self.bg_entry=tk.Entry(bgrow,textvariable=self.bg,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,highlightcolor=ACCENT,font=(self.font_family,9))
        self.bg_entry.pack(side='left',fill='x',expand=True,ipady=6)
        self.bg_entry.bind('<Return>',lambda _:self.preview())
        self.bg_swatch=tk.Label(bgrow,bg=BLACK,width=2,height=1,relief='flat')
        self.bg_swatch.pack(side='left',padx=7)
        self.flat_button(bgrow,'Color',self.pick_bg).pack(side='right')
        self.divider(st)

        self.section_title(st,'Scaling')
        combo=ttk.Combobox(st,textvariable=self.fit,values=('stretch','contain','cover'),state='readonly')
        combo.pack(fill='x'); combo.bind('<<ComboboxSelected>>',lambda _:self.preview())
        self.divider(st)
        cb=tk.Checkbutton(st,text='Skip unchanged frames',variable=self.only_changed,command=self.preview,bg=PANEL,fg=TEXT,activebackground=PANEL,activeforeground=TEXT,selectcolor=PANEL_2,font=(self.font_family,9),bd=0,highlightthickness=0)
        cb.pack(anchor='w')

        # Preview card
        preview_card=tk.Frame(right,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,bd=0)
        preview_card.pack(fill='both',expand=True,pady=(10,0))
        ptop=tk.Frame(preview_card,bg=PANEL); ptop.pack(fill='x',padx=14,pady=(12,8))
        tk.Label(ptop,text='PREVIEW',bg=PANEL,fg=TEXT,font=(self.font_family,10,'bold')).pack(side='left')
        self.preview_meta=tk.Label(ptop,text='32 × 12   •   5 FPS',bg=PANEL,fg=MUTED,font=(self.font_family,8))
        self.preview_meta.pack(side='right')
        self.preview_area=tk.Frame(preview_card,bg='#101218'); self.preview_area.pack(fill='both',expand=True,padx=10,pady=(0,10))
        self.preview_label=tk.Label(self.preview_area,bg=BLACK,fg=SECONDARY,text='Add an image',font=(self.font_family,9),compound='center')
        self.preview_label.pack(fill='both',expand=True,padx=1,pady=1)
        self.current_item_label=tk.Label(preview_card,text='Current item: —',bg=PANEL,fg=MUTED,font=(self.font_family,8),anchor='w')
        self.current_item_label.pack(fill='x',padx=14,pady=(0,11))

        # Status bar
        status=tk.Frame(self.root,bg=PANEL_2,height=28); status.pack(fill='x',side='bottom')
        self.status_left=tk.Label(status,text='Ready',bg=PANEL_2,fg=SECONDARY,font=(self.font_family,8))
        self.status_left.pack(side='left',padx=12,pady=6)
        self.status_right=tk.Label(status,text='0 files • 0.000 s',bg=PANEL_2,fg=MUTED,font=(self.font_family,8))
        self.status_right.pack(side='right',padx=12,pady=6)

    def make_mode_button(self,parent,text,value):
        b=tk.Button(parent,text=text,command=lambda:self.set_mode(value),bg=PANEL_2,fg=TEXT,activebackground=ACCENT_HOVER,activeforeground='#FFFFFF',relief='flat',bd=0,highlightthickness=0,font=(self.font_family,9),cursor='hand2',pady=6)
        self.mode_buttons[value]=b
        return b

    def set_mode(self,value):
        self.mode.set(value); self.update_mode_buttons(); self.preview()

    def update_mode_buttons(self):
        for value,b in self.mode_buttons.items():
            if value==self.mode.get():
                b.configure(bg=ACCENT,fg='#FFFFFF')
            else:
                b.configure(bg=PANEL_2,fg=TEXT)

    def spin(self,parent,label,var,a,b,inc,column):
        box=tk.Frame(parent,bg=PANEL); box.grid(row=0,column=column,sticky='ew',padx=(0 if column==0 else 4,4 if column<2 else 0)); parent.grid_columnconfigure(column,weight=1)
        tk.Label(box,text=label,bg=PANEL,fg=SECONDARY,font=(self.font_family,8)).pack(anchor='w',pady=(0,3))
        q=ttk.Spinbox(box,from_=a,to=b,increment=inc,textvariable=var)
        q.pack(fill='x'); q.bind('<Return>',lambda _:self.preview()); q.bind('<FocusOut>',lambda _:self.preview())

    # ---------- Keyboard/table ----------
    def bind_keys(self):
        self.root.bind('<Control-s>',lambda e:(self.save(),'break')[1])
        self.root.bind('<Delete>',lambda e:(self.remove(),'break')[1])
        self.root.bind('<Return>',lambda e:(self.edit_end(),'break')[1])
        self.root.bind('<Up>',lambda e:(self.move(-1),'break')[1])
        self.root.bind('<Down>',lambda e:(self.move(1),'break')[1])

    def _table_wheel(self,event):
        if getattr(event,'num',None)==4:self.table_canvas.yview_scroll(-3,'units')
        elif getattr(event,'num',None)==5:self.table_canvas.yview_scroll(3,'units')
        else:self.table_canvas.yview_scroll(int(-event.delta/120)*3,'units')
        return 'break'

    def draw_table(self):
        c=self.table_canvas; c.delete('all')
        width=max(c.winfo_width(),560); header_h=34; row_h=40
        cols=[('Type',70),('File',0),('From',82),('Until',82),('Duration',94)]
        fixed=sum(w for _,w in cols if w); cols[1]=(cols[1][0],max(180,width-fixed))
        x=0
        for name,w in cols:
            c.create_rectangle(x,0,x+w,header_h,fill=PANEL,outline='')
            c.create_text(x+10,header_h/2,text=name.upper(),fill=MUTED,font=(self.font_family,8,'bold'),anchor='w')
            x+=w
        for i,it in enumerate(self.items):
            y=header_h+i*row_h
            selected=(i==self.selected)
            fill='#241F3A' if selected else PANEL
            c.create_rectangle(0,y,width,y+row_h,fill=fill,outline='')
            if selected:c.create_rectangle(0,y,3,y+row_h,fill=ACCENT,outline='')
            vals=[it.kind,os.path.basename(it.path),f'{it.start:.3f}',f'{it.end:.3f}',f'{it.duration:.3f} s']
            x=0
            for j,((_,w),val) in enumerate(zip(cols,vals)):
                color=ACCENT if j==0 and selected else (TEXT if j!=0 else SECONDARY)
                c.create_text(x+10,y+row_h/2,text=val,fill=color,font=(self.font_family,9,'bold' if j==0 else 'normal'),anchor='w')
                x+=w
            c.create_line(0,y+row_h-1,width,y+row_h-1,fill=BORDER)
            c.tag_bind(c.find_all()[-1],'') if False else None
        total_h=header_h+max(1,len(self.items))*row_h
        c.configure(scrollregion=(0,0,width,total_h))
        # One transparent click layer per row is easier and stable.
        for i in range(len(self.items)):
            y0=header_h+i*row_h
            c.create_rectangle(0,y0,width,y0+row_h,fill='',outline='',tags=(f'row{i}',))
            c.tag_bind(f'row{i}','<Button-1>',lambda e,idx=i:self.select_index(idx))
            c.tag_bind(f'row{i>0 and "row"+str(i) or "row0"}','<Double-1>',lambda e,idx=i:self.edit_index(idx)) if False else None
        # Bind double click directly on canvas and resolve row from y.
        c.bind('<Double-1>',self.table_double_click)

    def table_double_click(self,event):
        idx=self.row_from_event(event)
        if idx is not None:self.select_index(idx); self.edit_end()

    def row_from_event(self,event):
        y=self.table_canvas.canvasy(event.y); idx=int((y-34)//40)
        return idx if 0<=idx<len(self.items) else None

    def select_index(self,idx):
        if not (0<=idx<len(self.items)):return
        self.selected=idx; self.draw_table(); self.preview()

    def ensure_visible(self,idx):
        if idx is None:return
        y=34+idx*40; self.table_canvas.yview_moveto(max(0,(y-40)/max(1,(34+len(self.items)*40))))

    # ---------- Existing processing logic ----------
    def add(self):
        paths=filedialog.askopenfilenames(filetypes=[('Images','*.png *.jpg *.jpeg *.webp *.bmp *.gif')])
        for p in paths:
            if p.lower().endswith('.gif'): d=self.gif_total(p); self.items.append(Item(p,'GIF',d))
            else:self.items.append(Item(p,'IMG',5.0))
        if paths:self.selected=len(self.items)-1
        self.recalc(); self.refresh(); self.preview()

    def gif_frames(self,p):
        im=Image.open(p); out=[]
        try:
            for fr in ImageSequence.Iterator(im):
                d=fr.info.get('duration',im.info.get('duration',100))
                try:d=float(d)/1000
                except:d=.1
                if d<=0:d=.1
                out.append((fr.convert('RGBA'),d))
        finally:im.close()
        return out

    def gif_total(self,p):return sum(d for _,d in self.gif_frames(p))

    def recalc(self):
        t=0
        for it in self.items:
            it.start=t
            if it.kind=='GIF':it.duration=self.gif_total(it.path)
            it.end=t+it.duration; t=it.end

    def edit_index(self,i):
        if 0<=i<len(self.items):self.selected=i; self.edit_end()

    def edit_end(self):
        if self.selected is None:return
        i=self.selected; it=self.items[i]
        if it.kind=='GIF':messagebox.showinfo('GIF','GIF duration is taken from its native frame delays.');return
        old=it.end
        win=tk.Toplevel(self.root); win.title('Edit end time'); win.configure(bg=PANEL); win.transient(self.root); win.grab_set(); win.resizable(False,False)
        tk.Label(win,text='END TIME',bg=PANEL,fg=SECONDARY,font=(self.font_family,9,'bold')).pack(anchor='w',padx=18,pady=(18,5))
        tk.Label(win,text=f'Current: {old:.3f} s',bg=PANEL,fg=TEXT,font=(self.font_family,10)).pack(anchor='w',padx=18)
        v=tk.StringVar(value=f'{old:.3f}')
        e=tk.Entry(win,textvariable=v,bg=PANEL_2,fg=TEXT,insertbackground=TEXT,relief='flat',bd=0,highlightthickness=1,highlightbackground=BORDER,highlightcolor=ACCENT,font=(self.font_family,10)); e.pack(fill='x',padx=18,pady=(10,4),ipady=7); e.focus(); e.select_range(0,'end')
        buttons=tk.Frame(win,bg=PANEL); buttons.pack(fill='x',padx=18,pady=(8,18))
        result=[None]
        def ok():result[0]=v.get();win.destroy()
        def cancel():win.destroy()
        self.flat_button(buttons,'Cancel',cancel).pack(side='right',padx=(5,0)); self.flat_button(buttons,'Apply',ok,primary=True).pack(side='right')
        win.bind('<Return>',lambda _:ok()); win.bind('<Escape>',lambda _:cancel()); self.root.wait_window(win)
        if result[0] is None:return
        try:new=float(result[0])
        except:messagebox.showerror('Invalid value','End time must be a number.');return
        if new<=it.start:messagebox.showerror('Invalid value','End time must be greater than start time.');return
        it.duration=new-it.start; self.recalc(); self.refresh(); self.preview()

    def remove(self):
        if self.selected is None or not self.items:return
        i=self.selected; del self.items[i]
        self.selected=min(i,len(self.items)-1) if self.items else None
        self.recalc(); self.refresh(); self.preview()

    def move(self,d):
        if self.selected is None:return
        i=self.selected; j=i+d
        if not 0<=j<len(self.items):return
        self.items[i],self.items[j]=self.items[j],self.items[i]; self.selected=j
        self.recalc(); self.refresh(); self.preview(); self.ensure_visible(j)

    def refresh(self):
        self.draw_table(); self.update_mode_buttons()
        total=self.items[-1].end if self.items else 0
        self.timeline_info.config(text=f'Files: {len(self.items)}    Duration: {total:.3f} s')
        self.status_left.config(text='Ready')
        self.status_right.config(text=f'{len(self.items)} files • {total:.3f} s')
        self.preview_meta.config(text=f'{self.w.get()} × {self.h.get()}   •   {self.fps.get():g} FPS')
        if self.selected is not None and self.items:
            self.current_item_label.config(text=f'Current item: {os.path.basename(self.items[self.selected].path)}')
        else:self.current_item_label.config(text='Current item: —')

    def pick_bg(self):
        c=colorchooser.askcolor(color=self.bg.get())
        if c[1]:self.bg.set(c[1]);self.bg_swatch.config(bg=c[1]);self.preview()

    def prepare(self,im):
        w,h=max(1,self.w.get()),max(1,self.h.get()); bg=self.hexrgb(self.bg.get())
        if self.fit.get()=='stretch':return im.resize((w,h),Image.Resampling.NEAREST)
        ratio=(min(w/im.width,h/im.height) if self.fit.get()=='contain' else max(w/im.width,h/im.height)); nw,nh=max(1,round(im.width*ratio)),max(1,round(im.height*ratio)); r=im.resize((nw,nh),Image.Resampling.NEAREST); c=Image.new('RGBA',(w,h),bg+(255,)); c.alpha_composite(r,((w-nw)//2,(h-nh)//2)); return c

    def hexrgb(self,s):
        s=s.strip().lstrip('#')
        if len(s)==3:s=''.join(x*2 for x in s)
        try:return tuple(int(s[i:i+2],16) for i in (0,2,4))
        except:return (0,0,0)

    def grid(self,im):
        im=self.prepare(im).convert('RGBA'); px=im.load(); w,h=im.size; chars=self.chars.get() or DEFAULT_CHARS; lines=[]
        for y in range(h):
            out=[]; last=None; buf=''
            for x in range(w):
                r,g,b,a=px[x,y]
                if a<255:r,g,b=self.hexrgb(self.bg.get())
                lum=.2126*r+.7152*g+.0722*b
                glyph='█' if self.mode.get()=='blocks' else chars[round(lum/255*(len(chars)-1))]
                key=(r,g,b,glyph)
                if last is not None and key!=last:
                    out.append(self.wrap(buf,last));buf=''
                buf+=glyph;last=key
            if buf:out.append(self.wrap(buf,last))
            lines.append(''.join(out))
        return '\n'.join(lines)

    def wrap(self,s,key):
        r,g,b,glyph=key
        if self.mode.get()=='blocks' and (r,g,b)==(0,0,0):return s
        return f'<font color="#{r:02X}{g:02X}{b:02X}">{html.escape(s)}</font>'

    def all_entries(self):
        result=[]; prev=None
        for it in self.items:
            if it.kind=='IMG':
                with Image.open(it.path) as im:grid=self.grid(im.convert('RGBA'))
                if not(self.only_changed.get() and grid==prev):result.append((it.start,it.duration,grid))
                prev=grid
            else:
                local=0
                for fr,d in self.gif_frames(it.path):
                    grid=self.grid(fr)
                    if not(self.only_changed.get() and grid==prev):result.append((it.start+local,d,grid))
                    prev=grid;local+=d
        return result

    def save(self):
        if not self.items:messagebox.showwarning('No files','Add at least one file.');return
        p=filedialog.asksaveasfilename(defaultextension='.xml',filetypes=[('XML','*.xml')])
        if not p:return
        try:
            root=ET.Element('transcript')
            for start,dur,body in self.all_entries():
                e=ET.SubElement(root,'text',start=f'{start:.3f}',dur=f'{dur:.3f}');e.text=body
            ET.ElementTree(root).write(p,encoding='utf-8',xml_declaration=False)
            self.status_left.config(text='XML saved successfully')
            messagebox.showinfo('Done',f'XML saved:\n{p}')
        except Exception as e:
            self.status_left.config(text='Save error')
            messagebox.showerror('Error',str(e))

    def preview(self):
        try:
            self.bg_swatch.config(bg=self.bg.get())
            self.preview_meta.config(text=f'{self.w.get()} × {self.h.get()}   •   {self.fps.get():g} FPS')
            if not self.items:
                self.preview_label.config(image='',text='Add an image'); self.current_item_label.config(text='Current item: —'); return
            i=self.selected if self.selected is not None and self.selected<len(self.items) else 0; it=self.items[i]
            im=(Image.open(it.path).convert('RGBA') if it.kind=='IMG' else self.gif_frames(it.path)[0][0]); im=self.prepare(im)
            area_w=max(120,self.preview_area.winfo_width()-4); area_h=max(120,self.preview_area.winfo_height()-4)
            scale=min(area_w/im.width,area_h/im.height,1)
            im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
            self.tkimg=ImageTk.PhotoImage(im.convert('RGB')); self.preview_label.config(image=self.tkimg,text='')
            self.current_item_label.config(text=f'Current item: {os.path.basename(it.path)}')
        except Exception as e:self.preview_label.config(image='',text=f'Preview error: {e}')

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()

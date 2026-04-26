import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, Menu
import subprocess
import jedi

fileSave = None
hint_win = None

def toplevel(event=None):
    # Задержка нужна, чтобы символ '(' успел появиться в поле txt
    root.after(10, _show_jedi_hint)

def _show_jedi_hint():
    global hint_win
    hide_hint()

    try:
        # Получаем текущую позицию курсора
        pos = txt.index(tk.INSERT)
        row, col = map(int, pos.split('.'))
        all_txt = txt.get("1.0", "end-1c")

        # Инициализируем Jedi
        script = jedi.Script(all_txt, path=fileSave if fileSave else "buffer.py")
        
        # Пробуем получить сигнатуру на текущей позиции и на одну левее
        signatures = script.get_signatures(row, col)
        if not signatures and col > 0:
            signatures = script.get_signatures(row, col - 1)

        if not signatures:
            return

        sig = signatures[0]
        # Формируем список параметров, убирая self для методов
        params = [p.name for p in sig.params]
        if params and params[0] == 'self':
            params.pop(0)
            
        arg_txt = f"{sig.name}({', '.join(params)})"

        # Создаем окно подсказки
        hint_win = tk.Toplevel(root)
        hint_win.wm_overrideredirect(True)
        
        # Расчет позиции окна относительно текста
        bbox = txt.bbox(tk.INSERT)
        if bbox:
            x, y, _, h = bbox
            root_x = txt.winfo_rootx() + x
            root_y = txt.winfo_rooty() + y
            hint_win.wm_geometry(f"+{root_x}+{root_y + h + 5}")
        
        label = tk.Label(hint_win, text=arg_txt, bg="#ffffe0", fg="black", 
                         relief="solid", borderwidth=1, font=("Consolas", 10), padx=4)
        label.pack()
        
    except Exception as e:
        print(f"Jedi hint error: {e}")

def hide_hint(event=None):
    global hint_win
    if hint_win:
        hint_win.destroy()
        hint_win = None

# --- Системные функции ---

def openfile():
    global fileSave
    fileOpen = filedialog.askopenfilename(title="Выберите файл")
    if fileOpen:
        with open(fileOpen, "r", encoding='utf-8') as file:
            content = file.read()
            txt.delete(1.0, tk.END)
            txt.insert(tk.INSERT, content)
            root.title(fileOpen)
            fileSave = fileOpen

def newfile():
    global fileSave
    fileSave = None
    txt.delete(1.0, tk.END)
    root.title("Новый файл")

def savefile():
    global fileSave
    fileSave = filedialog.asksaveasfilename(title="Выберите место сохранения", defaultextension='.py')
    if fileSave:
        all_text = txt.get("1.0", "end-1c")
        with open(fileSave, 'w', encoding='utf-8') as sfile:
            sfile.write(all_text)
        root.title(fileSave)

def autosavefile():
    if fileSave:
        all_text = txt.get("1.0", "end-1c")
        with open(fileSave, 'w', encoding='utf-8') as sfile:
            sfile.write(all_text)

def terminal():
    full_text = res_txt.get("1.0", tk.END)
    prompt_index = full_text.rfind('> ')
    if prompt_index == -1:
        res_txt.insert(tk.END, "\n> ")
        return
    command = full_text[prompt_index + 2:].strip()
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        res_txt.insert(tk.END, f"\n{result.stdout}")
        if result.stderr:
            res_txt.insert(tk.END, f"\nОшибка: {result.stderr}")
        res_txt.insert(tk.END, "\n> ")
        res_txt.see(tk.END)
    except Exception as e:
        res_txt.insert(tk.END, f"\nОшибка: {str(e)}\n> ")

def run():
    if fileSave is None:
        savefile()
    else:
        autosavefile()
    if fileSave:
        res_txt.insert(tk.END, f'python "{fileSave}"\n')
        terminal()

# --- Настройка окна ---

root = tk.Tk()
root.title("Python IDE Lite")
root.geometry('800x600')

# Биндинги
root.bind('<F1>', lambda e: openfile())
root.bind('<F2>', lambda e: newfile())
root.bind('<F3>', lambda e: savefile())
root.bind('<F5>', lambda e: run())
root.bind('<parenleft>', toplevel)
root.bind('<Key>', lambda e: hide_hint() if e.char not in ['(', ''] else None)
root.bind('<Button-1>', hide_hint)

# Меню
mainmenu = Menu(root)
root.config(menu=mainmenu)
filemenu = Menu(mainmenu, tearoff=0)
filemenu.add_command(label="Открыть (F1)", command=openfile)
filemenu.add_command(label="Новый (F2)", command=newfile)
filemenu.add_command(label="Сохранить (F3)", command=savefile)
mainmenu.add_cascade(label="Файл", menu=filemenu)
mainmenu.add_command(label='Запустить (F5)', command=run)

# Редактор
txt = scrolledtext.ScrolledText(root, wrap='none', font=("Consolas", 11))
txt.pack(expand=True, fill='both')

# Консоль вывода
res_txt = scrolledtext.ScrolledText(root, wrap='none', height=10, bg="#1e1e1e", fg="#ffffff")
res_txt.pack(fill='both')

res_txt.insert(tk.END, "> ")
root.mainloop()


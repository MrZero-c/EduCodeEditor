import tkinter as tk
from tkinter import scrolledtext,filedialog,ttk
from tkinter import *
import subprocess
import jedi

fileSave = None
res_windows = None
tplvl = None
res_txt = None
text = None
hint_win = None

def toplevel(event = None):
    global hint_win
    start = txt.index("insert")
    row,col = map(int,start.split('.'))
    all_txt = txt.get("1.0", "end-1c")
    script = jedi.Script(all_txt)
    sign = script.get_signatures(row,col)
    if not sign: return
    sig = sign[0]
    args = [p.name for p in sig.params]
    arg_txt = ",".join(args)

    try:
        hide_hint()
        hint_win = tk.Toplevel(root)
        x,y,_,h = txt.bbox(tk.INSERT)
        root_x = txt.winfo_rootx()+x
        root_y = txt.winfo_rooty()+y
        hint_win.wm_overrideredirect(True)
        hint_win.wm_geometry(f"+{root_x}+{root_y + 20}")
        label = tk.Label(hint_win, )
        label.config(text = args)
        label.pack()
    except Exception as e:
        print(f"error = {e}")


def hide_hint(event = None):
    global hint_win
    if hint_win:
        hint_win.destroy()
        hint_win = None


def openfile():
    global fileSave
    fileOpen = filedialog.askopenfilename(title = "Выберете файл")
    with open(fileOpen, "r", encoding = 'utf-8') as file:
        content = file.read()
        txt.delete(1.0, tk.END)  # Очищаем текстовое поле перед вставкой нового текста
        txt.insert(tk.INSERT, content)  # Вставляем содержимое файла
        root.title(fileOpen)
        fileSave = fileOpen


def newfile():
    global fileSave
    fileSave = None
    txt.delete(1.0, tk.END)
    root.title("Новый файл")

def savefile():
    global fileSave
    fileSave = filedialog.asksaveasfilename(title="Выберете место сохранения", defaultextension = '.py')
    all_text = txt.get("1.0", "end-1c")
    with open(fileSave,'w', encoding = 'utf-8') as sfile:
        sfile.write(all_text)
    root.title(fileSave)

def autosavefile():
    all_text = txt.get("1.0", "end-1c")
    with open(fileSave,'w', encoding = 'utf-8') as sfile:
        sfile.write(all_text)

def terminal():
    global res_txt
    full_text = res_txt.get("1.0", tk.END)
    prompt_index = full_text.rfind('> ') # Находим последнее приглашение
    if prompt_index == -1:
        res_txt.insert(tk.END, "\n> ")  # Если нет приглашения, добавляем новое
        return
    command = full_text[prompt_index + 2:].strip() # Извлекаем команду после приглашения
    try:
        res_txt.delete(f"{prompt_index + 2}.0", tk.END) # Очищаем область после приглашения
        result = subprocess.run(command,shell=True,capture_output=True,text=True) # Выполняем команду
        res_txt.insert(tk.END, f"\n{result.stdout}") # Добавляем результат
        if result.stderr:
            res_txt.insert(tk.END, f"\nОшибка: {result.stderr}")
        res_txt.insert(tk.END, "\n> ") # Добавляем новое приглашение
    except Exception as e:
        res_txt.insert(tk.END, f"\nОшибка: {str(e)}")

def run():
    if fileSave is None:
        savefile()
    else:
        autosavefile()

    res_txt.insert(tk.END, f'python {fileSave}\n')
    terminal()


def enter(event):
    terminal()
    return 'break'

def open_file_bind(event):
    openfile()

def new_file_bind(event):
    newfile()

def save_file_bind(event):
    savefile()

def run_bind(event):
    run()

def run_hint(event):
    toplevel()

def hide(event):
    hide_hint()


root = tk.Tk()  # Создание окна
root.title("Новый файл")  # Присвоение окну заголовка
root.geometry('500x500')  # Настройка размеров окна (500x500) и настройка его положения (+500+500)

root.bind('<F1>', open_file_bind)  # F1 - Открыть файл
root.bind('<F2>', new_file_bind)  # F2 - Создать новый файл
root.bind('<F3>', save_file_bind)  # F3 - Сохранить файл
root.bind('<F5>', run_bind)  # F5 - Запустить скрипт
root.bind('<parenleft>',toplevel)
root.bind('<Return>', hide_hint)     
root.bind('<parenright>', hide_hint) 
root.bind('<Button-1>', hide_hint)

mainmenu = Menu(root) # Создаем виджет меню и прикрепляем его к нашему окну
root.config(menu=mainmenu)

filemenu = Menu(mainmenu, tearoff = 0)
filemenu.add_command(label="Открыть...", command = openfile)
filemenu.add_command(label="Новый", command = newfile)
filemenu.add_command(label="Сохранить...", command = savefile)

helpmenu = Menu(mainmenu, tearoff = 0)
helpmenu.add_command(label="Помощь")
helpmenu.add_command(label="О программе")

mainmenu.add_cascade(label = "Файл", menu = filemenu)
mainmenu.add_cascade(label = "Помощь", menu = helpmenu)
mainmenu.add_command(label = 'Запустить',command = run)

txt = scrolledtext.ScrolledText(root, wrap = 'none', width=40, height=10,font=("Consolas", 10)) # Создаем текстовое поле с возможностью прокрутки
txt.pack(expand = True, fill='both')

h_scroll = ttk.Scrollbar(root, orient="horizontal", command=txt.xview)
h_scroll.pack(side = BOTTOM, fill = X)
txt.configure(xscrollcommand=h_scroll.set)

res_txt = scrolledtext.ScrolledText(root, wrap = 'none', width=10, height=10) # Создаем текстовое поле с возможностью прокрутки
res_txt.pack( fill='both')
res_txt.tag_configure('protect')

terminal()
root.mainloop()


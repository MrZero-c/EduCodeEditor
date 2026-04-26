import os
import tkinter as tk
from tkinter import scrolledtext,filedialog,ttk
from tkinter import *
import subprocess


fileSave = None
res_windows = None
res_txt = None
x = 1

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

def swapmode():
    global x
    x = -x

def check_cmd_active():
    try:
        # Пытаемся выполнить команду в cmd
        subprocess.check_output('tasklist | findstr cmd.exe', shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def run():
    if x == 1:
        if fileSave == None:
            savefile()
        else:
            autosavefile()
        if res_windows == None:
            create_res_windows()
        else:
            if res_windows.winfo_exists():
                None
            else:
                create_res_windows()
        # all_text = txt.get("1.0", "end-1c")
        res_txt.config(state = 'normal')
        result =  subprocess.run( ['python', fileSave], capture_output = True, text= True,timeout=10 )
        res_txt.insert(tk.END, result.stdout)
        res_txt.config(state='disabled')

    elif x == -1:
        if check_cmd_active() == True:
            autosavefile()
            os.system(f'cmd /k "python" {fileSave}')
        else:
            autosavefile()
            os.system(f'start cmd /k "python" {fileSave}')

def open_file_bind(event):
    openfile()

def new_file_bind(event):
    newfile()

def save_file_bind(event):
    savefile()

def run_bind(event):
    run()


root = tk.Tk()  # Создание окна
root.title("Новый файл")  # Присвоение окну заголовка
root.geometry('500x500')  # Настройка размеров окна (500x500) и настройка его положения (+500+500)

root.bind('<F1>', open_file_bind)  # F1 - Открыть файл
root.bind('<F2>', new_file_bind)  # F2 - Создать новый файл
root.bind('<F3>', save_file_bind)  # F3 - Сохранить файл
root.bind('<F5>', run_bind)  # F5 - Запустить скрипт
#root.bind('<F6>', toggle_mode_bind)  # F6 - Переключить режим вывода

mainmenu = Menu(root) # Создаем виджет меню и прикрепляем его к нашему окну
root.config(menu=mainmenu)

filemenu = Menu(mainmenu, tearoff = 0)
filemenu.add_command(label="Открыть...", command = openfile)
filemenu.add_command(label="Новый", command = newfile)
filemenu.add_command(label="Сохранить...", command = savefile)

helpmenu = Menu(mainmenu, tearoff = 0)
helpmenu.add_command(label="Помощь")
helpmenu.add_command(label="О программе")

modemenu = Menu(mainmenu,tearoff = 0 )
modemenu.add_command(label = 'Вывод', command = swapmode)
modemenu.add_command(label = 'Ввод-вывод', command = swapmode)


mainmenu.add_cascade(label = "Файл", menu = filemenu)
mainmenu.add_cascade(label = "Помощь", menu = helpmenu)
mainmenu.add_command(label = 'Запустить',command = run)
mainmenu.add_cascade(label =  "Режим", menu = modemenu)

txt = scrolledtext.ScrolledText(root, wrap = 'none', width=40, height=10,font=("Helvetica", 10, "bold")) # Создаем текстовое поле с возможностью прокрутки
txt.pack(expand = True, fill='both')

h_scroll = ttk.Scrollbar(root, orient="horizontal", command=txt.xview)
h_scroll.pack(side = BOTTOM, fill = X)
txt.configure(xscrollcommand=h_scroll.set)

def create_res_windows():
    global res_windows, res_txt
    res_windows = tk.Toplevel(root)
    res_windows.title("Результат")
    res_windows.geometry("500x500+700+200")
    # res_windows.withdraw()
    res_txt = scrolledtext.ScrolledText(res_windows, wrap = 'none', width=40, height=10) # Создаем текстовое поле с возможностью прокрутки
    res_txt.pack(expand = True, fill='both')

    res_h_scroll = ttk.Scrollbar(res_windows, orient="horizontal", command=res_txt.xview)
    res_h_scroll.pack(side = BOTTOM, fill = X)
    res_txt.configure(xscrollcommand=res_h_scroll.set)
    res_txt.config(state = 'disable')

root.mainloop()
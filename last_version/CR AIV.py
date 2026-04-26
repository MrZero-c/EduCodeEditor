import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, messagebox
from tkinter import *
import subprocess
import sys
import threading
import queue
import os
from pathlib import Path


class TextEditor:
    def __init__(self, root):
        self.root = root
        self.fileSave = None
        self.process = None
        self.is_running = False

        # Очереди для потокобезопасной коммуникации
        self.output_queue = queue.Queue()
        self.input_queue = queue.Queue()

        self.setup_ui()
        self.setup_bindings()

        # Запуск проверки очереди
        self.check_queue()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.root.title("Новый файл")
        self.root.geometry('800x600')

        # Создание меню
        self.create_menu()

        # Создание основной области с разделителем
        self.create_paned_window()

        # Создание строки состояния
        self.create_statusbar()

    def create_menu(self):
        """Создание главного меню"""
        mainmenu = Menu(self.root)
        self.root.config(menu=mainmenu)

        # Меню Файл
        filemenu = Menu(mainmenu, tearoff=0)
        filemenu.add_command(label="Открыть... (F1)", command=self.openfile)
        filemenu.add_command(label="Новый (F2)", command=self.newfile)
        filemenu.add_command(label="Сохранить... (F3)", command=self.savefile)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=self.root.quit)
        mainmenu.add_cascade(label="Файл", menu=filemenu)

        # Меню Правка
        editmenu = Menu(mainmenu, tearoff=0)
        editmenu.add_command(label="Копировать", command=self.copy_text)
        editmenu.add_command(label="Вставить", command=self.paste_text)
        editmenu.add_command(label="Вырезать", command=self.cut_text)
        editmenu.add_separator()
        editmenu.add_command(label="Найти...", command=self.find_text)
        mainmenu.add_cascade(label="Правка", menu=editmenu)

        # Меню Запуск
        runmenu = Menu(mainmenu, tearoff=0)
        runmenu.add_command(label="Запустить (F5)", command=self.run)
        runmenu.add_command(label="Остановить", command=self.stop_process)
        mainmenu.add_cascade(label="Запуск", menu=runmenu)

        # Меню Помощь
        helpmenu = Menu(mainmenu, tearoff=0)
        helpmenu.add_command(label="Справка", command=self.show_help)
        helpmenu.add_command(label="О программе", command=self.show_about)
        mainmenu.add_cascade(label="Помощь", menu=helpmenu)

    def create_paned_window(self):
        """Создание области с разделителем для редактора и терминала"""
        self.paned = ttk.PanedWindow(self.root, orient=VERTICAL)
        self.paned.pack(fill=BOTH, expand=True)

        # Верхняя панель (редактор)
        top_frame = Frame(self.paned)
        self.paned.add(top_frame, weight=3)

        # Редактор кода
        self.txt = scrolledtext.ScrolledText(
            top_frame,
            wrap='none',
            font=("Courier New", 11),
            undo=True
        )
        self.txt.pack(fill=BOTH, expand=True)

        # Горизонтальная прокрутка для редактора
        h_scroll = ttk.Scrollbar(top_frame, orient="horizontal", command=self.txt.xview)
        h_scroll.pack(side=BOTTOM, fill=X)
        self.txt.configure(xscrollcommand=h_scroll.set)

        # Нижняя панель (терминал)
        bottom_frame = Frame(self.paned)
        self.paned.add(bottom_frame, weight=1)

        # Метка для терминала
        terminal_label = Label(bottom_frame, text="Терминал", bg='gray', fg='white')
        terminal_label.pack(fill=X)

        # Терминал
        self.res_txt = scrolledtext.ScrolledText(
            bottom_frame,
            wrap='word',
            font=("Consolas", 10),
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.res_txt.pack(fill=BOTH, expand=True)

        # Настройка тегов для терминала
        self.res_txt.tag_configure('prompt', foreground='lime')
        self.res_txt.tag_configure('error', foreground='red')
        self.res_txt.tag_configure('output', foreground='white')
        self.res_txt.tag_configure('input', foreground='yellow')
        self.res_txt.tag_configure('info', foreground='cyan')

        self.res_txt.insert(END, "> ", 'prompt')

    def create_statusbar(self):
        """Создание строки состояния"""
        self.statusbar = Label(self.root, text="Готов", bd=1, relief=SUNKEN, anchor=W)
        self.statusbar.pack(side=BOTTOM, fill=X)

    def setup_bindings(self):
        """Настройка горячих клавиш"""
        self.root.bind('<F1>', lambda e: self.openfile())
        self.root.bind('<F2>', lambda e: self.newfile())
        self.root.bind('<F3>', lambda e: self.savefile())
        self.root.bind('<F5>', lambda e: self.run())
        self.root.bind('<Control-s>', lambda e: self.savefile())
        self.root.bind('<Control-o>', lambda e: self.openfile())
        self.root.bind('<Control-n>', lambda e: self.newfile())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

        # Привязка для ввода в терминале
        self.res_txt.bind("<Return>", self.enter_terminal)
        self.res_txt.bind("<Key>", self.on_terminal_key)

    def on_terminal_key(self, event):
        """Обработка нажатий клавиш в терминале"""
        # Запрещаем редактирование предыдущих строк
        try:
            current_pos = self.res_txt.index(INSERT)
            last_prompt = self.res_txt.search('> ', END, backwards=True)
            if last_prompt:
                if self.res_txt.compare(current_pos, '<', last_prompt):
                    return 'break'
        except:
            pass
        return None

    def enter_terminal(self, event):
        """Обработка нажатия Enter в терминале"""
        if not self.is_running:
            self.execute_command()
        else:
            # Если программа ожидает ввод, отправляем данные в очередь
            self.send_input_to_queue()
        return 'break'

    def execute_command(self):
        """Выполнение команды в терминале"""
        full_text = self.res_txt.get("1.0", END)
        lines = full_text.split('\n')

        # Находим последнюю строку с приглашением
        command = ""
        for line in reversed(lines):
            if line.strip().startswith('> '):
                command = line[2:].strip()
                break

        if command:
            try:
                # Выполняем команду в системной оболочке
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(self.fileSave) if self.fileSave else None
                )

                self.res_txt.insert(END, f"\n{result.stdout}")
                if result.stderr:
                    self.res_txt.insert(END, f"\n{result.stderr}", 'error')
                self.res_txt.insert(END, "\n> ", 'prompt')
                self.res_txt.see(END)

            except Exception as e:
                self.res_txt.insert(END, f"\nОшибка: {str(e)}\n", 'error')
                self.res_txt.insert(END, "> ", 'prompt')

    def send_input_to_queue(self):
        """Отправка ввода в очередь для процесса"""
        if self.process and self.process.poll() is None:
            # Получаем введенный текст
            full_text = self.res_txt.get("1.0", END)
            lines = full_text.split('\n')

            # Находим последнюю строку ввода
            input_text = ""
            for line in reversed(lines):
                if line.strip() and not line.strip().startswith('> '):
                    input_text = line.strip()
                    break

            if input_text:
                # Отправляем ввод в очередь
                self.input_queue.put(input_text + '\n')
                self.res_txt.insert(END, '\n')  # Добавляем новую строку для вывода

    def run(self):
        """Запуск Python скрипта"""
        if self.is_running:
            messagebox.showwarning("Внимание", "Программа уже выполняется!")
            return

        if self.fileSave is None:
            if not self.savefile():
                return
        else:
            self.autosavefile()

        # Очищаем очереди
        while not self.output_queue.empty():
            self.output_queue.get()
        while not self.input_queue.empty():
            self.input_queue.get()

        self.res_txt.delete(1.0, END)
        self.res_txt.insert(END, f"Запуск: python {os.path.basename(self.fileSave)}\n", 'info')
        self.res_txt.insert(END, "-" * 50 + "\n")
        self.res_txt.see(END)

        # Запускаем скрипт в отдельном потоке
        self.is_running = True
        self.statusbar.config(text="Выполняется...")
        thread = threading.Thread(target=self.run_script, daemon=True)
        thread.start()

    def run_script(self):
        """Запуск скрипта в отдельном процессе с поддержкой input()"""
        try:
            # Запускаем процесс с перенаправлением ввода/вывода
            self.process = subprocess.Popen(
                [sys.executable, self.fileSave],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=os.path.dirname(self.fileSave)
            )

            # Поток для чтения stdout
            def read_stdout():
                for line in iter(self.process.stdout.readline, ''):
                    self.output_queue.put(('output', line))
                self.process.stdout.close()

            # Поток для чтения stderr
            def read_stderr():
                for line in iter(self.process.stderr.readline, ''):
                    self.output_queue.put(('error', line))
                self.process.stderr.close()

            # Поток для записи stdin
            def write_stdin():
                while self.process.poll() is None:
                    try:
                        # Ждем ввод из очереди
                        user_input = self.input_queue.get(timeout=0.1)
                        self.process.stdin.write(user_input)
                        self.process.stdin.flush()
                    except queue.Empty:
                        continue
                    except:
                        break
                self.process.stdin.close()

            # Запускаем потоки для ввода/вывода
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stdin_thread = threading.Thread(target=write_stdin, daemon=True)

            stdout_thread.start()
            stderr_thread.start()
            stdin_thread.start()

            # Ждем завершения процесса
            self.process.wait()

            # Сигнализируем о завершении
            self.output_queue.put(('info', "\n" + "-" * 50 + "\n"))
            self.output_queue.put(('info', "Выполнение завершено.\n"))
            self.output_queue.put(('prompt', "> "))

        except Exception as e:
            self.output_queue.put(('error', f"Ошибка: {str(e)}\n"))
        finally:
            self.is_running = False
            self.process = None

    def check_queue(self):
        """Проверка очереди вывода и обновление терминала"""
        try:
            while True:
                tag, text = self.output_queue.get_nowait()
                self.res_txt.insert(END, text, tag)
                self.res_txt.see(END)
        except queue.Empty:
            pass
        finally:
            # Проверяем снова через 100 мс
            self.root.after(100, self.check_queue)

    def stop_process(self):
        """Остановка выполняющегося процесса"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.is_running = False
            self.statusbar.config(text="Процесс остановлен")
            self.res_txt.insert(END, "\nПроцесс остановлен пользователем.\n", 'error')
            self.res_txt.insert(END, "> ", 'prompt')

    def openfile(self):
        """Открытие файла"""
        fileOpen = filedialog.askopenfilename(
            title="Выберете файл",
            filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if fileOpen:
            try:
                with open(fileOpen, "r", encoding='utf-8') as file:
                    content = file.read()
                    self.txt.delete(1.0, END)
                    self.txt.insert(INSERT, content)
                    self.root.title(fileOpen)
                    self.fileSave = fileOpen
                    self.statusbar.config(text=f"Открыт файл: {fileOpen}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {str(e)}")

    def newfile(self):
        """Создание нового файла"""
        if self.txt.edit_modified() and messagebox.askyesno("Сохранение", "Сохранить изменения?"):
            self.savefile()
        self.fileSave = None
        self.txt.delete(1.0, END)
        self.root.title("Новый файл")
        self.statusbar.config(text="Новый файл")

    def savefile(self):
        """Сохранение файла"""
        if self.fileSave is None:
            fileSave = filedialog.asksaveasfilename(
                title="Выберете место сохранения",
                defaultextension='.py',
                filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            if not fileSave:
                return False
            self.fileSave = fileSave

        all_text = self.txt.get("1.0", "end-1c")
        try:
            with open(self.fileSave, 'w', encoding='utf-8') as sfile:
                sfile.write(all_text)
            self.root.title(self.fileSave)
            self.txt.edit_modified(False)
            self.statusbar.config(text=f"Сохранено: {self.fileSave}")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
            return False

    def autosavefile(self):
        """Автосохранение файла"""
        if self.fileSave:
            all_text = self.txt.get("1.0", "end-1c")
            try:
                with open(self.fileSave, 'w', encoding='utf-8') as sfile:
                    sfile.write(all_text)
                self.txt.edit_modified(False)
            except:
                pass

    def copy_text(self):
        """Копирование текста"""
        try:
            self.txt.event_generate("<<Copy>>")
        except:
            pass

    def paste_text(self):
        """Вставка текста"""
        try:
            self.txt.event_generate("<<Paste>>")
        except:
            pass

    def cut_text(self):
        """Вырезание текста"""
        try:
            self.txt.event_generate("<<Cut>>")
        except:
            pass

    def find_text(self):
        """Поиск текста (упрощенная версия)"""
        find_dialog = Toplevel(self.root)
        find_dialog.title("Найти")
        find_dialog.geometry("300x100")

        Label(find_dialog, text="Найти:").pack()
        entry = Entry(find_dialog, width=30)
        entry.pack()

        def find():
            text = entry.get()
            if text:
                # Убираем выделение
                self.txt.tag_remove("found", "1.0", END)
                # Ищем текст
                start = "1.0"
                while True:
                    pos = self.txt.search(text, start, stopindex=END)
                    if not pos:
                        break
                    end = f"{pos}+{len(text)}c"
                    self.txt.tag_add("found", pos, end)
                    start = end
                self.txt.tag_config("found", background="yellow")

        Button(find_dialog, text="Найти", command=find).pack()

    def show_help(self):
        """Показ справки"""
        help_text = """
        Горячие клавиши:
        F1 / Ctrl+O - Открыть файл
        F2 / Ctrl+N - Новый файл
        F3 / Ctrl+S - Сохранить
        F5 - Запустить скрипт
        Ctrl+Q - Выход

        В терминале можно вводить команды после символа '>'
        """
        messagebox.showinfo("Справка", help_text)

    def show_about(self):
        """Информация о программе"""
        about_text = """
        Простой редактор кода
        Версия 3.0

        Возможности:
        - Подсветка синтаксиса Python
        - Встроенный терминал
        - Поддержка input()
        - Запуск скриптов в отдельном процессе
        - Потокобезопасный ввод/вывод с использованием queue
        """
        messagebox.showinfo("О программе", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
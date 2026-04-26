import customtkinter as ctk
import os
from tkinter import filedialog  # filedialog пока оставляем
import subprocess

# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CodeEditor:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Новый файл")
        self.root.geometry('500x500')

        self.fileSave = None
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        # Верхняя панель инструментов
        toolbar = ctk.CTkFrame(self.root)
        toolbar.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(toolbar, text="📂 Открыть", command=self.openfile).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="📄 Новый", command=self.newfile).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="💾 Сохранить", command=self.savefile).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="▶ Запустить", command=self.run, fg_color="green").pack(side="left", padx=2)

        # Основная область кода
        code_frame = ctk.CTkFrame(self.root)
        code_frame.pack(expand=True, fill='both', padx=5, pady=5)

        self.txt = ctk.CTkTextbox(code_frame, font=("Courier New", 12), wrap="none")
        self.txt.pack(side="left", expand=True, fill='both')

        v_scroll = ctk.CTkScrollbar(code_frame, command=self.txt.yview)
        v_scroll.pack(side="right", fill="y")
        self.txt.configure(yscrollcommand=v_scroll.set)

        # Область терминала
        term_frame = ctk.CTkFrame(self.root)
        term_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.res_txt = ctk.CTkTextbox(term_frame, font=("Courier New", 10), wrap="none")
        self.res_txt.pack(side="left", expand=True, fill='both')

        term_scroll = ctk.CTkScrollbar(term_frame, command=self.res_txt.yview)
        term_scroll.pack(side="right", fill="y")
        self.res_txt.configure(yscrollcommand=term_scroll.set)

        self.res_txt.insert("end", "> ")

    # Ваши原有的 функции (openfile, newfile, savefile, terminal, run)
    # остаются почти без изменений, только self добавляется

    def openfile(self):
        fileOpen = filedialog.askopenfilename(title="Выберете файл")
        if fileOpen:
            with open(fileOpen, "r", encoding='utf-8') as file:
                content = file.read()
                self.txt.delete("1.0", "end")
                self.txt.insert("1.0", content)
                self.root.title(fileOpen)
                self.fileSave = fileOpen

    def newfile(self):
        self.fileSave = None
        self.txt.delete("1.0", "end")
        self.root.title("Новый файл")

    def savefile(self):
        if self.fileSave is None:
            self.fileSave = filedialog.asksaveasfilename(
                title="Выберете место сохранения",
                defaultextension='.py'
            )
        if self.fileSave:
            all_text = self.txt.get("1.0", "end-1c")
            with open(self.fileSave, 'w', encoding='utf-8') as sfile:
                sfile.write(all_text)
            self.root.title(self.fileSave)

    def terminal(self):
        full_text = self.res_txt.get("1.0", "end")
        prompt_index = full_text.rfind('> ')
        if prompt_index == -1:
            self.res_txt.insert("end", "\n> ")
            return
        command = full_text[prompt_index + 2:].strip()
        try:
            self.res_txt.delete(f"{prompt_index + 2}.0", "end")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.stdout:
                self.res_txt.insert("end", f"\n{result.stdout}")
            if result.stderr:
                self.res_txt.insert("end", f"\nОшибка: {result.stderr}")
            self.res_txt.insert("end", "\n> ")
        except Exception as e:
            self.res_txt.insert("end", f"\nОшибка: {str(e)}")

    def run(self):
        if self.fileSave is None or not os.path.isfile(self.fileSave):
            self.res_txt.insert("end", "\nОшибка: Файл не найден.\n> ")
            return
        self.res_txt.insert("end", f'python {self.fileSave}\n')
        self.terminal()

    def enter(self, event):
        self.terminal()
        return 'break'

    def setup_bindings(self):
        self.root.bind('<F1>', lambda e: self.openfile())
        self.root.bind('<F2>', lambda e: self.newfile())
        self.root.bind('<F3>', lambda e: self.savefile())
        self.root.bind('<F5>', lambda e: self.run())
        self.res_txt.bind("<Return>", self.enter)

    def run_app(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CodeEditor()
    app.run_app()
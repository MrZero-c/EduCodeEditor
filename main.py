import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk
import subprocess
import re

class Editor:
    def __init__(self,root):
        self.file_save_path = None
        self.root = root
        self.setup_ui()
        self.setup_menu()
        self.key_binds()
        self.tag_init()
        self.terminal_field.insert('end', '>')

    def setup_ui(self):
        self.input_field = scrolledtext.ScrolledText(self.root, wrap = 'none',width = 40,height = 10,font = ('Consolas', 10))
        self.input_field.pack(expand = True, fill = 'both')
        self.horizontal_scroll = ttk.Scrollbar(self.root, orient = 'horizontal', command=self.input_field.xview)
        self.horizontal_scroll.pack(side = tk.BOTTOM, fill = tk.X)
        self.input_field.configure(xscrollcommand=self.horizontal_scroll.set)
        self.terminal_field = scrolledtext.ScrolledText(self.root, wrap = 'none', width=10, height=10)
        self.terminal_field.pack(fill = 'both')

    def setup_menu(self):
        self.main_menu = tk.Menu(self.root)
        self.root.config(menu = self.main_menu)

        # Файловое меню

        self.file_menu = tk.Menu(self.main_menu, tearoff = 0)
        self.main_menu.add_cascade(label = "Файл", menu = self.file_menu)
        self.file_menu.add_command(label = "Открыть",command = self.open_file)
        self.file_menu.add_command(label = "Новый", command = self.new_file)
        self.file_menu.add_command(label = "Сохранить", command = self.save_file)
        
        # Функциональные кнопки

        self.main_menu.add_command(label = "Запустить", command = self.run_script)

    def key_binds(self):
        self.terminal_field.bind('<Return>', self.run_command) 
        self.terminal_field.bind('<Key>', self.check_readonly)
        self.input_field.bind('<KeyRelease>', self.highlight)

    def tag_init(self):
        self.input_field.tag_config('keyword', foreground = '#c678dd')
        self.input_field.tag_config('number', foreground = '#d19a66')
        self.input_field.tag_config('comment', foreground = '#98c379')
        self.input_field.tag_config('string', foreground = '#5c6370')



    def highlight(self, event = None):
        patterns = {
                'keyword':r'\b(if|else|for|while|def|import|return|elif|continue|in|as)\b',
                'number':r'\b\d+\b',
                'comment':r'#.*',
                'string':r'\".*?\"|\'.*?\'',
                }

        full_regex = "|".join([f"(?P<{name}>{pattern})" for name, pattern in patterns.items()])

        for i in patterns.keys():
            self.input_field.tag_remove(i,'1.0', tk.END)

        text = self.input_field.get('1.0', tk.END) 

        for match in re.finditer(full_regex, text):
            kind = match.lastgroup
            value = match.group()
            start_index = f'1.0 + {match.start()} chars'
            end_index = f'1.0 + {match.end()} chars'
            self.input_field.tag_add(kind,start_index, end_index)



    def check_readonly(self,event):
        cursor_index = self.terminal_field.index(tk.INSERT)
        line, sumb = cursor_index.split('.')
        sumb = int(sumb) + 2
        sumb = str(sumb)
        index = line + '.' + sumb
        tag_at_cursor = self.terminal_field.tag_names(index)
        if 'readonly' in tag_at_cursor:
            return 'break'
        
    def open_file(self, event = None):
        ask_file_path = filedialog.askopenfilename(title = "Выберете файл")
        if not ask_file_path:
            return
        with open(ask_file_path, 'r', encoding = 'utf-8') as file:
            open_file_text = file.read()
            self.input_field.delete(1.0, tk.END)
            self.input_field.insert(tk.INSERT, open_file_text)
            self.root.title(ask_file_path) 
            self.file_save_path = ask_file_path 

    def new_file(self, event = None):
        self.file_save_path = None
        self.input_field.delete(1.0, tk.END)
        self.root.title("Новый файл")

    def save_file(self,event = None):
        new_save_path = filedialog.asksaveasfilename(title = "Выберете место сохранения")
        if not new_save_path:
            return
        self.file_save_path = new_save_path
        save_file_text =  self.input_field.get(1.0, tk.END)
        with open(self.file_save_path, 'w', encoding = 'utf-8') as save_file:
            save_file.write(save_file_text)
        self.root.title(self.file_save_path)

    def auto_save_file(self):
        save_file_text =  self.input_field.get(1.0, tk.END)
        if self.file_save_path:
            with open(self.file_save_path, 'w', encoding = 'utf-8') as auto_save_file:
                auto_save_file.write(save_file_text)
        else:
            self.save_file()
    
    def get_terminal_command(self):
        all_content_with_terminal = self.terminal_field.get('1.0', tk.END)
        content_lines = all_content_with_terminal.splitlines()
        for line_index in range(len(content_lines)):
            invite_index = content_lines[line_index].find('>')
            if invite_index != -1:  
                new_command = self.terminal_field.get(f'{line_index + 1}.{invite_index + 1}', f'{line_index + 1}.end')
                command = new_command
        return command

    def run_command(self, event = None):
        terminal_command = self.get_terminal_command()
        command_result = subprocess.run(terminal_command, shell = True, capture_output = True, text = True)
        self.terminal_field.insert(tk.END, f'\n{command_result.stdout}', 'readonly')
        if command_result.stderr:
            self.terminal_field.insert(tk.END, f'\n{command_result.stderr}', 'readonly')
        self.terminal_field.insert(tk.INSERT, '>', 'readonly')
        self.terminal_field.see(tk.END)
        if event is not None:
            return "break"

    def run_script(self):
        self.auto_save_file()
        self.terminal_field.insert(tk.END, f'python {self.file_save_path}')
        self.run_command()    
        
if __name__ == '__main__':
    root = tk.Tk()
    app = Editor(root)
    root.mainloop()

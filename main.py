import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk
import subprocess
import re
import themes
import threading
import queue
import psutil

class Editor:
    def __init__(self,root):
        self.file_save_path = None
        self.root = root
        self.q = queue.Queue()
        self.setup_ui()
        self.setup_menu()
        self.themes_menu_setup()
        self.change_theme(themes.LIGHT_THEME)
        self.key_binds()
        self.tag_init()
        self.highlight()

    def setup_ui(self):
        self.input_field = scrolledtext.ScrolledText(self.root, wrap = 'none',width = 40,height = 10,font = ('Consolas', 10))
        self.input_field.pack(expand = True, fill = 'both')
        self.horizontal_scroll = ttk.Scrollbar(self.root, orient = 'horizontal', command=self.input_field.xview)
        self.horizontal_scroll.pack(side = tk.BOTTOM, fill = tk.X)
        self.input_field.configure(xscrollcommand=self.horizontal_scroll.set)

        #Creating object terminal

        self.terminal = Terminal(self.root)
        self.terminal.setup_terminal()

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
        self.main_menu.add_command(label = "Остановить", command = self.terminal.stop_running)
 
    def themes_menu_setup(self):
        self.themes_list = {'Black': themes.DARK_THEME,
                       'Tokyo_night': themes.TOKYO_NIGHT,
                       'White': themes.LIGHT_THEME}


        self.themes_menu = tk.Menu(self.main_menu, tearoff = 0)
        self.main_menu.add_cascade(label = "Темы", menu = self.themes_menu)
        for  label, name in self.themes_list.items():
            self.themes_menu.add_command(label = label, command = lambda t=name: self.change_theme(t))

    def key_binds(self):
        self.input_field.bind('<KeyRelease>', self.highlight)

    def tag_init(self):
        self.input_field.tag_config('keyword', foreground = self.syntax_theme['keyword'])
        self.input_field.tag_config('number', foreground = self.syntax_theme['number'])
        self.input_field.tag_config('comment', foreground = self.syntax_theme['comment'])
        self.input_field.tag_config('string', foreground = self.syntax_theme['string'])
        self.input_field.tag_config('oopword', foreground = self.syntax_theme['oopword'])
        self.input_field.tag_config('prepositions', foreground = self.syntax_theme['prepositions'])


    def change_theme(self,theme):
        if theme:
            self.root.config(bg = theme['root_bg'])
            self.input_field.config(bg = theme['input_bg'], fg = theme['input_fg'],bd = 0,relief = 'flat',highlightthickness=0,insertbackground=theme['cursor'])
            self.main_menu.config(bg = theme['menu_bg'],fg = theme['menu_fg'],bd = 0, relief = 'flat')
            menus = [self.file_menu, self.themes_menu]

            self.terminal.change_theme(theme)

            for m in menus:
                m.config(bg = theme['menu_bg'],fg = theme['menu_fg'])

            self.syntax_theme = theme['syntax']
            self.tag_init()
        

    def highlight(self, event = None):
        patterns = {
                'keyword':r'\b(if|else|for|while|def|import|return|elif|continue|range|from)\b',
                'number':r'\b\d+\b',
                'comment':r'#.*',
                'string':r'\".*?\"|\'.*?\'',
                'oopword':r'\b(self|class)\b',
                'prepositions':r'\b(in|as|note|None)\b'
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
        self.highlight()

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
    
    def run_script(self):
        self.auto_save_file()
        self.terminal.run_script(self.file_save_path)



class Terminal:
    def __init__(self, root):
       self.root = root
       self.q = queue.Queue()
       self.get_async_output()

    def setup_terminal(self):
        self.terminal = scrolledtext.ScrolledText(self.root, wrap = 'none', width = 10, height = 10)
        self.terminal.pack(fill = 'both')
        self.terminal.insert(tk.END, '>')
        self.key_binds_init()
        self.terminal.insert(tk.END, 'test', 'readonly')

    def key_binds_init(self):
        self.terminal.bind('<Return>', self.run_command)
        self.terminal.bind('<Key>', self.check_readonly)

    def check_readonly(self, event):
        cursor_index =  self.terminal.index('insert')
        after_cursor_index = self.terminal.index('insert + 1c')
        before_cursor_index = self.terminal.index('insert - 1c')
        tag = self.terminal.tag_names(cursor_index)
        tag_after_cursor = self.terminal.tag_names(after_cursor_index)
        tag_before_cursor = self.terminal.tag_names(before_cursor_index)
        print(event.keysym)
        ranges = self.terminal.tag_ranges('readonly')
        move_keys = ['Up','Down','Right','Left']
        if event.keysym == 'BackSpace' and 'readonly' in tag_before_cursor:
            return 'break'
        if  'readonly' in tag and 'readonly' in tag_before_cursor and event.keysym not in move_keys:
            return 'break'
            

    def get_commands(self):
        all_content_with_terminal = self.terminal.get('1.0', tk.END)
        content_lines = all_content_with_terminal.splitlines()
        for line_index in range(len(content_lines)):
            invite_index = content_lines[line_index].find('>')
            if invite_index != -1:  
                new_command = self.terminal.get(f'{line_index + 1}.{invite_index + 1}', f'{line_index + 1}.end')
                command = new_command
        return command
    
    def run_command(self, event = None):
        terminal_command = self.get_commands()
        self.thread_popen = threading.Thread(target = self.async_popen, args=(terminal_command,))
        self.thread_popen.daemon = True
        self.thread_popen.start()

        if event is not None:
            return "break"
        
    def run_script(self, script_path):
        self.terminal.insert(tk.END,f'python -u {script_path}')
        self.run_command()

        
    def stop_running(self, event=None):
            try:
                current_pid = self.command_result.pid
                parent = psutil.Process(current_pid)
            
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                parent.wait()
            
                with self.q.mutex:
                    self.q.queue.clear()
                
                self.terminal.insert(tk.END, "\nПроцесс остановлен\n>", 'readonly')
                self.terminal.see(tk.END)
            
            except (psutil.NoSuchProcess, AttributeError):
                pass

    def get_async_output(self):
        lines_processed = 0
        try:
            while lines_processed < 10:
                line = self.q.get_nowait()
                self.terminal.insert(tk.END, f'{line}', 'readonly')
                lines_processed += 1
                self.q.task_done()
        except queue.Empty:
            pass
        
        if lines_processed > 0:
            self.terminal.see(tk.END)
            
        self.root.after(1, self.get_async_output)

    def async_popen(self,command):
        self.command_result = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True, text = True,bufsize = 1)
        self.q.put(f'\n')
        for line in iter(self.command_result.stdout.readline, ''):
            self.q.put(line)
        for line in iter(self.command_result.stderr.readline, ''):
            if line:
                self.q.put(f'\n{line}')
        self.q.put(f'>')

    def change_theme(self, theme):
       self.terminal.config(bg = theme['term_bg'], fg = theme['term_fg'],bd = 0, relief = 'flat',highlightthickness=0,insertbackground=theme['cursor'])
        
if __name__ == '__main__':
    root = tk.Tk()
    app = Editor(root)
    root.mainloop()


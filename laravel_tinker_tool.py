import os
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import threading
import queue
import re
import json
import datetime

class LaravelTinkerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laravel Tinker Tool")
        self.root.geometry("1200x800")
        # Iniciar maximizado
        self.root.state('zoomed')
        
        self.project_path = tk.StringVar()
        self.output_queue = queue.Queue()
        
        # Historial de logs
        self.log_history = []
        
        # Habilitar transformador de código
        self.auto_transform = tk.BooleanVar(value=True)
        
        # Crear menú
        self.create_menu()
        
        # Crear widgets
        self.create_widgets()
        
        self.root.after(100, self.check_output_queue)
    
    def create_menu(self):
        # Crear barra de menú
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Menú Archivo
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir Proyecto", command=self.browse_project)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Edición
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edición", menu=edit_menu)
        edit_menu.add_command(label="Limpiar Editor", command=lambda: self.code_editor.delete(1.0, tk.END))
        
        # Menú Laravel
        laravel_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Laravel", menu=laravel_menu)
        laravel_menu.add_command(label="Listar Modelos", command=self.list_models)
        laravel_menu.add_command(label="Consulta Modelo", command=self.model_query_dialog)
        laravel_menu.add_separator()
        laravel_menu.add_command(label="Ejecutar Migraciones", 
                                command=lambda: self.run_artisan_command("migrate"))
        laravel_menu.add_command(label="Ver Rutas", 
                                command=lambda: self.run_artisan_command("route:list"))
        
        # Menú Logs
        logs_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Logs", menu=logs_menu)
        logs_menu.add_command(label="Limpiar Logs", command=self.clear_logs)
        logs_menu.add_command(label="Exportar Logs", command=self.export_logs)
        
        # Menú Vista
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Vista", menu=view_menu)
        view_menu.add_command(label="Mostrar último resultado en tabla", 
                            command=lambda: self.show_last_json_data())
        
        # Menú Configuración
        config_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Configuración", menu=config_menu)
        config_menu.add_checkbutton(label="Auto-transformar expresiones de modelo", 
                                variable=self.auto_transform, 
                                onvalue=True, 
                                offvalue=False)
        
        # Menú Ayuda
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
            
    def create_widgets(self):
        # Crear frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior para selección de proyecto
        project_frame = ttk.Frame(main_frame)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Etiqueta y campo para la ruta del proyecto
        ttk.Label(project_frame, text="Proyecto Laravel:").pack(side=tk.LEFT, padx=(0, 10))
        project_entry = ttk.Entry(project_frame, textvariable=self.project_path, width=50)
        project_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Botón para buscar proyecto
        ttk.Button(
            project_frame, 
            text="Buscar", 
            command=self.browse_project, 
            style="info.TButton"
        ).pack(side=tk.LEFT)
        
        # Panel dividido horizontalmente
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Frame izquierdo para el explorador de archivos
        explorer_frame = ttk.Labelframe(paned, text="Estructura del Proyecto", padding=10)
        paned.add(explorer_frame, weight=1)
        
        # Tree view para mostrar la estructura del proyecto
        self.tree = ttk.Treeview(explorer_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_file_select)
        
        # Frame para el editor y salida
        editor_output_frame = ttk.Frame(paned)
        paned.add(editor_output_frame, weight=3)
        
        # Dividir verticalmente editor y salida
        editor_paned = ttk.PanedWindow(editor_output_frame, orient=tk.VERTICAL)
        editor_paned.pack(fill=tk.BOTH, expand=True)
        
        # Editor de código
        editor_frame = ttk.Labelframe(editor_paned, text="Editor de Código PHP", padding=10)
        editor_paned.add(editor_frame, weight=2)
        
        # Usar Text normal en lugar de ScrolledText para mayor compatibilidad
        self.code_editor = tk.Text(editor_frame, wrap=tk.WORD)
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # Agregar scrollbar manualmente
        code_scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self.code_editor.yview)
        code_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_editor.config(yscrollcommand=code_scrollbar.set)
        
        # Configurar colores del editor (simulando sintaxis PHP)
        self.code_editor.tag_configure('keyword', foreground='#0066CC')
        self.code_editor.tag_configure('string', foreground='#008800')
        self.code_editor.tag_configure('comment', foreground='#808080', font=('Courier', 10, 'italic'))
        
        # Botones de acción para el editor
        editor_buttons = ttk.Frame(editor_frame)
        editor_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            editor_buttons, 
            text="Ejecutar", 
            command=self.execute_code, 
            style="success.TButton"
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            editor_buttons, 
            text="Limpiar", 
            command=lambda: self.code_editor.delete(1.0, tk.END), 
            style="warning.TButton"
        ).pack(side=tk.RIGHT)

        ttk.Button(
            editor_buttons,
            text="Pegar desde portapapeles",
            command=self.paste_from_clipboard,
            style="info.TButton"
        ).pack(side=tk.LEFT, padx=(0, 10))


        
        # Botones para consultas de modelo
        ttk.Separator(editor_buttons, orient=tk.VERTICAL).pack(side=tk.RIGHT, padx=10, fill=tk.Y)
        
        ttk.Button(
            editor_buttons,
            text="Listar Modelos",
            command=self.list_models,
            style="info.Outline.TButton"
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            editor_buttons,
            text="Consulta Modelo",
            command=self.model_query_dialog,
            style="info.TButton"
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Panel de salida
        output_frame = ttk.Labelframe(editor_paned, text="Logs", padding=10)
        editor_paned.add(output_frame, weight=1)
        
        # Usar Text normal en lugar de ScrolledText para evitar problemas con el estado
        self.output_text = tk.Text(output_frame, wrap=tk.WORD)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Agregar scrollbar manualmente
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        # Variable para almacenar los últimos datos JSON
        self.last_json_data = None
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def paste_from_clipboard(self):
        """
        Pega el contenido del portapapeles en el editor de código y lo ejecuta automáticamente.
        """
        try:
            # Obtener contenido del portapapeles
            clipboard_content = self.root.clipboard_get()

            if clipboard_content:
                # Limpiar el editor actual y pegar el contenido
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(tk.END, clipboard_content)

                # Aplicar resaltado de sintaxis
                self._highlight_syntax()

                # Registrar en log
                self.add_to_log("Texto pegado desde el portapapeles", "info")

                # Actualizar estado
                self.status_var.set("Ejecutando código pegado...")

                # Ejecutar el código automáticamente
                self.execute_code()
            else:
                self.add_to_log("El portapapeles está vacío", "info")
        except Exception as e:
            self.add_to_log(f"Error al pegar desde el portapapeles: {str(e)}", "error")
        
    def browse_project(self):
        project_directory = filedialog.askdirectory(title="Selecciona un proyecto Laravel")
        if project_directory:
            self.project_path.set(project_directory)
            self.status_var.set(f"Proyecto cargado: {project_directory}")
            self.load_project_tree(project_directory)
            
            # Registrar en log
            self.add_to_log(f"Proyecto cargado: {project_directory}", "info")
    
    def load_project_tree(self, directory):
        # Limpiar el árbol actual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Verificar si es un proyecto Laravel válido
        if not os.path.exists(os.path.join(directory, 'artisan')):
            self.add_to_log("Error: No parece ser un proyecto Laravel válido.", "error")
            return
            
        # Cargar la estructura del proyecto
        self._populate_tree("", directory)
        
        # Registrar en log
        self.add_to_log(f"Estructura del proyecto cargada: {directory}", "info")
    
    def _populate_tree(self, parent, directory):
        # Insertar el directorio actual
        if parent == "":
            node = self.tree.insert(parent, 'end', text=os.path.basename(directory), open=True)
        else:
            node = self.tree.insert(parent, 'end', text=os.path.basename(directory), open=False)
            
        # Añadir subdirectorios y archivos
        try:
            items = os.listdir(directory)
            
            # Ignorar algunos directorios comunes en Laravel
            ignored_dirs = ['.git', 'vendor', 'node_modules', 'storage/logs']
            
            for item in sorted(items):
                item_path = os.path.join(directory, item)
                
                # Comprobar si está en la lista de ignorados
                should_ignore = any(ignored in item_path for ignored in ignored_dirs)
                
                if not should_ignore:
                    if os.path.isdir(item_path):
                        self._populate_tree(node, item_path)
                    else:
                        self.tree.insert(node, 'end', text=item, values=(item_path,))
        except Exception as e:
            self.add_to_log(f"Error al cargar directorios: {str(e)}", "error")
    
    def on_file_select(self, event):
        item = self.tree.focus()
        if item:
            # Comprobar si es un archivo
            values = self.tree.item(item, 'values')
            if values and len(values) > 0:
                file_path = values[0]
                if os.path.isfile(file_path):
                    self.load_file_content(file_path)
    
    def load_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Limpiar editor y mostrar contenido
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(tk.END, content)
                
                # Aplicar destacado sintáctico simple
                self._highlight_syntax()
                
                self.status_var.set(f"Archivo cargado: {file_path}")
                
                # Registrar en log
                self.add_to_log(f"Archivo cargado: {file_path}", "info")
        except Exception as e:
            self.add_to_log(f"Error al cargar el archivo: {str(e)}", "error")
    
    def _highlight_syntax(self):
        # Implementación básica de resaltado de sintaxis PHP
        content = self.code_editor.get(1.0, tk.END)
        
        # Palabras clave de PHP
        keywords = ['function', 'class', 'return', 'if', 'else', 'foreach', 'while', 
                    'public', 'private', 'protected', 'use', 'namespace']
        
        # Esta es una implementación simple; para un resaltado completo, 
        # considera usar una biblioteca de resaltado de código
        
        for keyword in keywords:
            start_pos = '1.0'
            while True:
                start_pos = self.code_editor.search(r'\b' + keyword + r'\b', start_pos, tk.END, regexp=True)
                if not start_pos:
                    break
                    
                end_pos = f"{start_pos}+{len(keyword)}c"
                self.code_editor.tag_add('keyword', start_pos, end_pos)
                start_pos = end_pos
    
    def execute_code(self):
        if not self.project_path.get():
            self.add_to_log("Error: Por favor selecciona un proyecto Laravel primero.", "error")
            return
            
        code = self.code_editor.get(1.0, tk.END).strip()
        if not code:
            self.add_to_log("Error: No hay código para ejecutar.", "error")
            return
        
        original_code = code
        
        # Transformar el código si la opción está habilitada
        if self.auto_transform.get():
            transformed_code = self.transform_code(code)
            code = transformed_code
        
        # Si el código fue transformado, actualizar el editor
        if code != original_code:
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(tk.END, code)
            
        # Iniciar ejecución en un hilo separado
        self.status_var.set("Ejecutando código...")
        self.add_to_log("Ejecutando código...", "info")
        self.add_to_log(f"---- CÓDIGO ----\n{code}\n--------------", "code")
        
        threading.Thread(target=self._run_tinker, args=(code,), daemon=True).start()

    def _run_tinker(self, code):
        try:
            # Extraer posibles nombres de modelos del código
            import re
            model_names = set(re.findall(r'([A-Z][A-Za-z0-9_]*)::', code))

            # Lista de clases que no son modelos y no necesitan importación de App\Models
            non_model_classes = {'DB', 'Schema', 'Route', 'Auth', 'Storage', 'Config', 'Log', 'Cache', 'View',
                                 'Response', 'Request'}

            # Filtrar nombres de modelos, excluyendo los que no son modelos
            model_names = {model for model in model_names if model not in non_model_classes}

            # Crear un archivo temporal con el código
            temp_file = os.path.join(self.project_path.get(), 'temp_tinker.php')
            with open(temp_file, 'w', encoding='utf-8') as f:
                # Envolver el código en PHP
                f.write("<?php\n")
                f.write("// Configurar manejo de errores para mostrar todos los mensajes\n")
                f.write("ini_set('display_errors', 1);\n")
                f.write("ini_set('display_startup_errors', 1);\n")
                f.write("error_reporting(E_ALL);\n\n")

                # Importar clases comunes de Laravel
                f.write("use Illuminate\\Support\\Facades\\DB;\n")
                f.write("use Illuminate\\Support\\Facades\\Schema;\n")
                f.write("use Illuminate\\Support\\Facades\\Auth;\n")
                f.write("use Illuminate\\Support\\Facades\\Route;\n")
                f.write("use Illuminate\\Support\\Facades\\Storage;\n")
                f.write("use Illuminate\\Support\\Facades\\Cache;\n")
                f.write("use Illuminate\\Support\\Facades\\Config;\n")
                f.write("use Illuminate\\Support\\Facades\\Log;\n")

                # Añadir imports automáticos para modelos detectados
                for model in model_names:
                    f.write(f"use App\\Models\\{model};\n")
                f.write("\n")

                # Cargar Laravel
                f.write("try {\n")
                f.write("    require __DIR__.'/vendor/autoload.php';\n")
                f.write("    $app = require_once __DIR__.'/bootstrap/app.php';\n")
                f.write("    $kernel = $app->make(Illuminate\\Contracts\\Console\\Kernel::class);\n")
                f.write("    $kernel->bootstrap();\n")
                f.write("} catch (\\Exception $e) {\n")
                f.write("    echo \"Error al inicializar Laravel: \" . $e->getMessage() . \"\\n\";\n")
                f.write("    echo \"En archivo: \" . $e->getFile() . \" línea: \" . $e->getLine() . \"\\n\";\n")
                f.write("    exit(1);\n")
                f.write("}\n\n")

                # Funciones de ayuda para consultas de modelos
                f.write("function formatOutput($data) {\n")
                f.write("    if (is_object($data) && method_exists($data, 'toArray')) {\n")
                f.write("        return json_encode($data->toArray(), JSON_PRETTY_PRINT);\n")
                f.write("    } elseif (is_object($data) && method_exists($data, 'toJson')) {\n")
                f.write("        return $data->toJson(JSON_PRETTY_PRINT);\n")
                f.write("    } elseif (is_array($data)) {\n")
                f.write("        return json_encode($data, JSON_PRETTY_PRINT);\n")
                f.write("    } else {\n")
                f.write("        return var_export($data, true);\n")
                f.write("    }\n")
                f.write("}\n\n")

                # Código del usuario dentro de un bloque try-catch
                f.write("// Código del usuario:\n")
                f.write("try {\n")
                f.write(code)
                f.write("\n} catch (\\Exception $e) {\n")
                f.write("    echo \"Error: \" . $e->getMessage() . \"\\n\";\n")
                f.write("    echo \"En archivo: \" . $e->getFile() . \" línea: \" . $e->getLine() . \"\\n\";\n")
                f.write("}\n")

            # Ejecutar el código con PHP
            process = subprocess.Popen(
                ['php', temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_path.get(),
                text=True
            )

            stdout, stderr = process.communicate()

            # Eliminar el archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)

            # Variable para almacenar datos JSON si se detectan
            json_data = None

            # Enviar resultados a la cola
            if stdout:
                try:
                    # Verificar específicamente si es la salida del listado de modelos
                    if "Buscando modelos Eloquent en el proyecto" in stdout:
                        # Para la salida del listado de modelos, mantener el formato original
                        self.output_queue.put(("Salida:\n" + stdout, "normal"))
                    # Intentar formatear si es JSON
                    elif stdout.strip().startswith('{') or stdout.strip().startswith('['):
                        try:
                            json_data = json.loads(stdout)
                            formatted_json = json.dumps(json_data, indent=4)
                            self.output_queue.put(("Salida:\n" + formatted_json, "json"))

                            # Almacenar los datos JSON para uso posterior
                            self.last_json_data = json_data

                            # Añadir señal para mostrar el botón de vista de tabla
                            self.output_queue.put(("show_table_button", json_data))
                        except json.JSONDecodeError:
                            # Si falla el parseo JSON, mostrar como texto normal
                            self.output_queue.put(("Salida:\n" + stdout, "normal"))
                    else:
                        self.output_queue.put(("Salida:\n" + stdout, "normal"))
                except Exception as e:
                    # Si hay cualquier error en el procesamiento, mostrar la salida original
                    self.output_queue.put(("Salida (Error de formato):\n" + stdout + f"\n\nError: {str(e)}", "normal"))

            if stderr:
                self.output_queue.put(("Error:\n" + stderr, "error"))

            if not stdout and not stderr:
                self.output_queue.put(("El código se ejecutó correctamente sin salida.", "success"))

            # Actualizar estado
            self.output_queue.put(("status", "Ejecución completada."))

        except Exception as e:
            self.output_queue.put((f"Error al ejecutar: {str(e)}", "error"))
            self.output_queue.put(("status", "Error en la ejecución."))
            
    def check_output_queue(self):
        try:
            while True:
                message, msg_type = self.output_queue.get_nowait()
                
                if msg_type == "status":
                    self.status_var.set(message)
                    # Añadir el cambio de estado al log también
                    self.add_to_log(f"Estado: {message}", "status")
                elif msg_type == "show_table_button":
                    # Aquí es donde mostramos el botón para ver la tabla
                    self._show_table_button(message)
                else:
                    self.add_to_log(message, msg_type)
        except queue.Empty:
            pass
        finally:
            # Programar la siguiente verificación
            self.root.after(100, self.check_output_queue)
            
    def _show_table_button(self, json_data):
        """
        Muestra el botón para ver la tabla con los datos JSON
        
        Args:
            json_data: Datos en formato JSON a mostrar en la tabla
        """
        # Habilitar edición del widget de salida
        self.output_text.config(state=tk.NORMAL)
        
        # Insertar un botón para ver los datos en formato tabla
        button_text = "Ver datos en tabla"
        self.output_text.insert(tk.END, "\n")
        
        # Crear un tag para el botón
        button_tag = f"table_button_{id(json_data)}"
        self.output_text.tag_configure(button_tag, justify=tk.CENTER)
        self.output_text.tag_bind(button_tag, "<Button-1>", lambda e: self.create_table_view(json_data))
        
        # Insertar texto del botón con el tag
        start_index = self.output_text.index(tk.END)
        self.output_text.insert(tk.END, f"[{button_text}]", button_tag)
        end_index = self.output_text.index(tk.END)
        
        # Configurar la apariencia del botón
        self.output_text.tag_add(button_tag, start_index, end_index)
        self.output_text.tag_configure(button_tag, foreground="blue", underline=True)
        
        # Cambiar el cursor al pasar sobre el botón
        self.output_text.tag_bind(button_tag, "<Enter>", 
                                lambda e: self.output_text.config(cursor="hand2"))
        self.output_text.tag_bind(button_tag, "<Leave>", 
                                lambda e: self.output_text.config(cursor=""))
        
        self.output_text.insert(tk.END, "\n\n")
        
        # Desactivar edición
        self.output_text.config(state=tk.DISABLED)
        
        # Desplazarse al final
        self.output_text.see(tk.END)
    
    def show_last_json_data(self):
        """
        Muestra la última respuesta JSON en una tabla
        """
        if self.last_json_data is None:
            Messagebox.show_info("No hay datos JSON disponibles para mostrar en tabla.", "Información")
            return
            
        self.create_table_view(self.last_json_data)
    
    def create_table_view(self, data):
        """
        Crea una ventana con una tabla para mostrar los datos JSON
        
        Args:
            data (list/dict): Datos en formato JSON a mostrar
        """
        try:
            # Convertir el string JSON a un objeto Python si es necesario
            if isinstance(data, str):
                import json
                data = json.loads(data)
            
            # Si es un diccionario único, convertirlo a lista
            if isinstance(data, dict):
                data = [data]
                
            # Verificar que sea una lista de diccionarios
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                self.add_to_log("Error: Los datos no tienen un formato válido para tabla.", "error")
                return
                
            # Crear ventana para la tabla
            table_window = ttk.Toplevel(self.root)
            table_window.title("Resultados en Tabla")
            table_window.geometry("1000x600")
            
            # Frame principal con padding
            main_frame = ttk.Frame(table_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Frame para info y controles
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Mostrar número de registros
            records_label = ttk.Label(info_frame, text=f"Registros: {len(data)}")
            records_label.pack(side=tk.LEFT)
            
            # Botón para exportar
            export_btn = ttk.Button(
                info_frame, 
                text="Exportar CSV", 
                command=lambda: self.export_table_data(data),
                style="info.TButton"
            )
            export_btn.pack(side=tk.RIGHT)
            
            # Frame para la tabla con scrollbars
            table_frame = ttk.Frame(main_frame)
            table_frame.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbars
            v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Obtener todas las columnas únicas de todos los registros
            all_columns = set()
            for item in data:
                all_columns.update(item.keys())
                
            # Convertir a lista y ordenar alfabéticamente
            columns = sorted(list(all_columns))
            
            # Crear Treeview (tabla)
            tree = ttk.Treeview(
                table_frame, 
                columns=columns,
                show="headings",
                yscrollcommand=v_scrollbar.set,
                xscrollcommand=h_scrollbar.set
            )
            
            # Configurar scrollbars
            v_scrollbar.config(command=tree.yview)
            h_scrollbar.config(command=tree.xview)
            
            # Configurar encabezados de columnas
            for col in columns:
                # Truncar nombres de columnas muy largos
                display_name = col if len(col) < 25 else col[:22] + "..."
                tree.heading(col, text=display_name)
                
                # Calcular ancho basado en el nombre de la columna
                width = max(100, len(col) * 10)
                tree.column(col, width=width, minwidth=50)
            
            # Insertar datos
            for idx, item in enumerate(data):
                values = []
                for col in columns:
                    # Obtener el valor o un espacio en blanco si no existe
                    value = item.get(col, "")
                    
                    # Convertir a string para mostrar en la tabla
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    elif value is None:
                        value = "NULL"
                    else:
                        value = str(value)
                        
                    values.append(value)
                    
                # Insertar fila
                tree.insert("", "end", values=values, tags=("odd" if idx % 2 else "even",))
            
            # Configurar colores alternos para las filas
            tree.tag_configure("odd", background="#f5f5f5")
            tree.tag_configure("even", background="#ffffff")
            
            # Empaquetar la tabla
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Registrar en logs
            self.add_to_log(f"Vista de tabla creada con {len(data)} registros y {len(columns)} columnas", "info")
            
            # Centrar la ventana
            # Centrar la ventana
            table_window.transient(self.root)
            table_window.update_idletasks()
            width = table_window.winfo_width()
            height = table_window.winfo_height()
            x = (table_window.winfo_screenwidth() // 2) - (width // 2)
            y = (table_window.winfo_screenheight() // 2) - (height // 2)
            table_window.geometry(f'{width}x{height}+{x}+{y}')
            
        except Exception as e:
            self.add_to_log(f"Error al crear vista de tabla: {str(e)}", "error")

    def export_table_data(self, data):
        """
        Exporta los datos de la tabla a un archivo CSV
        
        Args:
            data (list): Lista de diccionarios con los datos
        """
        try:
            import csv
            
            # Solicitar ubicación para guardar
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Todos los archivos", "*.*")],
                title="Exportar a CSV"
            )
            
            if not file_path:
                return
                
            # Obtener todas las columnas
            all_columns = set()
            for item in data:
                all_columns.update(item.keys())
                
            columns = sorted(list(all_columns))
            
            # Escribir CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(data)
                
            self.add_to_log(f"Datos exportados correctamente a {file_path}", "success")
            
        except Exception as e:
            self.add_to_log(f"Error al exportar datos: {str(e)}", "error")
    
    def add_to_log(self, message, msg_type="normal"):
        # Añadir marca de tiempo
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "type": msg_type
        }
        
        # Añadir al historial de logs
        self.log_history.append(log_entry)
        
        # Habilitar edición del widget de salida
        self.output_text.config(state=tk.NORMAL)
        
        # Configurar etiquetas si aún no se han configurado
        if not hasattr(self, '_tags_configured'):
            self.output_text.tag_configure("error", foreground="red")
            self.output_text.tag_configure("success", foreground="green")
            self.output_text.tag_configure("json", foreground="#00AAAA")
            self.output_text.tag_configure("keyword", foreground="blue")
            self.output_text.tag_configure("info", foreground="black")
            self.output_text.tag_configure("status", foreground="#555555")
            self.output_text.tag_configure("code", foreground="#888888")
            self.output_text.tag_configure("timestamp", foreground="#888888", font=("TkDefaultFont", 8))
            self._tags_configured = True
            
        # Añadir timestamp al inicio de la línea
        self.output_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Agregar mensaje con formato según el tipo
        if msg_type == "error":
            self.output_text.insert(tk.END, message + "\n\n", "error")
        elif msg_type == "success":
            self.output_text.insert(tk.END, message + "\n\n", "success")
        elif msg_type == "json":
            self.output_text.insert(tk.END, message + "\n\n", "json")
            
            # Destacar algunas palabras clave en la salida JSON
            start_idx = self.output_text.index(tk.END + "-2l linestart")
            while True:
                for keyword in ['"id":', '"name":', '"created_at":', '"updated_at":', '"deleted_at":']:
                    start_pos = self.output_text.search(keyword, start_idx, tk.END)
                    if not start_pos:
                        continue
                    end_pos = f"{start_pos}+{len(keyword)}c"
                    self.output_text.tag_add('keyword', start_pos, end_pos)
                break  # Solo una pasada
        elif msg_type == "info":
            self.output_text.insert(tk.END, message + "\n\n", "info")
        elif msg_type == "status":
            self.output_text.insert(tk.END, message + "\n\n", "status")
        elif msg_type == "code":
            self.output_text.insert(tk.END, message + "\n\n", "code")
        else:
            self.output_text.insert(tk.END, message + "\n\n", "info")
        
        # Desactivar edición
        self.output_text.config(state=tk.DISABLED)
        
        # Desplazarse al final
        self.output_text.see(tk.END)
    
    def clear_logs(self):
        # Limpiar el historial de logs
        self.log_history = []
        
        # Limpiar el widget de salida
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # Actualizar estado
        self.status_var.set("Logs limpiados.")
    
    def export_logs(self):
        if not self.log_history:
            Messagebox.show_info("No hay logs para exportar.", "Exportar Logs")
            return
            
        # Solicitar ubicación para guardar
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Archivos de Log", "*.log"), ("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar Log"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in self.log_history:
                    f.write(f"[{entry['timestamp']}] [{entry['type'].upper()}] {entry['message']}\n")
                    
            self.status_var.set(f"Logs exportados a {file_path}")
            self.add_to_log(f"Logs exportados a {file_path}", "success")
            
        except Exception as e:
            self.add_to_log(f"Error al exportar logs: {str(e)}", "error")
    def list_models(self):
        if not self.project_path.get():
            Messagebox.show_error("Por favor selecciona un proyecto Laravel primero.", "Error")
            return
        
        # Código PHP mejorado para listar todos los modelos de la aplicación
        code = """
        // Mostrar información de depuración
        echo "Buscando modelos Eloquent en el proyecto...\\n\\n";
        
        // Obtener rutas de los directorios
        $modelsPath = app_path('Models');
        $appPath = app_path();
        
        echo "Directorio de modelos: {$modelsPath}\\n";
        echo "Directorio de la aplicación: {$appPath}\\n\\n";

        // Comprobar si los directorios existen
        $modelsExist = file_exists($modelsPath) && is_dir($modelsPath);
        $appExists = file_exists($appPath) && is_dir($appPath);
        
        echo "¿Existe el directorio Models?: " . ($modelsExist ? 'Sí' : 'No') . "\\n";
        echo "¿Existe el directorio App?: " . ($appExists ? 'Sí' : 'No') . "\\n\\n";
        
        $models = [];
        
        // Función para buscar recursivamente en subdirectorios
        function findModelsRecursively($directory, $namespace) {
            global $models;
            
            if (!file_exists($directory) || !is_dir($directory)) {
                return;
            }
            
            $files = scandir($directory);
            foreach ($files as $file) {
                if ($file === '.' || $file === '..') {
                    continue;
                }
                
                $path = $directory . '/' . $file;
                
                if (is_dir($path)) {
                    // Si es un directorio, buscamos recursivamente
                    $subNamespace = $namespace . '\\\\' . $file;
                    findModelsRecursively($path, $subNamespace);
                } elseif (is_file($path) && pathinfo($path, PATHINFO_EXTENSION) === 'php') {
                    // Si es un archivo PHP, verificamos si es un modelo
                    $content = file_get_contents($path);
                    $className = pathinfo($file, PATHINFO_FILENAME);
                    
                    // Verificar si es un modelo Eloquent
                    if (strpos($content, 'extends Model') !== false || 
                        strpos($content, 'extends \\\\Illuminate\\\\Database\\\\Eloquent\\\\Model') !== false ||
                        strpos($content, 'extends Authenticatable') !== false) {
                        $fullClassName = $namespace . '\\\\' . $className;
                        $models[] = $fullClassName;
                        echo "Modelo encontrado: {$fullClassName}\\n";
                    }
                }
            }
        }
        
        // Buscar en app/Models recursivamente
        if ($modelsExist) {
            echo "Buscando modelos en {$modelsPath} y subdirectorios...\\n";
            findModelsRecursively($modelsPath, 'App\\\\Models');
        }
        
        // Buscar directamente en app/ para Laravel < 8
        if ($appExists) {
            echo "\\nBuscando modelos en {$appPath}...\\n";
            $appFiles = glob($appPath . '/*.php');
            echo "Archivos PHP encontrados: " . count($appFiles) . "\\n";
            
            foreach ($appFiles as $file) {
                $content = file_get_contents($file);
                $baseName = basename($file, '.php');
                
                // Verificar si es un modelo Eloquent
                if (strpos($content, 'extends Model') !== false || 
                    strpos($content, 'extends \\\\Illuminate\\\\Database\\\\Eloquent\\\\Model') !== false ||
                    strpos($content, 'extends Authenticatable') !== false) {
                    $models[] = "App\\\\{$baseName}";
                    echo "Modelo encontrado: App\\\\{$baseName}\\n";
                }
            }
        }
        
        echo "\\n----------------------------------------\\n";
        
        // Mostrar los modelos encontrados
        if (count($models) > 0) {
            echo "\\nTotal de modelos Eloquent encontrados: " . count($models) . "\\n\\n";
            echo "Modelos disponibles:\\n";
            echo json_encode($models, JSON_PRETTY_PRINT);
        } else {
            echo "\\nNo se encontraron modelos Eloquent en el proyecto.\\n";
            echo "Sugerencias:\\n";
            echo "- Verifica que estás seleccionando un proyecto Laravel válido\\n";
            echo "- Asegúrate de que los modelos extiendan de Illuminate\\Database\\Eloquent\\Model\\n";
            echo "- Comprueba que los modelos estén en App\\Models\\ o App\\\\n";
            
            // Intenta buscar cualquier clase en app/ que podría ser un modelo
            echo "\\nBuscando posibles modelos por convención de nombres...\\n";
            if ($modelsExist) {
                $possibleModels = glob($modelsPath . '/*.php');
                foreach ($possibleModels as $file) {
                    echo "Posible modelo encontrado (por nombre): App\\\\Models\\\\" . basename($file, '.php') . "\\n";
                }
            }
            
            if ($appExists) {
                $possibleAppModels = glob($appPath . '/*.php');
                foreach ($possibleAppModels as $file) {
                    $name = basename($file, '.php');
                    if ($name != 'User' && $name != 'Model') {  // Ya verificamos estos
                        echo "Posible modelo encontrado (por nombre): App\\\\" . $name . "\\n";
                    }
                }
            }
        }
        """
        
        # Registrar la acción en los logs
        self.add_to_log("Listando modelos del proyecto...", "info")
        
        # Ejecutar el código para listar modelos
        self.code_editor.delete(1.0, tk.END)
        self.code_editor.insert(tk.END, code)
        self.execute_code()
        
    def model_query_dialog(self):
        if not self.project_path.get():
            Messagebox.show_error("Por favor selecciona un proyecto Laravel primero.", "Error")
            self.add_to_log("Error: Intento de consulta de modelo sin proyecto seleccionado", "error")
            return
        
        # Primero buscar los modelos disponibles para mostrarlos en la lista
        try:
            # Intentar encontrar modelos para sugerir al usuario
            models_to_suggest = []
            
            # Buscar en Models (Laravel >= 8)
            models_dir = os.path.join(self.project_path.get(), 'app', 'Models')
            if os.path.exists(models_dir) and os.path.isdir(models_dir):
                for file in os.listdir(models_dir):
                    if file.endswith('.php'):
                        model_name = os.path.splitext(file)[0]
                        models_to_suggest.append(f"App\\Models\\{model_name}")
            
            # Buscar también en App (Laravel < 8)
            app_dir = os.path.join(self.project_path.get(), 'app')
            if os.path.exists(app_dir) and os.path.isdir(app_dir):
                for file in os.listdir(app_dir):
                    if file.endswith('.php') and file not in ['User.php', 'Model.php']:
                        # Verificar si es un archivo PHP que podría ser un modelo
                        model_name = os.path.splitext(file)[0]
                        models_to_suggest.append(f"App\\{model_name}")
            
            # Si encontramos modelos, podemos mostrarlos en un combobox
            if models_to_suggest:
                query_dialog = ttk.Toplevel(self.root)
                query_dialog.title("Consulta de Modelo")
                query_dialog.geometry("500x400")
                
                # Frame principal
                main_frame = ttk.Frame(query_dialog, padding=15)
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # Etiqueta para selección de modelo
                ttk.Label(main_frame, text="Selecciona un modelo:").pack(anchor=tk.W, pady=(0, 5))
                
                # Combobox para seleccionar modelo
                model_var = tk.StringVar()
                model_combo = ttk.Combobox(main_frame, textvariable=model_var, values=models_to_suggest, width=40)
                model_combo.pack(fill=tk.X, pady=(0, 15))
                if models_to_suggest:
                    model_combo.current(0)
                
                # Etiqueta para tipo de consulta
                ttk.Label(main_frame, text="Selecciona el tipo de consulta:").pack(anchor=tk.W, pady=(0, 5))
                
                # Frame para los radiobuttons
                query_frame = ttk.Frame(main_frame)
                query_frame.pack(fill=tk.X, pady=(0, 15))
                
                # Tipo de consulta
                query_types = [
                    "Obtener todo (all())",
                    "Primero (first())",
                    "Encontrar por ID (find())",
                    "Contar (count())",
                    "Consulta personalizada"
                ]
                
                query_var = tk.StringVar(value=query_types[0])
                
                for query_type in query_types:
                    ttk.Radiobutton(
                        query_frame, 
                        text=query_type, 
                        variable=query_var, 
                        value=query_type
                    ).pack(anchor=tk.W, padx=10, pady=2)
                
                # Campo para parámetros adicionales
                ttk.Label(main_frame, text="Parámetros adicionales:").pack(anchor=tk.W, pady=(0, 5))
                params_entry = ttk.Entry(main_frame, width=40)
                params_entry.pack(fill=tk.X, pady=(0, 15))
                # Función para generar y ejecutar la consulta
                def generate_query():
                    model_name = model_var.get()
                    query_type = query_var.get()
                    params = params_entry.get().strip()
                    
                    if not model_name:
                        Messagebox.show_warning("Por favor selecciona un modelo.", "Advertencia")
                        return
                    
                    # Generar el código para la consulta
                    if query_type == "Obtener todo (all())":
                        code = f"echo formatOutput({model_name}::all());"
                    elif query_type == "Primero (first())":
                        code = f"echo formatOutput({model_name}::first());"
                    elif query_type == "Encontrar por ID (find())":
                        if not params:
                            Messagebox.show_warning("Por favor ingresa un ID en los parámetros.", "Advertencia")
                            return
                        code = f"echo formatOutput({model_name}::find({params}));"
                    elif query_type == "Contar (count())":
                        code = f"echo 'Total: ' . {model_name}::count();"
                    else:  # Consulta personalizada
                        if not params:
                            Messagebox.show_warning("Por favor ingresa una consulta personalizada.", "Advertencia")
                            return
                        code = f"echo formatOutput({model_name}::{params});"
                    
                    # Cerrar diálogo
                    query_dialog.destroy()
                    
                    # Mostrar y ejecutar el código
                    full_code = f"""
                    // Consulta al modelo {model_name}
                    {code}
                    """
                    
                    # Registrar la consulta en los logs
                    self.add_to_log(f"Ejecutando consulta para modelo {model_name} ({query_type})", "info")
                    
                    self.code_editor.delete(1.0, tk.END)
                    self.code_editor.insert(tk.END, full_code)
                    self.execute_code()
                
                # Botones de acción
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Button(
                    button_frame, 
                    text="Cancelar", 
                    command=query_dialog.destroy,
                    style="secondary.TButton"
                ).pack(side=tk.LEFT)
                
                ttk.Button(
                    button_frame, 
                    text="Ejecutar Consulta", 
                    command=generate_query,
                    style="primary.TButton"
                ).pack(side=tk.RIGHT)
                
                # Centrar diálogo
                query_dialog.transient(self.root)
                query_dialog.grab_set()
                self.root.wait_window(query_dialog)
                
            else:
                # Si no encontramos modelos, pedir al usuario que ingrese uno
                model_name = simpledialog.askstring(
                    "Consulta de Modelo", 
                    "No se encontraron modelos automáticamente.\n\n"
                    "Ingresa el nombre completo del modelo (ej: App\\Models\\User):",
                    parent=self.root
                )
                
                if not model_name:
                    return
                
                # Continuar con el diálogo tradicional
                self._show_query_dialog(model_name)
                
        except Exception as e:
            # Si hay error, usar el método tradicional
            model_name = simpledialog.askstring(
                "Consulta de Modelo", 
                "Ingresa el nombre del modelo (ej: App\\Models\\User):",
                parent=self.root
            )
            
            if not model_name:
                return
            
            self._show_query_dialog(model_name)
            
    def _show_query_dialog(self, model_name):
        # Diálogo para seleccionar el tipo de consulta
        query_types = [
            "Obtener todo (all())",
            "Primero (first())",
            "Encontrar por ID (find())",
            "Contar (count())",
            "Consulta personalizada"
        ]
        
        query_dialog = ttk.Toplevel(self.root)
        query_dialog.title("Tipo de Consulta")
        query_dialog.geometry("400x300")
        
        ttk.Label(query_dialog, text="Selecciona el tipo de consulta:").pack(pady=10)
        
        query_var = tk.StringVar()
        
        for query_type in query_types:
            ttk.Radiobutton(
                query_dialog, 
                text=query_type, 
                variable=query_var, 
                value=query_type
            ).pack(anchor=tk.W, padx=20, pady=5)
        
        # Campo para parámetros adicionales
        ttk.Label(query_dialog, text="Parámetros adicionales (opcional):").pack(pady=(10, 5))
        params_entry = ttk.Entry(query_dialog, width=40)
        params_entry.pack(padx=20, fill=tk.X)
        
        # Función para generar y ejecutar la consulta
        def generate_query():
            query_type = query_var.get()
            params = params_entry.get().strip()
            
            if not query_type:
                Messagebox.show_warning("Por favor selecciona un tipo de consulta.", "Advertencia")
                return
            
            # Generar el código para la consulta
            if query_type == "Obtener todo (all())":
                code = f"echo formatOutput({model_name}::all());"
            elif query_type == "Primero (first())":
                code = f"echo formatOutput({model_name}::first());"
            elif query_type == "Encontrar por ID (find())":
                if not params:
                    Messagebox.show_warning("Por favor ingresa un ID en los parámetros.", "Advertencia")
                    return
                code = f"echo formatOutput({model_name}::find({params}));"
            elif query_type == "Contar (count())":
                code = f"echo 'Total: ' . {model_name}::count();"
            else:  # Consulta personalizada
                if not params:
                    Messagebox.show_warning("Por favor ingresa una consulta personalizada.", "Advertencia")
                    return
                code = f"echo formatOutput({model_name}::{params});"
            
            # Cerrar diálogo
            query_dialog.destroy()
            
            # Mostrar y ejecutar el código
            full_code = f"""
            // Consulta al modelo {model_name}
            {code}
            """
            
            # Registrar la consulta en los logs
            self.add_to_log(f"Ejecutando consulta para modelo {model_name} ({query_type})", "info")
            
            self.code_editor.delete(1.0, tk.END)
            self.code_editor.insert(tk.END, full_code)
            self.execute_code()
        
        # Botones
        buttons_frame = ttk.Frame(query_dialog)
        buttons_frame.pack(pady=20, fill=tk.X)
        
        ttk.Button(
            buttons_frame, 
            text="Cancelar", 
            command=query_dialog.destroy,
            style="secondary.TButton"
        ).pack(side=tk.LEFT, padx=20)
        
        ttk.Button(
            buttons_frame, 
            text="Ejecutar Consulta", 
            command=generate_query,
            style="primary.TButton"
        ).pack(side=tk.RIGHT, padx=20)
        
        # Centrar diálogo
        query_dialog.transient(self.root)
        query_dialog.grab_set()
        self.root.wait_window(query_dialog)
    def run_artisan_command(self, command):
        if not self.project_path.get():
            Messagebox.show_error("Por favor selecciona un proyecto Laravel primero.", "Error")
            self.add_to_log("Error: Intento de ejecutar comando artisan sin proyecto seleccionado", "error")
            return
        
        self.status_var.set(f"Ejecutando: php artisan {command}...")
        
        # Registrar el comando en los logs
        self.add_to_log(f"Ejecutando comando artisan: {command}", "info")
        
        # Ejecutar el comando artisan en un hilo separado
        threading.Thread(
            target=self._execute_artisan, 
            args=(command,), 
            daemon=True
        ).start()
    
    def _execute_artisan(self, command):
        try:
            process = subprocess.Popen(
                ['php', 'artisan', command, '--no-ansi'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_path.get(),
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if stdout:
                self.output_queue.put((f"Resultado de 'php artisan {command}':\n\n{stdout}", "normal"))
            
            if stderr:
                self.output_queue.put((f"Error al ejecutar 'php artisan {command}':\n\n{stderr}", "error"))
                
            if not stdout and not stderr:
                self.output_queue.put((f"Comando 'php artisan {command}' ejecutado sin salida.", "success"))
            
            self.output_queue.put(("status", "Comando artisan completado."))
            self.output_queue.put((f"Comando 'php artisan {command}' finalizado", "status"))
            
        except Exception as e:
            self.output_queue.put((f"Error al ejecutar artisan: {str(e)}", "error"))
            self.output_queue.put(("status", "Error en el comando artisan."))
    
    def show_about(self):
        Messagebox.show_info(
            "Laravel Tinker Tool\n\n"
            "Una aplicación Python que emula la funcionalidad de Tinkerwell para proyectos Laravel.\n\n"
            "Permite ejecutar código PHP interactivamente dentro del contexto de un proyecto Laravel "
            "y realizar consultas a modelos Eloquent.\n\n"
            "Incluye sistema de logs para registrar todas las acciones realizadas y visualización de datos en tablas.",
            "Acerca de Laravel Tinker Tool"
        )
        
        # Registrar en logs
        self.add_to_log("Se mostró información sobre la aplicación", "info")

    def transform_code(self, code):
        """
        Transforma el código ingresado por el usuario para adaptarlo automáticamente
        al formato requerido por Tinker.

        Transformaciones:
        - ModelName::método() → echo formatOutput(App\\Models\\ModelName::método());
        - App\\ModelName::método() → echo formatOutput(App\\ModelName::método());

        Args:
            code (str): Código ingresado por el usuario

        Returns:
            str: Código transformado
        """
        try:
            # Eliminar espacios al inicio y final
            code = code.strip()

            # Eliminar punto y coma al final si existe
            if code.endswith(';'):
                code = code[:-1]

            # Si ya contiene "echo formatOutput", no aplicar transformación
            if "echo formatOutput" in code:
                return code

            # Si ya está formateado con var_dump o dd, devolverlo sin cambios
            if code.startswith("var_dump(") or code.startswith("dd("):
                return code

            # Si es un código generado por consulta de modelo, no transformar
            if "// Consulta al modelo" in code:
                return code

            # Si es un comando de Laravel (como DB::), no lo transformamos
            if code.startswith("DB::") or code.startswith("\\DB::") or code.startswith("Schema::"):
                # Simplemente añadir echo si no está ya
                if not code.startswith("echo"):
                    return f"echo formatOutput({code});"
                return code

            # Verificar si es una consulta de modelo simple (Modelo::método())
            # Patrón: palabra::método(args) - sin espacios antes de ::
            model_method_pattern = r'^([A-Za-z0-9_]+)::([A-Za-z0-9_]+\(.*\))(.*)$'
            import re
            match = re.match(model_method_pattern, code)

            if match:
                model_name = match.group(1)
                method_call = match.group(2)
                rest_of_code = match.group(3)

                # Si parece ser un nombre de modelo (primera letra mayúscula)
                if model_name[0].isupper():
                    # Transformar a formato completo con namespace
                    transformed = f"echo formatOutput(App\\Models\\{model_name}::{method_call}{rest_of_code});"

                    # Registrar la transformación
                    self.add_to_log(f"Código transformado: {code} → {transformed}", "info")

                    return transformed

            # Verificar si ya tiene namespace App pero sin formatOutput
            namespace_pattern = r'^App\\([A-Za-z0-9_\\]+)::([A-Za-z0-9_]+\(.*\))(.*)$'
            match = re.match(namespace_pattern, code)

            if match:
                namespace = match.group(1)
                method_call = match.group(2)
                rest_of_code = match.group(3)

                # Transformar a formato con formatOutput
                transformed = f"echo formatOutput(App\\{namespace}::{method_call}{rest_of_code});"

                # Registrar la transformación
                self.add_to_log(f"Código transformado: {code} → {transformed}", "info")

                return transformed

            # Si no coincide con ningún patrón pero parece código PHP válido
            if "::" in code or "->" in code:
                # Verificar si el código comienza con un nombre de clase
                # que podría ser un modelo Eloquent
                class_pattern = r'^([A-Z][A-Za-z0-9_]*)(::|\->)'
                class_match = re.match(class_pattern, code)
                if class_match and "::" in code[:10]:  # Si hay una clase y usa ::
                    model_name = class_match.group(1)
                    # Asegurarnos que tenga el namespace completo
                    if not code.startswith("App\\"):
                        transformed = f"echo formatOutput(App\\Models\\{code});"
                        self.add_to_log(f"Código transformado: {code} → {transformed}", "info")
                        return transformed

                # Si no es una clase o ya tiene namespace, simplemente envolver
                transformed = f"echo formatOutput({code});"
                self.add_to_log(f"Código transformado: {code} → {transformed}", "info")
                return transformed

            # Si no coincide con ningún patrón, devolver el código original
            return code

        except Exception as e:
            # Si hay algún error en la transformación, devolver el código original
            self.add_to_log(f"Error al transformar código: {str(e)}", "error")
            return code

def main():
    try:
        # Crear ventana principal con tema de ttkbootstrap
        root = ttk.Window(themename="cosmo")
        
        # Configurar icono si está disponible
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except:
            pass  # Si no hay icono, continuar sin él
        
        # Crear la aplicación
        app = LaravelTinkerApp(root)
        
        # Registrar inicio en los logs
        app.add_to_log("Aplicación iniciada correctamente", "info")
        
        # Iniciar la aplicación
        root.mainloop()
    except Exception as e:
        # Mostrar mensaje de error si ocurre algún problema al iniciar
        # Mostrar mensaje de error si ocurre algún problema al iniciar
        import traceback
        error_msg = f"Error al iniciar la aplicación:\n{str(e)}\n\n{traceback.format_exc()}"
        
        try:
            # Intentar mostrar un diálogo de error
            from tkinter import messagebox
            messagebox.showerror("Error", error_msg)
        except:
            # Si no se puede mostrar el diálogo, imprimir en consola
            print(error_msg)
            
        # Intentar registrar el error en un archivo de log
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("error_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [ERROR] {error_msg}\n\n")
        except:
            pass

if __name__ == "__main__":
    main()
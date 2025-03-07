#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Laravel Tinker Tool - Herramienta interactiva para proyectos Laravel
Autor: Tu Nombre
Versión: 1.0
Fecha: 2025
"""

import os
import subprocess
import sys

def check_requirements():
    """
    Verifica que todos los requerimientos estén instalados
    """
    print("Verificando requerimientos...")
    
    # Verificar PHP
    try:
        php_version = subprocess.check_output(['php', '-v'], text=True)
        print(f"PHP instalado: {php_version.splitlines()[0]}")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ERROR: PHP no está instalado o no está en el PATH.")
        print("Por favor instala PHP para utilizar esta aplicación.")
        return False
    
    # Verificar módulos Python
    try:
        import tkinter
        import ttkbootstrap
        print("Módulos Python requeridos: OK")
    except ImportError as e:
        print(f"ERROR: Módulo Python faltante: {e}")
        print("Por favor instala los módulos requeridos con:")
        print("pip install ttkbootstrap")
        return False
    
    return True

def main():
    """
    Función principal
    """
    # Verificar los requerimientos
    if not check_requirements():
        input("Presiona Enter para salir...")
        sys.exit(1)
    
    # Importar el módulo principal
    from laravel_tinker_tool import LaravelTinkerApp 
    import tkinter as tk
    import ttkbootstrap as ttk
    
    # Crear y ejecutar la aplicación
    root = ttk.Window(themename="cosmo")
    root.title("Laravel Tinker Tool")
    
    # Configurar icono si está disponible
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass
    
    # Iniciar la aplicación
    app = LaravelTinkerApp(root)
    app.add_to_log("Aplicación iniciada correctamente", "info")
    
    # Centrar la ventana en la pantalla
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')
    
    # Iniciar el loop principal
    root.mainloop()

if __name__ == "__main__":
    main()
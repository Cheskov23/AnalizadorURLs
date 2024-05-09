import tkinter as tk
from tkinter import ttk, filedialog
import os
import json
import requests
from bs4 import BeautifulSoup
import random
import re
from urllib.parse import urljoin
import validators
import threading
import textwrap

# Lista de User-Agents aleatorios
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Safari/605.1.15'
]

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.tooltip = tk.Toplevel(self.widget)
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1).pack()

    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()

def cargar_servicios_desde_json():
    """
    Carga los servicios desde un archivo JSON y devuelve un diccionario.
    """
    ruta_script = os.path.dirname(__file__)
    ruta_servicios_json = os.path.join(ruta_script, 'servicios.json')
    try:
        with open(ruta_servicios_json, 'r') as f:
            servicios = json.load(f)
            return servicios
    except FileNotFoundError as e:
        return None
    except Exception as e:
        return None

analizadas = set()
claves_encontradas = set()

def buscar_claves_api(url, servicios):
    """
    Busca claves API en una URL y devuelve un diccionario con las claves encontradas.
    """
    try:
        user_agent = random.choice(USER_AGENTS)
        headers = {'User-Agent': user_agent}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        contenido = response.text
        soup = BeautifulSoup(contenido, 'html.parser')

        scripts = soup.find_all('script', {'src': True})
        patron = re.compile(r'(apikey|api_key|apiToken|api_token|apiKey|api_key|access_token|secret|token|auth|access_key|secret_key|client_id|client_secret|api_password|api_secret|auth_token|auth_key|access_token|access_key|client_secret_key|client_secret_token|oauth_token|oauth_key|refresh_token|refresh_key|\w+_key)')

        claves = {}

        for script in scripts:
            src = script.get('src')
            if src:
                coincidencias = re.findall(patron, src)
                for coincidencia in coincidencias:
                    if coincidencia not in claves_encontradas:
                        claves_encontradas.add(coincidencia)
                        if coincidencia not in claves:
                            claves[coincidencia] = []
                        api_keys = re.findall(
                            r'(?:apiKey|api_key|apiToken|api_token|apikey|api_key|access_token|secret|token|auth|access_key|secret_key|client_id|client_secret|api_password|api_secret|auth_token|auth_key|access_token|access_key|client_secret_key|client_secret_token|oauth_token|oauth_key|refresh_token|refresh_key)\s*=\s*([^&"\']+)',
                            src)
                        for api_key in api_keys:
                            if api_key is not None:
                                servicio_etiquetado = etiquetar_url(src, servicios)
                                claves[coincidencia].append(
                                    {"url_madre": url, "etiqueta": servicio_etiquetado, "url": src, "api_key": api_key})

        texto_html = soup.get_text()
        coincidencias = re.findall(patron, texto_html)
        for coincidencia in coincidencias:
            if coincidencia not in claves_encontradas:
                claves_encontradas.add(coincidencia)
                if coincidencia not in claves:
                    claves[coincidencia] = []
                claves[coincidencia].append(
                    {"url_madre": url, "etiqueta": "desconocido", "url": url, "api_key": None})

        return claves

    except requests.RequestException as e:
        raise Exception(f"Error al realizar la solicitud HTTP a '{url}': {e}")
    except Exception as e:
        raise Exception(f"Error al buscar claves API en '{url}': {e}")

def etiquetar_url(url, servicios):
    """
    Etiqueta una URL con el servicio correspondiente si está en la lista de servicios.
    """
    for servicio, dominio in servicios.items():
        if dominio in url:
            return servicio
    return None  

def ejecutar_analisis(url, servicios, outfile, depth, threads, tree, explorar_button, guardar_button, analizar_button):
    """
    Ejecuta el análisis de una URL en un hilo separado.
    """
    try:
        analizar_url(url, servicios, outfile, depth, threads, tree)
    except Exception as e:
        print(f"Error al analizar {url}: {e}")
    finally:
        # Activar botones y cambiar el texto del botón "Analizar" a "Finalizado"
        activar_botones(explorar_button, guardar_button, analizar_button)
        analizar_button.config(text="Finalizado")
        print(f"Análisis de {url} finalizado.")

def analizar(url_radio_var, input_url_entry, archivo_entry, outfile_entry, depth_entry, threads_entry, explorar_button, guardar_button, analizar_button, tree):
    """
    Inicia el análisis de la URL o URLs proporcionadas.
    """
    try:
        # Desactivar botones y cambiar el texto del botón "Analizar" a "Ejecutando"
        desactivar_botones(explorar_button, guardar_button, analizar_button)
        analizar_button.config(text="Ejecutando")
        analizar_button.update_idletasks()  
        print("Inicio del análisis...")

        if url_radio_var.get():
            url = input_url_entry.get()
            archivo = None
        else:
            url = None
            archivo = archivo_entry.get()

        outfile = outfile_entry.get()
        depth = int(depth_entry.get())
        threads = int(threads_entry.get())

        servicios = cargar_servicios_desde_json()

        if url:
            if not url.strip():
                raise Exception("Error: La URL está vacía.")
            elif not validators.url(url):
                raise Exception("Error: La URL ingresada no es válida.")
            else:
                # Ejecutar el análisis en un hilo separado para evitar bloquear la interfaz de usuario
                analisis_thread = threading.Thread(target=ejecutar_analisis, args=(url, servicios, outfile, depth, threads, tree, explorar_button, guardar_button, analizar_button))
                analisis_thread.start()
        elif archivo:
            if not os.path.exists(archivo):
                raise Exception(f"Error: El archivo '{archivo}' no existe.")
            else:
                with open(archivo, 'r') as f:
                    urls = f.readlines()
                for url in urls:
                    url = url.strip()
                    # Ejecutar el análisis en un hilo separado para evitar bloquear la interfaz de usuario
                    analisis_thread = threading.Thread(target=ejecutar_analisis, args=(url, servicios, outfile, depth, threads, tree, explorar_button, guardar_button, analizar_button))
                    analisis_thread.start()

    except Exception as e:
        print(f"Error: {e}")

def analizar_url(url, servicios, outfile, depth, threads, tree, soup=None):
    """
    Analiza una URL en busca de claves API.
    """
    try:
        print(f"Analizando URL: {url}")

        # Verificar si se proporciona el objeto soup, si no, hacer una solicitud y analizar el HTML
        if soup is None:
            response = requests.get(url)
            response.raise_for_status()  
            contenido = response.text
            soup = BeautifulSoup(contenido, 'html.parser')

        claves = buscar_claves_api(url, servicios)
        if claves:
            for clave, lista_coincidencias in claves.items():
                print(f"Palabra clave: {clave}")
                for coincidencia in lista_coincidencias:
                    print(f"URL Madre: {coincidencia['url_madre']}, Etiqueta: {coincidencia['etiqueta']}, URL: {coincidencia['url']}, API Key: {coincidencia['api_key']}")
                    # Insertar los datos directamente en la tabla
                    if coincidencia['api_key'] is not None:
                        tree.insert("", "end", values=(coincidencia['url_madre'], coincidencia['etiqueta'], coincidencia['url'], coincidencia['api_key']))
                print()

            with open(outfile, 'a') as f:
                json.dump(claves, f, indent=4)
                f.write('\n')

            print(f"Los resultados se han añadido a '{outfile}'.")
            
        else:
            print("No se encontraron palabras clave en esta URL.")

        if depth > 0:
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/') or href.startswith(url):
                    full_url = urljoin(url, href)
                    if full_url not in analizadas:
                        analizadas.add(full_url)
                        try:
                            analizar_url(full_url, servicios, outfile, depth - 1, threads, tree, soup)
                        except requests.HTTPError as http_err:
                            print(f"Error HTTP al analizar URL '{full_url}': {http_err}")

    except Exception as e:
        print(f"Error al analizar URL '{url}': {e}")

def desactivar_botones(explorar_button, guardar_button, analizar_button):
    """
    Desactiva los botones de explorar, guardar y analizar.
    """
    explorar_button.config(state="disabled")
    guardar_button.config(state="disabled")
    analizar_button.config(state="disabled")

def activar_botones(explorar_button, guardar_button, analizar_button):
    """
    Activa los botones de explorar, guardar y analizar.
    """
    explorar_button.config(state="normal")
    guardar_button.config(state="normal")
    analizar_button.config(state="normal")

def mostrar_acerca_de():
    acerca_de_info = "Esta es una aplicación de búsqueda de claves API desarrollada por F.J.Sánchez."
    tk.messagebox.showinfo("Acerca de", acerca_de_info)

def mostrar_ayuda():
    ayuda_info = """
    Bienvenido al Buscador de Claves API.

    Para comenzar a buscar claves API, siga estos pasos:

    1. Ingrese la URL de la página web que desea analizar en el campo "URL", o seleccione "Cargar Archivo" para analizar un archivo que contenga URLs.
    2. Especifique el archivo de salida donde desea guardar los resultados en el campo "Resultados".
    3. Configure el nivel máximo de profundidad y el número máximo de hilos según sus preferencias.
    4. Haga clic en el botón "Analizar" para iniciar el análisis.
    
    Desarrollado por: F.J.Sánchez
    """
    tk.messagebox.showinfo("Ayuda", ayuda_info)

def main():
    """
    Función principal para ejecutar la aplicación.
    """
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Buscador de Claves API")

    # Crear un frame para contener los widgets
    frame = ttk.Frame(root, padding="20")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Crear los widgets
    url_radio_var = tk.BooleanVar(value=True)
    url_radio = ttk.Radiobutton(frame, text="Ingresar URL", variable=url_radio_var, value=True)
    url_radio.grid(row=1, column=0, sticky=tk.W)

    analizar_button = ttk.Button(frame, text="Analizar", command=lambda: analizar(url_radio_var, input_url_entry, archivo_entry, outfile_entry, depth_entry, threads_entry, explorar_button, guardar_button, analizar_button, tree))
    analizar_button.grid(row=7, column=1, sticky=(tk.W + tk.E))

    archivo_radio = ttk.Radiobutton(frame, text="Cargar Archivo", variable=url_radio_var, value=False)
    archivo_radio.grid(row=1, column=1, sticky=tk.W)

    input_url_label = ttk.Label(frame, text="URL:")
    input_url_label.grid(row=2, column=0, sticky=tk.W)

    input_url_entry = ttk.Entry(frame, width=50)
    input_url_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))

    archivo_label = ttk.Label(frame, text="Archivo:")
    archivo_label.grid(row=3, column=0, sticky=tk.W)

    archivo_entry = ttk.Entry(frame, width=50)
    archivo_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))

    explorar_button = ttk.Button(frame, text="Explorar", command=lambda: archivo_entry.insert(tk.END, filedialog.askopenfilename()))
    explorar_button.grid(row=3, column=2, sticky=tk.W)

    outfile_label = ttk.Label(frame, text="Resultados:")
    outfile_label.grid(row=4, column=0, sticky=tk.W)

    outfile_entry = ttk.Entry(frame, width=50)
    outfile_entry.grid(row=4, column=1, sticky=(tk.W, tk.E))

    guardar_button = ttk.Button(frame, text="Guardar como...", command=lambda: outfile_entry.insert(tk.END, filedialog.asksaveasfilename(defaultextension=".json")))
    guardar_button.grid(row=4, column=2, sticky=tk.W)

    depth_label = ttk.Label(frame, text="Nivel máximo de profundidad:")
    depth_label.grid(row=5, column=0, sticky=tk.W)

    tooltip_text = "Determina cuántos enlaces se analizarán. Aumentarlo puede proporcionar más datos, pero también puede aumentar el tiempo de ejecución."

    tooltip_lines = textwrap.wrap(tooltip_text.strip(), width=45)
    tooltip_justified = '\n'.join([line.lstrip() for line in tooltip_lines])

    Tooltip(depth_label, tooltip_justified)

    depth_entry = ttk.Entry(frame)
    depth_entry.grid(row=5, column=1, sticky=(tk.W, tk.E))
    depth_entry.insert(tk.END, "1")

    threads_label = ttk.Label(frame, text="Número máximo de hilos:")
    threads_label.grid(row=6, column=0, sticky=tk.W)

    tooltip_text = "Determina cuántas conexiones simultáneas se establecerán para analizar las páginas web. Aumentarlo puede acelerar el proceso de análisis al permitir más solicitudes simultáneas, pero un valor muy alto puede causar problemas de rendimiento."

    tooltip_lines = textwrap.wrap(tooltip_text.strip(), width=45)
    tooltip_justified = '\n'.join([line.lstrip() for line in tooltip_lines])

    Tooltip(threads_label, tooltip_justified)

    threads_entry = ttk.Entry(frame)
    threads_entry.grid(row=6, column=1, sticky=(tk.W, tk.E))
    threads_entry.insert(tk.END, "5")

    acerca_de_button = ttk.Button(frame, text="Acerca de", command=mostrar_acerca_de)
    acerca_de_button.grid(row=20, column=2, sticky=tk.E, padx=(0, 3))  # Menos espacio entre los botones

    ayuda_button = ttk.Button(frame, text="Ayuda", command=mostrar_ayuda)
    ayuda_button.grid(row=20, column=1, sticky=tk.E, padx=(3, 5))  # Más espacio a la derecha del botón "Acerca de"

    tree_frame = ttk.Frame(frame)
    tree_frame.grid(row=8, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))

    tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
    tree = ttk.Treeview(tree_frame, columns=("URL Madre", "Etiqueta", "URL", "API Key"), yscrollcommand=tree_scrollbar.set, height=4)
    tree_scrollbar.config(command=tree.yview)
    tree_scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Configurar encabezados de columnas
    tree.column("#0", width=0, stretch=tk.NO)
    tree.heading("URL Madre", text="URL Madre")
    tree.heading("Etiqueta", text="Etiqueta")
    tree.heading("URL", text="URL")
    tree.heading("API Key", text="API Key")

    frame.mainloop()

if __name__ == "__main__":
    main()

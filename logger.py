import keyboard # type: ignore
import pyautogui # type: ignore
import pyperclip # type: ignore
import time
from tkinter import Tk, simpledialog
from tkinter.filedialog import askopenfilename
import requests # type: ignore
import re
import configparser
import os
import threading


# Agrego un cambio o un comentario por aqui 

# Variables globales
indice = 0
datos = []
root = None  # Variable global para la ventana Tkinter
is_window_open = False

# Leer la clave API desde config.ini
def leer_api_key():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))  # Leer desde el mismo directorio que el script
    return config['API']['api_key']

API_KEY = leer_api_key()  # Ahora la API key se lee desde config.ini

# python 'c:/Users/david/Downloads/logger.py'

def _pegarCorreo():
    global is_window_open
    if not is_window_open:
        pyperclip.copy(datos[indice][0])
        pyautogui.press('backspace')
        pyautogui.hotkey("ctrl", "v") 
        print(f"Datos actuales: {datos[indice]}") # Pegado directo sin backspace
    

def _pegarContrasena():
    global is_window_open
    if not is_window_open:
        pyperclip.copy(datos[indice][1])
        pyautogui.press('backspace')
        pyautogui.hotkey("ctrl", "v")
        print(f"Datos actuales: {datos[indice]}")  # Pegado directo sin backspace

def obtener_mensajes(correo):
    url = f"https://mailsac.com/api/addresses/{correo}/messages"
    headers = {"Mailsac-Key": API_KEY}

    response = requests.get(url, headers=headers)
    mensajes = response.json()

    if not mensajes:
        print(f"No se encontraron mensajes para {correo}.")
        return None

    # Ordenar mensajes por fecha de recepción (descendente) y obtener el más reciente
    mensaje_reciente = max(mensajes, key=lambda m: m.get('received', ''))

    print(f"De: {mensaje_reciente['from']}")
    print(f"Asunto: {mensaje_reciente['subject']}")
    print(f"ID del Mensaje: {mensaje_reciente['_id']}")
    
    # Extraer el PIN del asunto del mensaje reciente
    return extraer_pin_del_asunto(mensaje_reciente['subject'])

def extraer_pin_del_asunto(asunto):
    # Utilizar una expresión regular para buscar el PIN en el asunto
    match = re.search(r'\b\d{6}\b', asunto)
    print(f"Asunto analizado: {asunto}")  # Imprimir el asunto para depuración
    return match.group(0) if match else None

def _pegarPIN():
    global is_window_open
    if not is_window_open:
        correo_actual = datos[indice][0]  # Obtener el correo actual
        pin = obtener_mensajes(correo_actual)  # Obtener el PIN desde Mailsac
        if pin:
            pyautogui.press('backspace')
            pyperclip.copy(pin)
            pyautogui.hotkey("ctrl", "v")  # Pegado directo sin backspace
            print(f"PIN pegado: {pin}")
        else:
            pyautogui.press('backspace')
            print("No se encontró un PIN.")

def _siguienteLinea():
    global indice
    if indice < len(datos) - 1:  # Verificar que no esté en la última línea
        pyautogui.press('backspace')
        indice += 1
        print(f"Datos actuales: {datos[indice]}")
    else:
        pyautogui.press('backspace')
        print("Ya estás en la última línea.")

def _lineaAnterior():
    global indice
    if indice > 0:  # Verificar que no esté en la primera línea
        pyautogui.press('backspace')
        indice -= 1
        print(f"Datos actuales: {datos[indice]}")
    else:
        pyautogui.press('backspace')
        print("Ya estás en la primera línea.")

def pedir_linea_tk():
    global is_window_open
    is_window_open = True
    valor = simpledialog.askinteger("Ir a línea", "Introduce el número de línea:")
    if valor is not None:
        print(f"Valor {valor} {is_window_open}");
        procesar_linea(valor)
        is_window_open = False
    return

def _irALinea():
    global indice
    global is_window_open
    if not is_window_open:
        is_window_open = True
        if root is not None:
            root.after(0, pedir_linea_tk)
            root.update_idletasks()
        else:
            print("Error: La ventana de Tkinter no está inicializada.")

def procesar_linea(nueva_linea):
    global indice
    global is_window_open
    try:
        nueva_linea = int(nueva_linea)  # Convertir el valor a entero
        if 1 <= nueva_linea <= len(datos):
            indice = nueva_linea - 1  # Convertir a índice 0 basado
            pyautogui.press('backspace')
            print(f"Ahora estás en la línea {indice + 1}.")
            print(f"Datos actuales: {datos[indice]}")
        else:
            print("Número de línea no válido.")
    except (ValueError, TypeError):
        print("Número de línea no válido.")

def _salir():
    print("Saliendo...")
    exit()

def manejar_teclas():
    # Configurar teclas rápidas del pad numérico
    keyboard.add_hotkey('+', _siguienteLinea)
    keyboard.add_hotkey('-', _lineaAnterior)
    keyboard.add_hotkey('5', _irALinea)
    keyboard.add_hotkey('1', _pegarCorreo)
    keyboard.add_hotkey('3', _pegarContrasena)
    keyboard.add_hotkey('4', _pegarPIN)
    keyboard.add_hotkey('esc', _salir)

    # Esperar indefinidamente
    keyboard.wait('esc')

def main():
    global root
    # Configurar la ventana oculta para el diálogo de archivos
    root = Tk()
    root.withdraw()

    archivo_path = askopenfilename(title="Selecciona el archivo de datos", filetypes=[("Archivos de texto", "*.txt")])

    if not archivo_path:
        print("No se seleccionó ningún archivo. El script se detendrá.")
        return

    print(f"Archivo seleccionado: {archivo_path}")

    global datos
    datos = []

    with open(archivo_path, 'r') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if ',' in linea:
                correo, contrasena = linea.split(',', 1)
                datos.append((correo, contrasena))
            else:
                print(f"Línea ignorada (formato incorrecto): {linea}")

    if datos:
        print("Datos leídos del archivo:")
        for dato in datos:
            print(dato)
        print("Presiona 'numpad_add' para cambiar de línea.")
        print("Presiona 'numpad_subtract' para regresar a la línea anterior.")
        print("Presiona 'numpad5' para ir a una línea específica.")
        print("Presiona 'numpad1' para pegar el correo.")
        print("Presiona 'numpad3' para pegar la contraseña.")
        print("Presiona 'numpad4' para pegar el PIN.")
        print("Presiona 'esc' para salir.")
        
        # Ejecutar el manejo de teclas en un hilo separado
        hilo_teclas = threading.Thread(target=manejar_teclas)
        hilo_teclas.start()

        # Mantener el hilo principal ejecutando el bucle de eventos de Tkinter
        root.mainloop()

    else:
        print("No se encontraron datos válidos en el archivo.")

if __name__ == '__main__':
    main()

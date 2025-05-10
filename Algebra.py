import json
import random
import requests
import re
import tkinter as tk
from tkinter import scrolledtext

# Configuración del endpoint de LM Studio
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# Cargar las preguntas desde el archivo JSON
def cargar_preguntas(archivo="Factorizacion_dif_cuadrados.json"):
    with open(archivo, 'r', encoding='utf-8') as f:
        return json.load(f)["preguntas"]

# Obtener preguntas aleatorias
def obtener_preguntas_aleatorias(preguntas, cantidad=2):
    return random.sample(preguntas, min(cantidad, len(preguntas)))

# Limpieza robusta de la respuesta del modelo
def limpiar_respuesta_modelo(texto):
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    texto = re.sub(r"\\[a-zA-Z]+\b", "", texto)
    texto = re.sub(r"\$+", "", texto)
    texto = re.sub(r"\\\(|\\\)", "", texto)
    texto = re.sub(r"\\", "", texto)
    texto = re.sub(r"[\[\]]", "", texto)
    texto = texto.replace("**", "").replace("*", "")
    texto = re.sub(r"#+", "", texto)
    return texto.strip()

# Generar explicaciones desde LM Studio
def generar_explicacion_local(errores):
    if not errores:
        return "¡Bien hecho! Parece que dominas la factorización por diferencia de cuadrados. Sigue practicando con ejercicios más avanzados."

    errores_formateados = "\n".join(
        [f"Se cometió un error en la pregunta {num + 1}: {preguntas_seleccionadas[num]['pregunta']}. "
         f"Respuesta dada: {resp}" for num, resp in errores]
    )

    prompt = f"""
    Un estudiante cometió errores en las siguientes preguntas de factorización por diferencia de cuadrados:

    {errores_formateados}

    Por favor:
    - No uses comandos de LaTeX, ni ecuaciones entre \\( \\), ni símbolos como \\.
    - No uses Markdown.
    - Escribe todo en texto plano.
    - Comienza con "Se cometió un error en la pregunta X: [Texto de la pregunta]".
    - Luego describe el error y cómo debió resolverse.
    - Da la respuesta correcta.
    - Añade consejos prácticos para evitar errores similares.

    Responde completamente en español.
    """

    data = {
        "model": "deepseek-r1-distill-llama-8b",
        "messages": [
            {"role": "system", "content": "Eres un tutor de matemáticas experto en factorización."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(LM_STUDIO_API_URL, json=data)

    if response.status_code == 200:
        respuesta_modelo = response.json()["choices"][0]["message"]["content"]
        return limpiar_respuesta_modelo(respuesta_modelo)
    else:
        return "⚠️ No se pudo conectar con el modelo local. Verifica que LM Studio está ejecutándose."

# Normalizar respuesta para comparación
def normalizar_respuesta(respuesta):
    return sorted(respuesta.replace(" ", "").lower().strip("()").split(")("))

# Mostrar recomendaciones en el área de texto
def mostrar_recomendaciones():
    recomendaciones = generar_explicacion_local(errores)
    recomendacion_text.config(state=tk.NORMAL)
    recomendacion_text.delete(1.0, tk.END)
    recomendacion_text.insert(tk.END, recomendaciones)
    recomendacion_text.config(state=tk.DISABLED)
    recomendacion_text.pack(padx=15, pady=10, fill="both", expand=True)

# Evaluar respuesta individual
def evaluar_respuesta(index):
    global puntaje_total

    respuesta_usuario = entradas_respuestas[index].get().strip()
    respuesta_correcta = preguntas_seleccionadas[index]["respuesta"]

    if normalizar_respuesta(respuesta_usuario) == normalizar_respuesta(respuesta_correcta):
        etiquetas_resultados[index].config(text="✅ Correcto", fg="green")
        puntaje_total += 1
    else:
        etiquetas_resultados[index].config(text=f"❌ Incorrecto. Respuesta: {respuesta_correcta}", fg="red")
        errores.append((index, respuesta_usuario))

    entradas_respuestas[index].config(state=tk.DISABLED)
    botones_evaluar[index].config(state=tk.DISABLED)

    if all(boton["state"] == tk.DISABLED for boton in botones_evaluar):
        mostrar_puntaje()

# Mostrar puntaje final
def mostrar_puntaje():
    total_preguntas = len(preguntas_seleccionadas)
    porcentaje = (puntaje_total / total_preguntas) * 100
    etiqueta_puntaje.config(text="Puntaje final:")
    resultado_final.config(text=f" {porcentaje:.2f}%", fg="blue")
    frame_puntaje.pack(pady=5)
    boton_recomendaciones.pack(side="left", padx=10)

# Interfaz gráfica
ventana = tk.Tk()
ventana.title("Evaluación de Álgebra")
ventana.geometry("850x550")

# Cargar preguntas
preguntas = cargar_preguntas()
preguntas_seleccionadas = obtener_preguntas_aleatorias(preguntas, 2)
puntaje_total = 0
errores = []

# Widgets
titulo = tk.Label(ventana, text="Evaluación Factorización por Diferencia de Cuadrados", font=("Arial", 13, "bold"))
titulo.pack(pady=10)

frame_preguntas = tk.Frame(ventana)
frame_preguntas.pack()

pregunta_labels = []
entradas_respuestas = []
botones_evaluar = []
etiquetas_resultados = []

for i, pregunta in enumerate(preguntas_seleccionadas):
    frame = tk.Frame(frame_preguntas)
    frame.pack(pady=5)

    pregunta_label = tk.Label(frame, text=f"{i + 1}. {pregunta['pregunta']}", font=("Arial", 12, "bold"))
    pregunta_label.pack(side="left", padx=5)

    entrada_respuesta = tk.Entry(frame, width=20, font=("Arial", 12))
    entrada_respuesta.pack(side="left", padx=5)

    boton_evaluar = tk.Button(frame, text="Evaluar", command=lambda i=i: evaluar_respuesta(i), font=("Arial", 12, "bold"), bg="blue", fg="white")
    boton_evaluar.pack(side="left", padx=5)

    etiqueta_resultado = tk.Label(frame_preguntas, text="", font=("Arial", 12, "bold"))
    etiqueta_resultado.pack()

    pregunta_labels.append(pregunta_label)
    entradas_respuestas.append(entrada_respuesta)
    botones_evaluar.append(boton_evaluar)
    etiquetas_resultados.append(etiqueta_resultado)

# Puntaje y recomendaciones
frame_puntaje = tk.Frame(ventana)
frame_puntaje.pack(pady=5)

etiqueta_puntaje = tk.Label(frame_puntaje, text="", font=("Arial", 12, "bold"))
etiqueta_puntaje.pack(side="left")

resultado_final = tk.Label(frame_puntaje, text="", font=("Arial", 13, "bold"))
resultado_final.pack(side="left", padx=10)

boton_recomendaciones = tk.Button(frame_puntaje, text="Mostrar Recomendaciones", command=mostrar_recomendaciones, font=("Arial", 12, "bold"), bg="green", fg="white")
boton_recomendaciones.pack_forget()

recomendacion_text = scrolledtext.ScrolledText(ventana, wrap=tk.WORD, width=90, height=10, font=("Arial", 12))
recomendacion_text.pack_forget()

ventana.mainloop()


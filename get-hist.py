import argparse
import getpass
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import re
import threading
import requests
from requests.auth import HTTPBasicAuth
import markdown
import json
import sys
import threading
import itertools
import time
import html2text
import os
from dotenv import load_dotenv
import subprocess # Importa el módulo subprocess para ejecutar comandos de la CLI

# Cargar archivo .env
load_dotenv()
# ========= CONFIG =========

# Variables de configuración
org = os.getenv("AZURE_ORG")
project = os.getenv("AZURE_PROJECT")
iteration_path = os.getenv("AZURE_ITERATION_PATH")
pat = os.getenv("AZURE_PAT")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Solicitar interactivamente si faltan variables
if not org:
    org = input("Introduce tu organización de Azure DevOps (AZURE_ORG): ")
if not project:
    project = input("Introduce tu proyecto de Azure DevOps (AZURE_PROJECT): ")
if not iteration_path:
    iteration_path = input("Introduce el Iteration Path (AZURE_ITERATION_PATH): ")
if not pat:
    pat = getpass.getpass("Introduce tu Personal Access Token de Azure DevOps (AZURE_PAT): ")
if not gemini_api_key:
    gemini_api_key = getpass.getpass("Introduce tu API Key de Gemini (GEMINI_API_KEY): ")

# Asegurarse de que la clave de API de Gemini esté disponible para subprocesos
if gemini_api_key:
    os.environ['GEMINI_API_KEY'] = gemini_api_key
# Se elimina la clave de OpenAI, ya no se usará
ado_api_version = "7.0"
max_historias = int(os.getenv("HISTORIAS_MAX", 7))
dias_sprint = int(os.getenv("DIAS_SPRINT", 10))
dias_complejidad = int(os.getenv("DIAS_COMPLEJIDAD", 2))

# Azure DevOps URLs
wiql_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version={ado_api_version}"

# Se elimina el cliente de OpenAI

# ========= FUNCIONES =========

import requests
from requests.auth import HTTPBasicAuth

def obtener_historias():
    """Consulta Azure DevOps para obtener historias de usuario de un sprint."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    # Paso 1: Obtener los IDs y títulos de las historias.
    # Esta consulta es válida y no fallará porque no pide campos restringidos.
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.Description]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Product Backlog Item'
        AND [System.IterationPath] = '{iteration_path}'
        """
    }
    
    # Realizar la primera petición a la API de WIQL
    resp = requests.post(wiql_url, json=query, auth=HTTPBasicAuth('', pat))
    resp.raise_for_status()  # Lanza una excepción si la petición falla
    data = resp.json()
    work_items = data.get("workItems", [])

    historias = []
    
    # Paso 2: Iterar sobre los IDs y obtener todos los detalles de cada historia.
    for item in work_items[:max_historias]:
        wid = item["id"]
        
        # Segunda petición: obtiene todos los campos, incluyendo los criterios de aceptación.
        # Esta llamada a la API de 'wit/workitems' sí soporta este campo.
        wi_url = f"https://dev.azure.com/{org}/_apis/wit/workitems/{wid}?api-version={ado_api_version}"
        wi = requests.get(wi_url, auth=HTTPBasicAuth('', pat)).json()
        descripcion_html = wi["fields"].get("System.Description", "")
        criterios_html = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
        
        descripcion_markdown = h.handle(descripcion_html)
        criterios_markdown = h.handle(criterios_html)
        historias.append({
            "id": wid,
            "titulo": wi["fields"]["System.Title"],
            "url": wi["_links"]["html"]["href"],
            "descripcion": descripcion_markdown,
            "aceptacion_criterios": criterios_markdown
        })
    
    return historias

def evaluar_historias_cli(historias):
    """
    Evalúa una lista de historias de usuario usando gemini-cli.
    
    Solicita a Gemini que evalúe todas las historias en un solo prompt
    y devuelva un array de JSON.
    """
    historias_str = ""
    for h in historias:
        historias_str += f"""
---
Historia ID: {h['id']}
Título: {h['titulo']}
Descripción: {h['descripcion']}
Criterios de Aceptación: {h['aceptacion_criterios']}
---
"""

    prompt = f"""
Eres un experto en gestión de historias de usuario y en paneles de Azure DevOps.
Tu tarea es evaluar las siguientes historias bajo los criterios INVEST.

Para cada historia, proporciona:
1. Una evaluación de cada criterio INVEST (Independiente, Negociable, Valiosa, Estimable, Pequeña, Testeable) con un puntaje de 1 a 5 y una breve justificación.
2. Una estimación de esfuerzo en puntos de historia (1-8).
3. Una estimación en días de trabajo aproximados.
4. Un valor de complejidad (1 = muy simple, 2.5 = normal, 5 = muy compleja).
5. Una lista de posibles mejoras o recomendaciones para optimizar la historia.

Responde exclusivamente con un array de objetos JSON. Cada objeto del array debe corresponder a una historia de usuario y tener la siguiente estructura:
{{
  "id": <ID de la historia>,
  "titulo": "<Título de la historia>",
  "evaluacion_invest": {{
    "Independiente": {{ "puntaje": <puntaje>, "justificacion": "<justificación>" }},
    "Negociable": {{ "puntaje": <puntaje>, "justificacion": "<justificación>" }},
    "Valiosa": {{ "puntaje": <puntaje>, "justificacion": "<justificación>" }},
    "Estimable": {{ "puntaje": <puntaje>, "justificacion": "<justificación>" }},
    "Pequeña": {{ "puntaje": <puntaje>, "justificacion": "<justificación>" }},
    "Testeable": {{ "puntaje": <puntaje>, "justificacion": "<justificación>" }}
  }},
  "complejidad": <complejidad>,
  "posibles_mejoras": ["<sugerencia_1>", "<sugerencia_2>", "..."]
}}

Aquí están las historias a evaluar:
{historias_str}
"""
    try:
        # guarda el prompt en un archivo
        with open("prompt.txt", "w") as f:
            f.write(prompt)

        result = subprocess.run(['gemini', '-p', prompt], capture_output=True, text=True, check=True)
        raw_output = result.stdout.strip()

        # Usar una expresión regular para encontrar el bloque JSON y eliminar los acentos graves
        match = re.search(r'```json\s*(\[.*?\])\s*```', raw_output, re.DOTALL)
        
        if not match:
            # Si no se encuentra un JSON válido con el formato de cerca de código,
            # intentamos buscar un JSON plano como respaldo.
            match = re.search(r'\[\s*\{.*?\}\s*\]', raw_output, re.DOTALL)
            if not match:
                raise ValueError("No se pudo encontrar un JSON válido en la salida de la CLI.")
            
        json_output = match.group(1).strip()
        
        return json.loads(json_output)

    except FileNotFoundError:
        print("Error: gemini-cli no se encontró. Asegúrate de que esté instalado y en tu PATH.")
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar gemini-cli: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON de la respuesta: {e}")
        print("Respuesta recibida:")
        print(json_output)
        return []

def estimar_dias(complejidad=1, capacidad_equipo=None, sprint_dias=10, dias_por_complejidad=2):
    """
    Calcula días estimados considerando complejidad de la historia y carga del equipo.
    
    complejidad: multiplicador de complejidad (0.5 = muy simple, 1 = normal, 2 = muy compleja)
    capacidad_equipo: dict con 'carga' (%) y opcionalmente 'historias' (cantidad total)
    sprint_dias: duración del sprint
    dias_por_complejidad: días base por unidad de complejidad
    """
    if capacidad_equipo is None:
        capacidad_equipo = {"carga": 0, "historias": 5}
    
    # Base días según complejidad
    base = dias_por_complejidad * complejidad

    # Overhead de ceremonias (repartido entre todas las historias)
    total_hu = capacidad_equipo.get("historias", 5)
    overhead_total = sprint_dias * 0.15
    overhead_por_historia = overhead_total / max(1, total_hu)

    # Ajuste por carga del equipo (%)
    ajuste = base * (1 + capacidad_equipo.get("carga", 0)/100)

    # Días finales
    return round(ajuste + overhead_por_historia, 2)


# === Servidor para el Dashboard ===
class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Sirve archivos desde el directorio 'public'
        super().__init__(*args, directory='public', **kwargs)

    def do_GET(self):
        if self.path == '/data':
            # Este endpoint especial sirve el archivo res.json desde el directorio raíz del proyecto
            try:
                with open('res.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, 'res.json no encontrado')
        else:
            # Para todas las demás peticiones, usa el comportamiento por defecto
            # que sirve archivos desde el directorio 'public'
            super().do_GET()


def start_server(port=8000):
    # El handler ya está configurado para usar el directorio 'public'
    httpd = HTTPServer(("", port), DashboardRequestHandler)
    print(f"🌐 Servidor corriendo en http://localhost:{port}")
    httpd.serve_forever()

# === Loader auxiliar ===
class Loader:
    def __init__(self, desc="Procesando...", end="Listo!", timeout=0.1):
        self.desc = desc
        self.end = end
        self.timeout = timeout
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate)
        self._thread.start()

    def _animate(self):
        for c in itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]):
            if not self._running:
                break
            sys.stdout.write(f"\r{self.desc} {c}")
            sys.stdout.flush()
            time.sleep(self.timeout)

    def stop(self):
        self._running = False
        self._thread.join()
        # Sobrescribir la línea completa con espacios
        sys.stdout.write("\r" + " " * (len(self.desc) + 10) + "\r")
        sys.stdout.write(f"{self.end}\n")
        sys.stdout.flush()
        
# Importar la función generar_markdown (asegúrate de que el archivo adjust_json.py exista y contenga esta función)
# from adjust_json import generar_markdown

# === MAIN ===
if __name__ == "__main__":
    historias = obtener_historias()
    
    capacidad_equipo = {
        "carga": 0,               # 0% de carga
        "historias": len(historias)  # número de HU del sprint
    }

    loader = Loader(desc=f"🔄 Evaluando {len(historias)} historias de usuario con Gemini CLI...")
    loader.start()

    # Llama a la nueva función que usa la CLI y espera la respuesta JSON
    resultados_json = evaluar_historias_cli(historias)
    loader.stop()
    print("✅ Evaluación de historias completada.")
    
    if resultados_json:
        # Crear un mapa de búsqueda para acceder fácilmente a la URL por ID
        historias_map = {h['id']: h for h in historias}

        # Calcular las estimaciones de días y agregar la URL a cada resultado
        for h_resultado in resultados_json:
            complejidad = h_resultado.get("complejidad", 1.0)
            estimacion_dias = estimar_dias(complejidad, capacidad_equipo, dias_sprint, dias_complejidad)
            h_resultado["estimacion_dias"] = estimacion_dias
            
            # Agregar la URL del objeto de historia original
            original_historia = historias_map.get(h_resultado['id'])
            if original_historia:
                h_resultado['url'] = original_historia['url']
        
        # Crear el objeto final con data y metadata
        metadata = {
            "organizacion": org,
            "proyecto": project,
            "sprint": iteration_path,
            "max_historias_evaluadas": max_historias,
            "dias_sprint_config": dias_sprint,
        }
        final_data = {
            "metadata": metadata,
            "data": resultados_json
        }
        # Guardar resultados en JSON
        with open("res.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print("✅ Resultados guardados en res.json")

        # Generar reporte en Markdown
        # generar_markdown("res.json", "historias_invest.md")

        # Servir el reporte renderizado
        threading.Thread(target=start_server, daemon=True).start()
        input("🚀 Presiona Enter para detener el servidor...\n")
    else:
        print("❌ No se pudieron obtener los resultados de la CLI.")
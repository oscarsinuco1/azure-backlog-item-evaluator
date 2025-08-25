import argparse
import getpass
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import re
import threading
import requests
from requests.auth import HTTPBasicAuth
import markdown
import requests
from requests.auth import HTTPBasicAuth
from openai import OpenAI
import json
from adjust_json import generar_markdown
import sys
import threading
import itertools
import time
import os
from dotenv import load_dotenv

# Cargar archivo .env
load_dotenv()
# ========= CONFIG =========

# Solicitar por input si no se pasó por flag
org = os.getenv("AZURE_ORG")
project = os.getenv("AZURE_PROJECT")
iteration_path = os.getenv("AZURE_ITERATION_PATH")
pat = os.getenv("AZURE_PAT")
openai_api_key = os.getenv("OPENAI_API_KEY")
ado_api_version = "7.0"

# Azure DevOps URLs
wiql_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version={ado_api_version}"

# ========= CLIENTES =========

# Azure DevOps URLs
wiql_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version={ado_api_version}"

# ========= CLIENTES =========
client = OpenAI(api_key=openai_api_key)

# ========= FUNCIONES =========
def obtener_historias():
    """Consulta Azure DevOps para obtener historias de usuario de un sprint."""
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.Description]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Product Backlog Item'
        AND [System.IterationPath] = '{iteration_path}'
        """
    }
    resp = requests.post(wiql_url, json=query, auth=HTTPBasicAuth('', pat))
    resp.raise_for_status()
    data = resp.json()
    work_items = data.get("workItems", [])
    
    historias = []
    for item in work_items:
        wid = item["id"]
        wi_url = f"https://dev.azure.com/{org}/_apis/wit/workitems/{wid}?api-version={ado_api_version}"
        wi = requests.get(wi_url, auth=HTTPBasicAuth('', pat)).json()
        historias.append({
            "id": wid,
            "titulo": wi["fields"]["System.Title"],
            "descripcion": wi["fields"].get("System.Description", "")
        })
    return historias

def evaluar_invest(texto):
    """Evalúa una historia según INVEST usando OpenAI, sugiere estimación y complejidad."""
    prompt = f"""
    Eres un experto en gestión de historias de usuario y en paneles de Azure DevOps.
    Tu tarea es evaluar la siguiente historia bajo los criterios INVEST, explicando de manera clara y breve cada uno.

    Historia:
    {texto}

    Responde en formato estructurado con:
    - Un título por cada criterio INVEST.
    - Un puntaje de 1 a 5 junto con una justificación breve.

    Al final, con base en la calidad, claridad y complejidad de la historia, sugiere:
    1. Estimación de esfuerzo en **puntos de historia** (1-8)
    2. Estimación en **días de trabajo aproximados** (considerando un sprint estándar de 10 días)
    3. Un valor de **complejidad** (0.5 = muy simple, 1 = normal, 2 = muy compleja)

    Ejemplo de formato esperado:

    - Independiente (4): explicación breve
    - Negociable (3): explicación breve
    - Valiosa (5): explicación breve
    - Estimable (4): explicación breve
    - Pequeña (3): explicación breve
    - Testeable (4): explicación breve

    **Estimación recomendada:** 5 puntos (~3 días)  
    **Complejidad sugerida:** 1.2
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()




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


# === Servidor que convierte .md a HTML y lo sirve ===
class MarkdownHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path.endswith(".md"):
            with open("index.html", "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        if self.path == "/data":
            with open("res.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()

            # Convertir el diccionario/array a JSON string
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        else:
            self.send_error(404, "Archivo no encontrado")


def start_server(port=8000):
    httpd = HTTPServer(("", port), MarkdownHandler)
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



# === MAIN ===
if __name__ == "__main__":
    historias = obtener_historias()
    
    capacidad_equipo = {
        "carga": 20,               # 20% extra de carga
        "historias": len(historias)  # número de HU del sprint
    }
    resultados = []

    for h in historias:
        texto = f"{h['titulo']}\n{h['descripcion']}"
        loader = Loader(desc=f"🔄 Evaluando historia {h['id']}...")
        loader.start()
        invest_eval = evaluar_invest(texto)
        
        # Buscar la línea que contiene "Complejidad sugerida"
        match = re.search(r"\*\*Complejidad sugerida:\*\*\s*([0-9]+(?:\.[0-9]+)?)", invest_eval)
        if match:
            complejidad = float(match.group(1))
        else:
            complejidad = 1.0  # valor por defecto si no se encuentra
        loader.stop()
        estimacion = estimar_dias(complejidad, capacidad_equipo)

        resultados.append({
            "id": h["id"],
            "titulo": h["titulo"],
            "invest": invest_eval,
            "estimacion_dias": estimacion,
            "complejidad": complejidad,
        })

    # Guardar resultados en JSON
    with open("res.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print("✅ Resultados guardados en res.json")

    # Generar reporte en Markdown
    generar_markdown("res.json", "historias_invest.md")

    # Servir el reporte renderizado
    threading.Thread(target=start_server, daemon=True).start()
    input("🚀 Presiona Enter para detener el servidor...\n")
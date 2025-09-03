import os
from dotenv import load_dotenv
import questionary
from InquirerPy import inquirer
from src.azure.api import obtener_organizaciones, obtener_proyectos, obtener_iterations

load_dotenv()

# Constantes de color para la terminal
BLUE = '\033[38;2;95;175;255m'  # Tono azul claro (#5fafff)
GREEN_BOLD = '\033[1;32m'
ENDC = '\033[0m'

# Variables de configuración
org = os.getenv("AZURE_ORG")
project = os.getenv("AZURE_PROJECT")
iteration_path = os.getenv("AZURE_ITERATION_PATH")
pat = os.getenv("AZURE_PAT")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Solicitar interactivamente si faltan variables
if not pat:
    pat = questionary.password("Introduce tu Personal Access Token de Azure DevOps (AZURE_PAT):").ask()

if not org:
    try:
        organizaciones_disponibles = obtener_organizaciones(pat)
        if len(organizaciones_disponibles) == 1:
            org = organizaciones_disponibles[0]
            print(f"🏢 Organización encontrada y seleccionada automáticamente: {BLUE}{org}{ENDC}")
        elif organizaciones_disponibles:
            org = inquirer.fuzzy(
                message="Busca o selecciona tu organización de Azure DevOps:",
                choices=organizaciones_disponibles,
                long_instruction="Usa las flechas para navegar, escribe para filtrar.",
                vi_mode=True,
                border=True,
            ).execute()
        else:
            print("No se encontraron organizaciones asociadas a tu PAT.")
            org = questionary.text("No se encontraron organizaciones. Introduce el nombre manualmente:").ask()
    except Exception as e:
        print(f"⚠️ No se pudieron obtener las organizaciones ({e}). Por favor, introduce el nombre manualmente.")
        org = questionary.text("Introduce tu organización de Azure DevOps (AZURE_ORG):").ask()

if not project:
    try:
        proyectos_disponibles = obtener_proyectos(org, pat)
        if len(proyectos_disponibles) == 1:
            project = proyectos_disponibles[0]
            print(f"🏗️ Proyecto encontrado y seleccionado automáticamente: {BLUE}{project}{ENDC}")
        elif proyectos_disponibles:
            project = inquirer.fuzzy(
                message="Busca o selecciona tu proyecto de Azure DevOps:",
                choices=proyectos_disponibles,
                long_instruction="Usa las flechas para navegar, escribe para filtrar.",
                vi_mode=True,
                border=True,
            ).execute()
        else:
            print(f"No se encontraron proyectos en la organización '{org}'.")
            project = questionary.text("No se encontraron proyectos. Introduce el nombre manualmente:").ask()
    except Exception as e:
        print(f"⚠️ No se pudieron obtener los proyectos ({e}). Por favor, introduce el nombre manualmente.")
        project = questionary.text("Introduce el nombre de tu proyecto:").ask()

if not iteration_path:
    try:
        iterations_disponibles = obtener_iterations(project, org, pat)
        if len(iterations_disponibles) == 1:
            iteration_path = iterations_disponibles[0]
            print(f"🗓️ Iteración encontrada y seleccionada automáticamente: {BLUE}{iteration_path}{ENDC}")
        elif iterations_disponibles:
            # Crear un mapa entre el nombre amigable y la ruta completa
            mapa_iteraciones = {}
            for path in iterations_disponibles:
                # Elimina el nombre del proyecto y la palabra "Iteration" del inicio
                # Ejemplo: de '\Proyecto\Iteration\Sprint 1' a 'Sprint 1'
                partes = path.split('\\')
                # El path empieza con '\', así que el primer elemento es vacío.
                # El segundo es el proyecto, el tercero es 'Iteration'. Nos quedamos con el resto.
                nombre_amigable = ' > '.join(partes[3:]) if len(partes) > 3 else path
                mapa_iteraciones[nombre_amigable] = path
            
            # Usar InquirerPy para un autocompletado que muestra todas las opciones al inicio
            # y permite filtrar al escribir.
            nombre_seleccionado = inquirer.fuzzy(
                message="Busca o selecciona el Iteration Path:",
                choices=list(mapa_iteraciones.keys()),
                long_instruction="Usa las flechas para navegar, escribe para filtrar.",
                vi_mode=True,
                border=True,
            ).execute()

            iteration_path = mapa_iteraciones.get(nombre_seleccionado)
        else:
            print(f"No se encontraron iteraciones en el proyecto '{project}'.")
    except Exception as e:
        print(f"⚠️ No se pudieron obtener las iteraciones ({e}). Por favor, introduce la ruta manualmente.")
        iteration_path = questionary.text("Introduce el Iteration Path (Ej: Proyecto\\Sprint 1):").ask()

if not gemini_api_key:
    gemini_api_key = questionary.password("Introduce tu API Key de Gemini (GEMINI_API_KEY):").ask()

# Asegurarse de que la clave de API de Gemini esté disponible para subprocesos
if gemini_api_key:
    os.environ['GEMINI_API_KEY'] = gemini_api_key

ado_api_version = "7.0"
max_historias = int(os.getenv("HISTORIAS_MAX", 7))
dias_sprint = int(os.getenv("DIAS_SPRINT", 10))
dias_complejidad = int(os.getenv("DIAS_COMPLEJIDAD", 2))
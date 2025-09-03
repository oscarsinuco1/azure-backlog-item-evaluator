import os
import getpass
from dotenv import load_dotenv

load_dotenv()

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
    gemini_api_key = getpass.getpass("Introduce tu API Key de Gemini (AZURE_GEMINI_API_KEY): ")

# Asegurarse de que la clave de API de Gemini esté disponible para subprocesos
if gemini_api_key:
    os.environ['GEMINI_API_KEY'] = gemini_api_key

ado_api_version = "7.0"
max_historias = int(os.getenv("HISTORIAS_MAX", 7))
dias_sprint = int(os.getenv("DIAS_SPRINT", 10))
dias_complejidad = int(os.getenv("DIAS_COMPLEJIDAD", 2))
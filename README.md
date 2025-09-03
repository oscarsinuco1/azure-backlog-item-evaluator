# Azure Backlog Item Evaluator con Gemini

Este proyecto permite **evaluar Historias de Usuario (HU) desde Azure DevOps** usando la IA de Google (Gemini), generar estimaciones de días y complejidad, y servir un dashboard interactivo.

---

## Requisitos

- Docker instalado en tu máquina  
- Un **Personal Access Token (PAT)** de Azure DevOps  
- Una **Cuenta de Google** para autenticarte con Google Cloud.

---

## Construir la imagen Docker

Desde la raíz del proyecto:

```bash
docker build -t azure-invest-analyzer .
```
## Ejecutar el contenedor

Puedes pasar los parámetros como variables de entorno (-e) al contenedor:

```bash
docker run -it --rm -p 8000:8000 --name invest-analyzer \
  -e AZURE_PAT="TU_PAT_AQUI" \
  -e GEMINI_API_KEY="TU_API_KEY_AQUI" \
  azure-invest-analyzer
```
## Acceder al servidor

Después de correr el contenedor, abre en tu navegador: [http://localhost:8000](http://localhost:8000) Ahí podrás ver el .md generado con la evaluación de todas las HU.

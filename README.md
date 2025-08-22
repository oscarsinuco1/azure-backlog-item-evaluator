# Azure Backlog Item Evaluator (Docker)

Este proyecto permite **evaluar Historias de Usuario (HU) desde Azure DevOps** usando OpenAI, generar estimaciones de días y complejidad, y servir un `.md` renderizado en HTML.  

Actualmente, los cálculos internos **usan 10 días de sprint y 20% de carga extra**.

---

## Requisitos

- Docker instalado en tu máquina  
- Un **Personal Access Token (PAT)** de Azure DevOps  
- Una **API Key de OpenAI**  

---

## Construir la imagen Docker

Desde la raíz del proyecto:

```bash
docker build -t test/azure-backlog-item-evaluator:1.0.0 .
```
## Ejecutar el contenedor

Puedes pasar los parámetros como variables de entorno (-e) al contenedor:

```bash
docker run -it --rm -p 8000:8000 \
  -e AZURE_ORG="TU_ORG_AQUI" \
  -e AZURE_PROJECT="TU_PROYECTO_AQUI" \
  -e AZURE_ITERATION_PATH="TU_ITERATION_PATH_AQUI" \
  -e AZURE_PAT="TU_PAT_AQUI" \
  -e OPENAI_API_KEY="TU_OPENAI_KEY" \
  test/azure-backlog-item-evaluator:1.0.0
```
## Acceder al servidor

Después de correr el contenedor, abre en tu navegador: [http://localhost:8000](http://localhost:8000) Ahí podrás ver el .md generado con la evaluación de todas las HU.

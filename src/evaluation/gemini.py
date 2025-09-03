import subprocess
import json
import re

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
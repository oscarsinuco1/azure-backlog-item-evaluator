import threading
import json

# Importar módulos refactorizados
from src.config.config import org, project, iteration_path, max_historias, dias_sprint, dias_complejidad
from src.azure.api import obtener_historias
from src.evaluation.gemini import evaluar_historias_cli
from src.logic.estimation import estimar_dias
from src.web.server import start_server
from src.utils.loader import Loader

# La función generar_markdown se mantiene en adjust_json.py y se puede importar si se desea usar.
# from adjust_json import generar_markdown

# === MAIN ===
if __name__ == "__main__":
    historias = obtener_historias()
    
    capacidad_equipo = {
        "carga": 0,  # 0% de carga
        "historias": len(historias)  # número de HU del sprint
    }

    loader = Loader(desc=f"🔄 Evaluando {len(historias)} historias de usuario con Gemini CLI...")
    loader.start()

    resultados_json = evaluar_historias_cli(historias)
    loader.stop()
    print("✅ Evaluación de historias completada.")
    
    if resultados_json:
        historias_map = {h['id']: h for h in historias}

        for h_resultado in resultados_json:
            complejidad = h_resultado.get("complejidad", 1.0)
            estimacion_dias = estimar_dias(complejidad, capacidad_equipo, dias_sprint, dias_complejidad)
            h_resultado["estimacion_dias"] = estimacion_dias
            
            original_historia = historias_map.get(h_resultado['id'])
            if original_historia:
                h_resultado['url'] = original_historia['url']
        
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
        with open("res.json", "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        print("✅ Resultados guardados en res.json")

        # Generar reporte en Markdown (descomentar si se desea usar)
        # generar_markdown("res.json", "historias_invest.md")

        threading.Thread(target=start_server, daemon=True).start()
        input("🚀 Presiona Enter para detener el servidor...\n")
    else:
        print("❌ No se pudieron obtener los resultados de la CLI.")
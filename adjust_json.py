import json

def generar_markdown(filename_json="res.json", filename_md="historias_invest.md"):
    # === Cargar resultados desde archivo JSON ===
    with open(filename_json, "r", encoding="utf-8") as f:
        resultados = json.load(f)

    md = "# 📊 Informe de Historias de Usuario\n\n"
    
    for r in resultados:
        md += f"## Historia {r['id']}\n"
        md += f"**Título:** {r['titulo']}\n\n"
        md += f"**Estimación de días:** {r['estimacion_dias']}\n\n"
        
        md += "### Evaluación INVEST\n"
        
        # Aquí simplemente imprimimos el texto ya estructurado
        invest_text = r["invest"]
        md += f"{invest_text}\n\n"
    
    # Guardar archivo .md
    with open(filename_md, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"✅ Reporte generado en {filename_md}")

# === Ejecutar ===
generar_markdown("res.json", "historias_invest.md")

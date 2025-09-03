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
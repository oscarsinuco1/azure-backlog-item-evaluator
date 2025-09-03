import json
import requests
from requests.auth import HTTPBasicAuth
import html2text

def _get_session(pat):
    """Crea y configura una sesión de requests con la autenticación PAT."""
    session = requests.Session()
    session.auth = HTTPBasicAuth('oscar.sinuco', pat)
    return session

def obtener_organizaciones(pat):
    """Obtiene las organizaciones a las que el usuario tiene acceso usando un PAT."""
    try:
        session = _get_session(pat)
        api_version = "6.0"
        
        # 1. Obtener el ID del perfil del usuario ("me")
        profile_url = f"https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version={api_version}"
        resp = session.get(profile_url)
        resp.raise_for_status()
        member_id = resp.json().get("id")


        # 2. Usar el ID para listar las organizaciones
        orgs_url = f"https://app.vssps.visualstudio.com/_apis/accounts?memberId={member_id}&api-version={api_version}"
        resp = session.get(orgs_url)
        resp.raise_for_status()
        organizaciones = resp.json().get("value", [])
        return [org["accountName"] for org in organizaciones]
    except requests.RequestException as e:
        print(f"Error al conectar con Azure DevOps para obtener organizaciones: {e}")
        return []

def obtener_proyectos(org, pat, ado_api_version="7.0"):
    """Obtiene la lista de proyectos para la organización configurada."""
    session = _get_session(pat)
    url = f"https://dev.azure.com/{org}/_apis/projects?api-version={ado_api_version}"
    resp = session.get(url)
    resp.raise_for_status()
    proyectos = resp.json().get("value", [])
    return [p["name"] for p in proyectos]

def _extraer_rutas_recursivamente(nodo, iteraciones_encontradas):
    """
    Función auxiliar para recorrer el árbol de nodos y extraer las iteraciones
    con sus atributos.
    """
    # El primer nodo es la raíz del proyecto, no tiene una ruta de iteración válida.
    # Solo añadimos los nodos que son "hojas" (no tienen hijos), que representan
    # las iteraciones finales donde se asignan los work items.
    if nodo.get("structureType") == "iteration" and not nodo.get("hasChildren"):
        # Guardamos el nodo completo para tener acceso a sus atributos (fechas)
        iteraciones_encontradas.append(nodo)
    
    if "children" in nodo and nodo["children"]:
        for hijo in nodo["children"]:
            _extraer_rutas_recursivamente(hijo, iteraciones_encontradas)

def obtener_iterations(project_name, org, pat, ado_api_version="7.1-preview.2"):
    """Obtiene toda la jerarquía de iteraciones de un proyecto usando los nodos de clasificación."""
    session = _get_session(pat)
    # Este método es más robusto que buscar por equipo, ya que obtiene todas las iteraciones del proyecto.
    url = f"https://dev.azure.com/{org}/{project_name}/_apis/wit/classificationnodes/Iterations"
    params = {"$depth": 10, "api-version": ado_api_version} # Aumentamos la profundidad para asegurar capturar todo
    
    resp = session.get(url, params=params)
    resp.raise_for_status()
    raiz = resp.json()
    
    iteraciones_encontradas = []
    _extraer_rutas_recursivamente(raiz, iteraciones_encontradas)

    # Ordenar las iteraciones por fecha de inicio (startDate) de más reciente a más antigua.
    # Las iteraciones sin fecha de inicio se tratarán como las más antiguas.
    iteraciones_ordenadas = sorted(
        iteraciones_encontradas,
        key=lambda i: i.get("attributes", {}).get("startDate", "1900-01-01"),
        reverse=True
    )
    return [i["path"] for i in iteraciones_ordenadas]

def obtener_historias(org, project, iteration_path, pat, ado_api_version, max_historias):
    """Consulta Azure DevOps para obtener historias de usuario de un sprint."""
    session = _get_session(pat)
    h = html2text.HTML2Text()
    h.ignore_links = False
    
    # El campo [System.IterationPath] en WIQL es relativo al proyecto.
    # La ruta completa es '\Proyecto\Iteration\RutaDelSprint'.
    # Para la consulta, necesitamos 'Proyecto\RutaDelSprint'.
    # Eliminamos la barra inicial y la parte '\Iteration'.
    partes = iteration_path.split('\\')
    # partes[1] es el proyecto, partes[3:] es la ruta relativa.
    iteration_path_for_wiql = '\\\\'.join([partes[1]] + partes[3:])

    wiql_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version={ado_api_version}"

    # Paso 1: Obtener los IDs y títulos de las historias.
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Product Backlog Item'
        AND [System.IterationPath] UNDER '{iteration_path_for_wiql}'
        """
    }
    
    # Realizar la primera petición a la API de WIQL
    resp = session.post(wiql_url, json=query)
    resp.raise_for_status()  # Lanza una excepción si la petición falla
    data = resp.json()
    work_items = data.get("workItems", [])

    historias = []
    
    # Paso 2: Iterar sobre los IDs y obtener todos los detalles de cada historia.
    for item in work_items[:max_historias]:
        wid = item["id"]
        
        wi_url = f"https://dev.azure.com/{org}/_apis/wit/workitems/{wid}?api-version={ado_api_version}"
        wi = session.get(wi_url).json()
        fields = wi.get("fields", {})
        descripcion_html = wi["fields"].get("System.Description", "")
        criterios_html = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
        
        historias.append({
            "id": wid,
            "titulo": wi["fields"]["System.Title"],
            "url": wi["_links"]["html"]["href"],
            "descripcion": h.handle(descripcion_html) if descripcion_html else "",
            "aceptacion_criterios": h.handle(criterios_html) if criterios_html else ""
        })
    
    return historias
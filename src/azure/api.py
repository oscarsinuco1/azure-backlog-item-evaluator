import requests
from requests.auth import HTTPBasicAuth
import html2text
from src.config.config import org, project, iteration_path, pat, ado_api_version, max_historias

def obtener_historias():
    """Consulta Azure DevOps para obtener historias de usuario de un sprint."""
    h = html2text.HTML2Text()
    h.ignore_links = False
    
    wiql_url = f"https://dev.azure.com/{org}/{project}/_apis/wit/wiql?api-version={ado_api_version}"

    # Paso 1: Obtener los IDs y títulos de las historias.
    query = {
        "query": f"""
        SELECT [System.Id], [System.Title], [System.Description]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Product Backlog Item'
        AND [System.IterationPath] = '{iteration_path}'
        """
    }
    
    # Realizar la primera petición a la API de WIQL
    resp = requests.post(wiql_url, json=query, auth=HTTPBasicAuth('', pat))
    resp.raise_for_status()  # Lanza una excepción si la petición falla
    data = resp.json()
    work_items = data.get("workItems", [])

    historias = []
    
    # Paso 2: Iterar sobre los IDs y obtener todos los detalles de cada historia.
    for item in work_items[:max_historias]:
        wid = item["id"]
        
        wi_url = f"https://dev.azure.com/{org}/_apis/wit/workitems/{wid}?api-version={ado_api_version}"
        wi = requests.get(wi_url, auth=HTTPBasicAuth('', pat)).json()
        descripcion_html = wi["fields"].get("System.Description", "")
        criterios_html = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
        
        historias.append({
            "id": wid,
            "titulo": wi["fields"]["System.Title"],
            "url": wi["_links"]["html"]["href"],
            "descripcion": h.handle(descripcion_html),
            "aceptacion_criterios": h.handle(criterios_html)
        })
    
    return historias
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import StringIO

# Creamos dos variables constantes, una con el URL básico de la Wikipedia, ya que tendremos que usarlo cada vez, y otra
# constante con el UserAgent
BASE_URL = "https://en.wikipedia.org"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def get_soup(url):
    """Esta función recibe un url, descarga la información del url con requests, y devuelve un objeto soup."""
    try:
        # Usamos la función requests.get para hacer el llamado a la página, y usamos el UserAgent que tengamos definido
        # como constante al inicio del código (HEADERS) para evitar que nos bloqueen
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        # Al convertir el código bruto en soup, indicamos que use html.parser
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error al acceder a {url}: {e}")
        return None

def get_table(soup, posible_ids):
    """Esta función recibe un objeto soup, busca la tabla de líderes estadísticos (identificada con las cabeceras
    Statistics Leaders o Statistical Leaders), y la convierte en una tabla de Pandas antes de devolverla."""
    # Inicializamos la variable seccion como None
    seccion = None
    # Buscamos en la página la cabecera de la sección de líderes estadísticos
    for id_sec in posible_ids:
        seccion = soup.find(id=id_sec)
        # Si encuentra el elemento con el id actual, salimos del bucle
        if seccion: break
    # Si la variable seccion no esta vacía, significa que ha encontrado la cabecera. Una vez tenemos la cabecera, hay
    # que subir un nivel en la jerarquía para situarnos en el bloque que incluye la cabecera, y una vez allí, buscamos
    # el sibling siguiente, que, dada la estructura habitual de la wikipedia, sabemos que será la tabla que queremos
    if seccion:
        # Subimos un nivel en la jerarquía
        parent = seccion.find_parent()
        # Por si acaso, comprobamos que no nos ha devuelto un nulo
        if parent:
            # Buscamos el siguiente sibling, que será la tabla
            tabla_html = parent.find_next_sibling('table')
            # Por si acaso, comprobamos que no nos ha devuelto un nulo
            if tabla_html:
                # USAMOS StringIO para evitar el error de FileNotFound
                # Referencia: https://stackoverflow.com/questions/57173815/web-scraping-a-table-and-passing-it-to-a-pandas-dataframe
                html_string = str(tabla_html)
                df = pd.read_html(StringIO(html_string))[0]
                return df
    # Si la variable seccion está vacía, no ha encontrado el apartado que buscamos y devuelve un nulo
    return None

def main():
    # El primer paso es recibir del usuario el año cuyos datos quiere revisar. Para ello usaremos la función input()
    year = input("Por favor, introduce el año de la temporada que quieres revisar: ")
    # Comprobamos que el usuario introduce un número, si introduce un argumento inválido, como por ejemplo carácteres,
    # indicamos que hay un error
    try:
        # Convertimos el string recibido por defecto a integer para poder calcular el año anterior
        year_int = int(year)
        year_prev = year_int - 1
        # Dado que la wikipedia se refiere a cada temporada como 1990-89, guardamos los dos últimos números del año
        # recibido para poder trabajar con ello al indicar el url
        short_year = year[-2:]
        # Obtenemos el url
        url_season = f"{BASE_URL}/wiki/{year_prev}-{short_year}_NBA_season"
    except ValueError:
        print("Por favor, introduce un año válido.")
        return
    # Una vez tenemos el url de la temporada regular, vamos a obtener los datos de esta primero, y después los de
    # playoffs
    print(f"\nBuscando datos de temporada regular en: {url_season}")
    # Obtenemos el objeto soup mediante la función get_soup
    sopa_regular = get_soup(url_season)
    if sopa_regular:
        # Antes de obtener los datos y crear el csv, creamos la carpeta de resultados, si no esta creada ya
        carpeta_resultados = "Resultados"
        if not os.path.exists(carpeta_resultados):
            os.makedirs(carpeta_resultados)
        df_regular = get_table(sopa_regular, ["Statistics_leaders", "Statistical_leaders"])
        if df_regular is not None:
            print("\nLíderes de Temporada Regular:")
            print(df_regular.head())
            # Comprobamos si el archivo ya existe, si no, lo guardamos en la carpeta Resultados
            nombre_regular = os.path.join(carpeta_resultados, f"nba_{year}_regular_leaders.csv")
            if os.path.exists(nombre_regular):
                print(f"El archivo '{nombre_regular}' ya existe.")
            else:
                df_regular.to_csv(nombre_regular, index=False)
        else:
            print("No se encontró la tabla de estadísticas de la temporada regular.")
        # Buscamos el enlace que contenga el título de los Playoffs de ese año. Para ello, usaremos una función lambda
        # a la que pediremos que busque un título cuyo enlace contenga la frase: {year} nba playoffs. Si por ejemplo
        # estamos buscando la entrada con los datos de playoffs de 1989, buscará 1989 nba playoffs. Es más seguro que
        # buscar un string dentro de una cabecera, por ejemplo, porque puede que la cabecera no contenga el año
        # específico, pero el enlace sí.
        # Referencia: https://realpython.com/beautiful-soup-web-scraper-python/
        print("\nBuscando entrada con los datos de Playoffs")
        id_playoffs = sopa_regular.find('a', title=lambda t: t and f"{year} nba playoffs" in t.lower())
        # Una vez hemos encontrado el objeto que contiene el enlace, lo usamos para obtener el url a la entrada de
        # los datos de Playoffs
        if id_playoffs:
            url_playoffs = BASE_URL + id_playoffs.get('href')
            print(f"Enlace encontrado: {url_playoffs}")
            # Con el url de la página, repetimos el mismo proceso que con la web de la temporada regular
            sopa_playoffs = get_soup(url_playoffs)
            if sopa_playoffs:
                df_playoffs = get_table(sopa_playoffs, ["Statistical_leaders", "Statistics_leaders"])
                if df_playoffs is not None:
                    print("\nLíderes de Playoffs:")
                    print(df_playoffs.head())
                    nombre_playoffs = os.path.join(carpeta_resultados, f"nba_{year}_playoffs_leaders.csv")
                    if os.path.exists(nombre_playoffs):
                        print(f"El archivo '{nombre_playoffs}' ya existe.")
                    else:
                        df_playoffs.to_csv(nombre_playoffs, index=False)
                else:
                    print("No se encontró la tabla de estadísticas en la página de Playoffs.")
        else:
            print("No se pudo encontrar un enlace directo a los datos Playoffs en esta página.")
    print("\nProceso finalizado.")

if __name__ == "__main__":
    main()
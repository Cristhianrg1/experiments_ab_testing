# Ejercicio ABTesting Challenge

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Hipótesis y Asunciones](#hipótesis-y-asunciones)
4. [Interpretación de la Resolución](#interpretación-de-la-resolución)
5. [Instrucciones de Instalación y Uso](#instrucciones-de-instalación-y-uso)
6. [Consideraciones y Tradeoffs](#consideraciones-y-tradeoffs)
7. [URL de la API y Ejemplos](#url-de-la-api-y-ejemplos)

## Introducción

Este proyecto permite procesar y analizar datos de experimentos relacionados con compras de productos, expandiendo la información de los experimentos y etiquetando los eventos en función de si resultaron en una compra, posteriormente ejecuta validaciones y hace comparaciones para determinar la variante que mejor desempeño obtuvo dentro del experimento.

## Estructura del proyecto

- **Dockerfile:** Archivo de configuración para crear un contenedor Docker que incluya todas las dependencias necesarias para ejecutar el proyecto.
- **Pipfile:** Archivo utilizado por Pipenv para gestionar las dependencias del proyecto.
- **Pipfile.lock:** Archivo generado por Pipenv que congela las versiones de las dependencias instaladas.
- **README.md:** Documento principal que contiene la descripción del proyecto, instrucciones de instalación, uso y otra información relevante.
- **api:** 
  - **ab_testing_api.py:** Archivo que contiene la implementación de la API para realizar pruebas A/B.
- **data:**
  - **processed_data:** Carpeta destinada a almacenar los datos procesados.
  - **raw_data:** Carpeta destinada a almacenar los datos sin procesar.
    - **experiments_dataset.csv:** Archivo CSV con los datos crudos de los experimentos.
- **main.py:** Script principal para ejecutar la api.
- **modules:**
  - **ab_testing:**
    - **ab_test_analyzer.py:** Módulo para analizar los resultados de las pruebas A/B.
    - **ab_test_manager.py:** Módulo para gestionar las pruebas A/B.
    - **checks_processor.py:** Módulo para procesar los cheques de las pruebas.
  - **data_processing:**
    - **data_loader.py:** Módulo para cargar los datos.
    - **data_processor.py:** Módulo para procesar los datos.
  - **utils:**
    - **utils.py:** Módulo que contiene funciones utilitarias utilizadas en diferentes partes del proyecto.
- **notebooks:**
  - **data_cleaning.ipynb:** Notebook de Jupyter utilizado para la limpieza de datos.
  - **time_window_analysis.ipynb:** Notebook de Jupyter utilizado para el análisis de la ventana de tiempo.



## Hipótesis y Asunciones

- **Hipótesis 1:** Los eventos de productos que ocurren dentro de una ventana de tiempo de 4 horas tienen una correlación significativa con las compras.
- **Hipótesis 2:** Los eventos de búsqueda que ocurren dentro de una ventana de tiempo de 4 horas tienen una correlación significativa con las compras.
- **Asunción 1:** Los datos proporcionados en el dataset son precisos y representan correctamente los eventos y compras.
- **Asunción 2:** La ventana de tiempo de 4 horas es adecuada para capturar la relación entre los eventos y las compras.

## Interpretación de la Resolución

- Los resultados muestran qué eventos de productos y búsquedas están relacionados con compras dentro de una ventana de 4 horas.
- La columna `with_purchase` indica si un evento resultó en una compra (`True`) o no (`False`).
- Ejemplo: Un evento de producto con `with_purchase = True` significa que el producto fue comprado dentro de 4 horas después del evento.

## Instrucciones de Instalación y Uso

Este proyecto puede ser configurado y ejecutado de dos maneras: usando Pipenv o usando Docker.


### Requisitos Previos

- Python 3.x
- Git
- Docker

### Método 1 Instalación (Pipenv)

1. Clonar el respositorio
```bash
git clone https://github.com/Cristhianrg1/experiments_ab_testing.git
cd experiments_ab_testing
```

2. Instalar pipenv
```bash
pip install pipenv
```

3. Instalar dependencias
```bash
pipenv install
```

4. Activar entorno virtual
```bash
pipenv shell
```

5. Ejecutar el main.py
```bash
python main.py --port 5000
```
Nota: Se puede cambiar el puerto 5000 por cualquier otro puerto según la necesidad y disponibilidad.

### Método 2 Instalación (Docker)
Nota: Se debe asegurar que docker esté en ejecución.

1. Clonar el respositorio
```bash
git clone https://github.com/Cristhianrg1/experiments_ab_testing.git
cd experiments_ab_testing
```

2. Construir imagen
```bash
docker build -t <nombre-imagen> .
```

3. Ejecutar contenedor
```bash
docker run -it --rm -p 5000:5000 <nombre-imagen>
```
Nota: Se puede cambiar el puerto 5000 por cualquier otro puerto según la necesidad y disponibilidad.  
Ejemplo: `5001:5000` disponibiliza el puerto 5001 en el servidor local y se comunica con el puerto 5000 del contenedor.


### Ejemplo uso de la api

1. CURL
```bash
curl -X GET http://127.0.0.1:5000/experiment/filters%2Fsort-by-ranking/result

# Respuesta
{
  "results": {
    "filters/sort-by-ranking": {,
      "number_of_participants": 4972,
      "variants": [
        {
          "id": "7057",
          "number_of_purchases": 149
        },
        {
          "id": "6971",
          "number_of_purchases": 156
        },
        {
          "id": "6972",
          "number_of_purchases": 177
        }
      ],
      "winner": "6972"
    }
  }
}
```

2. Python

```python
import requests
from urllib.parse import quote

experiment_id = "filters/sort-by-ranking"
day = "2021-08-02 00"
encoded_experiment_id = quote(experiment_id, safe='')
url = f"http://127.0.0.1:5000/experiment/{encoded_experiment_id}/result"
params = {
    "day": day
}

response = requests.get(url, params=params)
response.json()
```









## Consideraciones

Los experimentos deberian ser medidos por tipo de evento, ya que si existe un mismo experimento en distintos tipos de eventos, estos pueden verse afectados por el enfoque general del experimento, es decir, se puede confundir el experimento implementado en distintas secciones de una página.


### Hipótesis
- Usuarios con mas cantidad de eventos previos, tienden a tener mejor conversión.
- Las mejores variantes tienen a tener menor tiempo entre la busqueda y la compra final.
- Clientes que ven multiples productos previamente tienen mayor tasa de conversión.


Los enlaces relativos, como [código](notebooks/time_window_analysis.ipynb)
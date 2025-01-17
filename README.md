# Ejercicio ABTesting Challenge

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Asunciones y Consideraciones](#asunciones-y-consideraciones)
4. [Checks aplicados](#checks-aplicados)
5. [Pruebas de hipótesis aplicadas](#pruebas-de-hipótesis-aplicadas)
6. [Resultados](#resultados)
7. [Hipótesis adicionales](#hipótesis-adicionales)
5. [Instrucciones de Instalación y Uso](#instrucciones-de-instalación-y-uso)
6. [Consideraciones y Tradeoffs](#consideraciones-y-tradeoffs)
7. [Documentación de la API](#docuemtación-de-la-api)
8. [Referecias](#referencias)

## Introducción

Este proyecto permite procesar y analizar datos de experimentos relacionados con compras de productos, expandiendo la información de los experimentos y etiquetando los eventos en función de si resultaron en una compra, posteriormente ejecuta validaciones y hace comparaciones para determinar la variante que mejor desempeño obtuvo dentro del experimento.

## Estructura del proyecto

- **Dockerfile:** Archivo de configuración para crear un contenedor Docker que incluya todas las dependencias necesarias para ejecutar el proyecto.
- **Pipfile:** Archivo utilizado por Pipenv para gestionar las dependencias del proyecto.
- **Pipfile.lock:** Archivo generado por Pipenv que congela las versiones de las dependencias instaladas.
- **README.md:** Documento principal que contiene la descripción del proyecto, instrucciones de instalación, uso y otra información relevante.
- **api:** 
  - **ab_testing_api.py:** Archivo que contiene la implementación de la API para realizar pruebas A/B.
- **config:**
  - **google_sa_template.json:** Plantilla del archivo de credenciales de servicio de Google, que puede ser utilizada como referencia para configurar credenciales.
- **data:**
  - **processed_data:** Carpeta destinada a almacenar los datos procesados.
  - **raw_data:** Carpeta destinada a almacenar los datos sin procesar.
    - **experiments_dataset.csv:** Archivo CSV con los datos crudos de los experimentos.
- **main.py:** Script principal para ejecutar la API o la lógica principal del proyecto.
- **modules:**
  - **ab_testing:**
    - **ab_test_analyzer.py:** Módulo para analizar los resultados de las pruebas A/B.
    - **ab_test_manager.py:** Módulo para gestionar las pruebas A/B.
    - **checks_processor.py:** Módulo para procesar los checks de las pruebas.
  - **data_processing:**
    - **data_loader.py:** Módulo para cargar los datos.
    - **data_processor.py:** Módulo para procesar los datos.
    - **sequential_data_processor.py:** Módulo especializado en procesar datos secuenciales.
  - **utils:**
    - **utils.py:** Módulo que contiene funciones utilitarias utilizadas en diferentes partes del proyecto.
- **notebooks:**
  - **challenge_level_1.ipynb:** Notebook de Jupyter utilizado para abordar el primer nivel del desafío técnico.
  - **hypotesis_testing.ipynb:** Notebook de Jupyter utilizado para realizar pruebas de hipótesis en los datos de los experimentos.
  - **tests.ipynb:** Notebook de Jupyter utilizado para probar diferentes partes del código y validar la lógica.
  - **time_window_analysis.ipynb:** Notebook de Jupyter utilizado para el análisis de la ventana de tiempo.


## Asunciones y Consideraciones

- **Asociación evento y compra:** 
  
  - Se hizo un análisis para determinar el tiempo que se debe considerar para asociar una compra con un evento, el resultado determinó que para un evento de `SEARCH` el tiempo que permite asociar la compra con dicho evento es un tiempo de 210 minutos y para los demas de 81 minutos. El análisis de baso en detemrinar el comportamiento de los tiempos y este valor etá dentro del rango percentil 75% y 95%. Esto permite eliminar los valores atípicos y tener un tiempo que ayude a recopilar los valores de ventas asociados a un experimento de mejor forma. [ver análisis.](notebooks/time_window_analysis.ipynb)


  - Se aplicó una lógica para los eventos relacionados a `SEARCH` ya que al ser eventos de busqueda no tienen una relación directa con un item_id, por lo tanto, para estos casos se asoció unicamente el user_id y que la fecha de compra fuera posterior al evento y que el rango de tiempo no fuera superior a los 210 minutos estipulados anteriormente.

  - En el caso de los eventos que si se cuenta con el item_id, se asocio con variables item_id, user_id y que el tiempo de la compra fuera superior a la fecha del evento, pero que no fuera superior a los 81 minutos que se determinaron. Aquí se asumió que al ser un experimennto directamente en un producto, para validar que si existió conversión se debe buscar la asociación con el mismo item_id.


- **Eventos de compra:**

  Teniendo en cuenta que debe existir una variable que permitiera identificar las compras, se tomó del dataset el evento `BUY` como el dataset de las compras por usuario.


- **Limpieza de duplicados:**

  - Para evitar que existieran usuarios duplicados en alguno de los experimentos+variante, lo que se hizo fue agrupar la información de forma que se contar la cantidad de veces que el usuario tuvo exposición al experimento y la cantidad de veces que terminaron en compras, esto permitó que la información no se duplicara ni se inflara la cantidad de conversiones para que posteriormente fueran hechas las prubas de hipótesis.


- **No considerar variante DEFAULT:**

  - Habiendo hecho un análisis para evaluar si la variante `DEFAULT` se debía omitir, se concluye que en este caso es importante exlcuirla de los análisis. En principio se evaluó los experimentos en los que aparecía dicha variante, y en ninguno de ellos los experimentos cumplian con los tamaños de muestra adecuados, al removerla, dos de ellos tuvieron un tamaños de muestra adecuados para ralizar los test de hipétesis. Aunque tan solo dos grupos fueros los que cambiaron, se puedo evaluar por otro lado que su efecto al retirarla era mínimo al evaluar si el winner_id era o no diferente cuando se mantenía o se quitaba, por lo que en este caso era ideal excluirla. [ver análisis.](notebooks/challenge_level_1.ipynb)


## Checks aplicados

- **Tamaños de los segmentos:**

  Se aplicó un check que permitiera identificar si el tamaño de las muestras para cada variante era el adecuedo y que con esto se cumpliera uno de los supuestos que luego permitirían deeterminar con una prueba de hipótesis si el resultado era significativo.


- **Independencia de usuarios en las variantes:**

  - Se aplicó un check que permitira identificar si dentro del mismo experimento el usuario estaba en dos variantes, en principio se podría pensar en invalidar el experimento, pero para evitar esto, es posible aplicar una serie de técnicas que podrían ayudar a dar validez al experimento:
    
    - Análisis de Sensibilidad: Realizar un análisis de sensibilidad para comparar los resultados con y sin los usuarios duplicados. Esto te permitirá entender el impacto de estos duplicados en los resultados del experimento.
    - Ponderación: Aplica técnicas estadísticas para ajustar los resultados teniendo en cuenta los usuarios que participaron en más de una variante. Una técnica podría ser ponderar menos a los usuarios que participaron en varias variantes.
    - Asignación basada en máxima probabilidad: Usar un modelo predictivo para calcular la probabilidad de que el usuario perteneza a uno o a otra variante, de acuerdo a esta probabilidad, asignar el usuario a la variante más probable.




- **Exposición experimentos en distintos eventos:**

  - Este check busca validar si un experimento se está aplicando en distintos eventos/zonas de la plataforma, esto posteriormente podría ser evaluado para entender si el experimento tiene distintos impactos dependiendo a donde se aplique.


**Duplicidad de los usuarios en el experimento:**

  - No está directamente aplicado como check, pero se buscó dentro del código evitar que para el momento de la evalación del experimento el usuario se contara doble vez.


## Pruebas de hipótesis aplicadas

En el análisis de experimentos, se utilizó un enfoque mixto para probar la significancia estadística de las variantes en los experimentos:

- Prueba z-test para Experimentos con Dos Variantes:

  Como se menciona en el artículo "A/B testing: A systematic literature review" (Quin, Weyns, Galster, & Costa Silva, 2024), los métodos más comunes para la evaluación de A/B testing siguen siendo las pruebas de hipótesis clásicas. En este caso, al tratarse de un problema de proporcionalidad, se hizo uso de la prueba z-test, que es adecuada para comparar tasas de conversión entre dos variantes y determinar si la diferencia observada es estadísticamente significativa. Este enfoque está respaldado adicionalmente por Aslam (2024), quien discute la efectividad del Z-test clásico en el análisis de datos bien definidos, asegurando un control robusto del error Tipo I y la validez estadística en contextos donde los datos no presentan indeterminaciones significativas.

- Prueba chi-square para Experimentos con Más de Dos Variantes:

  Para experimentos con más de dos variantes, se utilizó la prueba de independencia chi-square. Esta prueba es útil para determinar si hay diferencias significativas en las tasas de conversión entre todas las variantes de un experimento. Sin embargo, la prueba chi-square solo indica si existe alguna diferencia significativa entre las variantes, pero no especifica cuáles variantes son significativamente diferentes entre sí.

  Para resolver esto, se realizó una prueba post-hoc en la que se compararon las variantes de forma pareada, haciendo las combinaciones y evaluando para cada par el z-test. Luego, se aplicó una corrección para múltiples pruebas utilizando el método Bonferroni, lo que permitió hacer ajustes y evitar errores de tipo I, asegurando así que las conclusiones fueran estadísticamente válidas (Vickerstaff, Omar, & Ambler, 2019).

  Este enfoque está respaldado por García-Pérez (2023), quien discute la importancia de aplicar correcciones como Bonferroni para controlar la tasa de error de tipo I en escenarios de múltiples pruebas, como en análisis post-hoc tras una prueba chi-square. Además, Shan y Gerstenberger (2017) proponen un enfoque exacto para el análisis post-hoc después de una prueba chi-square, subrayando la necesidad de métodos robustos para garantizar la validez estadística, incluso en estudios con gran cantidad de datos. Estos métodos aseguran que el riesgo de identificar falsos positivos se mantenga bajo control, garantizando la validez de las comparaciones entre variantes.


## Resultados

Al realizar el procesamiento de datos y testeo de los experimentos se pueden evidenciar los siguientes puntos:

  - Existen experimentos que solo cuentan con una variante, por lo que puede ser un problema de asignación de usuarios a las variantes que están dentro del experimento.
  - Experimentos con mas de una variante, normalmente no cumplen con los tamaños de muestra adecuados y adicional a esto sus significancias estadísticas tampoco indican que hayan variante mejores a otras. Esto indica que hay un problema en el desarrollo e implementación de experimentos con mas de una variante, tanto en la selección como en el enfoque y lo que se busca probar.
  - Por el contrario, con experimentos con dos variantes les fue posible identificar el ganador y su significancia estadística en algunos de los experimentos, pero aún asi, se pueden evidenciar problemas en la seleccion de muestras porque varios de los experimentos de dos variables también contaban con tamaños innadecuados.
  - La variante DEFAULT fue eliminada de los experimentos por lo que se evideció que no tenía efecto positivo dentro de los análisis y/o decisiones de los experimentos.
  - Se deben implementar checks a la hora de asignar usuarios en los experimentos, dentro de los análisis hechos, se pudo notar quee existen experimentos en donde un mismo usuario podía etar asignado a dos variantes, y esto de cierta forma desahbilita la veracidad de los resultados.


## Hipótesis adicionales

- **Hipótesis 1:** Estar expuesto a múltiples experimentos afecta la conversión.
- **Hipótesis 2:** Los usuarios expuestos a un mayor número de experimentos muestran una disminución en la tasa de conversión.
- **Hipótesis 3:** Efectos de una variante puede verse afectada por la hora del día.
- **Hipótesis 4:** Los eventos de búsqueda que ocurren dentro de una ventana de tiempo de 4 horas tienen una correlación significativa con las compras.
- **Hipótesis 5:** Hay menos conversión posterior a la primera exposición del experimento.
- **Hipótesis 6:** El historial previo y reciente en eventos afecta la conversión.
- **Hipótesis 7:** La conversión puede verse afectada si un cliente previamente hizo una compra.
- **Variante DEFAULT afecta los resultados:** La variante DEFAULT no se debería tener en cuenta


## Resultados hipótesis adicionales

WIP

## Interpretación de la Resolución

- Los resultados muestran qué eventos de productos y búsquedas están relacionados con compras dentro de una ventana de 4 horas.
- La columna `with_purchase` indica si un evento resultó en una compra (`True`) o no (`False`).
- Ejemplo: Un evento de producto con `with_purchase = True` significa que el producto fue comprado dentro de 4 horas después del evento.

## Instrucciones de Instalación y Uso

Este proyecto puede ser configurado y ejecutado de dos maneras: usando Pipenv o usando Docker.


### Requisitos Previos

- Python
- Git
- Docker

### Configurar entorno

1. Clonar el respositorio
```bash
git clone https://github.com/Cristhianrg1/experiments_ab_testing.git
cd experiments_ab_testing
```

2. Crear archivo `.env` luego copia y pega el siguiente contenido:
  ```bash
  EXPERIMENTS_FILE_PATH="data/experiments_dataset.csv"
  GOOGLE_APPLICATION_CREDENTIALS="config/google_sa.json"
  BUCKET_NAME=ab_testing_challenge_bucket
  EXPERIMENTS_FILE_NAME=experiments_dataset.csv
  ENV=local
  ```

3. Configurar credenciales de google
  
  - Solicitar credenciales: compartiré un archivo `google_sa.json`.
  - Guardar las credenciales: guardar el archivo en la carpeta `config` en la raíz del proyecto. Mantener el mismo nombre.
  ```bash
  config/google_sa.json
  ```

### Método 1 Instalación (Pipenv)

1. Instalar pipenv
```bash
pip install pipenv
```

2. Instalar dependencias
```bash
pipenv install
```

3. Activar entorno virtual
```bash
pipenv shell
```

4. Ejecutar el main.py
```bash
python main.py --port 5000
```
Nota: Se puede cambiar el puerto 5000 por cualquier otro puerto según la necesidad y disponibilidad.

### Método 2 Instalación (Docker)
Nota: Se debe asegurar que docker esté en ejecución.

1. Construir imagen
```bash
docker build -t <nombre-imagen> .
```

2. Ejecutar contenedor
```bash
docker run -it --rm -p 8080:8080 <nombre-imagen>
```
Nota: Se puede cambiar el puerto 8080 por cualquier otro puerto según la necesidad y disponibilidad.  
Ejemplo: `5001:5000` disponibiliza el puerto 5001 en el servidor local y se comunica con el puerto 8080 del contenedor.


### Ejemplo uso de la api 

- #### Local

1. CURL
```bash
curl -X  GET 'http://127.0.0.1:8080/experiment/filters%2Fsort-by-ranking/result?day=2021-08-02+00'
```

2. Python

```python
import requests
from urllib.parse import quote

experiment_id = "filters/sort-by-ranking"
day = "2021-08-02 00"
encoded_experiment_id = quote(experiment_id, safe='')
url = f"http://127.0.0.1:8080/experiment/{encoded_experiment_id}/result"
params = {
    "day": day
}

response = requests.get(url, params=params)
response.json()
```


- #### Hosteada

Para consultar el servicio es importante tener las credenciales compartidas, como se mencionó en [la configuración del entorno](#configurar-entorno), donde se creo una variable de entorno y se guardó el archivo con el nombre google_sa.json, estas credenciales permitirán hacer uso de la API.

```python
import os
import requests
from urllib.parse import quote

from google.auth.transport.requests import Request
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
URL = 'https://ab-test-api-gfeygdcx7a-uc.a.run.app'

credentials = service_account.IDTokenCredentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    target_audience=URL
)
credentials.refresh(Request())
token = credentials.token

experiment_id = "filters/sort-by-ranking"
day = "2021-08-02 00"
encoded_experiment_id = quote(experiment_id, safe='')
headers = {"Authorization": f"Bearer {token}"}
url = f"https://ab-test-api-gfeygdcx7a-uc.a.run.app/experiment/{encoded_experiment_id}/result"
params = {
    "day": day
}

response = requests.get(url, params=params, headers=headers)
response.json()
```

- #### Respuesta
```bash
{
  'results': {
    'filters/sort-by-ranking': {
      'checks': {
        'experiment_independence': True,
        'normal_approximation': True,
        'num_of_variants': 3,
        'sample_size_adequacy': {'6971': True, '6972': True, '7057': True},
        'user_independence': False
      },
    'number_of_participants': 5629,
    'statistical_tests': {
          'chi_square': {
            'chi2': 2.549391302369261,
            'p_value': 0.2795160256484701,
            'significant_difference': False
          }
      },
    'variants': [
        {'id': '6971', 'number_of_purchases': 159},
        {'id': '6972', 'number_of_purchases': 173},
        {'id': '7057', 'number_of_purchases': 146}
      ],
    'winner': '6972'
    }
  }
}
```

### Consideraciones y tradeoffs

Con el desarrollo de esta prueba, se pudo evidenciar que aún cuando el dataset no es de un tamaño sobredimensionado, es necesario implementar algunas mejoras dentro del proceso, son las siguientes:

-  El flujo de datos puede mejorar, en esta implementación se consulta todo el dataset, se procesan todos los datos para que posteriormente se apliquen las pruebas, teniendo en cuenta esto, se pueden crear flujos de trabajo separados que hagan esto, por ejemplo, un proceso de datos que diariamente haga el procesamiento de datos y los almacene dentro de una herrmienta adecuada, otro proceso que tome diariamente estos datos y calcule las pruebas de hipótesis para que posteriormente las almacene en una base de datos, y por último el end point que en este caso ya solo se tiene que encargar de ir a consultar las pruebas de hipótesis ejecutadas y traer la que el usuario solicitó. Creo que esta estructura puede mejorar el rendimiento de la API.

- Utilizar tecnologías basadas en la nube, en mi caso usé Google Cloud Storage para almacenar el archivo .CSV, pero asi mismo se pueden utilizar herramientas para almancenar cada uno de los pasos, una parte podría ser en BigQuery y los reultados de los test directamente en una base de datos no relacional, que permitan que la API sea mas eficiente.

- Implementación o preprocesamiento de los datos usando procesamiento distribuido, como lo puede hacer Spark.

- Mantener la API en un sistema como por ejemplo Cloud RUN, que permite montar la API teniendo creado el contenedor de Docker, y a su vez ayuda a escalar de mejor manera dicha API.

- Se deberia evaluar el impacto económico que generan estas soliciones y comparar vs los costos que pueden llegar a tener el implementar nuevas herramientas y uso de servicios en la nube, esto permitiría comparar si realmente es beneficioso.

### Referencias

- Quin, F., Weyns, D., Galster, M., & Costa Silva, C. (2024). "A/B testing: A systematic literature review". *Journal of Systems and Software*. https://doi.org/10.1016/j.jss.2024.112011
- García-Pérez, M. A. (2023). "Use and misuse of corrections for multiple testing". *Methods in Psychology, 8*, 100120. https://doi.org/10.1016/j.metip.2023.100120
- Shan, G., & Gerstenberger, S. (2017). Fisher’s exact approach for post hoc analysis of a chi-squared test. PLOS ONE, 12(12), e0188709. https://doi.org/10.1371/journal.pone.0188709
- Vickerstaff, V., Omar, R. Z., & Ambler, G. (2019). "Methods to adjust for multiple comparisons in the analysis and sample size calculation of randomised controlled trials with multiple primary outcomes". *BMC Medical Research Methodology*. https://bmcmedresmethodol.biomedcentral.com/articles/10.1186/s12874-019-0754-4
- Aslam, M. (2024). Analysis of imprecise measurement data utilizing Z-test for correlation. Journal of Big Data, 11(4), 1-10. https://doi.org/10.1186/s40537-023-00873-7

# Seleccion-alumnos-pizarra

Herramienta para seleccionar alumnos a salir a la pizarra de forma aleatoria.
Está motivada por un curso en que cada estudiante declara que hizo ciertas preguntas entre un set de varias... y comúnmente se asume que la hizo, sin embargo, el día de la evaluación, puede ser llevado/a a la pizarra a mostrar su resolución en caso de haberla declarado como hecha.
Esta herramienta apunta a ser un ejercicio de programación, pero también podría servir para facilitar la partición de estudiantes en varios grupos y también la selección aleatorizada para hacer su pregunta.

La implementación se encuentra hecha en una clase `StudentPicker`.
Al ejecutar el script, debería procesarse la entrada y generar un reporte con los resultados.
La herramienta tiene más de un método para particionar y asignar problemas. Los dos métodos mejor desarrollados son
`shuffled_scored_partitioner` y `question_assignment`, para particionar el conjunto de estudiantes y para asignar una pregunta a cada estudiante de una partición.

Actualmente, ejecutar el script usa estos parámetros:
```
    questions_scores = [1,2,2,1,1]
    questions_names  = ["P1a","P1b","P2","P3a","P3b"]
    # p1a : 1
    # p1b : 2
    # p2  : 2
    # p3a : 1
    # p3b : 1

    students_answers = {               #hot encoding
        "pedro"       :[1,1,1,1,0],
        "juan"        :[0,1,1,1,0], 
        "diego"       :[0,0,1,1,0],
        "jaime"       :[0,0,0,1,0],
        "francisco"   :[1,1,1,1,1],
        "matias"      :[0,1,1,1,0],
        "camila"      :[0,1,1,1,0],
        "alonso"      :[0,1,1,1,0],
        "natacha"     :[1,1,1,1,0],
        "maya"        :[1,1,1,1,0],
    }
    
```



**TODO**: Programar una clase para que absorba una tabla de google forms.
#### ideas:
  - Podría darse acceso a una sesión de google con tokens y usar las librerías `ezsheets`, `google-api-python-client`, `google-auth-httplib2` y `google-auth-oauthlib`
  - Alternativamente, podría programarse para que consuma una tabla en `.csv`.
  - Idealmente, la tabla debería:
      - tener los nombres de la preguntas en los encabezados.
      - representar a cada alumno como una fila.
      - el valor de una (fila,columna) debería ser `1` si la completó, y `0` si no.

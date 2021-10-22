# Seleccion-alumnos-pizarra

Herramienta para seleccionar alumnos a salir a la pizarra de forma aleatoria
Está motivada por un curso en que cada alumno declara que hizo ciertas preguntas entre varias, y comúnmente asumimos que la hizo, sin embargo, el día de la evaluación, puede ser llamado a la pizarra a mostrar su resolución en caso de haberla declarado como hecha.

La implementación se encuentra hecha en una clase `StudentPicker`.
Al ejecutar el script, debería procesarse la entrada y generar un reporte con los resultados.

Actualmente usa estos parámetros:
```
    questions_scores = [1,2,2,1,1]
    questions_names  = ["P1a","P1b","P2","P3a","P3b"]
    # p1a : 1
    # p1b : 2
    # p2  : 2
    # p3a : 2
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
  - Podría darse acceso a una sesión de google con tokens y usar las librerías `ezsheets, google-api-python-client, google-auth-httplib2, google-auth-oauthlib`
  - Alternativamente, podría programarse para que consuma una tabla en `.csv`.
  - Idealmente, la tabla debería:
      - tener los nombres de la preguntas en los encabezados.
      - representar a cada alumno como una fila.
      - el valor de una (fila,columna) debería ser `1` si la completó, y `0` si no.

import re
import pandas as pd
import csv

from .google_utilities import google_sheets_worker
from .globals_records import record_id, column_mapping, model_mapping

# Seteo de variables
records_file = "registros.csv"


# Lectura y verificación de los registros
def read_records():
    """
    Lee el archivo de registros 'registros.csv' y válida las columnas 'registro' e 'id'.
    Devuelve un diccionario con listas de registros válidos, ids de hojas de cálculo y errores encontrados.
    """

    # Creando listas para las columnas
    records = []
    ids_sheet = []
    error = []

    # Expresiones regulares para validar las columnas
    regex_col1 = r'^[a-zA-Z0-9]{1,5}$'
    regex_col2 = r'^.{44}$'

    # Lectura del archivo de registros usando Pandas
    try:
        df = pd.read_csv('registros.csv')
    except FileNotFoundError:
        print("El archivo 'registros.csv' no se encuentra.")
        return

    # Validación de columnas
    for i, row in df.iterrows():
        registro_control = row['registro']
        id_sheet_control = row['id']

        if not re.match(regex_col1, registro_control):
            error.append(f"\nIrregularidad en fila {i+2} del archivo de registros: "
                           "Formato no válido en la columna 'registro'\n"
                           "Soluciona el problema para continuar\n")
        else:
            records.append(registro_control)

        if not re.match(regex_col2, id_sheet_control):
            error.append(f"\nIrregularidad en fila {i+2} del archivo de registros: "
                           "Formato no válido en la columna 'id'\n"
                           "Soluciona el problema para continuar\n")
        else:
            ids_sheet.append(id_sheet_control)

    if not records:
        print('No existen registros para trabajar, agrega uno para continuar')
        edit_records()

    else:
        # Valores a devolver
        result = {
            'registros': records,
            'ids_sheet': ids_sheet,
            'errores': error
        }
        return result


def verify_existing_record(record_name):
    # Verifica si el registro ya existe en el archivo
    with open(records_file, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == record_name:
                return True
    return False


# Agregar nuevos registros al archivo
def edit_records():
    """
    Una función para editar registros. Pide al usuario que introduzca el nombre de un registro (hasta 5 letras o números), o 'cancelar' para salir.
    Valida el nombre del registro, comprueba si ya existe, añade el registro a un archivo utilizando la biblioteca csv e imprime un mensaje de éxito.
    """
    while True:
        # Consulta el nombre del registro
        record_name = input(
            "Ingresa el nombre del registro (máximo 5 letras o números), o escribe 'cancelar' para salir: ").upper()

        if record_name.lower() == "cancelar":
            print("Proceso de edición de registros cancelado.")
            break

        # Validación del nombre del registro
        if re.match(r'^[a-zA-Z0-9]{1,5}$', record_name):
            # Verifica si el registro ya existe
            if verify_existing_record(record_name):
                print(f"El registro '{record_name}' ya existe en el archivo.")
                continue

            # Agrega los valores al archivo de registros utilizando la biblioteca csv
            with open(records_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([record_name, record_id])

            print(f"Registro '{record_name}' agregado correctamente.")
            raise SystemExit
        else:
            print("Nombre de registro no válido. Inténtalo nuevamente.")


# Buscar contraseña
def get_passwords_for_reconfigured_devices(start: int, end: int, sheet_id: str) -> list:
    # Leer el archivo CSV
    df_serie_a = pd.read_csv('Registros_viejos_serie_A.csv')
    df_serie_c = pd.read_csv('Registros_viejos_serie_C.csv')

    # Crear una lista vacía para almacenar los resultados
    devices_data = []

    # Obtener los modems a reconfigurar
    ont_to_congif = google_sheets_worker(
        sheet_id=sheet_id,
        registro='Reconfigurados',
        column=column_mapping.get('Modem'),
        start=start,
        end=end,
        option='obtener'
    )

    for device in ont_to_congif:
        # Setear valores iniciales
        modem, model, access_password, random_password = None, None, None, None
        series, record, device_number = None, None, None

        try:
            modem = device[0].upper()
            series = modem[0]
            record = str(re.sub("\d","", modem))
            device_number = int(re.sub("\D","", modem))

        except AttributeError:
            print(f"El modem {device} no es válido. Por favor, ingrese un modem valido.")

        # Seleccionar el DataFrame adecuado según la serie especificada
        if series == 'A':
            is_series_c_or_f = False
            df = df_serie_a

        elif series == 'C':
            is_series_c_or_f = True
            df = df_serie_c

        elif series == 'F':
            is_series_c_or_f = True

            # Obtiene los valores desde sheets
            modem, model, access_password, random_password = google_sheets_worker(
                sheet_id=sheet_id,
                registro=record,
                start= device_number,
                option='iterar'
            )

            # Obtiene el valor correspondiente a la clave del modelo
            for key in model_mapping.keys():
                if key in str(model):
                    model = model_mapping[key][0]
                    break
            else:
                print('Error: No se encontró una clave válida en el output')
                continue

        else:
            raise ValueError("Serie no válida.")

        if series in ('A', 'C'):
            # Filtrar el DataFrame por el valor de la columna "NUMERO"
            filtro = df['NUMERO'].str.casefold() == modem.casefold()
            resultados = df.loc[filtro]

            if series == 'A':
                # Verificar si se encontraron resultados y mostrar la contraseña correspondiente
                if not resultados.empty:
                    modem = resultados.iloc[0]['NUMERO']
                    access_password = resultados.iloc[0]['CONTRASEÑA']
                    random_password = resultados.iloc[0]['RANDOM_PASSWORD']

                else:
                    print("No se encontró ninguna contraseña para el modem ingresado.")

            elif series == 'C':
                # Verificar si se encontraron resultados y mostrar la contraseña correspondiente
                if not resultados.empty:
                    modem = resultados.iloc[0]['NUMERO']
                    access_password = resultados.iloc[0]['CONTRASEÑA']
                    model_value = resultados.iloc[0]['MODELO']

                    if pd.isna(model_value):
                        print("No se encontró un modelo para el modem ingresado.")
                    else:
                        model = int(str(model_value).replace(',', ''))

                        # Obtiene el valor correspondiente a la clave del modelo
                        for key in model_mapping.keys():
                            if key in str(model):
                                model = model_mapping[key][0]
                                break
                        else:
                            print('Error: No se encontró una clave válida en el output')
                            continue

                else:
                    print("No se encontró ninguna contraseña para el modem ingresado.")

        devices_data.append((is_series_c_or_f, modem, record, device_number, model, access_password, random_password if random_password else None))

    return devices_data

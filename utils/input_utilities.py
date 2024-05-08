from .record_utilities import edit_records
from subprocess import Popen

# Obtiene la cantidad de dispositivos a realizar
def number_of_devices() -> int:
    # Setear archivos para el usuario
    archivo_ayuda = "ayuda.html"

    while True:
        # Configurar cantidad de dispositivos
        repetitions = input("¿Cuántas veces deseas repetirlo?: ")

        # Proceso para ingresar a los registros
        if repetitions.casefold() == "administrar":
            edit_records()

        # Proceso para recibir ayuda
        elif repetitions.casefold() == "ayuda":
            try:
                Popen(["start", archivo_ayuda], shell=True)
            except FileNotFoundError:
                print("No se pudo encontrar un visor de HTML adecuado en tu sistema.")
            except Exception as e:
                print(f"Se produjo un error: {e}")

        # Proceso convencional
        else:
            try:
                repetitions = int(repetitions)
                if repetitions == 0:
                    print("Por favor, ingresa un número válido para la cantidad de repeticiones.")
                elif repetitions > 0:
                    return repetitions
                else:
                    print("La cantidad debe ser un número positivo.")
            except ValueError:
                print("Por favor, ingresa un número válido para la cantidad de repeticiones.")


# Declarar el registro a utilizar
def set_record(registros_dict: dict) -> tuple:
    while True:
        # Verificar si el registro existe
        record = input(f"¿Qué registro usar? {'/'.join(registros_dict.keys())}: ").upper()

        if record in registros_dict:
            # El usuario ingresó una llave válida
            sheet_id = registros_dict[record]
            print(f"Se va a trabajar con el registro: {record}")

            return (record, sheet_id)

        else:
            # El usuario ingresó una llave no válida
            print(f"El registro {record} no es válido. Por favor, ingresa uno válido.")


# Declarar el primer modem
def set_first_modem(is_reconfigured: bool = False) -> int:
    # Obtención de número inicial y determinación del rango en google sheets
    if is_reconfigured == True:
        in_message = "¿Cuál es el la linea del modem inicial?: "
    else:
        in_message = "¿Cuál es el número del modem inicial?: "

    while True:
        try:
            first_modem = int(input(in_message))

            if first_modem <= 0:
                print("Por favor, ingresa un número positivo para el número inicial del modem.")
            else:
                break  # Sale del bucle si se ingresó un número válido positivo

        except ValueError:
            print("Por favor, ingresa un número válido para el número inicial del modem.")

    return first_modem


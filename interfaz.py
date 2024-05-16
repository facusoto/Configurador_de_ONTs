# Imports comunes
import psutil

# Importar funciones externas
from device_configurator import device_configurator
from utils.globals_records import record_id, column_mapping
from utils.google_utilities import google_sheets_worker
from utils.input_utilities import number_of_devices, set_record, set_first_modem
from utils.record_utilities import read_records, get_passwords_for_reconfigured_devices
from utils.ssh_utilities import verify_model


# Realizar preguntas y setear intervalos
def configurar_marco_trabajo(registros_dict: dict):

    # Mensajes de bienvenida
    print('\n.:: Bienvenido al Generador de ONTs ::.')
    print("Escribe 'administrar' para abrir el registro, 'ayuda' para ver el manual de Usuario o simplemente continúa el proceso\n")

    # Obtiene la cantidad de modems a realizar
    # Además sirve para obtener ayuda y configurar los registros
    amount: int = number_of_devices()

    # Identifica si es un modem a reconfigurar
    while True:
        try:
            is_reconfigured = int(input("¿Deseas reconfigurar un módem existente?: (1 = Si, 0 = No): "))
            if is_reconfigured not in (0, 1):
                raise ValueError("Por favor, introduce una opción válida (0 o 1)")
            break

        except ValueError:
            print("Por favor, introduce una opción válida (0 o 1)")
            continue

    # Reconfiguración de modems
    if is_reconfigured:
        first_modem: int = set_first_modem(is_reconfigured=True)

        # Determinar el rango en Google Sheets
        # No se suma la línea de encabezado a 'start' para la busqueda
        start: int = first_modem
        end: int = (first_modem + amount)

        modems_to_reconfigure: list = get_passwords_for_reconfigured_devices(start, end, record_id)

        # Proceso de reconfiguración
        for item in modems_to_reconfigure:

            # Obtiene la información del módem
            is_series_c_or_f = item[0]
            device_name = item[1]
            record = item[2]
            device_number = item[3]
            model = item[4]
            access_password = item[5]
            reconfigured_previous_password = item[6]

            # Verificar modelo si pertenece a la serie A
            # Este registro no contiene modelos, se utiliza la función de verificación de modelo
            if not is_series_c_or_f:
                model = verify_model(password=access_password)

            # Función configuradora de modems
            device_configurator(
                sheet_id=record_id,
                device_number=device_number,
                access_password=access_password,
                record=record,
                modem_index=start,
                model=model,
                existing_randomly_password=reconfigured_previous_password,
                is_reconfigured=True
            )

            start += 1
            input('Proceso completado. Cambia el cable del modem y presiona "Enter".\n------')


    # Configuración de modems nuevos (no reconfigurados)
    elif not is_reconfigured:
        # Obtiene el registro a utilizar
        record, sheet_id = set_record(registros_dict)

        # Obtiene el modem inicial
        first_modem = set_first_modem(is_reconfigured=False)

        # Se determina el rango en Google sheets
        start: int = (first_modem + 1)
        end: int = (first_modem + amount)

        # Obtiene la lista de contraseñas desde sheets
        device_password_list: list = google_sheets_worker(
            sheet_id=sheet_id,
            registro=record,
            column=column_mapping.get('ONT_password'),
            start=start,
            end=end,
            option='obtener'  # Obtener contraseñas
        )

        # Mensaje de inicio del proceso
        print(f"Buscando las contraseñas en el registro: {record}\n------")

        # Comprobar que la request contiene contraseñas
        if not device_password_list:
            print('El intervalo seleccionado está vacío, por favor ingresa las contraseñas en el registro')
            raise SystemExit  # Termina la ejecución del programa en caso de error

        else:
            # Mensaje de inicio del proceso
            print("Iniciando proceso de configuración de modems...\n------")

            for i in range(0, amount):
                try:
                    # Seteando los valores que se van a enviar a la función
                    access_password = device_password_list[i][0]
                    device_number = first_modem + i
                    model = verify_model(password=access_password)

                    # Función configuradora de modems
                    device_configurator(
                        sheet_id=sheet_id,
                        device_number=device_number,
                        access_password=access_password,
                        record=record,
                        model=model
                    )

                    # Mensaje para cuando se finaliza el proceso en cada modem.
                    input('Proceso completado. Cambia el cable del modem y presiona "Enter".\n------')

                except IndexError:
                    print('El intervalo está vacío. Ingresa la contraseña del modem en el registro.')
                    print("Proceso de configuración va a continuar, cambia el cable del modem y presiona 'Enter'")
                    continue
            else:
                # Mensaje de final de proceso
                print("¡Proceso de configuración concluido!")


# Ejecución final
def ejecutar_programa():
    # Busca todos los procesos en ejecución llamados "chromedriver.exe"
    for process in psutil.process_iter(attrs=['name']):
        if process.name() == 'chromedriver.exe':
            try:
                # Intenta terminar el proceso
                process.terminate()
            except Exception as e:
                print(f"No se pudo terminar el proceso: {str(e)}")

    # Llama a la función de lectura y verificación
    resultado = read_records()

    # Si encuentra errores los imprime, si no los encuentra ejecuta el programa
    if resultado['errores']:
        for error in resultado['errores']:
            print(error)
    else:
        # Creando un diccionario de los registros
        reg_dict = {clave: valor for clave, valor in zip(resultado['registros'], resultado['ids_sheet'])}

        # Función que hará el trabajo
        configurar_marco_trabajo(registros_dict=reg_dict)


if __name__ == "__main__":
    # Llama a la función para ejecutar el programa
    ejecutar_programa()

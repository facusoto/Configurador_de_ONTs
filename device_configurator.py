from datetime import datetime
from utils.company_info import company_name
from utils.globals_records import column_mapping
from utils.google_utilities import google_sheets_worker, update_cell
from utils.smart_olt_utilities import SmartOLT
# Importar las clases para configurar los modems
from device_configurators.askey_3505 import Init3505
from device_configurators.askey_8115 import Init8115
from device_configurators.askey_8225 import Init8225
from device_configurators.mitra_2541 import Init2541
from device_configurators.mitra_2741 import Init2741
from device_configurators.mitra_2742 import Init2742


# Variables
date = datetime.today().strftime('%d/%m/%Y')


def device_configurator(
        sheet_id: str,
        device_number: int,
        access_password: str,
        record: str,
        modem_index: int = None,
        model: int = None,
        existing_randomly_password: str = None,
        is_reconfigured: bool = False
    ):
    """
    Configure the ONT with the provided parameters.

    Parameters:
    - sheet_id (str): The ID of the Google Sheets document.
    - device_number (int): The device number.
    - access_password (str): The ONT password for accessing the configuration.
    - record (str): The registration information.
    - modem_index (int): The index of the modem in the list of reconfigured modems.
    - model (int): The model number.
    - existing_randomly_password (str): Randomly generated password found.
    - is_reconfigured (bool): Whether the device is being reconfigured.

    Returns:
    - None
    """


    # Funcion auxiliar para actualizar las celdas
    def update(record=record, column=None, sheet_id=sheet_id, device_number=device_number, output_data=None):
        # Cambia los valores del registro si se trata de un reconfigurado
        if is_reconfigured:
            record = 'Reconfigurados'
            device_number = modem_index

        update_cell(record, column, sheet_id, device_number, output_data)


    # Definir valores del módem
    record_number = f"{record.upper()}{device_number}"
    wifi_2g = record_number + f"_{company_name}"
    wifi_5g = record_number + f"_{company_name}_5Ghz"

    # Crear un diccionario para mapear modelos a sus detalles
    model_paramethers = {
        1: {"Modelo": "Askey 8115", "Wan service": record_number, "Clase": Init8115},
        2: {"Modelo": "Askey 8225", "Wan service": record_number, "Clase": Init8225},
        3: {"Modelo": "Askey 3505", "Wan service": record_number, "Clase": Init3505},
        4: {"Modelo": "Mitra 2541", "Wan service": record_number, "Clase": Init2541},
        5: {"Modelo": "Mitra 2741", "Wan service": record_number, "Clase": Init2741},
        6: {"Modelo": "Mitra 2742", "Wan service": record_number, "Clase": Init2742}
    }

    # Realizar el trabajo de acuerdo al modelo
    if model in model_paramethers:
        # Obtener los detalles del modelo
        model_details = model_paramethers[model]

        # Imprimir datos del módem
        if is_reconfigured:
            print("Almacenado en la línea:", modem_index)
        else:
            print("Número:", device_number)

        print("Contraseña:", access_password)
        print("Wifi 2g:", wifi_2g)
        print("Wifi 5g:", wifi_5g)

        # Imprimir valores relacionados con el modelo
        print(f"Modelo: {model_details['Modelo']}")
        print(f"Wan service: {model_details['Wan service']}")

        # Verifica si el modem es reconfigurado
        if is_reconfigured:
            # Verifica si hay una contraseña previa
            existing_randomly_password = existing_randomly_password
        else:
            try:
                check_existing = google_sheets_worker(
                    sheet_id=sheet_id,
                    registro=record,
                    column=column_mapping.get('generated_wifi_password'),
                    number=device_number,
                    option='verificar' # Verifica si hay una contraseña previa
                )

                existing_randomly_password = int(check_existing[0][0])

                if not (isinstance(existing_randomly_password, int) and 10 ** 7 <= existing_randomly_password <= 10 ** 8 - 1):
                    existing_randomly_password = None

            except (ValueError, IndexError, TypeError):
                existing_randomly_password = None

        # Crea una instancia de la clase correspondiente, ejecuta la configuración
        configurator = model_details["Clase"](device_number, access_password, model_details["Wan service"], wifi_2g, wifi_5g, existing_randomly_password)

        # Método para obtener los datos del modelo
        raw_data = configurator.get_data()

        # Verifica que el reultado no sea None, causas probables: Contraseña erronea.
        if raw_data is None:
            print("Proceso interrumpido: No se obtuvieron valores del módem.")
        else:
            # Separar los datos obtenidos en distintas variables
            sn, mac, rx_power = raw_data

            # Ejecutar el programa si la rx_power está dentro de un intervalo aceptable
            if rx_power:

                # Almacenar datos en Google Sheets
                # Agregar la información de ONT si es reconfigurado
                if is_reconfigured:
                    update(column=column_mapping.get('ONT_password'), output_data=[[access_password]])

                update(column=column_mapping.get('Fecha'), output_data=[[date]])
                update(column=column_mapping.get('Modelo'), output_data=[[model_details['Modelo']]])
                update(column=column_mapping.get('SN'), output_data=sn)
                update(column=column_mapping.get('MAC'), output_data=mac)

                # Continuar con la ejecución
                configurator.config_panel_access()

                if model == 4:
                    for i in range(2):
                        configurator.wan_test_value(bandera=i)
                else:
                    configurator.wan_test_value()

                # Verificar la conexión con la OLT
                OLT_worker = SmartOLT(sn[0][0], model, OLT=3)
                if OLT_worker.auth_ONT():
                    OLT_worker.check_internet_connection()

                # Continuar con la ejecución
                configurator.wan_official_value()
                configurator.multiple_configurations()
                wifi_password, generated_wifi_password = configurator.configure_wifi_2g()

                # Almacenar las contraseñas en Google Sheets
                update(column=column_mapping.get('wifi_password'), output_data=wifi_password)
                update(column=column_mapping.get('generated_wifi_password'), output_data=generated_wifi_password)

                # Configurar 5G y cambio de contraseña
                configurator.configure_wifi_5g()
                configurator.change_password()

                # Finalizar el proceso de Selenium tras finalizar
                configurator.kill()

            else:
                print("Proceso interrumpido: La potencia del modem es demasiado alta, por favor limpia el modem y vuelve a intentarlo.")
    else:
        print("Modelo no válido, ¿Cómo llegaste hasta acá?")

    # Final del proceso y alerta sonora
    print("------\007")
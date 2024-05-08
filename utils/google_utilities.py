from google.oauth2 import service_account
from googleapiclient.discovery import build
from .globals_records import column_mapping, alpha_to_num

# Variables para Google Sheets!
SAMPLE_SPREADSHEET_ID = None
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Obtener o verificar las contraseñas desde Google Sheets
def google_sheets_worker(
        sheet_id,
        registro,
        column: str = None,
        start: int = None,
        end: int = None,
        number: int = None,
        option: str = None
    ):
    """
    A function that works with Google Sheets get contents.
    """

    iterated_values = []
    try:
        if option == 'obtener':
            # Obtener contraseñas desde Google Sheets
            result_passes = sheet.values().get(spreadsheetId=sheet_id, range=f'{registro}!{column}{start}:{column}{end}').execute()
            passes_values = result_passes.get('values', [])

            if not passes_values:
                print('La celda está vacía en la hoja de cálculo para las contraseñas.')
                return None

            return passes_values

        elif option == 'verificar':
            # Verificar si existe una contraseña de WiFi previa
            result_prev_pass = sheet.values().get(spreadsheetId=sheet_id, range=f'{registro}!{column}{number + 1}').execute()
            prev_pass_values = result_prev_pass.get('values', [])

            if not prev_pass_values:
                print('No existe contraseña de WiFi previa, se generará una.')
                return None

            return prev_pass_values

        elif option == 'iterar':
            # Obtener todos los valores de la fila especificada
            result_row = sheet.values().get(spreadsheetId=sheet_id, range=f'{registro}!{start + 1}:{start + 1}').execute()
            row_values = result_row.get('values', [])

            if row_values:
                # Suponiendo que las columnas de interés son las primeras tres
                modem_value = row_values[0][alpha_to_num(column_mapping.get('Modem'))]
                model_value = row_values[0][alpha_to_num(column_mapping.get('Modelo'))]
                ont_password = row_values[0][alpha_to_num(column_mapping.get('ONT_password'))]
                generated_wifi_password = row_values[0][alpha_to_num(column_mapping.get('generated_wifi_password'))]

                if all((modem_value, model_value, ont_password, generated_wifi_password)):
                    # Agregar los valores a la lista de contraseñas
                    iterated_values.extend([modem_value, model_value, ont_password, generated_wifi_password])
                else:
                    print('Alguna de las celdas está vacía, por favor verifica la hoja de cálculo.')
                    return None
            else:
                print('La fila está vacía, por favor verifica la hoja de cálculo.')
                return None

            return iterated_values


    except Exception as e:
        print('Error al conectar al servidor de Google Sheets. Verifica tu conexión e intenta de nuevo.')
        print(e)
        raise SystemExit


# Google sheets, grabación de datos
def update_cell(record, column, sheet_id, number, output_data):

    # Limpiar la celda
    sheet.values().clear(
        spreadsheetId=sheet_id,
        range=f'{record}!{column}{number + 1}'
    ).execute()

    # Actualizar la celda
    sheet.values().update(
        spreadsheetId=sheet_id,
        range=f'{record}!{column}{number + 1}',
        valueInputOption="USER_ENTERED",
        body={"values": output_data}
    ).execute()
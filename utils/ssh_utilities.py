from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from re import search
from .record_utilities import model_mapping


def verify_model(password: str, command: str = 'show device_model'):
    # Define los parámetros de conexión SSH
    device = {
        'device_type': 'generic',
        'host': '192.168.1.1',
        'username': 'admin',
        'password': password,
    }

    while True:
        try:
            # Crea una conexión SSH
            connection = ConnectHandler(**device)
            output = ''

            # Ejecuta un comando en el dispositivo remoto
            try:
                output = connection.send_command(command)
            except NetmikoTimeoutException as e:
                # Verificar si la excepción realmente corresponde a un timeout
                if "Pattern not detected" in str(e):
                    # Manejar el caso específico de patrón no detectado
                    print("Patrón no detectado en la salida del dispositivo.")
                else:
                    # Manejar otros casos de timeout
                    print("Se ha producido un tiempo de espera en la conexión.")
                    # Puedes agregar más lógica según sea necesario para manejar otros casos de timeout
            except Exception as e:
                # Manejar otros tipos de excepciones
                output = connection.send_command(command, strip_prompt=False)

            for key in model_mapping.keys():
                if key in output:
                    output = model_mapping[key][0]
                    break
            else:
                print('Error: No se encontró una clave válida en el output')
                continue

            # Cierra la conexión
            connection.disconnect()

            return output

        except NetmikoTimeoutException:
            print("Error: no se pudo establecer la conexión SSH con el dispositivo.")
            continue

        except NetmikoAuthenticationException:
            print("Error: el usuario y la contraseña son incorrectos.")
            break


# Función para cambiar el SSID y contraseña
def wifi_config_ssh(ONT_password: str, access_password: str, ssid: str, plus: str = ''):
    # Define los parámetros de conexión SSH
    device = {
        'device_type': 'generic',
        'host': '192.168.1.1',
        'username': 'admin',
        'password': ONT_password,
    }

    while True:
        try:
            # Crea una conexión SSH
            connection = ConnectHandler(**device)

            #
            # Obtener la contraseña wifi
            #
            password = 'No se encontró la contraseña'

            if plus != "_plus":
                output = connection.send_command('show wifi')
                pattern = r'wifi password (.+)'
                resultado = search(pattern, output)
                if resultado:
                    password = resultado.group(1)
                    print('La contraseña es: ' + password)
                else:
                    print("No se encontró la contraseña en el texto.")

            #
            # Cambiar la SSID
            #
            connection.send_command(f'set wifi{plus} ssid {ssid}', read_timeout=60)
            connection.send_command('save')
            while True:
                verification = connection.send_command(f'show wifi{plus} ssid')
                print(f'Actual: {verification} - Esperado: {ssid}')
                if ssid in verification:
                    print("El SSID se ha cambiado correctamente.")
                    break
                else:
                    connection.send_command(f'set wifi{plus} ssid {ssid}')
                    print("El SSID no se ha podido cambiar.")

            #
            # Cambiar la contraseña
            #
            connection.send_command(f'set wifi{plus} password {access_password}')
            connection.send_command('save')
            while True:
                verification = connection.send_command(f'show wifi{plus} password')
                print(f'Actual: {verification} - Esperado: {access_password}')
                if access_password in verification:
                    print("La contraseña se ha cambiado correctamente.")
                    break
                else:
                    connection.send_command(f'set wifi{plus} password {access_password}')
                    print("La contraseña no se ha podido cambiar.")

            #
            # Setear el Channel y la autenticación
            #
            connection.send_command(f'set wifi{plus} channel {60 if plus == "_plus" else 1}', read_timeout=60)
            connection.send_command(f'set wifi{plus} authentication wpa2-psk', read_timeout=60)
            connection.send_command('save')

            # Cierra la conexión
            connection.disconnect()

            return password

        except NetmikoTimeoutException:
            print("Error: no se pudo establecer la conexión SSH con el dispositivo.")
            continue
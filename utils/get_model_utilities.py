import re
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
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

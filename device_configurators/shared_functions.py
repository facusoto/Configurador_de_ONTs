from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, ReadTimeout
from re import search

#  Setear la contrasena del modem
designed_ONT_password = 'Rr2023Fa'


#  Obtener la Gpon y MAC
def get_gpon_and_mac(gpon: str, mac: str) -> list:
    """
    Función que toma una cadena que representa una GPON y una dirección MAC,
    Elimina caracteres específicos de la cadena GPON y la formatea en función de determinadas condiciones,
    Elimina caracteres específicos de la MAC y devuelve una lista con las direcciones GPON y MAC modificadas.
    """

    # Elimina los '-' del texto de la Gpon
    gpon = f"{gpon.upper().replace('-', '')}"

    # Formatea las cadenas de texto de manera más clara
    if "46414D41" in gpon:
        gpon = [[f"{gpon.replace('46414D41', 'FAMA')}"]]
    elif "41534B59" in gpon:
        gpon = [[f"{gpon.replace('41534B59', 'ASKY')}"]]
    elif "4D535443" in gpon:
        gpon = [[f"{gpon.replace('4D535443', 'MSTC')}"]]
    else:
        raise ValueError('Error')

    # Elimina los ':' del texto de la MAC
    mac = [[f"{mac.upper().replace(':', '')}"]]

    return [gpon, mac]


#  Realiza la prueba de la rx_power
def rx_power_report(rx_power: int):

    """
    Una función para informar sobre el nivel de potencia de un módem.

    Args:
        rx_power (int): El nivel de rx_power del módem.

    Returns:
        None
    """

    if rx_power == 0:
        print("¡Modem sin potencia, límpialo o revisa la conexión!")
    else:
        # Evalúa y muestra el estado de la potencia
        if rx_power >= 245:
            potencia_msg = "Mala potencia"
        elif 220 < rx_power < 245:
            potencia_msg = "Buena potencia"
        elif 160 <= rx_power <= 220:
            potencia_msg = "Excelente potencia"
        else:
            potencia_msg = "Potencia desconocida"

        # Imprime el mensaje de potencia
        print(f"Potencia: {rx_power} - {potencia_msg}")
        # Se imprime que se obtuvieron los datos solo si pasa la prueba de la potencia
        print("¡Datos de modem obtenidos!")


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

if __name__ == "__main__":
    wifi_config_ssh(ONT_password='4FbwHbQy', access_password='263553213213352', ssid='para_probar')
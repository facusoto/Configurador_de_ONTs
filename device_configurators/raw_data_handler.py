#  Obtener la Gpon y MAC en el formato adecuado
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


def rx_power_report(rx_power: int) -> bool:
    """
    Una función para informar sobre el nivel de potencia de un módem.

    Args:
        rx_power (int): El nivel de rx_power del módem.

    Returns:
        Boolean: True si la prueba de la potencia fue exitosa, False en caso contrario.
    """

    if rx_power == 0:
        print("¡Modem sin potencia, límpialo o revisa la conexión!")
        return False
    else:
        # Evalúa y muestra el estado de la potencia
        if rx_power >= 245:
            potencia_msg = "Mala potencia"
            result = False
        elif 220 < rx_power < 245:
            potencia_msg = "Buena potencia"
            result = True
        elif 160 <= rx_power <= 220:
            potencia_msg = "Excelente potencia"
            result = True
        else:
            potencia_msg = "Potencia desconocida"
            result = False

        print(f"Potencia: {rx_power} - {potencia_msg}")
        if result:
            print("¡Datos de modem obtenidos!")

        return result

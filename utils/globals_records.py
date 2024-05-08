# No me gusta hard setear pero ya no tengo ganas de nada
record_id = '1BS9uJn_2zfKPXYnbIJEk6rGy80fVSLloCUlixYOFpik'

# Mapeo de modelos
model_mapping = {
    '8115': [1, 'RTF8115VW'],
    '8225': [2, 'RTF8225VW'],
    '3505': [3, '3505VW'],
    '2541': [4, 'MSTCK00BRA0915-0083'],
    '2741': [5, 'GPT-2741GNAC'],
    '2742': [6, 'GPT-2742GX4X5V6']
}

# Mapeo de columnas en el archivo de Google Sheets
column_mapping = {
    'Fecha': 'A',
    'Modem': 'B',
    'Modelo': 'C',
    'SN': 'D',
    'MAC': 'E',
    'ONT_password': 'F',
    'generated_wifi_password': 'G',
    'wifi_password': 'H'
}


def alpha_to_num(alpha):
    num = 0
    for i in range(len(alpha)):
        num = num * 26 + (ord(alpha[i].upper()) - ord('A')) + 1
    return num - 1  # -1 porque los índices en Python comienzan en 0
import subprocess
import requests
import time
import json

from .globals_records import model_mapping


# Carga la configuración
def load_configuration():
    with open('config.json') as archivo_config:
        configuration = json.load(archivo_config)
    return configuration


# Identifica el tipo de modelo en SmartOLT
def get_proper_ONT_name(model: int):
    model_name = next((val[1] for val in model_mapping.values() if val[0] == model), None)

    if model_name is not None:
        return model_name
    else:
        print("Modelo no identificado, no se como llegaste hasta acá")
        return None



class SmartOLT():
    def __init__(self, sn, model: int, OLT: int = 3):
        config = load_configuration()
        self.subdomain = config['subdomain']
        self.api_key = config['api_key']
        self.model = model
        self.OLT = OLT
        self.sn = sn


    # Busca una ONT en un OLT
    def find_ONT_in_OLT(self, sn: int, subdomain: int, api_key: int):

        # Obtener valores simplificados
        sn = self.sn
        subdomain = self.subdomain
        api_key = self.api_key
        OLT = self.OLT

        # URL de la petición
        url = f"https://{subdomain}.smartolt.com/api/onu/unconfigured_onus_for_olt/{OLT}"

        payload={}
        headers = {
            'X-Token': f'{api_key}'
        }

        # Se realiza la petición
        response = requests.request("GET", url, headers=headers, data=payload)
        ONTs = json.loads(response.text)

        # Se busca la ONT
        element = next((item for item in ONTs["response"] if item["sn"] == sn), False)

        return element


    # Autoriza una ONT
    def auth_ONT(self) -> bool:

        # Obtener valores simplificados
        sn = self.sn
        subdomain = self.subdomain
        api_key = self.api_key
        OLT = self.OLT

        # Confirma la existencia de la ONT
        ONT_check = self.find_ONT_in_OLT(sn, subdomain, api_key)

        if ONT_check == False:
            print(f"La ONT {sn} no existe en el OLT {OLT}")
            return False

        else:
            # Verifica la existencia del nombre de ONT
            onu_type_name = ONT_check["onu_type_name"]
            onu_type = onu_type_name if onu_type_name != "" else get_proper_ONT_name(self.model)


            # URL de la petición
            url = f"https://{subdomain}.smartolt.com/api/onu/authorize_onu"

            payload={
                'olt_id': f'{OLT}',
                'pon_type': 'gpon',
                'board': '3',
                'port': '3',
                'sn': f'{sn}',
                'onu_type': f'{onu_type}',
                'custom_profile': 'Generic_1',
                'onu_mode': 'Routing',
                'svlan': '298',
                'tag_transform_mode': 'translate',
                'vlan': '10',
                'zone': '22',
                'name': f'{sn}',
                'onu_external_id': f'{sn}'
            }
            files=[

            ]
            headers = {
            'X-Token': f'{api_key}'
            }

            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            response = json.loads(response.text)

            if response["status"] == True:
                print(f"La ONT {sn} ha sido autorizada")
                return True
            else:
                print(f"La ONT {sn} no ha sido autorizada")
                print(f"Error: {response['error']}")
                return False


    # Corfirma el internet utilizando PING
    def check_internet_connection(self) -> bool:
        time.sleep(5)
        result = subprocess.run(['ping', '8.8.8.8', '-S', '192.168.1.2', '-n', '7'], capture_output=True, text=True)
        print(result.stdout)

        if "Tiempo de espera agotado" in result.stdout or "Red de destino inaccesible" in result.stdout or"Request timed out" in result.stdout:
            print("La conexión ha fallado.")
            return False
        else:
            print("Conexión exitosa.")
            return True


if __name__ == '__main__':
    olt = SmartOLT('ASKY004DD244')
    olt.auth_ONT()
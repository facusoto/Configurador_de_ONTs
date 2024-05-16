import time
import requests
from random import randint
from .raw_data_handler import get_gpon_and_mac, rx_power_report
from ..utils.company_info import designed_ONT_password
from ..utils.ssh_utilities import wifi_config_ssh

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from selenium.common.exceptions import UnexpectedAlertPresentException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class Init3505:
    def __init__(self, device_number, access_password, wan_service, wifi_2g, wifi_5g, existing_randomly_password):

        # Especifica la ubicación del ejecutable del chromedriver descargado
        chromedriver_path = 'C:/Windows/old_chrome/chromedriver_win32/chromedriver.exe'

        # Especifica la ubicación del ejecutable de Chrome descargado
        chrome_path = "C:/Windows/old_chrome/chrome-win/chrome.exe"

        # Configuraciónes previas al instanciado
        chrome_options = Options()
        chrome_options.binary_location = chrome_path

        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--output=/dev/null")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Crea una instancia del controlador de Chrome con las opciones configuradas
        self.driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)

        # Configura el tiempo de espera
        self.wait = WebDriverWait(self.driver, 30)

        # Configuración de datos obtenidos desde Sheets
        self.device_number = device_number
        self.access_password = access_password
        self.wan_service = wan_service
        self.wifi_2g = wifi_2g
        self.wifi_5g = wifi_5g
        self.existing_randomly_password = existing_randomly_password

        # Configuración de una contraseña aleatoria
        self.random_password = existing_randomly_password if self.existing_randomly_password is not None else randint(10000000, 99999999)

    def get_data(self):
        driver = self.driver
        # Ingreso, verificación de rx_power y subida de datos de modem
        try:
            driver.delete_all_cookies()
            driver.get('http://192.168.1.1/')
            print("Ingresando a 192.168.1.1")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                driver.quit()
                print("------\007")
                raise SystemExit

        # Frame de ingreso
        new_frame = driver.find_element_by_xpath("/html/frameset/frame[1]")
        driver.switch_to.frame(new_frame)

        input_pass = driver.find_element_by_name('Password')
        input_pass.send_keys(self.access_password)

        # Buscar y cliquear botón de ingreso (cambiante)
        try:
            entrar = driver.find_element_by_class_name('te_acceso_router_enter')
            entrar.click()

        except NoSuchElementException:
            entrar = driver.find_element_by_xpath("//input[@value='Entrar']")
            entrar.click()

        # Esperar un segundo e ir a la pestaña de información
        time.sleep(2)

        # Verificar si se puede cambiar de página, si no se puede la contraseña es incorrecta
        try:
            driver.get('http://192.168.1.1/te_info.html')

        except UnexpectedAlertPresentException:
            print('La contraseña introducida es incorrecta, por favor verificala')
            driver.quit()
            print("------\007")
            raise SystemExit

        # --------------------
        # Variables a utilizar
        gpon_element = ''
        mac_element = ''
        rx_power_element = ''
        no_power = "--- dBm"

        # Toma de valores en dos modelos
        try:
            gpon_element = driver.find_element_by_xpath('//*[@id="tdId"]').text
            mac_element = driver.find_element_by_xpath('//*[@id="tdMac"]').text
            rx_power_element = driver.find_element_by_xpath('//*[@id="tdRx"]').text

        except NoSuchElementException:
            gpon_element = driver.find_element_by_xpath('//*[@id="tdId"]').text
            mac_element = driver.find_element_by_xpath('//*[@id="PCformat"]/div[3]/table/tbody/tr[9]').text
            rx_power_element = driver.find_element_by_xpath('/html/body/div/div[1]/div[7]/div[2]/div[3]/span[1]').text

        except TimeoutException:
            print("No se pudo acceder y obtener los datos")

        # Formatea el gpon y la mac
        gpon, mac = get_gpon_and_mac(gpon=gpon_element, mac=mac_element)

        # Formatea la rx_power
        if rx_power_element != no_power:
            rx_power = int(''.join(filter(str.isdigit, rx_power_element))[:3])
        else:
            rx_power = 0

        # Hace un reporte de la rx_power
        device_status = rx_power_report(rx_power)

        return gpon, mac, device_status

    def config_panel_access(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/')

        # Ventana de ingreso
        try:
            new_frame = driver.find_element_by_xpath('/html/frameset/frame[1]')
            driver.switch_to.frame(new_frame)

            # Acceder datos
            user = driver.find_element_by_name("Username")
            user.send_keys("admin")

            password = driver.find_element_by_name("Password")
            password.send_keys(self.access_password)

            entrar = driver.find_element_by_xpath("//input[@value='Entrar']")
            entrar.click()

            driver.switch_to.default_content()

        except NoSuchElementException:
            print("No fue necesario acceder de nuevo")

        time.sleep(3)

    def change_password(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/password.html')

        # Frame Menu (Management)
        if self.access_password != designed_ONT_password:
            # Ingresar la contraseña actual y la nueva contraseña
            driver.find_element_by_name("pwdOld").send_keys(self.access_password)
            driver.find_element_by_name("pwdNew").send_keys(designed_ONT_password)
            driver.find_element_by_name("pwdCfm").send_keys(designed_ONT_password)

            # Hacer clic en el botón de aplicar cambios
            driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

            print("Contraseña cambiada con éxito")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def wan_test_value(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/wancfg.cmd')

        # Eliminar configuración previa
        try:
            rml_inputs = driver.find_elements_by_xpath("//input[@name='rml']")

            # Encontrar los elementos y eliminarlos
            for rml_input in rml_inputs:
                if rml_input.is_displayed():
                    rml_input.click()
            driver.find_element_by_xpath("//input[@value='Remove']").click()

        except NoSuchElementException:
            print("No se encontraron Input RML, algo inusual ocurrió.")

        # Agregar nueva configuración (Espera cautelosa)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Add']")))
        driver.find_element_by_xpath("//input[@value='Add']").click()

        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Configuración VLAN
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='vlanMuxPr']")))
        vlan_min = driver.find_element_by_name("vlanMuxPr")
        vlan_min.clear()
        vlan_min.send_keys("0")

        vlan_max = driver.find_element_by_name("vlanMuxId")
        vlan_max.clear()
        vlan_max.send_keys("10")

        driver.find_element_by_xpath("//select[@name='vlanTpid']/option[text()='0x8100']").click()
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Configuración PPP
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='pppUserName']")))
        ppp_user_name = driver.find_element_by_name("pppUserName")
        ppp_user_name.clear()
        ppp_user_name.send_keys('test')

        ppp_password = driver.find_element_by_name("pppPassword")
        ppp_password.clear()
        ppp_password.send_keys("123456")

        driver.find_element_by_xpath("//input[@value='Next']").click()
        driver.find_element_by_name("chkIpv4DefaultGtwy").click()

        driver.find_element_by_xpath("//input[@value='Next']").click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Finalizar configuración
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Apply/Save']")))
        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        print("Cambio de WAN")

    def wan_official_value(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/wancfg.cmd')

        # Ingresar la configuración de WAN
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='rml']")))
        wan_service = driver.find_element_by_xpath("//input[contains(@value, 'Edit')]")
        wan_service.click()

        # Configuración PPP
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='pppUserName']")))
        ppp_user_name = driver.find_element_by_name("pppUserName")
        ppp_user_name.clear()
        ppp_user_name.send_keys(self.wan_service)

        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Finalizar configuración
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Apply/Save']")))
        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        print("Cambio de WAN")

    def multiple_configurations(self):
        driver = self.driver

        # ---------------------
        # Configuración de IPv6
        driver.get('http://192.168.1.1:8000/ipv6lancfg.html')

        # Buscar elementos input de tipo checkbox excluyendo 'enableRadvdUla'
        checkboxes = driver.find_elements_by_xpath('//input[@type="checkbox" and not(@name="enableRadvdUla")]')

        # Verificar si se encontraron elementos
        if not checkboxes:
            print('No se encontraron botones para clickear, error')
        else:
            # Cliquear en los elementos que estén seleccionados
            for checkbox in checkboxes:
                if checkbox.is_selected():
                    checkbox.click()

        driver.find_element_by_xpath("//input[@value='Save/Apply']").click()

        # ---------------------
        # Configuración de DHCP
        driver.get('http://192.168.1.1:8000/adminlancfg.html')

        # Habilitar radio DHCP
        dhcp_enable = driver.find_element_by_xpath('//*[@id="dhcpInfo"]/table[1]/tbody/tr[2]/td/input')
        dhcp_enable.click()

        # Setear servidores DNS
        dns_server_1 = driver.find_element_by_name("lanHostDns1")
        dns_server_1.clear()
        dns_server_1.send_keys("8.8.8.8")

        dns_server_2 = driver.find_element_by_name("lanHostDns2")
        dns_server_2.clear()
        dns_server_2.send_keys("8.8.4.4")

        driver.find_element_by_xpath('//input[@value="Apply/Save"]').click()

        # --------------------------
        # Configuración de IP Filter
        driver.get('http://192.168.1.1:8000/scbidirectionalflt.cmd?action=view')

        # Selecciona el primer elemento y edita
        driver.find_element_by_xpath("//tr[2]/td[6]/input").click()
        driver.find_element_by_xpath("//input[@value='Edit']").click()

        # Selecciona default action
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='entryDefaultAction']")))
        default_action = Select(driver.find_element_by_name("entryDefaultAction"))
        default_action.select_by_value('Permit')

        driver.find_element_by_xpath('//input[@name="applyEntry"]').click()

        # --------------------
        # Configuración de DNS
        driver.get('http://192.168.1.1:8000/dnscfg.html')

        # Habilitar radio DNS
        dns_enable = driver.find_element_by_xpath("//table[3]/tbody/tr[1]/td/input")
        dns_enable.click()

        # Setear servidores DNS
        dns_server_1 = driver.find_element_by_name("dnsPrimary")
        dns_server_1.clear()
        dns_server_1.send_keys("8.8.8.8")

        dns_server_2 = driver.find_element_by_name("dnsSecondary")
        dns_server_2.clear()
        dns_server_2.send_keys("8.8.4.4")

        print("Cambios varios")

    def configure_wifi_2g(self):

        # Realiza las configuraciones por SSH
        password = str(self.random_password)

        self.output_pass = wifi_config_ssh(ONT_password=self.access_password ,access_password=password, ssid=self.wifi_2g)
        self.output_pass = [[self.output_pass]]

        print("Wifi 2g configurado")
        return self.output_pass, [[self.random_password]]

    def configure_wifi_5g(self):

        # Realiza las configuraciones por SSH
        password = str(self.random_password)
        wifi_config_ssh(ONT_password=self.access_password, access_password=password, ssid=self.wifi_5g, plus='_plus')
        print("Wifi 5g configurado")

    def kill(self):
        driver = self.driver
        driver.quit()

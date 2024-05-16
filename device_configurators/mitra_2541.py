import time
from time import sleep
from random import randint
from .raw_data_handler import get_gpon_and_mac, rx_power_report
from ..utils.company_info import designed_ONT_password

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager


class Init2541:
    def __init__(self, device_number, access_password, wan_service, wifi_2g, wifi_5g, existing_randomly_password):

        # Especifica la ubicación del ejecutable del chromedriver descargado
        chromedriver_path = 'C:/Windows/old_chrome/chromedriver_win32/chromedriver.exe'

        # Especifica la ubicación del ejecutable de Chrome descargado
        chrome_path = "C:/Windows/old_chrome/chrome-win/chrome.exe"

        # Configuraciónes previas al instanciado
        chrome_options = Options()
        chrome_options.binary_location = chrome_path

        #chrome_options.add_argument("--headless")
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
            driver.get('http://192.168.1.1')
            print("Ingresando a 192.168.1.1")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                raise SystemExit

        # Campo contraseña
        input_password = driver.find_element_by_name('pass')
        input_password.send_keys(self.access_password)

        # Buscar y cliquear botón de ingreso (cambiante)
        try:
            login_enter = driver.find_element_by_class_name('sendBtu2')
            login_enter.click()

        except NoSuchElementException:
            login_enter = driver.find_element_by_class_name('sendBtu')
            login_enter.click()

        # Variables a utilizar
        gpon_element = ''
        mac_element = ''
        rx_power_element = ''

        # Verificar si la URL ha cambiado debido a la contraseña incorrecta
        if "logIn_mhs_pw_error.html" in driver.current_url:
            print("Contraseña incorrecta. Corrige la contraseña en Google sheets y vuelve a intentar.")
            # Puedes lanzar una excepción aquí o realizar otra acción adecuada.
        else:
            # Toma de valores en dos modelos
            try:
                # Obtén los elementos modelo 1
                gpon_element = driver.find_element_by_xpath('//*[@id="gsn"]').text
                mac_element = driver.find_element_by_xpath('//*[@class="FLOATBOX"][1]//div[9]/span').text
                rx_power_element = driver.find_element_by_xpath('//*[@class="FLOATBOX"][3]//div[3]/span[1]').text

            except NoSuchElementException:
                # Obtén los elementos modelo 2
                gpon_element = driver.find_element_by_xpath('//*[@id="gsn"]').text
                mac_element = driver.find_element_by_xpath('/html/body/div/div[1]/div[5]/div[3]/div[2]/div[9]').text
                rx_power_element = driver.find_element_by_xpath('/html/body/div/div[1]/div[7]/div[2]/div[3]/span[1]').text

            except TimeoutException:
                print("No se pudo acceder y obtener los datos")

            # Formatea el gpon y la mac
            gpon, mac = get_gpon_and_mac(gpon=gpon_element, mac=mac_element)

            # Obtiene el valor de rx_power
            rx_power = int(''.join(filter(str.isdigit, rx_power_element))[:3])

            # Hace un reporte de la rx_power
            device_status = rx_power_report(rx_power)

            return gpon, mac, device_status

    def config_panel_access(self):
        # Ingreso a la página 192.168.1.1:8000
        driver = self.driver
        driver.get('http://192.168.1.1/logIn_main.html')

        # Ingresando a configuración avanzada
        user = driver.find_element_by_name("user")
        user.send_keys("admin")

        password = driver.find_element_by_name("pass")
        password.send_keys(self.access_password)

        entrar = driver.find_element_by_name("acceptLogin")
        entrar.click()

    def wan_test_value(self, bandera: int = 0):
        # Ingreso a la página 192.168.1.1:8000
        Init2541.config_panel_access(self)

        driver = self.driver

        # Acceder al menú (Wan service)
        driver.switch_to.default_content()
        menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
        driver.switch_to.frame(menu_frame)

        # Hacer click en Advanced setup > WAN
        driver.find_element_by_xpath('//*[@id="folder10"]//a').click()
        driver.find_element_by_xpath('//*[@href="wancfg.cmd"]').click()

        # Acceder al menú (Wan service)
        driver.switch_to.default_content()
        base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.switch_to.frame(base_frame)

        if bandera == 0:
            # Eliminar configuración previa
            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='rml']")))
                rml_inputs = driver.find_elements_by_xpath("//input[@name='rml']")

                # Encontrar los elementos y eliminarlos
                for rml_input in rml_inputs:
                    if rml_input.is_displayed():
                        rml_input.click()

                # Eliminar la configuración
                driver.find_element_by_xpath("//input[@value='Remove']").click()
                print("Configuración eliminada")

                # Ir al inicio de sesión
                sleep(2)
                Init2541.config_panel_access(self)

            except (NoSuchElementException, TimeoutException):
                print("No se encontraron Input RML, algo inusual ocurrió.")

        elif bandera == 1:
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

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
            driver.find_element_by_xpath("//input[@value='Next']").click()

            # Configuración PPP
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='pppUserName']")))
            ppp_user_name = driver.find_element_by_name("pppUserName")
            ppp_user_name.clear()
            ppp_user_name.send_keys('test')

            ppp_password = driver.find_element_by_name("pppPassword")
            ppp_password.clear()
            ppp_password.send_keys("123456")

            driver.find_element_by_name("enblNat").click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
            driver.find_element_by_xpath("//input[@value='Next']").click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
            driver.find_element_by_xpath("//input[@value='Next']").click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
            driver.find_element_by_xpath("//input[@value='Next']").click()

            # Finalizar configuración
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Apply/Save']")))
            driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

            print("Cambio de WAN")

    def wan_official_value(self, bandera: int = 0):
        # Ingreso a la página 192.168.1.1:8000
        Init2541.config_panel_access(self)

        driver = self.driver

        # Acceder al menú (Wan service)
        driver.switch_to.default_content()
        menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
        driver.switch_to.frame(menu_frame)

        # Hacer click en Advanced setup > WAN
        driver.find_element_by_xpath('//*[@id="folder10"]//a').click()
        driver.find_element_by_xpath('//*[@href="wancfg.cmd"]').click()

        # Acceder al menú (Wan service)
        driver.switch_to.default_content()
        base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.switch_to.frame(base_frame)

        # Agregar nueva configuración (Espera cautelosa)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Add']")))
        driver.find_element_by_xpath("//input[contains(@value, 'Edit')]").click()

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
        # Ingreso a la página 192.168.1.1:8000
        Init2541.config_panel_access(self)

        driver = self.driver

        # ---------------------------
        # Configuración de DNS Server

        def config_dns(self):
            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
            driver.switch_to.frame(menu_frame)

            # Hacer click en Advanced setup > DNS Server
            driver.find_element_by_xpath('//*[@id="folder10"]//a').click()
            driver.find_element_by_xpath('//span[contains(text(),"DNS")]/parent::a').click()
            driver.find_element_by_xpath('//*[@href="dnscfg.html"]').click()

            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
            driver.switch_to.frame(base_frame)

            # Utilizar esta DNS
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '(//input[@name="dns"])[2]')))
            driver.find_element_by_xpath('(//input[@name="dns"])[2]').click()

            # Agregar DNS
            ssid2g = driver.find_element_by_name("dnsPrimary")
            ssid2g.clear()
            ssid2g.send_keys('8.8.8.8')

            ssid2g = driver.find_element_by_name("dnsSecondary")
            ssid2g.clear()
            ssid2g.send_keys('8.8.4.4')

            driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        # ---------------------
        # Configuración de UPNP

        def config_upnp(self):
            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
            driver.switch_to.frame(menu_frame)

            # Hacer click en Advanced setup > DNS Server
            driver.find_element_by_xpath('//*[@id="folder10"]//a').click()
            driver.find_element_by_xpath('//*[@href="upnpcfg.html"]').click()

            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
            driver.switch_to.frame(base_frame)

            # Encuentra el elemento checkbox por su atributo "name"
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='chkUpnp']")))
            checkbox_element = driver.find_element_by_name('chkUpnp')

            # Verifica si el checkbox está marcado, de no estarlo lo marca
            if not checkbox_element.is_selected():
                checkbox_element.click()

            driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        # ---------------------
        # Configuración de IPv6

        def config_ipv6(self):
            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
            driver.switch_to.frame(menu_frame)

            # Hacer click en Advanced setup > DNS Server
            driver.find_element_by_xpath('//*[@id="folder10"]//a').click()
            driver.find_element_by_xpath('//span[contains(text(),"LAN")]/parent::a').click()
            driver.find_element_by_xpath('//*[@href="ipv6lancfg.html"]').click()

            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
            driver.switch_to.frame(base_frame)

            # Encuentra el elemento checkbox por su atributo "name"
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="checkbox" and not(@name="enableRadvdUla")]')))
            checkbox_element = driver.find_elements_by_xpath('//input[@type="checkbox" and not(@name="enableRadvdUla")]')

            # Verifica si el checkbox está marcado, de no estarlo lo marca
            for element in checkbox_element:
                if element.is_selected():
                    element.click()

            driver.find_element_by_xpath("//input[@value='Save/Apply']").click()

        # ---------------------
        # Realizar configuración de ONT (De horrible forma, pero funciona)

        config_dns(self)
        Init2541.config_panel_access(self)
        config_upnp(self)
        Init2541.config_panel_access(self)
        config_ipv6(self)
        try:
            Init2541.config_panel_access(self)
        except UnexpectedAlertPresentException:
            while True:
                try:
                    alert = driver.switch_to.alert
                    alert.accept()
                except NoAlertPresentException:
                    # No hay más alertas, salir del bucle
                    break
            Init2541.config_panel_access(self)

    def configure_wifi_2g(self):
        # Ingreso a la página 192.168.1.1:8000
        driver = self.driver

        # -------------------------
        # Configurar el wifi 2.4GHz

        def config_2g(self):
            # Acceder al menú (Wireless)
            driver.switch_to.default_content()
            menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
            driver.switch_to.frame(menu_frame)

            # Hacer click en Wireless > Basic
            try:
                driver.find_element_by_xpath('//*[@id="folder47"]//a').click()
            except ElementNotInteractableException:
                driver.find_element_by_xpath('//*[@id="folder48"]//a').click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@href="wlcfg.html"]')))
            driver.find_element_by_xpath('//*[@href="wlcfg.html"]').click()

            # Volver al frame base
            driver.switch_to.default_content()
            base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
            driver.switch_to.frame(base_frame)

            # Cambiar nombre SSID
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="wlSsid"]')))
            ssid2g = driver.find_element_by_name("wlSsid")
            ssid2g.clear()
            ssid2g.send_keys(self.wifi_2g)

            # Cambiar región
            driver.find_element_by_xpath("//select[@name='wlCountry']/option[text()='UNITED STATES']").click()
            apply2g = driver.find_element_by_xpath("//input[@value='Apply/Save']")
            apply2g.click()

        # ---------------------------
        # Ir a la página de seguridad

        def config_security(self):
            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
            driver.switch_to.frame(menu_frame)

            # Hacer click en Advanced setup > DNS Server
            try:
                driver.find_element_by_xpath('//*[@id="folder47"]//a').click()
            except ElementNotInteractableException:
                driver.find_element_by_xpath('//*[@id="folder48"]//a').click()

            driver.find_element_by_xpath('//*[@href="wlsecurity.html"]').click()

            # Acceder al menú (Wan service)
            driver.switch_to.default_content()
            base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
            driver.switch_to.frame(base_frame)

            # Obteniendo la contraseña de fábrica
            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="revealcheck"]')))
                driver.find_element_by_id("revealcheck").click()
                wifi_pass = driver.find_element_by_id("wifiPass")
                wifi_pass_text = wifi_pass.get_attribute('value')
                self.output_pass = [[wifi_pass_text]]

                # Setear la contraseña
                wifi_pass.clear()
                wifi_pass.send_keys(self.random_password)

            except ElementNotInteractableException:
                print("Red wifi actualmente abierta, no reiniciaste el modem de fábrica")

            if self.output_pass is not None:
                print("¡Contraseña wifi obtenida!")
            else:
                print("Contraseña no obtenida")

            # Guargar configuración
            driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

            print("Wifi 2g configurado")

        config_2g(self)
        Init2541.config_panel_access(self)
        config_security(self)

        return self.output_pass, [[self.random_password]]

    def configure_wifi_5g(self):
        # Ingreso a la página 192.168.1.1:8000
        Init2541.config_panel_access(self)

        driver = self.driver

        # Acceder al menú (Wireless 5GHz)
        driver.switch_to.default_content()
        menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
        driver.switch_to.frame(menu_frame)

        # Hacer click en Wireless 5GHz
        try:
            driver.find_element_by_xpath('//*[@id="folder53"]//a').click()
        except (ElementNotInteractableException, NoSuchElementException):
            driver.find_element_by_xpath('//*[@id="folder55"]//a').click()

        driver.find_element_by_xpath('(//*[@href="wlextcfg.html"])[2]').click()

        # Volver al frame base
        driver.switch_to.default_content()
        base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.switch_to.frame(base_frame)

        # Cambiar nombre SSID
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="wlSsid"]')))
        ssid5g = driver.find_element_by_name("wlSsid")
        ssid5g.clear()
        ssid5g.send_keys(self.wifi_5g)

        # Cambiar contraseña
        ssid5g = driver.find_element_by_name("wlWpaPsk")
        ssid5g.clear()
        ssid5g.send_keys(self.random_password)

        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()
        print("Wifi 5g configurado")

    def change_password(self):
        # Ingreso a la página 192.168.1.1:8000
        Init2541.config_panel_access(self)

        driver = self.driver

        # Acceder al menú (Management)
        driver.switch_to.default_content()
        menu_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='menufrm']")))
        driver.switch_to.frame(menu_frame)

        # Hacer click en Acess control > Passwords
        driver.find_element_by_xpath("//a[span[text() = 'Management']]").click()

        driver.find_element_by_xpath('//span[contains(text(),"Access Control")]/parent::a').click()
        driver.find_element_by_xpath('//*[@href="password.html"]').click()

        # Volver al frame base
        driver.switch_to.default_content()
        base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.switch_to.frame(base_frame)

        if self.access_password != designed_ONT_password:
            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="userName"]')))
                driver.find_element_by_name("userName").send_keys("admin")
                driver.find_element_by_name("pwdOld").send_keys(self.access_password)
                driver.find_element_by_name("pwdNew").send_keys(designed_ONT_password)
                driver.find_element_by_name("pwdCfm").send_keys(designed_ONT_password)

            except NoSuchElementException:
                print("Error, no encontrado (?")

            apply_manage = driver.find_element_by_xpath("//input[@value='Apply/Save']")
            apply_manage.click()

            print("Cambio de contraseña")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def kill(self):
        driver = self.driver
        driver.quit()

if __name__ == '__main__':
    # Acá hice las pruebas para el nuevo modelo de firmware
    # Es una porquería horrible y tarda mil años. Pero funciona.

    iniciar = Init2541(device_number=10, access_password="A6uik6M2", wan_service="a", wifi_2g="a", wifi_5g="a", existing_randomly_password='')

    # Iniciar ONT
    iniciar.config_panel_access()

    # Configurar wan
    for i in range(2):
        iniciar.cambio_wan(bandera=i)
        iniciar.config_panel_access()

    # Configurar varios
    iniciar.multiple_configurations()

    # Configurar 2g
    valores = iniciar.configure_wifi_2g()
    for i in valores:
        print(i)

    # Configurar 5g
    iniciar.configure_wifi_5g()

    # -------------------------

    # Cerrar ONT
    # iniciar.kill()
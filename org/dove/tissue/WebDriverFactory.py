import configparser as cp
import os
import platform
import re
import stat
import tarfile
import zipfile
import requests

from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.ie.options import Options


def set_file_executable(path):
    if os.path.isfile(path) and not os.access(path, os.X_OK):
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)


class WebDriverFactory:
    def __init__(self):
        self.os_name = platform.system()
        self.os_bit = platform.architecture()
        self.config_name = "config.ini"
        self.automation_browser = None
        self.automation_local = True
        self.automation_url = None
        self.download_url = 'Executable driver found.'
        self.chrome_driver_api_url = 'https://chromedriver.storage.googleapis.com'
        self.chrome_driver_path = f'driver{os.path.sep}chrome'
        self.chrome_driver_name = 'chromedriver.exe' if self.os_name == 'Windows' else 'chromedriver'
        self.firefox_driver_api_url = 'https://github.com/mozilla/geckodriver/releases'
        self.firefox_driver_path = f'driver{os.path.sep}firefox'
        self.firefox_driver_name = 'geckodriver.exe' if self.os_name == 'Windows' else 'geckodriver'
        self.edge_driver_api_url = 'https://msedgedriver.azureedge.net'
        self.edge_driver_path = f'driver{os.path.sep}edge'
        self.edge_driver_name = 'msedgedriver.exe' if self.os_name == 'Windows' else 'msedgedriver'
        self.ie_driver_api_url = 'https://selenium-release.storage.googleapis.com'
        self.ie_driver_path = f'driver{os.path.sep}ie'
        self.ie_driver_name = 'IEDriverServer.exe'

    def set_config(self):
        config = cp.ConfigParser()
        config.read(self.config_name)
        item = config.get('automation', 'automation.browser')
        if item in ['chrome', 'firefox', 'edge', 'ie', 'safari']:
            self.automation_browser = item
        else:
            raise NotImplementedError(f'Unsupported browser name: {item}')
        self.automation_local = config.get('automation', 'automation.local').lower() in ['true', 'y', 'yes']
        if not self.automation_local:
            self.automation_url = config.get('automation', 'automation.url')

    def get_local_chrome_version(self):
        if self.os_name == 'Windows':
            with os.popen(r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version') as stream:
                version = re.split(r'\s+', stream.readlines()[2].strip())[2]
        else:
            with os.popen(r'/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version') as stream:
                version = stream.read().strip('Google Chrome ').strip()
        print(f'Installed Chrome Browser version: {version}')
        return version

    def get_latest_chrome_version(self, version):
        latest_release = requests.get(f'{self.chrome_driver_api_url}/LATEST_RELEASE_{re.split(r"[.]", version)[0]}')
        self.chrome_driver_path += f'{os.path.sep}{latest_release.text}'
        print(f'Latest Chromedriver version: {latest_release.text}')
        return latest_release.text

    def download_chromedriver(self, version):
        if not os.path.exists(self.chrome_driver_path):
            print('Not found on executable chromedriver. Chromedriver will be downloaded.')
            self.download_url = f'{self.chrome_driver_api_url}/{version}/chromedriver_'
            if self.os_name == 'Windows':
                self.download_url += 'win32.zip'
            else:
                self.download_url += 'mac64.zip'
            file = requests.get(self.download_url, stream=True)
            file_name = 'chromedriver.zip'
            with open(file_name, 'wb') as fd:
                print(f'Downloading from {self.download_url}')
                for chunk in file:
                    fd.write(chunk)
            zipfile.ZipFile(file_name).extractall(self.chrome_driver_path)
            os.remove(file_name)
        else:
            print(f'{self.download_url}')

    def setup_chromedriver(self):
        self.download_chromedriver(self.get_latest_chrome_version(self.get_local_chrome_version()))
        set_file_executable(f'{self.chrome_driver_path}'
                            f'{os.path.sep}{self.chrome_driver_name}')
        os.environ['PATH'] += f'{os.pathsep}{os.path.abspath(self.chrome_driver_path)}'

    def download_geckodriver(self):
        latest_release = requests.get(f'{self.firefox_driver_api_url}/latest', allow_redirects=True)
        gecko_version = re.split(r'[/]+', latest_release.url)[-1]
        self.firefox_driver_path += f'{os.path.sep}{gecko_version}'
        if not os.path.exists(self.firefox_driver_path):
            print(f'Not found on executable geckodriver. Geckodriver will be downloaded.')
            self.download_url = f'{self.firefox_driver_api_url}/download/{gecko_version}' \
                                f'/geckodriver-{gecko_version}-'
            if self.os_name == 'Windows':
                self.download_url += 'win32.zip' if self.os_bit == '32bit' else 'win64.zip'
            else:
                self.download_url += 'macos.tar.gz'
            file = requests.get(self.download_url, stream=True)
            file_name = 'geckodriver.zip' if self.os_name == 'Windows' else 'geckodriver.tar.gz'
            with open(file_name, 'wb') as fd:
                print(f'Downloading from {self.download_url}')
                for chunk in file:
                    fd.write(chunk)
            if self.os_name == 'Windows':
                zipfile.ZipFile(file_name).extractall(self.firefox_driver_path)
            else:
                tar = tarfile.open(file_name, 'r:gz')
                tar.extractall(self.firefox_driver_path)
                tar.close()
            os.remove(file_name)
        else:
            print(f'{self.download_url}')

    def setup_geckodriver(self):
        self.download_geckodriver()
        set_file_executable(f'{self.firefox_driver_path}'
                            f'{os.path.sep}{self.firefox_driver_name}')
        os.environ['PATH'] += f'{os.pathsep}{os.path.abspath(self.firefox_driver_path)}'

    def get_local_edge_version(self):
        if self.os_name == 'Windows':
            with os.popen(r'reg query "HKEY_CURRENT_USER\Software\Microsoft\Edge\BLBeacon" /v version') as stream:
                version = re.split(r'\s+', stream.readlines()[2].strip())[2]
        else:
            with os.popen(r'/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --version') as stream:
                version = stream.read().strip('Microsoft Edge ').strip()
        print(f'Installed Edge Browser version: {version}')
        return version

    def download_edgedriver(self, version):
        self.edge_driver_path += f'{os.path.sep}{version}'
        if not os.path.exists(self.edge_driver_path):
            print(f'Not found on executable edgedriver. Edgedriver will be downloaded.')
            self.download_url = f'{self.edge_driver_api_url}/{version}/edgedriver_'
            if self.os_name == 'Windows':
                self.download_url += 'win64.zip' if self.os_bit == '64bit' else 'win32.zip'
            else:
                self.download_url += 'mac64.zip'
            file = requests.get(self.download_url, stream=True)
            file_name = 'msedgedriver.zip'
            with open(file_name, 'wb') as fd:
                print(f'Downloading from {self.download_url}')
                for chunk in file:
                    fd.write(chunk)
            zipfile.ZipFile(file_name).extractall(self.edge_driver_path)
            os.remove(file_name)
        else:
            print(f'{self.download_url}')

    def setup_edgedriver(self):
        self.download_edgedriver(self.get_local_edge_version())
        set_file_executable(f'{self.edge_driver_path}'
                            f'{os.path.sep}{self.edge_driver_name}')
        os.environ['PATH'] += f'{os.pathsep}{os.path.abspath(self.edge_driver_path)}'

    def download_iedriver(self):
        if not os.path.exists(self.ie_driver_path):
            print(f'Not found on executable iedriver. IE driver will be downloaded.')
            self.download_url = f'{self.ie_driver_api_url}/3.150/IEDriverServer_Win32_3.150.1.zip'
            file = requests.get(self.download_url, stream=True)
            file_name = 'IEDriverServer.zip'
            with open(file_name, 'wb') as fd:
                print(f'Downloading from {self.download_url}')
                for chunk in file:
                    fd.write(chunk)
            zipfile.ZipFile(file_name).extractall(self.ie_driver_path)
            os.remove(file_name)
        else:
            print(f'{self.download_url}')

    def setup_iedriver(self):
        self.download_iedriver()
        os.environ['PATH'] += f'{os.pathsep}{os.path.abspath(self.ie_driver_path)}'

    def launch(self):
        self.set_config()
        if self.automation_browser == 'chrome':
            if self.automation_local:
                self.setup_chromedriver()
                return webdriver.Chrome()
        elif self.automation_browser == 'firefox':
            if self.automation_local:
                self.setup_geckodriver()
                return webdriver.Firefox()
        elif self.automation_browser == 'edge':
            self.setup_edgedriver()
            return webdriver.Edge()
        elif self.automation_browser == 'ie':
            self.setup_iedriver()
            ie_options = Options()
            ie_options.ignore_protected_mode_settings = True
            ie_options.ensure_clean_session = True
            ie_options.require_window_focus = True
            ie_options.ignore_zoom_level = True
            return webdriver.Ie(options=ie_options)
        elif self.automation_browser == 'safari':
            return webdriver.Safari()
        return webdriver.Remote(command_executor=self.automation_url,
                                desired_capabilities=DesiredCapabilities.CHROME.copy()
                                if self.automation_browser == 'chrome'
                                else DesiredCapabilities.FIREFOX.copy())

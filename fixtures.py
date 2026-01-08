# fixtures.py - ПОЛНАЯ версия для Google Colab
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def chrome_driver():
    """Chrome ИДЕАЛЬНО для Google Colab"""
    options = Options()

    # 🔥 ОСНОВНЫЕ флаги Colab
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # 🔥 ФИКС DevToolsActivePort
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-ipc-flooding-protection')

    # 🔥 СТАБИЛЬНОСТЬ
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')

    # ПУТИ Colab
    service = Service('/usr/bin/chromedriver')
    options.binary_location = '/usr/bin/chromium-browser'

    driver = webdriver.Chrome(service=service, options=options)
    return driver

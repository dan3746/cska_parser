from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.project_root = Path(__file__).parent.parent  # Корень проекта
        self.data_file = self.project_root / "parsed_data.txt"
        self.archive_dir = self.project_root / "archive_results"
        self.base_stat_path = self.project_root / "cska_stats.xlsx"

    def open(self, url):
        self.driver.get(url)
        return self

    def click_element(self, locator) -> None:
        """
        Клик по элементу с ожиданием кликабельности
        """
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()

    def find_element(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_elements(self, locator):
        return self.driver.find_elements(*locator)

    def read_data_file(self):
        """
        Читает НАЗВАНИЯ ВСЕХ файлов из директории архивных файлов в корне проекта

        Returns:
            Список имён файлов: ['file1.xlsx', 'file2.txt', ...]
        """

        # Получаем ВСЕ файлы (не папки)
        file_names = [
            file_path.name for file_path in self.archive_dir.iterdir()
            if file_path.is_file()
        ]

        # Сортируем для стабильности
        file_names.sort()
        print(f"✅ Найдено файлов в {self.archive_dir}: {len(file_names)}")
        return file_names

    def write_to_data_file(self, line: str) -> None:
        """
        Добавляет новую строку в конец файла parsed_data.txt

        Args:
            line: Строка для записи
        """
        with open(self.data_file, 'a', encoding='utf-8') as f:
            f.write(line + '\n')


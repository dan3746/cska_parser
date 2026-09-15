import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.reader.excel import load_workbook
from openpyxl.workbook import Workbook

from pages.base_page import BasePage
from selenium.webdriver.common.by import By


LAST_MATCH_DATA_LOCATOR = (
    "(//div[contains(@class, 'schedule-game')]//div[@class='promo__game-row']"
    "/div[normalize-space(.) != '0']/ancestor::div[contains(@class, 'schedule-game')])"
    "[1]//span[@class='ng-binding']"
)


class MatchParser(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.players = {}
        self.goalkeepers = {}
        self.new_players = {}
        self.new_data = {}

    def get_last_match_data(self):
        # Ваш XPath с ancestor/contains
        match_data = self.find_elements((
            By.XPATH, LAST_MATCH_DATA_LOCATOR
        ))
        return match_data

    def parse_cska_stats(self):
        """
        Парсит Excel файл ЦСКА и возвращает список игроков с матчами и голами

        Returns:
            Список словарей: [{'name': 'Маркина Полина', 'matches': '212', 'count': '1330'}, ...]
        """

        try:
            workbook = openpyxl.load_workbook(self.base_stat_path)
            sheet = workbook.active  # Лист1

            data = {}
            # Находим строку с заголовками (пропускаем 1-2 строки с описанием)
            for row in range(4, sheet.max_row + 1):  # Начинаем с 3-й строки
                cell_name = sheet.cell(row=row, column=1).value
                cell_matches = sheet.cell(row=row, column=2).value
                cell_goals = sheet.cell(row=row, column=3).value

                # Пропускаем пустые строки и заголовки
                if cell_name and cell_matches and cell_goals or cell_goals == 0:
                    data[cell_name] = {
                        'matches': int(cell_matches),
                        'count': int(cell_goals),
                    }
                elif not self.players:
                    self.players = data
                    data = {}
            self.goalkeepers = data
            print(f"✅ Спарсено {len(self.players)} игроков и {len(self.goalkeepers)} вратарей  из {self.base_stat_path}")

        except Exception as e:
            print(f"❌ Ошибка парсинга Excel: {e}")

    def open_last_match(self):
        """
        Открывает последний матч
        """

        self.click_element((
            By.XPATH, LAST_MATCH_DATA_LOCATOR
        ))
        self.click_element((
            By.XPATH, "(//a[normalize-space(text())='Статистика'])[1]"
        ))
        self.click_element((
            By.XPATH, "(//a[normalize-space(text())='ЦСКА'])[2]"
        ))

    def add_new_stats(self):
        """
        Получаем статистику по последнему матчу
        """
        players_locator = "//tr/td[2]/a[normalize-space(text())='{}']/ancestor::tr/td[4]"
        goalkeepers_locator = "(//tr/td[2]/a[normalize-space(text())='{}']/ancestor::tr/td[3])[2]"

        players_el = self.find_elements((
            By.XPATH, "//tr/td[2]"
        ))
        cur_locator = players_locator
        players = [player.text for player in players_el[:-1]]
        for player_name in players:
            if players.count(player_name) > 1 and cur_locator == players_locator:
                continue
            if player_name:
                player_count = self.find_elements((
                    By.XPATH, cur_locator.format(player_name)
                ))[0].text
                count = int(player_count.split('/')[0]) if player_count else 0

                if cur_locator == players_locator:
                    if not self.players.get(player_name):
                        self.players[player_name] = {
                            'matches': 1,
                            'count': count,
                        }
                    elif self.players.get(player_name):
                        self.players[player_name]['matches'] += 1
                        self.players[player_name]['count'] += count
                    else:
                        raise AttributeError(f"Unknown player name {player_name}")
                elif cur_locator == goalkeepers_locator:
                    if not self.goalkeepers.get(player_name):
                        self.goalkeepers[player_name] = {
                            'matches': 1,
                            'count': count,
                        }
                    elif self.goalkeepers.get(player_name):
                        self.goalkeepers[player_name]['matches'] += 1
                        self.goalkeepers[player_name]['count'] += count
                else:
                    raise AttributeError(f"Unknown player name {player_name}")

            else:
                cur_locator = goalkeepers_locator
                print(f"✅ Статистика полевых игроков обновлена")
        print(f"✅ Статистика вратарей обновлена")

    def clear_and_rewrite_excel(self):
        """
        1. Загружает Excel файл
        2. УДАЛЯЕТ ВСЕ данные с 3-й строки
        3. Записывает НОВЫЕ данные с теми же именами игроков
        4. Сохраняет структуру/форматирование
        """

        try:
            # Загружаем СТРУКТУРУ
            wb = load_workbook(self.base_stat_path)
            ws = wb.active  # Лист1

            # 1. ОЧИЩАЕМ ДАННЫЕ (оставляем заголовки A1:C3)
            for row in ws.iter_rows(min_row=4, max_row=ws.max_row, max_col=3):
                for cell in row:
                    cell.value = None

            # 2. Записываем новые данные
            # Полевые игроки
            players = list(self.players.keys())
            for i in range(len(players)):
                player_name = players[i]
                ws[f'A{i + 4}'].value = player_name
                ws[f'B{i + 4}'].value = self.players[player_name]['matches']
                ws[f'C{i + 4}'].value = self.players[player_name]['count']

            # Вратари
            goalkeepers = list(self.goalkeepers.keys())
            for i in range(len(goalkeepers)):
                goalkeeper_name = goalkeepers[i]
                ws[f'A{i + 6 + len(players)}'].value = goalkeeper_name
                ws[f'B{i + 6 + len(players)}'].value = self.goalkeepers[goalkeeper_name]['matches']
                ws[f'C{i + 6 + len(players)}'].value = self.goalkeepers[goalkeeper_name]['count']

            wb.save(self.base_stat_path)

            print(f"✅ Очищено и перезаписано: {self.base_stat_path}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

    def archive_excel_file(self, new_filename):
        """
        Копирует Excel файл из корня в archive_results с timestamp в названии

        Args:
            new_filename: Базовое имя (по умолчанию - имя исходного файла)

        Returns:
            Path к новому файлу или None при ошибке
        """

        new_name = f"{new_filename}{self.base_stat_path.suffix}"
        destination_file = self.archive_dir / new_name
        source_path = Path(self.base_stat_path).resolve()  # Абсолютный путь
        dest_path = Path(destination_file).resolve()

        # 🔥 ROBOCOPY - ОДИН РАЗ И НАВСЕГДА
        cmd = [
            'robocopy',
            str(source_path.parent),
            str(dest_path.parent),
            source_path.name,
            '/COPY:DAT',  # Data, Attributes, Timestamps
            '/R:0',  # Не повторять при ошибках
            '/W:0'  # Без ожидания
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode in [0, 1]:
            new_dest = dest_path.parent / source_path.name
            new_dest.rename(new_dest.parent / new_name)
            print(f"✅ Скопировано и переименовано:")
            print(f"   {source_path.name} → {new_name}")
            return new_dest
        else:
            print(f"❌ robocopy ошибка: {result.stderr}")
            return None


values = ["minutes", "goals", "assists", "penalties", "earned_penalties", "blocks"]
player_columns_nums = {
    "games": 2,
    "minutes": 5,
    "goals": 6,
    "assists": 16,
    "penalties": 12,
    "earned_penalties": 18,
    "blocks": 24,
}
goalkeeper_columns_nums = {
    "games": 2,
    "saves": 5,
    "penalty_saves": 11,
}

class SeasonsParser(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.players = {}
        self.goalkeepers = {}

    def get_seasons_stats(self):
        """
        Получаем статистику по последнему матчу
        """
        time.sleep(5)

        while True:
            players_locator = "(//table)[1]//tr/td[4]/a"
            players = [player.text for player in self.find_elements((By.XPATH, players_locator))]
            for player in players:
                if not self.players.get(player):
                    self.players[player] = {
                        "games": 0,
                        "minutes": 0,
                        "goals": 0,
                        "assists": 0,
                        "penalties": 0,
                        "earned_penalties": 0,
                        "blocks": 0,
                    }
                for column, column_num in player_columns_nums.items():
                    column_value_locator = f"//a[normalize-space(text())='{player}']/ancestor::tr/td[{column_num}]"
                    column_value = self.find_element((
                        By.XPATH, column_value_locator
                    )).text
                    if column_value:
                        if column in ["goals", "penalties"]:
                            column_value = column_value.split('/')[0]
                        self.players[player][column] += int(column_value)
            print(f"✅ Статистика полевых игроков обновлена")

            goalkeepers_locator = "(//table)[2]//tr/td[4]/a"
            goalkeepers = [goalkeeper.text for goalkeeper in self.find_elements((By.XPATH, goalkeepers_locator))]
            for goalkeeper in goalkeepers:
                if not self.goalkeepers.get(goalkeeper):
                    self.goalkeepers[goalkeeper] = {
                        "games": 0,
                        "saves": 0,
                        "penalty_saves": 0,
                    }
                for column, column_num in goalkeeper_columns_nums.items():
                    column_value_locator = f"//a[normalize-space(text())='{goalkeeper}']/ancestor::tr/td[{column_num}]"
                    column_value = self.find_element((
                        By.XPATH, column_value_locator
                    )).text
                    self.goalkeepers[goalkeeper][column] += int(column_value.split('/')[0])
            print(f"✅ Статистика вратарей обновлена")


            cur_season = self.find_element((
                By.XPATH, '//div[@class="ss-single"]'
            )).text
            next_season = [int(year) - 1 for year in cur_season.split('-')]
            if f"{next_season[0]}-{next_season[1]}" == "2018-2019":
                break
            season_locator = '//div[@class="input-wrp"]//div[@aria-haspopup="listbox"]'
            self.click_element((
                By.XPATH, season_locator
            ))
            time.sleep(5)
            self.click_element((
                By.XPATH, f"//div[normalize-space(text())='{next_season[0]}-{next_season[1]}']"
            ))
            time.sleep(10)


    def create_excel_file(self, new_filename):
        """
        Создаёт новый Excel файл в корне проекта с отдельными листами для каждого ключа
        в self.players и self.goalkeepers. Данные сортируются по значению по убыванию.

        Args:
            new_filename: Базовое имя файла (без расширения)

        Returns:
            Path к новому файлу или None при ошибке
        """
        # Создаём новую книгу Excel
        wb = Workbook()
        # Удаляем лист по умолчанию
        default_sheet = wb.active
        wb.remove(default_sheet)


        # for player_column in player_columns_nums.keys():
        #     # Создаём лист с именем (ограничиваем до 31 символа — лимит Excel)
        #     sheet_name = f"Полевые игроки - {player_column}"
        #     ws = wb.create_sheet(title=sheet_name)
        #
        #     # Заголовок таблицы
        #     ws.append(["ФИО игрока", player_column])
        #
        #     sorted_data = sorted(self.players.items(), key=lambda item: item[1][player_column], reverse=True)
        #     result = [(player, stats[player_column]) for player, stats in sorted_data]
        #
        #     for player_name, value in result:
        #         ws.append([player_name, value])

        for goalkeeper_columns in goalkeeper_columns_nums.keys():
            # Создаём лист с именем (ограничиваем до 31 символа — лимит Excel)
            sheet_name = f"Вратари - {goalkeeper_columns}"
            ws = wb.create_sheet(title=sheet_name)

            # Заголовок таблицы
            ws.append(["ФИО игрока", goalkeeper_columns])

            sorted_data = sorted(self.goalkeepers.items(), key=lambda item: item[1][goalkeeper_columns], reverse=True)
            result = [(player, stats[goalkeeper_columns]) for player, stats in sorted_data]

            for player_name, value in result:
                ws.append([player_name, value])

        # Сохраняем файл в корне проекта (папка, где находится текущий скрипт)
        root_dir = Path(__file__).parent
        file_path = root_dir / f"{new_filename}.xlsx"
        wb.save(file_path)

        print(f"✅ Создан Excel файл:")
        print(f"   {file_path}")
        print(f"   Листов: {len(wb.sheetnames)}")
        print(f"   Листы: {wb.sheetnames}")

        return file_path
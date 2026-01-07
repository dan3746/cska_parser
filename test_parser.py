from parsers.match_parser import MatchParser
from fixtures import chrome_driver  # Импорт фикстуры


def test_parse_last_match(chrome_driver):  # Используем фикстуру как тест
    parser = MatchParser(chrome_driver)
    match_data = parser.open_base_match().get_last_match_data()
    match_date_list = match_data[1].text.split(',')
    match_name = f"{match_data[0].text} - {match_data[3].text}"
    match_date = f"{match_date_list[0]} - {match_date_list[1]}"

    print("Найден последний матч:", match_name)
    print("Проходивший:", match_date)

    txt_match = parser.read_data_file()
    file_name = f"{match_name} {match_date}"

    if file_name in txt_match:
        print('Матч уже был учтен в списке')
        return

    parser.parse_cska_stats()
    parser.open_last_match()
    parser.add_new_stats()
    parser.clear_and_rewrite_excel()
    parser.archive_excel_file(file_name)
    print(0)
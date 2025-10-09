from functions.desgin.banner import print_banner
from functions.scanner.servers import scan_serv
from functions.scanner.ports import scan
import asyncio
import os
import time
from tqdm import tqdm
import sys

timeout = 1.2
rang = '1-65535'

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def clear_console():
    # Для Windows
    if os.name == 'nt':
        os.system('cls')
    # Для Linux и macOS
    else:
        os.system('clear')


def main_menu():
    print_banner()
    print('1 - загрузить ips')
    print('2 - начать скан')
    print('3 - настройки')
    return input('>')


def parse_ip_range(ip_range):
    try:
        if '/' in ip_range:
            # Это диапазон CIDR
            ip_part, mask_part = ip_range.split('/')
            mask = int(mask_part)

            # Разбиваем IP на октеты
            octets = list(map(int, ip_part.split('.')))

            # Конвертируем IP в число
            ip_num = (octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3]

            # Вычисляем маску сети и количество IP
            network_mask = (0xFFFFFFFF << (32 - mask)) & 0xFFFFFFFF
            network_addr = ip_num & network_mask
            num_hosts = 2 ** (32 - mask)

            # Генерируем все IP
            ips = []
            for i in range(num_hosts):
                current_ip = network_addr + i
                # Конвертируем число обратно в IP
                ip_str = f"{(current_ip >> 24) & 0xFF}.{(current_ip >> 16) & 0xFF}.{(current_ip >> 8) & 0xFF}.{current_ip & 0xFF}"
                ips.append(ip_str)

            return ips
        else:
            # Это одиночный IP
            # Проверяем валидность IP
            octets = list(map(int, ip_range.split('.')))
            if len(octets) != 4 or any(octet < 0 or octet > 255 for octet in octets):
                raise ValueError(f"Некорректный IP-адрес: {ip_range}")

            return [ip_range]

    except Exception as e:
        print(f"Ошибка парсинга '{ip_range}': {e}")
        return []


def read_ip_ranges_simple(filename):
    all_ips = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):  # Пропускаем пустые строки и комментарии
                    ips = parse_ip_range(line)
                    all_ips.extend(ips)
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
        return []
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return []

    return all_ips



def read_ip_ranges_generator(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    ips = parse_ip_range(line)
                    for ip in ips:
                        yield ip
    except FileNotFoundError:
        print(f"Файл {filename} не найден")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")


def is_valid_ip(ip_str):
    try:
        octets = ip_str.split('.')
        if len(octets) != 4:
            return False
        for octet in octets:
            num = int(octet)
            if num < 0 or num > 255:
                return False
        return True
    except:
        return False




ips = []

async def main():
    global timeout, rang
    global ips
    while True:
        res = main_menu()
        if res == '1':
            all_ips = os.listdir('ips')
            all_ips = [item for item in all_ips if os.path.isfile(os.path.join('ips', item))]

            print('выберите список')
            for i, ip_file in enumerate(all_ips, start=1):
                print(i, '-', ip_file)

            choice = int(input('>'))
            ips = read_ip_ranges_simple('ips/' + all_ips[choice - 1])

            clear_console()
            print(f'-ЗАГРУЖЕННО {len(ips)} ip-')

        elif res == '2':
            if not ips:
                print("Сначала загрузите список IP!")
                continue

            for ip in ips:
                print(f'сканирую порты:{ip}')
                ports = await scan(ip, rang, timeout)
                print(f'сканирую сервера:{ip}')
                await scan_serv(ip, ports, timeout)
                print(f'Сканирование {ip} завершено')

            print('Все ip просканированны')
            print('нажмите Enter для продолжения')
            input('>')
            clear_console()

        elif res == '3':
            print("-НАСТРОЙКИ-")
            print("1 - Timeout")
            print("2 - Range")
            print("3 - Filters")
            settings = input('>')
            if settings == '1':
                timeout = int(input('введите таймаут (1.2) по умолчанию >'))
            elif settings == '2':
                rang = input('введите радиус (1 - 65535) по умолчанию >')
            elif settings == '3':
                rang = input('введите радиус (1 - 65535) по умолчанию >')

        else:
            clear_console()
            print("Неверный выбор!")

if __name__ == '__main__':

    asyncio.run(main())

import asyncio
import re
from mcstatus import JavaServer


def clean_motd(motd):
    """Удаляем цветовые коды и лишние пробелы."""
    if motd is None:
        return ""
    motd = str(motd)
    motd = re.sub(r'§.', '', motd)  # убрать цветовые коды (§x)
    motd = motd.replace('\n', ' ').replace('\r', ' ')
    motd = re.sub(r'\s+', ' ', motd).strip()
    return motd


def is_valid_lan_motd(motd: str) -> bool:
    """
    Проверяет, подходит ли MOTD под формат LAN:
    <текст из [A-Za-z0-9_ и пробелов]> - <любой текст>
    """
    # допустимая часть перед дефисом
    pattern = r'^[A-Za-z0-9_ ]+\s*-\s*.+$'
    return bool(re.match(pattern, motd))


async def check(ip, port, semaphore, timeout=3.0):
    async with semaphore:
        server = None
        try:
            server = JavaServer(ip, port)

            # Проверяем статус сервера с таймаутом
            try:
                status = await asyncio.wait_for(server.async_status(), timeout=timeout)
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                # Сервер не отвечает, пропускаем
                return
            except Exception:
                # Другие ошибки соединения, пропускаем
                return

            # Пробуем query (необязательно)
            query_status = False
            try:
                await asyncio.wait_for(server.async_query(), timeout=timeout)
                query_status = True
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                pass  # Query не поддерживается или недоступен
            except Exception:
                pass  # Другие ошибки query

            motd = clean_motd(status.description)
            online = getattr(status.players, "online", 0) or 0
            max_players = getattr(status.players, "max", 0)

            # Проверяем LAN формат
            is_lan = (
                " - " in motd and
                online >= 1 and
                max_players == 8 and
                is_valid_lan_motd(motd)
            )

            server_type = "🟠 LAN-мир (открыт для сети)" if is_lan else "🟢 Публичный сервер"

            # Получаем имена игроков
            players_sample = None
            try:
                sample = status.players.sample
                if sample:
                    names = []
                    for p in sample:
                        try:
                            if isinstance(p, dict) and "name" in p:
                                names.append(p["name"])
                            else:
                                names.append(getattr(p, "name", str(p)))
                        except Exception:
                            continue  # Пропускаем проблемных игроков
                    if names:
                        players_sample = ", ".join(names)
            except Exception:
                pass

            latency = f"{round(status.latency)} ms" if status.latency is not None else "n/a"

            # Выводим только отвечающие серверы
            try:
                version_name = getattr(status.version, "name", "Unknown")
                print(f"{ip}:{port} │ {version_name} │ "
                      f"{online}/{max_players} │ {latency} │ query:{query_status} │ "
                      f"{server_type} │ MOTD: {motd}"
                      + (f" │ Players: {players_sample}" if players_sample else ""))
            except Exception:
                # Если не можем вывести информацию, пропускаем
                return

            # Записываем в файл только если есть онлайн игроки
            if online > 0:
                try:
                    with open("result.txt", "a", encoding="utf-8") as file:
                        file.write(f"\n{ip}:{port}")
                except Exception:
                    pass  # Игнорируем ошибки записи в файл

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            # Сетевые ошибки - пропускаем молча
            return
        except Exception:
            # Любые другие ошибки пропускаем молча
            return



async def scan_servers(ip: str, ports, timeout: float = 1.2):
    semaphore = asyncio.Semaphore(50)
    tasks = [check(ip, port, semaphore, timeout) for port in ports]
    await asyncio.gather(*tasks)


async def scan_serv(ip: str, ports, timeout: float = 1.2):
    await scan_servers(ip, ports, timeout)

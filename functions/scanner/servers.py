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
        try:
            server = JavaServer(ip, port)
            status = await asyncio.wait_for(server.async_status(), timeout=timeout)

            # Пробуем query
            try:
                await asyncio.wait_for(server.async_query(), timeout=timeout)
                query_status = True
            except Exception:
                query_status = False

            motd = clean_motd(status.description)
            online = getattr(status.players, "online", 0) or 0
            max_players = getattr(status.players, "max", 0)

            # Проверяем по условиям LAN
            is_lan = (
                " - " in motd and
                online >= 1 and
                max_players == 8 and
                is_valid_lan_motd(motd)
            )

            server_type = "🟠 LAN-мир (открыт для сети)" if is_lan else "🟢 Публичный сервер"

            # Попытка получить имена игроков
            players_sample = None
            try:
                sample = status.players.sample
                if sample:
                    names = []
                    for p in sample:
                        if isinstance(p, dict) and "name" in p:
                            names.append(p["name"])
                        else:
                            names.append(getattr(p, "name", str(p)))
                    players_sample = ", ".join(names)
            except Exception:
                players_sample = None

            latency = f"{round(status.latency)} ms" if status.latency is not None else "n/a"

            print(f"{ip}:{port} │ {status.version.name} │ "
                  f"{online}/{max_players} │ {latency} │ query:{query_status} │ "
                  f"{server_type} │ MOTD: {motd}"
                  + (f" │ Players: {players_sample}" if players_sample else ""))

            if online > 0:
                with open("result.txt", "a", encoding="utf-8") as file:
                    file.write(f"\n{ip}:{port}")

        except Exception:
            pass


async def scan_servers(ip: str, ports, timeout: float = 1.2):
    semaphore = asyncio.Semaphore(50)
    tasks = [check(ip, port, semaphore, timeout) for port in ports]
    await asyncio.gather(*tasks)


async def scan_serv(ip: str, ports, timeout: float = 1.2):
    await scan_servers(ip, ports, timeout)
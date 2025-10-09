import asyncio
import socket
from typing import List
import time


class AsyncPortScanner:
    def __init__(self, timeout: float = 1.0, concurrency_limit: int = 500):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.scanned_ports = 0
        self.total_ports = 0
        self.start_time = 0

    async def check_port(self, host: str, port: int, open_ports: List[int]) -> None:
        async with self.semaphore:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=self.timeout
                )
                writer.close()
                await writer.wait_closed()
                open_ports.append(port)  # Добавляем только номер порта
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                pass  # Игнорируем закрытые порты
            except Exception:
                pass  # Игнорируем другие ошибки
            finally:
                self.scanned_ports += 1
                self.update_progress()

    def update_progress(self):
        elapsed = time.time() - self.start_time
        ports_per_second = self.scanned_ports / elapsed if elapsed > 0 else 0
        percent = (self.scanned_ports / self.total_ports) * 100
        bar_length = 30
        filled_length = int(bar_length * self.scanned_ports // self.total_ports)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\r|{bar}| {percent:.1f}% ({self.scanned_ports}/{self.total_ports}) "
              f"{ports_per_second:.1f} портов/сек", end='', flush=True)

    async def scan_ports(self, host: str, ports: List[int]) -> List[int]:
        self.total_ports = len(ports)
        self.scanned_ports = 0
        self.start_time = time.time()

        open_ports = []  # Теперь храним только номера открытых портов
        tasks = []
        for port in ports:
            task = asyncio.create_task(self.check_port(host, port, open_ports))
            tasks.append(task)

        await asyncio.gather(*tasks)
        print()
        return sorted(open_ports)  # Возвращаем отсортированный список портов


def parse_ports(ports_str: str) -> List[int]:
    ports = set()
    for part in ports_str.split(','):
        if '-' in part:
            start, end = part.split('-')
            start_val = int(start)
            end_val = int(end)
            if start_val < 1 or end_val > 65535:
                raise ValueError("Ports must be in range 1-65535")
            ports.update(range(start_val, end_val + 1))
        else:
            port_val = int(part)
            if port_val < 1 or port_val > 65535:
                raise ValueError("Ports must be in range 1-65535")
            ports.add(port_val)
    return sorted(ports)


async def async_scan(host: str, ports_str: str, timeout: float = 1.2, concurrency: int = 400):

    ports = parse_ports(ports_str)
    scanner = AsyncPortScanner(timeout=timeout, concurrency_limit=concurrency)
    open_ports = await scanner.scan_ports(host, ports)  # Теперь получаем только список портов

    total_time = time.time() - scanner.start_time
    print(f"\nСканирование завершено за {total_time:.2f} секунд")
    print(f"Найдено открытых портов: {len(open_ports)}")

    return open_ports

async def scan(ip: str, ports: str, timeout: float = 1.2, concurrency: int = 400):
    open_ports = await (async_scan(ip, ports))
    return open_ports
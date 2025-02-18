from mcstatus import JavaServer
import socket
import concurrent.futures
from colorama import init, Fore, Style
import sys
import json
import threading

# Инициализация colorama
init(autoreset=True)

BATCH_SIZE = 10000  # Количество портов, проверяемых одновременно
MAX_WORKERS = 80000  # Количество потоков для быстрого сканирования
lock = threading.Lock()  # Глобальный лок для потокобезопасной записи в файл

def log(message, color="\033[90m"):
    print(f"{color}[LOG] {message}\033[0m")

def resolve_domain(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def save_to_file(filename, server):
    with lock:
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        data.append(server)
        
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    
    log(f"Добавлен сервер {server['ip']}:{server['port']} в {filename}", "\033[91m")

def check_server(ip, port, filename):
    try:
        server = JavaServer.lookup(f"{ip}:{port}")
        status = server.status()
        
        motd = status.description if isinstance(status.description, str) else " ".join(
            line['text'] for line in status.description.get('extra', []) if isinstance(line, dict) and 'text' in line
        )
        
        if "Server not found" in motd:
            return None
        
        result = {
            "ip": ip,
            "port": port,
            "motd": motd,
            "players": f"{status.players.online}/{status.players.max}",
            "version": status.version.name,
            "core": status.version.protocol,
            "latency": round(status.latency, 2)
        }
        
        print(
            f"\n{Fore.GREEN}-----------------------------------------\n"
            f"{Fore.YELLOW} Сервер найден на {Fore.MAGENTA}{ip}:{port}\n"
            f"{Fore.CYAN} MOTD: {Fore.WHITE}{motd}\n"
            f"{Fore.CYAN} Игроки: {Fore.WHITE}{status.players.online}/{status.players.max}\n"
            f"{Fore.CYAN} Версия: {Fore.WHITE}{status.version.name}\n"
            f"{Fore.CYAN} Core: {Fore.WHITE}{status.version.protocol}\n"
            f"{Fore.CYAN} Пинг: {Fore.WHITE}{round(status.latency, 2)} ms\n"
            f"{Fore.GREEN}-----------------------------------------\n"
        )
        
        save_to_file(filename, result)
        return result
    except (socket.timeout, ConnectionRefusedError):
        return None
    except Exception:
        return None

def scan_minecraft_servers(ip, start_port, end_port):
    filename = f"{ip}.json"
    ports = list(range(start_port, end_port + 1))
    total_ports = len(ports)
    log(f"Запуск сканирования {total_ports} портов на {ip}...", "\033[90m")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_server, ip, port, filename): port for port in ports}
        for i, _ in enumerate(concurrent.futures.as_completed(futures)):
            sys.stdout.write(f"\r\033[90mПроверено {i + 1}/{total_ports} портов...\033[0m")
            sys.stdout.flush()
    
    log("Сканирование завершено!", "\033[90m")

def scan_ip_range(base_ip, start_port, end_port):
    filename = f"range_scan_{base_ip}.json"
    for i in range(256):
        ip = f"{base_ip}.{i}"
        log(f"Сканируем {ip}...")
        scan_minecraft_servers(ip, start_port, end_port)

def main():
    mode = input("\033[91mВыберите режим сканирования:\n1 - Сканировать один IP\n2 - Сканировать диапазон IP (xxx.xxx.xxx.0-255)\nВаш выбор: \033[0m")
    if mode == "1":
        ip_or_domain = input("\033[91mВведите IP-адрес или доменное имя: \033[0m").strip()
        ip = resolve_domain(ip_or_domain) if not ip_or_domain.replace(".", "").isdigit() else ip_or_domain
        if not ip:
            print("\033[91mОшибка: Неверный домен или IP-адрес.\033[0m")
            return
        
        start_port = int(input("\033[91mВведите начальный порт: \033[0m"))
        end_port = int(input("\033[91mВведите конечный порт: \033[0m"))
        
        scan_minecraft_servers(ip, start_port, end_port)

    elif mode == "2":
        base_ip = input(f"{Fore.CYAN}Введите первые три октета IP (например, 192.168.1): {Fore.WHITE}")
        start_port = int(input(f"{Fore.CYAN}Введите начальный порт: {Fore.WHITE}"))
        end_port = int(input(f"{Fore.CYAN}Введите конечный порт: {Fore.WHITE}"))
        scan_ip_range(base_ip, start_port, end_port)
    else:
        print(f"{Fore.RED}Неверный выбор. Перезапустите программу и выберите 1 или 2.")


if __name__ == "__main__":
    main()

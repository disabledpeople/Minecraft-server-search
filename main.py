from mcstatus import JavaServer
import socket
import concurrent.futures
from colorama import init, Fore, Style
import sys
import time

# Инициализация colorama
init(autoreset=True)

BATCH_SIZE = 100  # Количество портов, проверяемых одновременно

def log(message, color=Fore.WHITE):
    print(f"{color}[LOG] {message}{Style.RESET_ALL}")

def print_banner():
    banner = f"""
    {Fore.GREEN}=======================================
    {Fore.YELLOW}        __  __    _____    _____ 
    {Fore.YELLOW}       |  \/  |  / ____|  / ____|
    {Fore.YELLOW}       | \  / | | (___   | (___  
    {Fore.YELLOW}       | |\/| |  \___ \   \___ \ 
    {Fore.YELLOW}       | |  | |  ____) |  ____) |
    {Fore.YELLOW}       |_|  |_| |_____/  |_____/                        
    {Fore.GREEN}=======================================
    {Fore.CYAN}     Server Scanner v1.1 by betarika
    {Fore.GREEN}=======================================
    """
    print(banner)

def check_server(ip, port):
    try:
        server = JavaServer.lookup(f"{ip}:{port}")
        status = server.status()
        
        motd = status.description if isinstance(status.description, str) else " ".join(
            line['text'] for line in status.description.get('extra', []) if isinstance(line, dict) and 'text' in line
        )
        
        result = (
            f"\n{Fore.GREEN}-----------------------------------------\n"
            f"{Fore.YELLOW} Сервер найден на {Fore.MAGENTA}{ip}:{port}\n"
            f"{Fore.CYAN} MOTD: {Fore.WHITE}{motd}\n"
            f"{Fore.CYAN} Игроки: {Fore.WHITE}{status.players.online}/{status.players.max}\n"
            f"{Fore.CYAN} Версия: {Fore.WHITE}{status.version.name}\n"
            f"{Fore.CYAN} Core: {Fore.WHITE}{round(status.latency, 2)} ms\n"
            f"{Fore.CYAN} Пинг: {Fore.WHITE}{status.version.protocol}\n"
            f"{Fore.GREEN}-----------------------------------------\n"
        )
        print(result)
        return result
    except (socket.timeout, ConnectionRefusedError):
        return None
    except Exception:
        return None

def scan_minecraft_servers(ip, start_port, end_port):
    ports = list(range(start_port, end_port + 1))
    total_ports = len(ports)
    log(f"Запуск сканирования {total_ports} портов...", Fore.YELLOW)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for i in range(0, total_ports, BATCH_SIZE):
            batch = ports[i:i + BATCH_SIZE]
            sys.stdout.write(f"\r{Fore.BLUE}Сканирование портов {batch[0]}-{batch[-1]}... ")
            sys.stdout.flush()
            futures = {executor.submit(check_server, ip, port): port for port in batch}
            for future in concurrent.futures.as_completed(futures):
                future.result()
            print()  # Перенос строки после завершения батча
    
    log("Сканирование завершено!", Fore.YELLOW)

def main():
    print_banner()
    ip = input(f"{Fore.CYAN}Введите IP-адрес (пример 92.158.1.38): {Fore.WHITE}")
    start_port = int(input(f"{Fore.CYAN}Введите начальный порт: {Fore.WHITE}"))
    end_port = int(input(f"{Fore.CYAN}Введите конечный порт: {Fore.WHITE}"))
    
    print(f"\n{Fore.YELLOW}Сканирование...{Style.BRIGHT}")
    scan_minecraft_servers(ip, start_port, end_port)
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Сканирование завершено!")

if __name__ == "__main__":
    main()

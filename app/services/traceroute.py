import subprocess
import re
import socket
import logging
from typing import List, Dict, Any
from .geolocation import get_geolocation
import dns.resolver

logger = logging.getLogger(__name__)

def resolve_dns(target: str) -> str:
    try:
        # Check if already IP
        socket.inet_aton(target)
        return target
    except socket.error:
        pass
    
    try:
        answers = dns.resolver.resolve(target, 'A')
        return answers[0].to_text()
    except Exception as e:
        logger.error(f"DNS Resolution failed for {target}: {e}")
        return None

def is_valid_target(target: str) -> bool:
    # Regex to allow valid domains, IPv4, IPv6. Prevents command injection.
    pattern = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$|^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$|^([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}$')
    return bool(pattern.match(target))

def resolve_hostname(ip: str) -> str:
    if not ip or ip == "*":
        return "-"
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "-"

async def run_traceroute(target: str) -> List[Dict[str, Any]]:
    if not is_valid_target(target):
        raise ValueError("Invalid target format.")

    # Using -n for no DNS resolution by traceroute itself (we do it manually), -m 30 for max hops, -w 1 for timeout
    cmd = ["traceroute", "-n", "-q", "1", "-w", "1", "-m", "30", target]
    
    logger.info(f"Running traceroute command: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=60)
        
        if process.returncode != 0:
            logger.error(f"Traceroute failed: {stderr}")
            raise RuntimeError("Traceroute execution failed.")
            
        hops = []
        lines = stdout.split('\n')[1:] # Skip header
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                hop_num = int(parts[0])
                ip = parts[1]
                
                if ip == "*":
                    hops.append({
                        "hop_number": hop_num,
                        "ip": "-",
                        "hostname": "-",
                        "delay": 0.0,
                        "country": "-",
                        "city": "-",
                        "lat": None,
                        "lon": None
                    })
                else:
                    delay = float(parts[2]) if len(parts) > 2 else 0.0
                    hostname = resolve_hostname(ip)
                    country, city, lat, lon = get_geolocation(ip)
                    
                    hops.append({
                        "hop_number": hop_num,
                        "ip": ip,
                        "hostname": hostname,
                        "delay": delay,
                        "country": country or "-",
                        "city": city or "-",
                        "lat": lat,
                        "lon": lon
                    })
        return hops

    except subprocess.TimeoutExpired:
        process.kill()
        logger.error("Traceroute command timed out")
        raise RuntimeError("Traceroute command timed out")
    except Exception as e:
        logger.error(f"Traceroute error: {e}")
        raise RuntimeError(str(e))
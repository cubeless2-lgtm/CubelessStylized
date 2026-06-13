"""Send a raw command JSON to the UnrealMCP editor bridge (127.0.0.1:55557).

Usage: python send_bridge_command.py <json-file-or-inline-json>
"""
import json
import socket
import sys


def main() -> None:
    arg = sys.argv[1]
    try:
        payload = json.loads(arg)
    except json.JSONDecodeError:
        with open(arg, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)

    data = json.dumps(payload).encode("utf-8")
    with socket.create_connection(("127.0.0.1", 55557), timeout=30) as s:
        s.sendall(data)
        s.settimeout(30)
        chunks = []
        while True:
            try:
                chunk = s.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            chunks.append(chunk)
            try:
                json.loads(b"".join(chunks).decode("utf-8"))
                break
            except json.JSONDecodeError:
                continue
    print(b"".join(chunks).decode("utf-8"))


if __name__ == "__main__":
    main()

"""Minimal UnrealMCP bridge client: send execute_python to 127.0.0.1:55557.

Usage:
  python bridge_exec.py <script.py> [--defer] [--raw]   # run file content as Unreal Python
  python bridge_exec.py --code "print('hi')"            # run inline code

Prints the JSON response. Exit code 1 on bridge/command failure.

By default the code is wrapped in a throwaway function scope before sending.
Engine PythonScriptPlugin executes inline code in the PERSISTENT console
globals (PyConsoleGlobalDict): top-level variables survive until editor
shutdown, and any unreal.Object wrapper they hold becomes a GC root via
FPyReferenceCollector, blocking asset deletes (ForceDelete dialog spam).
Function locals die on return, so wrapping prevents the leak. --raw bypasses
(needed only for code that must mutate the console globals itself).
"""
import json
import socket
import sys


def wrap_scoped(code: str) -> str:
    body = "\n".join(("    " + ln) if ln.strip() else ln for ln in code.splitlines())
    return (
        "def __ieta_scoped__():\n" + body + "\n"
        "__ieta_scoped__()\n"
        "del __ieta_scoped__\n"
        "import gc as __ieta_gc\n"
        "__ieta_gc.collect()\n"
        "del __ieta_gc\n"
    )


def send_command(command: str, params: dict, timeout: float = 300.0) -> dict:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(("127.0.0.1", 55557))
    try:
        sock.sendall(json.dumps({"type": command, "params": params}).encode("utf-8"))
        chunks = []
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            chunks.append(chunk)
            # The bridge sends one JSON document; try to parse eagerly.
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except json.JSONDecodeError:
                continue
        return json.loads(b"".join(chunks).decode("utf-8"))
    finally:
        sock.close()


def main() -> int:
    args = sys.argv[1:]
    defer = "--defer" in args
    raw = "--raw" in args
    args = [a for a in args if a not in ("--defer", "--raw")]
    if not args:
        print("usage: bridge_exec.py <script.py> | --code <code> [--defer] [--raw]")
        return 1
    if args[0] == "--code":
        code = args[1]
    else:
        with open(args[0], "r", encoding="utf-8") as handle:
            code = handle.read()
    if not raw:
        code = wrap_scoped(code)
    response = send_command(
        "execute_python",
        {"code": code, "mode": "ExecuteFile", "defer_to_ticker": defer},
    )
    print(json.dumps(response, ensure_ascii=False, indent=2))
    status_ok = response.get("status") == "success" if isinstance(response, dict) else False
    return 0 if status_ok else 1


if __name__ == "__main__":
    sys.exit(main())

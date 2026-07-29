import subprocess, sys

# 检查是否有 checkpoint sweep 相关 python 进程在运行
try:
    out = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, StartTime, CPU, @{n='Cmd';e={(Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine}} | Format-List | Out-String"],
        text=True, stderr=subprocess.STDOUT, timeout=30
    )
    print("=== RUNNING PYTHON PROCESSES ===")
    print(out if out.strip() else "(no python process found via Get-Process)")
except Exception as e:
    print("ERR:", e)

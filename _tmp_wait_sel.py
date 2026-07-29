import os, time, subprocess

mappo_sel = "results/paper_config_runs/dev_1m/checkpoint_sweeps/mappo_seeds1_2/validation_selected_checkpoints.csv"
happo_sel = "results/paper_config_runs/dev_1m/checkpoint_sweeps/happo_seeds1_2/validation_selected_checkpoints.csv"

def proc_alive(keyword):
    try:
        # 用 wmic 更稳定地匹配命令行
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object {$_.CommandLine -like '*" + keyword + "*'} | "
             "Measure-Object | Select-Object -ExpandProperty Count"],
            text=True, stderr=subprocess.STDOUT, timeout=20)
        return out.strip() not in ("", "0")
    except Exception as e:
        return True  # 检测失败时保守认为仍活着

deadline = time.time() + 60*60  # 最多等 1 小时
while time.time() < deadline:
    m_done = os.path.exists(mappo_sel)
    h_done = os.path.exists(happo_sel)
    m_alive = proc_alive("evaluate_3d_checkpoint_sweep")
    h_alive = proc_alive("evaluate_happo_checkpoint_sweep")
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] mappo_sel={m_done}(proc={m_alive}) happo_sel={h_done}(proc={h_alive})")
    if m_done and h_done:
        print("BOTH_SELECTION_FILES_PRESENT")
        break
    if not m_alive and not h_alive:
        # 两个进程都退出后再等一小会儿让文件 flush
        time.sleep(10)
        m_done = os.path.exists(mappo_sel)
        h_done = os.path.exists(happo_sel)
        if m_done and h_done:
            print("BOTH_SELECTION_FILES_PRESENT")
        else:
            print("PROCS_DEAD_INCOMPLETE m=%s h=%s" % (m_done, h_done))
        break
    time.sleep(60)

print("MONITOR_DONE")

import sys, torch
p = sys.argv[1]
try:
    payload = torch.load(p, map_location="cpu", weights_only=False)
    update = int(payload.get("update", 0))
    opt = bool(payload.get("optimizer_state") or payload.get("optimizer_states"))
    print(f"{update} {int(opt)} 1")
except Exception as e:
    print(f"0 0 0")

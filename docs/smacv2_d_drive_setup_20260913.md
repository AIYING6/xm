# SMACv2 全 D 盘运行时部署

目标目录固定为：

```text
D:\MARL\StarCraftII\
├── Versions\...\SC2_x64.exe
└── Maps\SMAC_Maps\32x32_flat.SC2Map
```

Python 环境 `D:\Anaconda\envs\.conda\envs\cac` 和项目目录
`D:\Code\Codex\ri_gmappo_uav` 已在 D 盘；不会向 C 盘安装项目运行时。

## 一次性人工安装

1. 使用 Battle.net 安装免费的 StarCraft II Starter Edition；安装位置选择
   `D:\MARL\StarCraftII`。不要选择默认 C 盘路径。
2. 安装完成后，在项目根目录执行下列**只读检查**：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_smacv2_d_drive_runtime.ps1
```

3. 若输出 `SMACV2_MAPS_MISSING`，确认目标目录无误后执行显式地图安装：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_smacv2_d_drive_runtime.ps1 -InstallMaps
```

该参数只会从本项目 `third_party\smacv2` 的官方地图副本复制到
`D:\MARL\StarCraftII\Maps\SMAC_Maps`；不会删除或覆盖 SC2 的其他目录。

4. 在当前 PowerShell 会话中设置运行时路径：

```powershell
$env:SC2PATH = 'D:\MARL\StarCraftII'
```

随后运行随机合法动作 smoke test；该 smoke test 不训练、不更新参数。

## 边界

- SMACv2 官方 README 指定 Windows 通过 StarCraft 官网/Battle.net 安装客户端；SMAC/SMACv2 需要通过 `SC2PATH` 定位非默认安装目录，并要求自定义地图位于 SC2 的 `Maps` 目录。
- 目录验证或地图复制成功，只表示运行时前提满足，**不**表示 MAPPO 已可学、新算法已确定或论文主张成立。

# T527 - eMMC 5.1 KiCad 库生成器

本仓库使用 Python 自动生成符合 JEDEC 标准的 eMMC 5.1 153-ball FBGA 封装与原理图符号，可直接用于 KiCad 7/8。

## 📦 生成内容

- `emmc_kicad/eMMC.pretty/eMMC153_FBGA-11.5x13_P0.5.kicad_mod` - KiCad 封装
  - 封装尺寸 11.5 x 13.0 x 1.0 mm
  - Ball pitch 0.5mm, 直径 0.3mm, 阵列 14x14 去除 43 个空位得到 153
  - 符合 JEDEC MO-276 BA, E1=D1=6.5mm
  - 包含 Fab/CrtYd/Silk 层, A1 标记
- `emmc_kicad/eMMC.kicad_sym` - KiCad 原理图符号
  - 符号 `eMMC_5.1_153BGA`
  - 左侧 Bus (DAT0-7, CMD, CLK, DS, RST_n), 右侧 Power (VCC, VCCQ, VSS, VSSQ, VDDi), 顶部/底部 NC/RFU/VSF
  - 引脚编号与封装一一对应 (A1-P14)
- `emmc_kicad/emmc153_pinout.csv` - 引脚表
- `emmc_kicad/generate_emmc.py` - 生成器脚本

## 🔧 eMMC 5.1 关键规格

| 项目 | 值 |
|------|-----|
| 标准 | JEDEC JESD84-B51, HS400 |
| 封装 | FBGA 153 balls, 11.5x13mm, 0.5mm pitch |
| 数据速率 | HS400 400MB/s, 200MHz DDR |
| 总线 | 1-bit/4-bit/8-bit, 8 数据线 |
| 信号 | CLK (M6), CMD (M5), DAT0-7 (A3-A5,B2-B6), DS (H5), RST_n (K5) |
| 电源 | VCC x4 (E6,F5,J10,K9) 2.7-3.6V, VCCQ x5 (C6,M4,N4,P3,P5) 1.8V/3.3V |
| 地 | VSS x6 (A6,E7,G5,H9/H10,J5,K8), VSSQ x5 (C4,N2,N5,P4,P6) |
| VDDi | C2 - 内部 LDO, 接 1uF+4.7uF 到地 |
| RFU | A7,E5,G3,K6,K7 - 保留, 悬空, 禁止布线 |
| VSF | E8,E9,F9,G9,K11,P10 - 厂商自定义, 悬空 |
| NC | 其余 - 结构支撑, 允许布线穿过 (JEDEC) |

## 🚀 快速开始

```bash
# 生成库
python3 emmc_kicad/generate_emmc.py

# 查看生成文件
ls emmc_kicad/eMMC.pretty/
ls emmc_kicad/*.kicad_sym
cat emmc_kicad/emmc153_pinout.csv
```

### KiCad 中使用

1. **封装库**:
   - 复制 `eMMC.pretty` 到工程或 `~/Documents/KiCad/7.0/footprints/`
   - PCB编辑器 -> 首选项 -> 管理封装库 -> 添加 `eMMC.pretty`

2. **符号库**:
   - 原理图编辑器 -> 首选项 -> 管理符号库 -> 添加 `eMMC.kicad_sym`

3. **原理图设计**:
   - 放置 `eMMC_5.1_153BGA`
   - VCC/VCCQ 每个球 0.1uF+4.7uF 去耦, 靠近引脚
   - VDDi 接 1uF + 4.7uF 到 GND
   - RST_n 上拉 47k 到 VCCQ, 并联 0.1uF 到 GND
   - CMD/DAT0-3 上拉 47k 到 VCCQ (DAT0 必须), DAT4-7 上拉 47k (8-bit时)
   - CLK 串联 0-22Ω 终端, DS 下拉 47k
   - RFU/VSF 悬空

4. **PCB 设计**:
   - 焊盘 NSMD: 铜 0.3mm, 阻焊 0.35mm
   - 线宽/间距 0.15mm/0.15mm (6mil) 可从 NC 间逃逸
   - 过孔 0.3mm/0.6mm
   - 高速等长: DAT0-7 <0.5mm偏差, CLK/DS 参考
   - 阻抗 50Ω 单端
   - 完整电源平面, 地平面

## 📜 生成器原理

`generate_emmc.py` 核心逻辑:

```python
ROWS = ['A','B','C','D','E','F','G','H','J','K','L','M','N','P'] # 14行
COLS = 1..14
NO_BALL = 43 个空位 (中心去 populated)
ball_coord(row,col): (col-7.5)*0.5, (6.5 - row_index)*0.5
FUNC_MAP: 功能映射 (DAT, CLK, CMD, VCC等)
生成 .kicad_mod: S-Expression, SMD roundrect pads
生成 .kicad_sym: version 20231120, 左Bus右Power
```

可扩展到 169-ball (12x16mm), 221-ball 等, 只需改 `BODY_W/H`, `NO_BALL`.

## 📚 参考

- JEDEC JESD84-B51 / MO-276 BA / Figure 3.12.1-49
- Micron MTFCxxG eMMC datasheet
- AllianceMemory ASFC32G31T3
- SMARTsemi KTM8GL1ASI01
- Octavo Systems "Designing for Flexibility around eMMC"
- Flexxon eMMC 5.1 153ball SPEC

## 📄 文件

```
T527/
  emmc_kicad/
    generate_emmc.py          # 生成器
    eMMC.pretty/
      eMMC153_FBGA-11.5x13_P0.5.kicad_mod
    eMMC.kicad_sym             # 符号库
    emmc153_pinout.csv         # 引脚表
    README_AUTO.md             # 自动生成详细说明
  README.md
```

## ✅ 验证

生成的封装包含 153 焊盘, 符号包含 153 引脚, 坐标符合 JEDEC.

```bash
grep -c "(pad" emmc_kicad/eMMC.pretty/*.kicad_mod  # 应输出 153
grep -c "(pin" emmc_kicad/eMMC.kicad_sym            # 应输出 153
```

MIT License - 可自由用于商业项目.


# eMMC 5.1 KiCad 库 - Python 生成

本库由 `generate_emmc.py` 自动生成, 包含 eMMC 5.1 153-ball FBGA 封装与原理图符号.

## 规格

- **标准**: JEDEC eMMC 5.1 (JESD84-B51), 兼容 HS400 (200MHz DDR, 400MB/s)
- **封装**: FBGA 153-ball, Body 11.5 x 13.0 x 1.0 mm, Pitch 0.5mm, Ball Ø 0.3mm
- **Ball Map**: MO-276 BA, E1=6.5mm, D1=6.5mm, SE=SD=0.25mm BSC
- **球数**: 153 (14x14 网格除去 43 个空位得到)
- **电源**:
  - VCC: 4 balls (E6, F5, J10, K9) - NAND Flash 供电 2.7-3.6V
  - VCCQ: 5 balls (C6, M4, N4, P3, P5) - 控制器 & IO 供电 1.7-1.95V / 2.7-3.6V
  - VSS: 6+ balls (A6, E7, G5, H9/H10, J5, K8) - GND
  - VSSQ: 5 balls (C4, N2, N5, P4, P6) - IO GND
  - VDDi: 1 ball (C2) - 内部 LDO 输出, 接 1uF+4.7uF 去耦到 GND
- **信号**:
  - CLK: M6 - 时钟输入, 最大 200MHz
  - CMD: M5 - 命令双向, OD(初始化) / PP(传输)
  - DAT0-DAT7: A3,A4,A5,B2,B3,B4,B5,B6 - 双向数据, 默认仅 DAT0, 可配置 4/8-bit
  - DS: H5 - Data Strobe, HS400 模式器件产生, 用于读取对齐
  - RST_n: K5 - 硬件复位, 低有效, 需上拉
  - RFU: A7,E5,G3,K6,K7 - 保留未来使用, 保持悬空, 布线时避开
  - VSF: E8,E9,F9,G9,K11,P10 - 厂商自定义, 悬空, 避开布线
  - NC: 其余 - 纯机械支撑, 标准允许布线穿过 (Octavo Systems App Note)

## 文件结构

```
emmc_kicad/
  generate_emmc.py
  eMMC.pretty/
    eMMC153_FBGA-11.5x13_P0.5.kicad_mod
  eMMC.kicad_sym
  README.md
```

## 使用方法

1. 在 KiCad 中:
   - 复制 `eMMC.pretty` 到你的工程或全局库路径, 在 PCB 编辑器 - 管理封装库 添加
   - 导入 `eMMC.kicad_sym` 到原理图库表

2. 原理图:
   - 放置符号 `eMMC_5.1_153BGA`
   - VCC/VCCQ 需去耦: 每个电源球附近 0.1uF + 4.7uF, VDDi 接 1uF+电容到 GND
   - RST_n 上拉 10k-47k 到 VCCQ, 并接 0.1uF 到 GND 做复位延时
   - CMD, DAT0-7 上拉 10k-47k 到 VCCQ (DAT0 必须, 其他可选但推荐), CLK 下拉 10k optional
   - DS 下拉 10k 到 GND (按 JEDEC)
   - 未使用的 DAT线若不配置 8-bit 可悬空但建议上拉
   - RFU/VSF 保持悬空, 不布线通过

3. PCB:
   - 封装原点居中, A1 在左上, 有丝印圆圈标记
   - 焊盘 0.3mm, 非阻焊定义 (NSMD) 推荐阻焊开窗 0.35mm
   - 走线 6mil/6mil, 过孔 12mil/24mil 可从 NC 球间逃逸 (Octavo 推荐)
   - 电源完整性: VCC/VCCQ 各层完整平面, 多点过孔
   - 高速: CLK, DS 50Ω 单端 / 100Ω 差分阻抗, 等长 DAT0-7 < 0.5mm 偏差, CMD 参考 DAT
   - 散热: 底部大铜皮, 热过孔

## Python 生成器说明

`generate_emmc.py` 做了:

- 定义 14x14 网格, 坐标计算 `ball_coord()`
- 定义 43 个 No Ball 位置达到 153
- 定义功能映射 `FUNC_MAP`
- 生成 `.kicad_mod`: 包含 Fab/CrtYd/Silk, 焊盘命名 A1-P14, 类型 SMD roundrect
- 生成 `.kicad_sym`: 左 Bus 右 Power 上 NC 下 RFU/VSF

可二次开发:

- 修改 `NO_BALL` 以适配不同厂商 depopulation
- 修改 `FUNC_MAP` 以适配 VSF 差异
- 修改 `BODY_W/H`, `BALL_PITCH` 生成其他尺寸 (如 12x16 169BGA, 12x18 221等)

## 兼容性

- KiCad 6/7/8 兼容的 S-Expression 格式
- Footprint 符合 KLC 命名规范

## 参考

- JEDEC Standard No. 21-C Figure 3.12.1-49 Ball Assignment
- JEDEC JESD84-B51 eMMC 5.1
- Micron MTFC16GAKAECN datasheet (153 ball top view)
- AllianceMemory ASFC32G31T3 datasheet
- SMARTsemi KTM8GL1ASI01 datasheet
- Octavo Systems App Note "Designing for Flexibility around eMMC"
- Flexxon XTRA III eMMC 5.1 153ball SPEC

生成时间: 自动

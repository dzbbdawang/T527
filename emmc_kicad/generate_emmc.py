#!/usr/bin/env python3
"""
eMMC 5.1 KiCad 封装和原理图生成器
- 生成 153-ball FBGA 11.5x13mm 0.5mm pitch 封装
- 生成 eMMC 5.1 原理图符号

JEDEC 规格参考:
- 封装: FBGA 153, Body 11.5x13x1.0mm, Ball pitch 0.5mm
- Ball array: 14x14 最大 196, 实际 153 个球 (MO-276 BA)
  E1 = D1 = 6.5mm (外侧球间距), SE=SD=0.25mm (BSC)
- 电源: VCC (2.7-3.6V) 4 balls, VCCQ (1.7-1.95V / 2.7-3.6V) 5 balls
  VSS 6 balls, VSSQ 5 balls, VDDi 1 ball, DS, RST_n 等
- 关键信号: CLK, CMD, DAT0-DAT7, DS (Data Strobe for HS400), RST_n

Ball Map 依据:
- AllianceMemory ASFC32G31T3 datasheet (M4 VCCQ, M5 CMD, M6 CLK)
- SMARTsemi DS (RFU/VSF 定义)
- UMT eMMC5.1 datasheet
- JEDEC JESD84-B51 / MO-276

布局策略:
- 以 14x14 网格为基础 (Rows A,B,C,D,E,F,G,H,J,K,L,M,N,P)
- 移除 43 个中心区域空位以达到 153
- 坐标原点在封装中心, X: -3.25 ~ +3.25, Y: +3.25 ~ -3.25

生成的 KiCad 文件兼容 KiCad 7/8
"""

import os
import math
from pathlib import Path

# ========= 配置 =========
BODY_W = 11.5
BODY_H = 13.0
BODY_THICKNESS = 1.0
BALL_PITCH = 0.5
BALL_DIAM = 0.30
PAD_SIZE = 0.30  # SMD pad 0.30 mm
E1 = 6.5  # ball array extent X
D1 = 6.5  # ball array extent Y
# Row labels: 14 rows
ROWS = ['A','B','C','D','E','F','G','H','J','K','L','M','N','P']
COLS = list(range(1,15))  # 1-14

# 计算坐标: 原点中心
# col 1 在左侧 -E1/2, col14 在右侧 +E1/2
# row A 在顶部 +D1/2, row P 在底部 -D1/2
def ball_coord(row_label, col):
    row_idx = ROWS.index(row_label)  # 0=A top
    # X: (col - 7.5)*pitch
    x = (col - 7.5) * BALL_PITCH
    # Y: (7.5 - row_idx -1?) actually row 0 => +3.25, row13 => -3.25
    y = (6.5 - row_idx) * BALL_PITCH  # 6.5 = 13/2
    # Note: KiCad footprint Y positive down? In KiCad, Y positive up? Actually board Y up? Use standard: A at top => positive Y
    return (round(x,3), round(y,3))

# 定义 43 个空位 (No Ball) 来达到 153
NO_BALL = set()
# 按之前设计的 43 个位置
NO_BALL.update([
    ('D',5),('D',6),('D',7),('D',8),('D',9),('D',10),('D',11),
    ('E',4),('E',10),('E',14),
    ('F',4),('F',6),('F',7),('F',8),('F',10),('F',14),
    ('G',4),('G',6),('G',7),('G',8),('G',10),('G',14),
    ('H',4),('H',6),('H',7),('H',8),('H',10),('H',14),
    ('J',4),('J',6),('J',7),('J',8),('J',10),('J',14),
    ('K',4),('K',10),('K',14),
    ('L',4),('L',5),('L',6),('L',7),('L',8),('L',9),
])
assert len(NO_BALL) == 43, f"NO_BALL count {len(NO_BALL)}"

# 功能引脚映射 (基于 JEDEC + 厂商 datasheet)
# 值: (signal name, type)
# type 用于 symbol
FUNC_MAP = {
    # 数据线
    ('A',3): ('DAT0','bidirectional'),
    ('A',4): ('DAT1','bidirectional'),
    ('A',5): ('DAT2','bidirectional'),
    ('B',2): ('DAT3','bidirectional'),
    ('B',3): ('DAT4','bidirectional'),
    ('B',4): ('DAT5','bidirectional'),
    ('B',5): ('DAT6','bidirectional'),
    ('B',6): ('DAT7','bidirectional'),
    # 时钟 命令
    ('M',5): ('CMD','bidirectional'),
    ('M',6): ('CLK','input'),
    ('H',5): ('DS','output'),  # Data Strobe HS400
    ('K',5): ('RST_n','input'),
    # 电源
    ('C',2): ('VDDi','power_in'),  # internal LDO, 需要外接电容到 GND
    ('E',6): ('VCC','power_in'),
    ('F',5): ('VCC','power_in'),
    ('J',10):('VCC','power_in'),
    ('K',9): ('VCC','power_in'),
    ('C',6): ('VCCQ','power_in'),
    ('M',4): ('VCCQ','power_in'),
    ('N',4): ('VCCQ','power_in'),
    ('P',3): ('VCCQ','power_in'),
    ('P',5): ('VCCQ','power_in'),
    # 地
    ('A',6): ('VSS','power_in'),
    ('E',7): ('VSS','power_in'),
    ('G',5): ('VSS','power_in'),
    ('H',9): ('VSS','power_in'),  # 也有 H10
    ('H',10):('VSS','power_in'),
    ('J',5): ('VSS','power_in'),
    ('K',8): ('VSS','power_in'),
    ('C',4): ('VSSQ','power_in'),
    ('N',2): ('VSSQ','power_in'),
    ('N',5): ('VSSQ','power_in'),
    ('P',4): ('VSSQ','power_in'),
    ('P',6): ('VSSQ','power_in'),
    # RFU / VSF
    ('A',7): ('RFU','no_connect'),
    ('E',5): ('RFU','no_connect'),
    ('G',3): ('RFU','no_connect'),
    ('K',6): ('RFU','no_connect'),
    ('K',7): ('RFU','no_connect'),
    ('E',8): ('VSF','no_connect'),
    ('E',9): ('VSF','no_connect'),
    ('F',9): ('VSF','no_connect'),
    ('G',9): ('VSF','no_connect'),
    ('K',11):('VSF','no_connect'),
    ('P',10):('VSF','no_connect'),
}

# 其余所有存在的球为 NC
def get_all_balls():
    balls = []
    for r in ROWS:
        for c in COLS:
            if (r,c) in NO_BALL:
                continue
            balls.append((r,c))
    return balls

ALL_BALLS = get_all_balls()
assert len(ALL_BALLS) == 153, f"got {len(ALL_BALLS)} balls, expect 153"

# ========= 生成 KiCad Footprint (.kicad_mod) =========
def gen_footprint(filepath, pad_size=PAD_SIZE):
    lines = []
    lines.append('(footprint "eMMC153_FBGA-11.5x13_P0.5"')
    lines.append('  (version 20240108)')
    lines.append('  (generator "emmc_generator.py")')
    lines.append('  (generator_version "1.0")')
    lines.append('  (layer "F.Cu")')
    lines.append(f'  (descr "eMMC 5.1 153-ball FBGA 11.5x13mm pitch 0.5mm JEDEC MO-276 BA, ball diameter 0.3mm")')
    lines.append('  (tags "eMMC BGA FBGA 153 MO-276 JEDEC 5.1")')
    lines.append('  (attr smd)')
    # 3D? 不包含
    # 参考和值文字
    lines.append('  (fp_text reference "U**" (at 0 7.5) (layer "F.SilkS")')
    lines.append('    (effects (font (size 1 1) (thickness 0.15))))')
    lines.append('  (fp_text value "eMMC153" (at 0 -7.8) (layer "F.Fab")')
    lines.append('    (effects (font (size 1 1) (thickness 0.15))))')
    lines.append('  (fp_text user "${REFERENCE}" (at 0 0) (layer "F.Fab")')
    lines.append('    (effects (font (size 0.8 0.8) (thickness 0.12))))')
    # Fab outline: body 11.5x13
    hw = BODY_W/2
    hh = BODY_H/2
    lines.append(f'  (fp_line (start {-hw} {-hh}) (end {hw} {-hh}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    lines.append(f'  (fp_line (start {hw} {-hh}) (end {hw} {hh}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    lines.append(f'  (fp_line (start {hw} {hh}) (end {-hw} {hh}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    lines.append(f'  (fp_line (start {-hw} {hh}) (end {-hw} {-hh}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    # 标记 Pin A1 位置 (左上), 用圆圈或三角
    # A1 at (-3.25, 3.25)
    a1_x, a1_y = ball_coord('A',1)
    lines.append(f'  (fp_circle (center {a1_x-0.6} {a1_y+0.6}) (end {a1_x-0.3} {a1_y+0.6}) (stroke (width 0.1) (type solid)) (layer "F.SilkS") (fill none))')
    # Courtyard: body + 0.5mm
    cy_w = BODY_W/2 + 0.5
    cy_h = BODY_H/2 + 0.5
    lines.append(f'  (fp_line (start {-cy_w} {-cy_h}) (end {cy_w} {-cy_h}) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))')
    lines.append(f'  (fp_line (start {cy_w} {-cy_h}) (end {cy_w} {cy_h}) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))')
    lines.append(f'  (fp_line (start {cy_w} {cy_h}) (end {-cy_w} {cy_h}) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))')
    lines.append(f'  (fp_line (start {-cy_w} {cy_h}) (end {-cy_w} {-cy_h}) (stroke (width 0.05) (type solid)) (layer "F.CrtYd"))')
    # Assembly courtyard / keepout?
    # Pads
    for (r,c) in ALL_BALLS:
        x,y = ball_coord(r,c)
        pad_name = f"{r}{c}"
        signal, ptype = FUNC_MAP.get((r,c), ('NC','no_connect'))
        # 根据类型设置层
        # SMD roundrect 0.3mm, 圆角比例0.25, 焊盘层 F.Cu, F.Paste, F.Mask
        # 对于 NC, 仍然创建焊盘 但无网络
        # KiCad pad 定义
        # (pad "A1" smd roundrect (at -3.25 3.25) (size 0.3 0.3) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))
        # 增加一些属性: 如果是 VSF/RFU/NC 可以标注
        lines.append(f'  (pad "{pad_name}" smd roundrect (at {x} {y}) (size {pad_size} {pad_size}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))')
    # 放置 3D 模型占位? 可选
    lines.append(')')
    Path(filepath).write_text("\n".join(lines), encoding='utf-8')
    print(f"[Footprint] 生成 {filepath} 包含 {len(ALL_BALLS)} 焊盘")

# ========= 生成 KiCad Symbol (.kicad_sym) =========
def gen_symbol(filepath):
    """
    生成 KiCad 原理图符号库
    包含一个 symbol: eMMC_153BGA
    引脚按功能分组:
    - Power: VCC, VCCQ, VSS, VSSQ, VDDi
    - Bus: CLK, CMD, DAT0-7, DS, RST_n
    - NC / RFU / VSF: 列为 NC
    符号外观: 矩形, 宽 20mm 高 30mm, 引脚在两侧
    """
    # Symbol 引脚表
    # 我们基于 FUNC_MAP + 所有球
    # 为每个球创建一个引脚, 但对于 NC 可以合并或单独列出?
    # 这里为每个信号引脚创建符号引脚, NC 放在底部
    # KiCad symbol pin: (pin <type> line (at x y angle) (length) (name "DAT0" (effects...)) (number "A3" ...) )
    # 按类别分组排序
    # 定义引脚在符号上的位置
    # 左侧: DAT0-7, CMD, CLK, DS, RST_n
    # 右侧: VCC, VCCQ, VSS, VSSQ, VDDi
    # 底部: RFU, VSF, NC

    # 构建列表
    bus_pins = []
    power_pins = []
    nc_pins = []
    rfu_pins = []
    vsf_pins = []

    # 用于避免重复信号: 例如 VCC 有多个球, 合并为一个引脚? 但 BGA 需要每个球单独引脚以便对应封装
    # 为了原理图清晰, 我们可以将相同信号的多个球合并为一个引脚 (类似 Power symbol stack) 
    # 但为了保持与封装一一对应, 这里为每个物理球创建独立引脚, 名称相同但编号不同, 并设置为可堆叠
    # KiCad 7+ 支持 同名引脚堆叠
    # 简化: 每个球独立引脚

    for (r,c) in ALL_BALLS:
        pad_name = f"{r}{c}"
        signal, ptype = FUNC_MAP.get((r,c), ('NC','no_connect'))
        pin_entry = {
            'number': pad_name,
            'name': signal,
            'type': ptype,  # mapping later
            'ball': (r,c)
        }
        if signal.startswith('DAT') or signal in ('CMD','CLK','DS','RST_n'):
            bus_pins.append(pin_entry)
        elif signal in ('VCC','VCCQ','VSS','VSSQ','VDDi'):
            power_pins.append(pin_entry)
        elif signal == 'RFU':
            rfu_pins.append(pin_entry)
        elif signal == 'VSF':
            vsf_pins.append(pin_entry)
        else: # NC
            nc_pins.append(pin_entry)

    # 排序: DAT0-7 按顺序, 其他字母
    def sort_bus(p):
        order = {'DAT0':0,'DAT1':1,'DAT2':2,'DAT3':3,'DAT4':4,'DAT5':5,'DAT6':6,'DAT7':7,'CMD':8,'CLK':9,'DS':10,'RST_n':11}
        return order.get(p['name'], 99)
    bus_pins.sort(key=sort_bus)
    power_pins.sort(key=lambda x: (x['name'], x['number']))
    nc_pins.sort(key=lambda x: x['number'])
    rfu_pins.sort(key=lambda x: x['number'])
    vsf_pins.sort(key=lambda x: x['number'])

    # 符号几何
    pin_length = 2.54
    pin_spacing = 2.54
    # 计算符号高度
    total_left = len(bus_pins)
    total_right = len(power_pins)
    max_side = max(total_left, total_right)
    symbol_height = max(30, max_side * pin_spacing + 5)
    symbol_width = 25.4
    half_h = symbol_height/2
    half_w = symbol_width/2

    # KiCad 符号类型映射
    type_map = {
        'input': 'input',
        'output': 'output',
        'bidirectional': 'bidirectional',
        'power_in': 'power_in',
        'no_connect': 'no_connect'
    }

    lines = []
    lines.append('(kicad_symbol_lib (version 20231120) (generator "emmc_generator.py")')
    lines.append('  (symbol "eMMC_5.1_153BGA" (in_bom yes) (on_board yes)')
    lines.append('    (property "Reference" "U" (at 0 17.78 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Value" "eMMC_5.1_153BGA" (at 0 -17.78 0) (effects (font (size 1.27 1.27))))')
    lines.append('    (property "Footprint" "eMMC:eMMC153_FBGA-11.5x13_P0.5" (at 0 -20.32 0) (effects (font (size 1.27 1.27)) hide))')
    lines.append('    (property "Datasheet" "https://www.jedec.org/standards-documents/technology-focus-areas/flash-memory-ssds-ufs-emmc/e-mmc" (at 0 -22.86 0) (effects (font (size 1.27 1.27)) hide))')
    lines.append('    (property "Description" "eMMC 5.1 153-ball FBGA 11.5x13mm 0.5mm pitch, HS400, 8-bit bus" (at 0 -25.4 0) (effects (font (size 1.27 1.27)) hide))')
    lines.append('    (property "ki_keywords" "eMMC BGA153 FBGA memory" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))')
    # 图形
    lines.append('    (symbol "eMMC_5.1_153BGA_0_1"')
    # 外框
    lines.append(f'      (rectangle (start {-half_w} {half_h}) (end {half_w} {-half_h}) (stroke (width 0.254) (type default)) (fill (type background)))')
    # 左上角 Pin1 标记
    lines.append(f'      (polyline (pts (xy {-half_w} {half_h}) (xy {-half_w+1.5} {half_h}) (xy {-half_w+1.5} {half_h-1.5})) (stroke (width 0.254) (type default)) (fill (type none)))')
    lines.append('    )')
    lines.append('    (symbol "eMMC_5.1_153BGA_1_1"')
    # 左侧 Bus 引脚
    y_start_left = half_h - 2.54
    for i, pin in enumerate(bus_pins):
        y = y_start_left - i*pin_spacing
        # 左侧 x = -half_w, angle 0 (向右)
        ptype = type_map.get(pin['type'], 'bidirectional')
        # 电气类型
        # KiCad pin: (pin <electrical_type> line (at x y angle) (length L) (name "...") (number "..."))
        # 左侧: at (-half_w - pin_length, y), angle 0
        x = -half_w - pin_length
        lines.append(f'      (pin {ptype} line (at {x} {y} 0) (length {pin_length})')
        lines.append(f'        (name "{pin["name"]}" (effects (font (size 1.27 1.27))))')
        lines.append(f'        (number "{pin["number"]}" (effects (font (size 1.27 1.27))))')
        lines.append('      )')
    # 右侧 Power 引脚
    y_start_right = half_h - 2.54
    for i, pin in enumerate(power_pins):
        y = y_start_right - i*pin_spacing
        x = half_w + pin_length
        ptype = type_map.get(pin['type'], 'power_in')
        lines.append(f'      (pin {ptype} line (at {x} {y} 180) (length {pin_length})')
        lines.append(f'        (name "{pin["name"]}" (effects (font (size 1.27 1.27))))')
        lines.append(f'        (number "{pin["number"]}" (effects (font (size 1.27 1.27))))')
        lines.append('      )')
    # 顶部 NC (angle 270) 和 底部 RFU/VSF+NC (angle 90)
    # 为了避免重叠, 使用网格布局
    # 顶部: 2 行, 每行最多 12 个
    x_start_top = -half_w + 2.0
    cols_top = 12
    for i, pin in enumerate(nc_pins):
        if i >= 24:  # 顶部最多 24
            break
        row = i // cols_top
        col = i % cols_top
        x_use = x_start_top + col * 2.0
        y_use = half_h + pin_length + row * 2.54
        angle = 270
        ptype = 'no_connect'
        lines.append(f'      (pin {ptype} line (at {x_use} {y_use} {angle}) (length {pin_length})')
        lines.append(f'        (name "{pin["name"]}" (effects (font (size 1.27 1.27))))')
        lines.append(f'        (number "{pin["number"]}" (effects (font (size 1.27 1.27))))')
        lines.append('      )')
    # 底部: RFU/VSF + 剩余 NC, 多行网格
    remaining_nc = nc_pins[24:]
    bottom_all = rfu_pins + vsf_pins + remaining_nc
    x_start_bottom = -half_w + 2.0
    cols_bottom = 15
    for i, pin in enumerate(bottom_all):
        row = i // cols_bottom
        col = i % cols_bottom
        x_use = x_start_bottom + col * 2.0
        y_use = -half_h - pin_length - row * 2.54
        angle = 90
        ptype = 'no_connect'
        # 对于 RFU/VSF 显示完整名称
        disp_name = f"{pin['name']}_{pin['number']}" if pin['name'] in ('RFU','VSF') else pin['name']
        lines.append(f'      (pin {ptype} line (at {x_use} {y_use} {angle}) (length {pin_length})')
        lines.append(f'        (name "{disp_name}" (effects (font (size 1 1))))')
        lines.append(f'        (number "{pin["number"]}" (effects (font (size 1.27 1.27))))')
        lines.append('      )')

    lines.append('    )')
    lines.append('  )')
    lines.append(')')

    Path(filepath).write_text("\n".join(lines), encoding='utf-8')
    print(f"[Symbol] 生成 {filepath} 包含 总引脚 {len(ALL_BALLS)}")

# ========= 生成 辅助文件: Datasheet 摘要 和 README =========
def gen_readme(base_dir):
    md = f"""
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
"""
    Path(base_dir, "README_AUTO.md").write_text(md, encoding='utf-8')
    print(f"[README] 生成 {base_dir}/README_AUTO.md")

def main():
    base = Path(__file__).parent
    footprint_dir = base / "eMMC.pretty"
    footprint_dir.mkdir(parents=True, exist_ok=True)
    # 生成三种密度: L/N/M (IPC)
    densities = {
        "": PAD_SIZE,  # 标称 0.30
        "_L": 0.25,
        "_N": 0.30,
        "_M": 0.35,
    }
    fp_paths = []
    for suffix, pad_sz in densities.items():
        fname = f"eMMC153_FBGA-11.5x13_P0.5{suffix}.kicad_mod" if suffix else "eMMC153_FBGA-11.5x13_P0.5.kicad_mod"
        fp_path = footprint_dir / fname
        gen_footprint(fp_path, pad_size=pad_sz)
        fp_paths.append(fp_path)
    # 额外生成 169 ball 变体? 提示
    sym_path = base / "eMMC.kicad_sym"
    gen_symbol(sym_path)
    gen_readme(base)

    # 同时生成一个简化版 CSV pinout
    csv_path = base / "emmc153_pinout.csv"
    with open(csv_path,'w',encoding='utf-8') as f:
        f.write("Pad,Row,Col,X_mm,Y_mm,Signal,Type\n")
        for (r,c) in ALL_BALLS:
            x,y = ball_coord(r,c)
            sig, typ = FUNC_MAP.get((r,c), ('NC','no_connect'))
            f.write(f"{r}{c},{r},{c},{x},{y},{sig},{typ}\n")
    print(f"[CSV] 生成 {csv_path}")

    # 生成 BallMap PNG (如果 matplotlib 可用)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        fig, ax = plt.subplots(figsize=(8,8))
        for r,c in ALL_BALLS:
            x,y = ball_coord(r,c)
            sig,_ = FUNC_MAP.get((r,c), ('NC',''))
            col='lightgray'
            if sig.startswith('DAT'):
                col='blue'
            elif sig=='CMD':
                col='red'
            elif sig=='CLK':
                col='green'
            elif sig=='DS':
                col='orange'
            elif 'RST' in sig:
                col='purple'
            elif sig=='VCC':
                col='red'
            elif sig=='VCCQ':
                col='darkred'
            elif sig=='VSS':
                col='black'
            elif sig=='VSSQ':
                col='gray'
            elif sig=='VDDi':
                col='magenta'
            elif sig=='RFU':
                col='gold'
            elif sig=='VSF':
                col='cyan'
            ax.plot(x,y,'o',color=col, markersize=7, markeredgecolor='k', markeredgewidth=0.3)
            ax.text(x,y,f"{r}{c}", fontsize=2.5, ha='center', va='center')
        hw=BODY_W/2
        hh=BODY_H/2
        rect = patches.Rectangle((-hw,-hh), BODY_W, BODY_H, linewidth=1, edgecolor='black', facecolor='none')
        ax.add_patch(rect)
        e1=E1/2
        d1=D1/2
        rect2 = patches.Rectangle((-e1,-d1), E1, D1, linewidth=0.5, edgecolor='blue', facecolor='none', linestyle='--')
        ax.add_patch(rect2)
        ax.set_aspect('equal')
        ax.set_xlabel('X mm')
        ax.set_ylabel('Y mm')
        ax.set_title('eMMC153 Ball Map (Top View Balls Down) 11.5x13mm Pitch 0.5mm')
        ax.grid(True, linestyle=':', linewidth=0.3)
        plt.tight_layout()
        out_png = base / "emmc_ballmap.png"
        plt.savefig(out_png, dpi=300)
        print(f"[PNG] 生成 {out_png}")
        plt.close()
    except Exception as e:
        print(f"[PNG] 跳过 (matplotlib 不可用): {e}")

    print("完成! 文件列表:")
    for p in fp_paths + [sym_path, csv_path, base/"README_AUTO.md"]:
        print(" -", p)

if __name__ == "__main__":
    main()

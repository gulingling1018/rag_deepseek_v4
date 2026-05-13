# Chunk Quality Report

- Generated at: 2026-05-13 13:28:16Z
- Documents: 5
- Chunks: 677
- Vectors: 677
- Content length median: 325
- Content length average: 458.5
- Short chunks (<100 chars): 77
- Very short chunks (<50 chars): 23
- Long chunks (>2000 chars): 0
- Formula chunks: 29
- Formula leakage chunks: 0
- Bad start chunks: 29
- Block types: {'text': 541, 'table': 44, 'formula': 29, 'code': 63}
- Table confidence: {'low': 11, 'medium': 7, 'high': 26}

## Documents

| Document | Source format | Chunks | Block types | Median len | Short <100 |
|---|---:|---:|---|---:|---:|
| 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) | pdf+pymupdf4llm | 436 | `{'text': 363, 'table': 44, 'formula': 29}` | 344 | 27 |
| ESP32 Product Documentation | web | 16 | `{'text': 16}` | 342 | 5 |
| ESP-IDF Get Started ESP32 | web | 15 | `{'text': 13, 'code': 2}` | 284 | 3 |
| ESP-IDF Build System ESP32 | web | 207 | `{'text': 146, 'code': 61}` | 306 | 42 |
| Espressif Manuals And Guides Test Catalog | markdown | 3 | `{'text': 3}` | 230 | 0 |

## Issue Summary

- Section path issue chunks: 0
- Path pollution rate: 0.0000
- Section path issue parts: {}
- PDF section path issue chunks: 0 / 436
- Chapter transition path errors: 0
- Heading recall sample candidates: 0
- Formula chunks: 29
- Formula leakage chunks: 0
- Formula leakage rate: 0.0000
- Bad start chunks: 29
- Bad start rate: 0.0428
- Table issue counts: {'packed_multi_value_cells': 11}
- Table confidence distribution: {'low': 11, 'medium': 7, 'high': 26}
- Code chunks: 63
- Single-line code chunks: 23
- Short code chunks (<100 chars): 35
- Code chunks without adjacent text context: 0

## Priority Findings

1. Track chapter-transition path errors separately; a path should not contain two chapter-level headings.
2. Keep table chunks, but treat low-confidence packed multi-value tables as risky evidence instead of exact row/column data.
3. Single-line command/code chunks are correctly typed as code, but small commands still need parent context for intent.
4. Watch heading recall samples so stricter path cleaning does not silently drop real front-matter or section titles.

## Examples: bad_start_chunks

### 1. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 9

- block_type: `text`
- section_path: `汽车理论`
- page_label: `第 13 页`
- location_label: `第 13 页`
- detail: `starts like a continuation`

```text
中心到前外轮接地中心的距离( 见图 0-2)。 它是机动性的主要指标, 对通过性有很大意 义。 因为它在很大程度上表征了汽车能够通过狭窄弯曲地带或绕开不可越过的障碍物的 能力。 图 0-2 中, A 为最小转弯半径时的最大转弯宽度, a、 b 为突伸距。 二、 技术经济性 汽车的技术经济性主要用生产率和燃油经济性来表示。 而燃油经济性可用百公里油 耗、 折旧费、 维修费等衡量。 折旧费、 维修费等又与可靠性和耐用性有关。 1. 生产率 汽车的生产率用单位时间内完成的运输吨公里数来表示。 生产率的大小与汽车的行 驶速度、 装载质量和道路条件等有关。 2. 油耗 油耗包括燃油消耗和全损耗系统用油消耗。 燃油消耗用满载时每公里所耗燃油量来...
```

### 2. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 16

- block_type: `text`
- section_path: `第一章 地面—轮胎力学`
- page_label: `第 18 页`
- location_label: `第 18 页`
- detail: `starts like a continuation`

```text
擦、 地面变形的阻尼( 软路面) 以及轮胎与地面间的弹性变形和局部的滑移等造成的。 虽然轮胎的迟滞损失由于轮胎的内摩擦形成, 最终以热能的形式耗散到大气 中。 但从对轮胎的受力分析可以看到, 这种损失的表现形式是一种阻碍车轮滚动的 阻力偶。 当车轮不滚动时, 地面对车轮法向反作用力的分布是前后对称的; 但当车 轮滚动时, 在法线 n—n′前后相对应点 d 和 d′( 见图 1-2a) 处变形虽然相同, 但由于 弹性迟滞现象, 处于压缩过程的前部 d 点的地面法向反作用力就会大于处于恢复过 程的后部 d′点的地面法向反作用力, 这可以从图 1-2b 中看出。 设取同一变形 δ, 压 缩时的受力为 CF, 恢复时的受力为 DF, 而 C...
```

### 3. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 22

- block_type: `text`
- section_path: `第一章 地面—轮胎力学`
- page_label: `第 20 页`
- location_label: `第 20 页`
- detail: `starts like a continuation`

```text
系数的关系曲线 为了更直观地反映充气压力对轮胎滚动阻力的影响, 图 1-8 给出了充气压力以及行 驶速度与滚动阻力系数的关系曲线。 随着充气压力的增大, 轮胎的径向刚度增大, 弹性 损失将减小, 从而滚动阻力系数降低。 而随着行驶速度的增加, 滚动阻力系数增大。 因 此在汽车的使用中为了提高经济性需要考虑轮胎的正常气压范围。 若是在松软路面上, 轮胎充气压力与滚动阻力的关系如图 1-9 所示。 与在硬路面上轮胎的滚动阻力系数相 比, 松软路面上轮胎的滚动阻力表现出了不一致性。
```

### 4. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 23

- block_type: `text`
- section_path: `第一章 地面—轮胎力学`
- page_label: `第 21 页`
- location_label: `第 21 页`
- detail: `starts like a continuation`

```text
与充气压力的关系曲线 二、 穿水阻力 前面主要分析的是干路面上汽 车直线行驶时的滚动阻力, 而在 湿路面上汽车直线行驶时的滚动 阻力将发生变化。 图 1-10 所示为 在湿路面上轮胎的滚动状态。 所谓湿路面, 即路面有一定的 积水层。 当汽车在有积水层的路面 上行驶时, 必须排挤水层, 因此行 驶阻力将增加, 存在着附加的穿水 阻力 F w 。 同时由于路面的积水, 汽 车行驶时会出现比较危险的滑水现 象。 穿水阻力是汽车行驶阻力的一 个有效补充, 一般认为存在如下 关系: F w = Cbu [n] (1-7) 式中, C 为比例常数; b 为轮胎的宽 度; u 为汽车的行驶车速; n 为幂指 数, 当水层厚度大于 0. 5mm ...
```

### 5. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 29

- block_type: `text`
- section_path: `第一章 地面—轮胎力学`
- page_label: `第 26 页`
- location_label: `第 26 页`
- detail: `starts like a continuation`

```text
中心线 aa 是均匀分布的。 而当车轮滚动时, 接地印迹中心线 aa 不仅与车轮平面 cc 错 开一定的距离 Δh, 而且转动了一个角度 α( 侧偏角), 因而接地印迹前端离轮胎平面 cc 近, 侧向变形小; 接地印迹后端离轮胎平面 cc 远, 侧向变形大。 假设地面微元侧向反 作用力的分布与变形成正比, 故地面微元侧向反作用力的分布情况将如图 1-19 所示。 其合力 F Y 的大小与侧向力 F′ Y 相等, 但其作用点必然在接地印迹几何中心的后面, 偏离 了一个距离 e。 该偏离的距离 e 称为轮胎拖距。 F Y e 就是回正力矩 T Z 。
```

### 6. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 71

- block_type: `text`
- section_path: `第二章 汽车动力性`
- page_label: `第 49 页`
- location_label: `第 49 页`
- detail: `starts like a continuation`

```text
因此, D—u a 曲线与 f—u a 曲线间距离之 3. 汽车爬坡能力的确定 g δ 倍就是汽车各档的加速度。 汽车的上坡能力用汽车在良好路面上等速行驶的最大爬坡度评价, 此时, [d][u] dt [= 0,] 则式(2 16) 为 D = ψ = fcosα+sinα = f 1-sin [2] α +sinα 解此方程得 α =arcsin D-f 1-D [2] +f [2] 1+f [2] 然后按 tanα = i, 可求出坡度值。 若将I档最大动力因数 D Imax 和滚动阻力系数 f 代 入上式, 就可直接求出最大爬坡度 i max 。 如果只是粗略估算汽车上坡能力, 则可认为 cosα≈1 和 sinα≈tanα ...
```

### 7. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 128

- block_type: `text`
- section_path: `第三章 汽车的燃油经济性`
- page_label: `第 80 页`
- location_label: `第 80 页`
- detail: `starts like a continuation`

```text
则有 i′ = A [n] u a (3-3) 现在假设汽车在某道路阻力系数为 ψ 的道路上以 u′ a 速度行驶, 需要发动机提供功 率 P′ e 。 如图 3-9b 所示, 这时发动机可以在 n 0 、 n′ e 、 n 1 、 n 2 、...等无数种转速及相应的 负荷率工作, 但只有在 P′ e 水平线与曲线 A 2 A 3 的交点处工作, 即转速为 n′ e 和大致为 90%负荷率工作时, 燃油消耗率 b 最小。 此时, P′ e = P ψ +P w η T 把 u′ a 和 n′ e 代入式(3-3), 即得无级变速器应有的传动比 i′。 依照上面的方法, 在同一 ψ 值的道路上, 把汽车在不同车速时无级变速器应有的 ...
```

### 8. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 154

- block_type: `text`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择 > 第二节 传动系统最小传动比的选择`
- page_label: `第 93 页`
- location_label: `第 93 页`
- detail: `starts like a continuation`

```text
的选定是很重要的。 传动系统的总传动比是传动系统中各部件传动比的乘积, 即 i t = i g i 0 i c 式中, i t 是传动系统的总传动比; i g 是变速器传动比; i 0 是主减速器传动比; i c 是分动 器、 副变速器传动比。 普通的汽车没有分动器或副变速器。 变速器的最小传动比为直接档或超速档, 当变 速器为直接档时, 传动系统的最小传动比就是主减速器传动比 i 0 ; 当变速器为超速档 时, 最小传动比应为变速器最高档 传动比与主减速器传动比的乘积。 下面讨论变速器最小传动比为 1 时的汽车最小传动比的选择, 即 主减速器传动比 i 0 的选择。 选择主减速器传动比时应考虑 汽车最高车速、 汽车的后备功率、 汽...
```

### 9. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 170

- block_type: `text`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择 > 第五节 利用燃油经济性 加速时间曲线确定动力装置参数`
- page_label: `第 103 页`
- location_label: `第 103 页`
- detail: `starts like a continuation`

```text
的每升燃油行驶公里数代表燃油经济性, 以原地起步加速时间代表动力性, 作出不同参 — 数匹配下的燃油经济性 加速时间曲线, 并利用此曲线来确定有关参数。 一 、 主减速器传动比的确定 按下列步骤确定主减速器传动比: 1) 一辆汽车, 在动力装置其他参数不变的条件下, 先选定主减速器传动比范围, 然后从大到小改变 i 0 , 每对应一个 i 0 值, 计算出不同的加速时间和每升燃油行驶里 程数。 — 2) 根据计算结果在燃油经济性 加速时间图上找出计算点, 用光滑曲线连接各点, 可得到不同 i 0 时的燃油经济性—加速时间曲线, 如图 4-6 所示。 — 3) 根据作出的燃油经济性 加 速时间曲线图, 按我们的预定目标 选择 i 0 ...
```

### 10. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 173

- block_type: `text`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择`
- page_label: `第 104 页`
- location_label: `第 104 页 - 第 105 页`
- detail: `starts like a continuation`

```text
曲线。 它是以 0~1km 连续换档加速的末速度作为动力性评价指标的。 可以看出, 装用 带超速档的或最高档为直接档的 6 档变速器, 燃油经济性都比用 5 档变速器时有所改 善。 如果驱动桥的传动比采用 5. 897, 则装用最高档为直接档的 6 档变速器时, 不但燃 油消耗量可减少 1. 08L/ 100km( 减少 3. 6%), 而且 0 ~1km 连续换档加速的末速度也可 以增加 0. 58km/ h( 增加 0. 7%)。
```

### 11. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 176

- block_type: `text`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择`
- page_label: `第 106 页`
- location_label: `第 106 页`
- detail: `starts like a continuation`

```text
与不同变速器的最佳燃油经济性和动力性曲线 a) 同一变速器选用三种不同排量发动机 b) 装用三种具有不同传动比的 4 档变速器 加速时间要求为 13. 5s 的条件下,C 型变速器的燃油经济性最好, 比 A 型提高 4. 4%。
```

### 12. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 181

- block_type: `text`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择`
- page_label: `第 108 页`
- location_label: `第 108 页`
- detail: `starts like a continuation`

```text
而单调减小; 最高车速单调减小;CBDTRUCK 工况柴油百公里油耗随主减速器传动比 增大而增大。 把 CBDTRUCK 工况柴油百公里油耗和 0 ~40km/ h 原地起步连续换档加速时间的关 系表示于图 4-11 矿用自卸汽车动力性-燃油经济性曲线中, 可以直观地对其变化趋势做 出判断。 图中曲线之 “ 拐点” 对应于最佳的主减速器传动比。 对几何相似的不同排量的发 动机重复以上过程, 就可以在同一坐标中获得类似的曲线。 它们的公切线称为 “ 最佳 动力性与燃油经济性曲线”, 该曲线包含了所有可能的理想主减速器传动比值。
```

## Examples: product_page:empty_section_path

### 1. ESP32 Product Documentation / chunk 0

- block_type: `text`
- section_path: ``
- location_label: `ESP32 Wi-Fi & Bluetooth SoC | Espressif Systems:1-60`
- detail: `empty section_path`

```text
Home Hardware Product Overview SoCs Modules DevKits Espressif M5Stack Equipment Product Selector ESP32-Wrap ESP32-P ESP32-P4 ESP32-E ESP32-E22 ESP32-S ESP32-S31 ESP32-S3 ESP32-S2 ESP32-C ESP32-C6 ESP32-C61 ESP32-C5 ESP32-C3 ESP32-C2 ESP32-H ESP32-H4 ESP32-H21 ESP32-H2 ESP32 ESP32 ESP8266 ESP8266 SDKs General Frameworks...
```

### 2. ESP32 Product Documentation / chunk 1

- block_type: `text`
- section_path: ``
- location_label: `ESP32 Wi-Fi & Bluetooth SoC | Espressif Systems:61-120`
- detail: `empty section_path`

```text
ESP-IoT-Solution AI ESP-SR ESP-WHO ESP-DL ESP-NN IoT & Multimedia ESP-Brookesia ESP-GMF ESP-ADF Connectivity Co-Processors ESP-Hosted ESP-AT ESP-IoT-Bridge Networking & Protocols ESP-Matter SDK ESP-Mesh-Lite ESP-BLE-MESH ESP HomeKit SDK Third-Party Ecosystems ESP-Arduino Zephyr® for Espressif Cloud Special Menu ESP Rai...
```

### 3. ESP32 Product Documentation / chunk 2

- block_type: `text`
- section_path: ``
- location_label: `ESP32 Wi-Fi & Bluetooth SoC | Espressif Systems:121-180`
- detail: `empty section_path`

```text
Get Started Dashboard Cloud Services Maintain & Iterate Tools Support Consult & Customize Develop Resources Get Started GitHub Repository Client APPs Nova Home (Source Code Available) ESP RainMaker (Fully Open Source) Dashboard (Public) Solution Integration Matter Fabric ESP-Mesh-Lite AWS IoT ExpressLink Solutions Spec...
```

### 4. ESP32 Product Documentation / chunk 3

- block_type: `text`
- section_path: ``
- location_label: `ESP32 Wi-Fi & Bluetooth SoC | Espressif Systems:181-240`
- detail: `empty section_path`

```text
ESP AWS IoT ExpressLink Solution Peripherals Device Drivers USB Solutions Smart Sensing Wi-Fi CSI Sensing Wi-Fi FTM Ranging Support Technical Documents All Types SoCs Modules DevKits Equipment Services Self-Service Resources Software Hardware & RF Cloud Certification Manufacturing On-Site Assistance Download Technical ...
```

### 5. ESP32 Product Documentation / chunk 4

- block_type: `text`
- section_path: ``
- location_label: `ESP32 Wi-Fi & Bluetooth SoC | Espressif Systems:241-300`
- detail: `empty section_path`

```text
Export Compliance ISO Certification FAQ ESP-FAQ Commercial FAQ Ecosystem Partnership and Resource AWS Technology Partner Third-Party Collaborations Third-Party SDKs Education ESP Education Developer Zone ESP Developer Portal Espressif DevCon M5Stack Tech Blogs ESP32 Forum Community Courses Rust Books Videos Projects Co...
```

### 6. ESP32 Product Documentation / chunk 5

- block_type: `text`
- section_path: ``
- location_label: `ESP32 Wi-Fi & Bluetooth SoC | Espressif Systems:301-331`
- detail: `empty section_path`

```text
Investor Relations Reports Investor Inquiries Corporate Responsibility Reports Wildlife Protection Join Us Espressif Careers Find Your Job Contact Contact Espressif Sales Contact Distributors Technical Inquiries Schematic & PCB Design Review Get Samples Become Our Supplier Comments & Suggestions
```

## Examples: product_page:unexpected_section_path

### 1. ESP32 Product Documentation / chunk 6

- block_type: `text`
- section_path: `Search form`
- location_label: `Search form`
- detail: `Search form`

```text
Search
```

### 2. ESP32 Product Documentation / chunk 8

- block_type: `text`
- section_path: `ESP32 > You are here`
- location_label: `You are here`
- detail: `ESP32 > You are here`

```text
Home»ハード»ESP32-Wrap»ESP32» ESP32
```

### 3. ESP32 Product Documentation / chunk 13

- block_type: `text`
- section_path: `ESP32 > Buy Now > Stay Informed with Us`
- location_label: `Stay Informed with Us`
- detail: `ESP32 > Buy Now > Stay Informed with Us`

```text
Get the latest on innovations, product launches, upcoming events, documentation updates, PCN notifications, advisories, and more. Subscribe PRODUCTS SoCs Modules DevKits Product Selector DEVELOPERS Developer Portal ESP DevCon Tech Blogs News COMPANY About Espressif Logo Guidelines Sales Questions Careers RESOURCES Tech...
```

### 4. ESP32 Product Documentation / chunk 14

- block_type: `text`
- section_path: `ESP32 > Buy Now > Stay Informed with Us`
- location_label: `Stay Informed with Us`
- detail: `ESP32 > Buy Now > Stay Informed with Us`

```text
Copyright © 2026 Espressif Systems. All rights reserved. 沪公网安备 31011502019094 号 沪ICP备2021026420号 Terms of Service Privacy Policy 690 Bibo Road Block 2 Suite 204, Zhangjiang Shanghai, China
```

### 5. ESP32 Product Documentation / chunk 15

- block_type: `text`
- section_path: `ESP32 > Languages`
- location_label: `Languages`
- detail: `ESP32 > Languages`

```text
English 简体中文 日本語 /
```

## Examples: short_chunks_lt_100

### 1. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 45

- block_type: `table`
- section_path: `第二章 汽车动力性`
- page_label: `第 35 页`
- location_label: `第 35 页`
- detail: `len=90`

```text
表 2-2 传动系统各部件的传动效率 |ηT（%）|部件名称| |---|---| |95<br>95<br>90|单级减速主减速器<br>双级减速主减速器<br>传动轴和万向节|
```

### 2. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 65

- block_type: `formula`
- section_path: `第二章 汽车动力性`
- page_label: `第 46 页`
- location_label: `第 46 页`
- detail: `len=27`

```text
dt = a [1] [d][u] t u 2 t =
```

### 3. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 92

- block_type: `text`
- section_path: `第二章 汽车动力性`
- page_label: `第 63 页`
- location_label: `第 63 页`
- detail: `len=98`

```text
桥组成。 主减速器传动比 i 0 = 5. 83, 变速器各档传动比分别为 6. 09、3. 09、1. 71、1, 传动系统效率 η T =0. 85。 已知发动机 80%负荷时的若干工况如下:
```

### 4. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 93

- block_type: `table`
- section_path: `第二章 汽车动力性`
- page_label: `第 63 页`
- location_label: `第 63 页`
- detail: `len=88`

```text
|106 62<br>.|147 55<br>.|169 84<br>.|174 95<br>.| |---|---|---|---| |600|1000|1500|2000|
```

### 5. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 111

- block_type: `formula`
- section_path: ``
- page_label: `第 71 页`
- location_label: `第 71 页`
- detail: `len=50`

```text
i = 1 Q i = Q 1 + Q 2 + ... + Q n n- 1 或 Q a = [1]
```

### 6. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 121

- block_type: `table`
- section_path: `第三章 汽车的燃油经济性 > 第三节 影响汽车燃油经济性的因素`
- page_label: `第 75 页`
- location_label: `第 75 页`
- detail: `len=98`

```text
表 3-7 影响燃油经济性的使用因素 |影 响 因 素|使 用 条 件| |---|---| |城市道路、郊区道路、一般公路、高<br>等级公路|驾驶习惯| |路上行人及车辆的密集程度|气候状况|
```

### 7. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 153

- block_type: `formula`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择`
- page_label: `第 92 页`
- location_label: `第 92 页`
- detail: `len=37`

```text
= 0. 02, C D A mη T = 4×10 [-4] ~1×10
```

### 8. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 190

- block_type: `table`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择`
- page_label: `第 112 页`
- location_label: `第 112 页`
- detail: `len=97`

```text
表 4-10 AF13 自动变速器主要参数 |Ⅰ档|Ⅱ档|Ⅲ档|Ⅳ档|倒档| |---|---|---|---|---| |2. 807|1. 479|1. 000|0. 735|2. 769|
```

### 9. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 205

- block_type: `text`
- section_path: `第五章 汽车的制动性 > 第一节 制动性的评价指标`
- page_label: `第 117 页`
- location_label: `第 117 页`
- detail: `len=83`

```text
3. 制动时汽车行驶的方向稳定性 制动时汽车行驶的方向稳定性是指制动时汽车按给定路径行驶的能力。 若制动时发 生跑偏、 侧滑或失去转向能力, 则汽车将偏离原来的路径。
```

### 10. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 229

- block_type: `text`
- section_path: `第五章 汽车的制动性`
- page_label: `第 127 页`
- location_label: `第 127 页`
- detail: `len=81`

```text
改进制动系统结构, 减少制动器的作用时间, 是缩短制动距离的一项有效措施。 例 如某款红旗轿车由真空助力制动系统改为压缩空气助力( 气顶液) 制动系统后, 两种不
```

### 11. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 230

- block_type: `table`
- section_path: `第五章 汽车的制动性`
- page_label: `第 127 页`
- location_label: `第 127 页`
- detail: `len=83`

```text
表 5-5 装有两种不同助力系统时某款红旗轿车的制动效能 |制动时间/s|制动距离/m| |---|---| |2. 12|12. 25| |1. 45|8. 25|
```

### 12. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 262

- block_type: `formula`
- section_path: `第五章 汽车的制动性`
- page_label: `第 145 页`
- location_label: `第 145 页`
- detail: `len=77`

```text
E f = [z] φ f β = b L φ f h g L 后轴的制动效率为 φ r h g L E r = [z] φ r = a L (1-β)+
```

### 13. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 264

- block_type: `table`
- section_path: `第五章 汽车的制动性`
- page_label: `第 145 页`
- location_label: `第 145 页`
- detail: `len=78`

```text
|质量 m/kg|质心高h g / m|轴距L/m| |---|---|---| |1160|0. 46|2. 54| |1540|0. 48|2. 54|
```

### 14. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 272

- block_type: `text`
- section_path: `第五章 汽车的制动性 > 第六节 汽车防抱死制动系统(ABS) 和制动辅助系统(BAS)`
- page_label: `第 149 页`
- location_label: `第 149 页`
- detail: `len=91`

```text
一 、 防抱死制动系统 凡驾驶过汽车的人都有一些体验: 在被雨淋湿而带有泥土的柏油路上或在积雪道路 上紧急制动时, 汽车会发生侧滑甚至调头旋转; 左、 右两侧车轮如果行驶在不同的路面
```

### 15. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 285

- block_type: `table`
- section_path: `第五章 汽车的制动性`
- page_label: `第 156 页`
- location_label: `第 156 页`
- detail: `len=61`

```text
表 5-12 行车制动热衰退恢复试验方法 |基 准 试 验|衰 退 试 验| |---|---| |0/ 0|0/ 30|
```

### 16. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 299

- block_type: `text`
- section_path: `第六章 汽车的操纵稳定性 > 第一节 概 述`
- page_label: `第 162 页`
- location_label: `第 162 页`
- detail: `len=93`

```text
横摆运动。 其中沿 x 方向的平动、 沿 z 方向的平动以及绕 y 轴的转动与转向操纵没有直 接的关系, 而其他的运动是由转向操纵直接引起的, 因此也就是汽车操纵稳定性研究的 主要内容。
```

### 17. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 303

- block_type: `text`
- section_path: `第六章 汽车的操纵稳定性 > 第一节 概 述`
- page_label: `第 163 页`
- location_label: `第 163 页`
- detail: `len=91`

```text
二、 驾驶人-汽车系统 对汽车操纵稳定性的研究中可以将汽车仅作为一个开路系统进行分析和研究。 在这 种开路系统中, 不考虑驾驶人的情况, 只是机械地将转向盘作必要的转动, 不允许根据
```

### 18. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 376

- block_type: `formula`
- section_path: ``
- page_label: `第 203 页`
- location_label: `第 203 页`
- detail: `len=87`

```text
(2) 均方值 即 q [2] ( t) 的均值, 为 E[ q [2] ( t)] = lim T→∞ (3) 方差 即[ q( t)-μ q ] [2] 的均值, 为 1
```

### 19. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 377

- block_type: `formula`
- section_path: ``
- page_label: `第 203 页`
- location_label: `第 203 页`
- detail: `len=17`

```text
2 q [= lim] T→∞ 1
```

### 20. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 381

- block_type: `formula`
- section_path: ``
- page_label: `第 204 页`
- location_label: `第 204 页`
- detail: `len=57`

```text
∞ -∞ [R] [q] [(] [τ][)e] -j2πfτ dτ (7- 6) R q ( τ)= [1] ∞
```

## Examples: single_line_code_chunks

### 1. ESP-IDF Get Started ESP32 / chunk 11

- block_type: `code`
- section_path: `Get Started > Uninstall ESP-IDF > Uninstall Using EIM CLI`
- location_label: `Uninstall Using EIM CLI`
- detail: `len=20`

```text
eim uninstall v5.4.2
```

### 2. ESP-IDF Get Started ESP32 / chunk 13

- block_type: `code`
- section_path: `Get Started > Uninstall ESP-IDF > Uninstall Using EIM CLI`
- location_label: `Uninstall Using EIM CLI`
- detail: `len=9`

```text
eim purge
```

### 3. ESP-IDF Build System ESP32 / chunk 9

- block_type: `code`
- section_path: `Build System > Using the Build System > Using CMake Directly > Flashing with Ninja or Make`
- location_label: `Flashing with Ninja or Make`
- detail: `len=11`

```text
ninja flash
```

### 4. ESP-IDF Build System ESP32 / chunk 10

- block_type: `code`
- section_path: `Build System > Using the Build System > Using CMake Directly > Flashing with Ninja or Make`
- location_label: `Flashing with Ninja or Make`
- detail: `len=14`

```text
make app-flash
```

### 5. ESP-IDF Build System ESP32 / chunk 12

- block_type: `code`
- section_path: `Build System > Using the Build System > Using CMake Directly > Flashing with Ninja or Make`
- location_label: `Flashing with Ninja or Make`
- detail: `len=32`

```text
ESPPORT=/dev/ttyUSB0 ninja flash
```

### 6. ESP-IDF Build System ESP32 / chunk 14

- block_type: `code`
- section_path: `Build System > Using the Build System > Using CMake Directly > Flashing with Ninja or Make`
- location_label: `Flashing with Ninja or Make`
- detail: `len=47`

```text
make -j3 app-flash ESPPORT=COM4 ESPBAUD=2000000
```

### 7. ESP-IDF Build System ESP32 / chunk 42

- block_type: `code`
- section_path: `Build System > Component CMakeLists Files > Controlling Component Compilation`
- location_label: `Controlling Component Compilation`
- detail: `len=69`

```text
target_compile_options(${COMPONENT_LIB} PRIVATE -Wno-unused-variable)
```

### 8. ESP-IDF Build System ESP32 / chunk 75

- block_type: `code`
- section_path: `Build System > Component Requirements > Circular Dependencies`
- location_label: `Circular Dependencies`
- detail: `len=83`

```text
set_property(TARGET ${COMPONENT_LIB} APPEND PROPERTY LINK_INTERFACE_MULTIPLICITY 3)
```

### 9. ESP-IDF Build System ESP32 / chunk 83

- block_type: `code`
- section_path: `Build System > Component Requirements > Requirements in the Build System Implementation > Adding Link-Time Dependencies`
- location_label: `Adding Link-Time Dependencies`
- detail: `len=55`

```text
idf_component_add_link_dependency(FROM other_component)
```

### 10. ESP-IDF Build System ESP32 / chunk 85

- block_type: `code`
- section_path: `Build System > Component Requirements > Requirements in the Build System Implementation > Adding Link-Time Dependencies`
- location_label: `Adding Link-Time Dependencies`
- detail: `len=73`

```text
idf_component_add_link_dependency(FROM other_component TO that_component)
```

### 11. ESP-IDF Build System ESP32 / chunk 90

- block_type: `code`
- section_path: `Build System > Overriding Parts of the Project > Wrappers to Redefine or Extend Existing Functions`
- location_label: `Wrappers to Redefine or Extend Existing Functions`
- detail: `len=83`

```text
target_link_libraries(${COMPONENT_LIB} INTERFACE "-Wl,--wrap=function_to_redefine")
```

### 12. ESP-IDF Build System ESP32 / chunk 118

- block_type: `code`
- section_path: `Build System > Example Component CMakeLists > Embedding Binary Data`
- location_label: `Embedding Binary Data`
- detail: `len=58`

```text
target_add_binary_data(myproject.elf "main/data.bin" TEXT)
```

### 13. ESP-IDF Build System ESP32 / chunk 132

- block_type: `code`
- section_path: `Build System > Flash Arguments`
- location_label: `Flash Arguments`
- detail: `len=58`

```text
esptool --chip esp32 write-flash @build/flash_project_args
```

### 14. ESP-IDF Build System ESP32 / chunk 144

- block_type: `code`
- section_path: `Build System > Using Prebuilt Libraries with Components`
- location_label: `Using Prebuilt Libraries with Components`
- detail: `len=97`

```text
add_prebuilt_library(target_name lib_path [REQUIRES req1 req2 ...] [PRIV_REQUIRES req1 req2 ...])
```

### 15. ESP-IDF Build System ESP32 / chunk 149

- block_type: `code`
- section_path: `Build System > ESP-IDF CMake Build System API > Idf-build-commands`
- location_label: `Idf-build-commands`
- detail: `len=59`

```text
idf_build_get_property(var property [GENERATOR_EXPRESSION])
```

### 16. ESP-IDF Build System ESP32 / chunk 151

- block_type: `code`
- section_path: `Build System > ESP-IDF CMake Build System API > Idf-build-commands`
- location_label: `Idf-build-commands`
- detail: `len=45`

```text
idf_build_set_property(property val [APPEND])
```

### 17. ESP-IDF Build System ESP32 / chunk 153

- block_type: `code`
- section_path: `Build System > ESP-IDF CMake Build System API > Idf-build-commands`
- location_label: `Idf-build-commands`
- detail: `len=53`

```text
idf_build_component(component_dir [component_source])
```

### 18. ESP-IDF Build System ESP32 / chunk 158

- block_type: `code`
- section_path: `Build System > ESP-IDF CMake Build System API > Idf-build-commands`
- location_label: `Idf-build-commands`
- detail: `len=32`

```text
idf_build_executable(executable)
```

### 19. ESP-IDF Build System ESP32 / chunk 160

- block_type: `code`
- section_path: `Build System > ESP-IDF CMake Build System API > Idf-build-commands`
- location_label: `Idf-build-commands`
- detail: `len=55`

```text
idf_build_get_config(var config [GENERATOR_EXPRESSION])
```

### 20. ESP-IDF Build System ESP32 / chunk 162

- block_type: `code`
- section_path: `Build System > ESP-IDF CMake Build System API > Idf-build-commands`
- location_label: `Idf-build-commands`
- detail: `len=58`

```text
idf_build_add_post_elf_dependency(elf_filename dep_target)
```

## Examples: table:packed_multi_value_cells

### 1. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 19

- block_type: `table`
- section_path: `第一章 地面—轮胎力学`
- page_label: `第 19 页`
- location_label: `第 19 页`
- detail: `0. 010～0. 018<br>0. 018～0. 020<br>0. 020～0. 025<br>0. 025～0. 030<br>0. 035～0. 050<br>0. 025～0. 035<br>0. 050～0. 150`

```text
表 1-1 在不同路面上滚动阻力系数 f 的数值 |滚动阻力系数|路面类型| |---|---| |0. 010～0. 018<br>0. 018～0. 020<br>0. 020～0. 025<br>0. 025～0. 030<br>0. 035～0. 050<br>0. 025～0. 035<br>0. 050～0. 150|泥泞土路（雨季或解冻期）<br>干砂<br>湿砂<br>结冰路面<br>压紧的雪道|
```

### 2. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 77

- block_type: `table`
- section_path: `第二章 汽车动力性 > 第五节 电动汽车的动力性计算`
- page_label: `第 51 页`
- location_label: `第 51 页`
- detail: `1650<br>1. 955<br>0. 29<br>0. 015<br>0. 283<br>0. 92`

```text
表 2-5 电动轿车整车的基本参数 |数值|参数| |---|---| |1650<br>1. 955<br>0. 29<br>0. 015<br>0. 283<br>0. 92|旋转质量换算系数δ<br>电动机及其控制器效率ηmc<br>主减速比i0<br>变速器速比ig<br>蓄电池组总能量EB / （kW·h）<br>蓄电池的平均放电效率ηq|
```

### 3. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 116

- block_type: `table`
- section_path: `第三章 汽车的燃油经济性`
- page_label: `第 73 页`
- location_label: `第 73 页`
- detail: `1326. 8<br>1354. 7<br>1284. 4<br>1122. 9<br>1141. 0<br>1051. 2<br>1233. 9<br>1129. 7 | -416. 46<br>-303. 98<br>-189. 75<br>-121. 59<br>-98. 893<br>-73. 714<br>-84. 478<br>-45. 291`

```text
表 3-5 拟合公式的系数 |B<br>0|B<br>1|B<br>2|B<br>3| |---|---|---|---| |1326. 8<br>1354. 7<br>1284. 4<br>1122. 9<br>1141. 0<br>1051. 2<br>1233. 9<br>1129. 7|-416. 46<br>-303. 98<br>-189. 75<br>-121. 59<br>-98. 893<br>-73. 714<br>-84. 478<br>-45. 291|72. 379<br>36. 657<br>14. 524<br>7. 0035<br>4. 4763<br>2. 8593<br>2. 9788<br>0....
```

### 4. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 119

- block_type: `table`
- section_path: `第三章 汽车的燃油经济性`
- page_label: `第 74 页`
- location_label: `第 74 页`
- detail: `19. 34<br>28. 64<br>38. 30<br>47. 75<br>61. 78<br>71. 34<br>80. 76<br>90. 28 | 3. 44<br>5. 64<br>8. 60<br>12. 38<br>20. 08<br>27. 08<br>35. 60<br>46. 09`

```text
表 3-6 各车速下的等速百公里油耗计算结果 |ua /<br>（km·h-1）|P /<br>e<br>kW|b/<br>[g·（kW·h）-1]| |---|---|---| |19. 34<br>28. 64<br>38. 30<br>47. 75<br>61. 78<br>71. 34<br>80. 76<br>90. 28|3. 44<br>5. 64<br>8. 60<br>12. 38<br>20. 08<br>27. 08<br>35. 60<br>46. 09|537. 16<br>481. 26<br>438. 50<br>383. 23<br>334. 74<br>319. 91<br>314. 31<br>3...
```

### 5. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 147

- block_type: `table`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择 > 第一节 发动机的主要性能指标和功率的确定`
- page_label: `第 89 页`
- location_label: `第 89 页`
- detail: `ηet =<br>We<br>Q1<br>= 3. 6<br>beHμ<br>×106<br>（<br>）`

```text
表 4-1 有效指标定义及计算方法 |定 义|计 算 方 法| |---|---| |发动机通过曲轴对外输出的<br>功率|Pe =Pi-Pm<br>Pe =<br>Ttqn<br>9550=<br>pmeVsin<br>30τ<br>（<br>）| |有效功率与指示功率之比|ηm =<br>Pe<br>Pi<br>= 1-<br>Pm<br>Pi| |发动机通过曲轴输出的转矩|Ttq =<br>9550Pe<br>n| |单位气缸工作容积输出的有<br>效功|pme =<br>30Peτ<br>Vsin| |单位有效功的燃油消耗量|be = B<br>Pe<br>×1000| |发动机的有效功We 与所消<br>耗燃料热量Q1 之...
```

### 6. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 184

- block_type: `table`
- section_path: `第四章 汽车发动机功率和传动系统传动比的选择`
- page_label: `第 110 页`
- location_label: `第 110 页`
- detail: `10. 67 / 7. 05 / 5. 18 / 3. 83/<br>2. 78 / 1. 84 / 1. 35 / 1. 00 | 10. 67 / 7. 19 / 4. 85 / 3. 27/<br>2. 20 / 1. 48 / 1. 00`

```text
表 4-9 变速器档位数对汽车动力性和燃油经济性的影响 |档 位 数|变速器传动比值|燃油经济性/<br>[L·（100t·km）-1]| |---|---|---| |档位数|变速器传动比值|CBDTRUCK 工况| |8|10. 67 / 7. 05 / 5. 18 / 3. 83/<br>2. 78 / 1. 84 / 1. 35 / 1. 00|4. 17| |7|10. 67 / 7. 19 / 4. 85 / 3. 27/<br>2. 20 / 1. 48 / 1. 00|4. 18| |6|10. 67 / 6. 65 / 4. 12 / 2. 58/<br>1. 60 / 1. 00|4. 19| |5|10. 67...
```

### 7. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 206

- block_type: `table`
- section_path: `第五章 汽车的制动性 > 第一节 制动性的评价指标`
- page_label: `第 117 页`
- location_label: `第 117 页`
- detail: `≤19m 或<br>≥6. 2m/ s2（空载）<br>≤20m 或<br>≥5. 9m/ s2（满载）`

```text
表 5-4 一些国家轿车制动规范对行车制动性能的要求 |中国<br>GB 7258—2012|瑞典<br>F18|美联邦135| |---|---|---| |φ≥0. 7|φ= 0. 8|Skid No81| |任何载荷|任何载荷|轻、满载| |50km/ h|80km/ h|96. 54km/ h| |不许偏出<br>2. 5m 通道|不抱死跑偏|不抱死跑偏<br>3. 66m| |≤19m 或<br>≥6. 2m/ s2（空载）<br>≤20m 或<br>≥5. 9m/ s2（满载）|≥5. 8m/ s2|≤65. 8m| |<500N|<490N|66. 7～667N|
```

### 8. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 349

- block_type: `table`
- section_path: `第六章 汽车的操纵稳定性`
- page_label: `第 188 页`
- location_label: `第 188 页`
- detail: `46～51<br>51～58<br>51～61<br>76～89<br>76～102<br>114～140<br>154～216 | 127～154<br>127～154<br>154～165<br>165～178<br>165～178<br>165～190<br>178～183`

```text
表 6-3 汽车的侧翻阈值范围 |车 辆 类 型|质心高度/cm|轮距/cm|侧翻阈值/g| |---|---|---|---| |跑车<br>微型轿车<br>豪华轿车<br>轻型客货两用车<br>客货两用车<br>中型货车<br>重型货车|46～51<br>51～58<br>51～61<br>76～89<br>76～102<br>114～140<br>154～216|127～154<br>127～154<br>154～165<br>165～178<br>165～178<br>165～190<br>178～183|1. 2～1. 7<br>1. 1～1. 5<br>1. 2～1. 6<br>0. 9～1. 1<br>0. 8～1. ...
```

### 9. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 388

- block_type: `table`
- section_path: ``
- page_label: `第 205 页`
- location_label: `第 205 页`
- detail: `G q（n0）/ （10-6 m3）（n0 = 0 . 1m-1） | σ q / （10-3 m）（0 . 011m-1<n<2 . 83m-1）`

```text
表 7-1 路面不平度 8 级分类标准 |路 面 等 级|G q（n0）/ （10-6 m3）（n0 = 0 . 1m-1）|σ q / （10-3 m）（0 . 011m-1<n<2 . 83m-1）| |---|---|---| |路面等级|几何平均值|几何平均值| |A<br>B<br>C<br>D<br>E<br>F<br>G<br>H|16<br>64<br>256<br>1024<br>4096<br>16384<br>65536<br>262144|3. 81<br>7. 61<br>15. 23<br>30. 45<br>60. 90<br>121. 80<br>243. 61<br>487. 22|
```

### 10. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 412

- block_type: `table`
- section_path: `第七章 汽车行驶平顺性 > 第五节 人体对振动的反应以及平顺性的评价`
- page_label: `第 219 页`
- location_label: `第 219 页`
- detail: `1. 00<br>1. 00<br>1. 00<br>0. 63<br>0. 40<br>0. 20 | 0. 80<br>0. 50<br>0. 40`

```text
表 7-2 频率加权函数、 轴加权系数 |位 置|坐标轴名称|频率加权函数|轴加权系数k| |---|---|---|---| |座<br>椅<br>支<br>承<br>面|xs<br>ys<br>zs<br>γx<br>γy<br>γz|wd<br>wd<br>wk<br>we<br>we<br>we|1. 00<br>1. 00<br>1. 00<br>0. 63<br>0. 40<br>0. 20| |靠<br>背|xb<br>yb<br>zb|wc<br>wd<br>wd|0. 80<br>0. 50<br>0. 40| |脚|xf<br>yf<br>zf|wk<br>wk<br>wk|0. 25<br>0. 25<br>0...
```

### 11. 汽车理论 (张文春,徐立友) (z-library.sk, 1lib.sk, z-lib.sk) / chunk 418

- block_type: `table`
- section_path: ``
- page_label: `第 221 页`
- location_label: `第 221 页`
- detail: `<0. 315<br>0. 315～0. 63<br>0. 5～1. 0<br>0. 8～1. 6<br>1. 25～2. 5<br>>2. 0 | 110<br>110～116<br>114～120<br>118～124<br>112～128<br>126`

```text
表 7-3 L aw 和 a w 与人的主观感觉之间的关系 |加权加速度均方根值 /（m/s2）<br>a<br>w|加权振级L /dB<br>aw|人的主观感觉| |---|---|---| |<0. 315<br>0. 315～0. 63<br>0. 5～1. 0<br>0. 8～1. 6<br>1. 25～2. 5<br>>2. 0|110<br>110～116<br>114～120<br>118～124<br>112～128<br>126|没有不舒适<br>有一些不舒适<br>相当不舒适<br>不舒适<br>很不舒适<br>极不舒适|
```

## RAG Smoke Test Questions

The machine-readable version is saved as `rag_smoke_questions.json`. Suggested metrics: Hit@1, Hit@3, Hit@5, MRR, context precision, context recall, citation accuracy.

- `esp32_wireless_capabilities`: ESP32 集成了哪些无线能力？
- `esp_idf_prerequisites`: ESP-IDF 开发环境需要哪些软件组件？
- `idf_py_build_equivalent`: idf.py build 等价于哪些 CMake 或 Ninja 命令？
- `idf_component_definition`: ESP-IDF 项目中的 component 是什么？
- `esp32_product_resources`: ESP32 产品页提到哪些资源入口？
- `vehicle_power_performance_indexes`: 汽车动力性能用哪些指标衡量？
- `tire_coordinate_axes`: 轮胎坐标系的 x/y/z 轴如何定义？
- `rolling_resistance_factors`: 滚动阻力系数与哪些因素有关？
# ThermoAudit：能源流程数据校核工具

面向能源动力、制冷、氢液化等流程研究，帮助研究者在分析结果前发现**质量不守恒、功率符号错误、换热方向异常和候选方案筛选错误**。

这是可运行的开源首版（0.1.0），不是已经被广泛使用的成熟项目。全部示例为合成教学数据，不来自论文、他人的模型或真实装置。

仓库：https://github.com/5dzph/thermoaudit 。维护者：5dzph。

## 最快打开方式

1. 下载或克隆项目，进入包含 README 的文件夹。
2. 已安装 Python 3.10 以上的 Windows 用户双击 `run_demo.bat`。
3. 运行成功后会打开两个本地浏览器报告：流程校核、Pareto 候选比较。
4. 没有安装 Python 时，可先打开 `demo_reports` 中的 HTML 查看静态预期结果摘要。运行程序会生成完整报告。

源码运行不需要下载第三方 Python 库。浏览器仅显示本地报告，不上传数据。

```bat
py -3 -m thermoaudit audit examples/balanced_hx.json --out reports
py -3 -m thermoaudit pareto examples/candidates.csv --weights 2 1 1 --out reports
py -3 -m unittest discover -s tests -v
```

macOS/Linux 可将 `py -3` 改为 `python3`。若 Windows 提示找不到 Python，请安装 Python 3.10 以上后重试；项目不包含 Python 安装程序。

## 已实现

| 功能 | 首版范围 |
| --- | --- |
| 质量守恒 | 各设备边界及换热器两侧分别检查 |
| 能量守恒 | 显式指定热流与轴功符号，输出残差和容差 |
| 换热器 | 两流股逆流，两端温差和被动换热方向检查 |
| 比能耗 | 总净输入功率 ÷ 边界产品质量流量，换算为 kWh/kg |
| 多目标筛选 | 比能耗最小、㶲效率最大、CAPEX 最小 |
| 折中候选 | 权重可调、归一化规则公开、排除不可行点 |
| 输出 | 离线 HTML、机器可读 JSON、输入文件 SHA-256 |

**“校核通过”不等于模型收敛或物理可行。** 换热器只检查两端，不证明内部没有夹点。程序不提供氢物性、正仲氢转换、有限 UA 求解、HYSYS 自动化或遗传算法优化。㶲效率和 CAPEX 是外部输入，不由程序估算。

## 使用你自己的数据

复制 `examples/balanced_hx.json`，按 [字段与公式说明](docs/data-contract.md) 填入流股和设备。单位固定为 kg/s、K、kJ/kg、kW，不能直接填 kg/h 或 ℃。轴功以“设备向外输出”为正，因此压缩机输入功通常为负。

多目标数据按 `examples/candidates.csv` 的表头导出；Excel 可另存为 UTF-8 CSV，当前不直接读取 xlsx。㶲效率为 0–1 小数，例如 45% 应填 `0.45`。所有候选方案须使用一致的经济基准和系统边界。`feasible` 根据实际约束填写。

退出码 0 表示所列检查通过；1 表示检测到失衡等问题并已生成报告；2 表示输入或文件操作错误。请不要把退出码 1 当作程序坏了。

## 持续维护

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，待开发功能见 [ROADMAP.md](ROADMAP.md)。申请准备说明见 [docs/release-and-application.zh-CN.md](docs/release-and-application.zh-CN.md)。当前仅为项目首版，尚未提交 Codex for Open Source 申请，也没有已核实的社区采用数据。

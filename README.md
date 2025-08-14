# 🚀 Memrix :: 记忆星核

![LOGO](https://raw.githubusercontent.com/PlaxtonFlarion/SoftwareCenter/main/Assets/MemrixSource/app_readme.png)

---

## 🏆 项目简介 · Memrix :: 记忆星核

### ⭐️ 前沿技术
- **Memrix** 是一款跨平台的性能测试工具，专为硬件测试人员、开发者、售后工程师和技术爱好者设计。
- **Memrix** 运行于 **Windows** 与 **macOS** 平台，识别设备潜在的内存问题与性能瓶颈。
- **Memrix** 以专业的测试逻辑、清晰的报告输出和灵活的参数配置，为测试场景提供一个稳定可靠的解决方案。

### ⭐️ 核心优势
- **即插即测** 无需额外驱动或环境配置，连接设备即可开始测试。
- **多维覆盖** 支持内存、I/O、帧率等多类性能指标采集与分析。
- **趋势识别** 集成斜率拟合、抖动判断、多项式趋势分析等算法，辅助诊断。
- **自动报告** 测试结束后自动生成结构化图文报告，便于分析、归档与共享。
- **灵活配置** 采样间隔、时长、过滤逻辑等参数可完全自定义，适配多种场景。

---

## 🎯 使命宣言
- **Memrix** 致力于最简洁、高效的性能优化工具。为移动应用开发者提供一个无与伦比的优化利器。
- **Memrix** 专注于提升应用的内存使用效率，使性能优化不再是难题。

---

## 🔧 工程艺术
- **Memrix** 构建于一系列高效的编程框架和技术之上，涵盖了从前端到后端，再到底层硬件的全栈技术。

---

## 🌐 平台兼容
- **Memrix** 设计之初，就考虑到了跨平台的需求，无论是 **Windows** 还是 **macOS**，**Memrix** 都能完美适配。
- **Memrix** 可以在任何平台上启动和运行，用户无需担心操作系统的限制，享受统一的用户体验和性能优化服务。

---

## 📦 内置工具

### ⭐️ Memrix 内置了以下工具的不同版本，确保无论在哪个平台，Memrix 都能完美运行:
- **[Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools)**: 提供 ADB 接入、进程采样、系统信息访问等能力。
- **[Perfetto](https://perfetto.dev/)**: 用于高精度帧时序追踪、CPU / 内存 / IO 级别的底层性能分析。

### ⭐️ 自动检测
- **Memrix** 能智能识别您的操作系统，并自动选择适合的工具版本。无需担心手动配置问题，一切都为简化您的体验而设计。

### ⭐️ 优化安装
- 为了确保应用的轻便高效，我们采用了文件压缩技术，并在必要时下载特定组件，减少对您设备存储的占用。

### ⭐️ 定期更新
- 我们致力于提供最新版本的内置工具，以确保性能和安全性。您可以放心，**Memrix** 将随时保持更新。

---

## 🧭 安装指南

### ⭐️ Memrix 提供简洁明了的安装包，让您能够轻松开始您的性能测试之旅。
- **1. 下载**: 访问我们的 [发布页面](https://github.com/PlaxtonFlarion/SoftwareCenter/releases) 下载最新版的 **Memrix** 安装包。
- **2. 安装**: 运行下载的安装包，并按照提示完成安装过程，安装完成后设置系统环境变量。
- **3. 启动**: 安装完成后，通过命令行启动 **Memrix** 开始体验高效的性能测试。
- **4. 体验**: 如果您使用的是 **Windows** 操作系统，为了增加体验感，强烈建议您使用 [Windows Terminal](https://github.com/microsoft/terminal) 等现代终端。
- **5. 就绪**: 在 **Memrix** 启动前，确保所有系统正常。

---

## 📖 快速上手
### ⭐️ Memrix 提供了一系列命令行参数来控制不同的功能和行为。
- **Memrix** 的使用可能需要一定的命令行知识。如果您不熟悉命令行操作，建议先了解基础的命令行使用方法。

---

## 🔰 核心操控

### ⚜️ 星痕律动（`--storm`）  
#### 📔 功能描述:  
- 执行 **内存波动 + I/O 行为** 联合采样。  
- 追踪进程内多维内存指标与系统调用特征，建模资源使用轨迹。  
#### 📔 参数说明:  
- **布尔值**，默认为 `False`  
#### 📔 实际应用:  
```
memrix --storm --focus <com.example.application>
```

---

### ⚜️ 帧影流光（`--sleek`）  
#### 📔 功能描述:  
- 执行 **帧率稳定性与交互流畅度** 分析。  
- 基于 Perfetto 时序数据，自动识别滑动段 / 拖拽段 / 掉帧段，并评分体验质量。  
#### 📔 参数说明:  
- **布尔值**，默认为 `False`  
#### 📔 实际应用:  
```
memrix --sleek --focus <trace_file.perfetto>
```

---

### ⚜️ 真相快照（`--forge`）  
#### 📔 功能描述:  
- 生成结构化测试报告与可视化图表。  
- 汇总内存 / IO / 流畅度结果，统一渲染为 HTML 报告。  
#### 📔 参数说明: 
- **字符串**，报告输出文件夹名称。  
#### 📔 实际应用: 
```
memrix --forge <output_dir>
```

---

### ⚜️ 星核蓝图（`--align`）  
#### 📔 功能描述:  
- 启用结构化评分机制，自动对内存、流畅度、I/O 等指标进行多维度判级与可视化评估。  
- 所有配置基于 YAML 文件（默认内置），支持覆盖修改或外部引用，结构灵活，参数清晰。  
- 评分结果将用于报告生成、准出标准校验与风险标注。
#### 📔 参数说明:
- **布尔值**，默认 `False`，启用后从预设路径加载 YAML 配置进行指标校验与报告嵌入。
#### 📔 实际应用:  
```
memrix --storm --align
```
#### 📄 通用结构概览:
```yaml
aligns:
  common:
    app_label: ...
    mem_speed: ...
    gfx_speed: ...
  mem:
    base:
      headline: ...
      standard: {...}
      sections: [...]
    leak:
      headline: ...
      standard: {...}
      sections: [...]
  gfx:
    base:
      headline: ...
      standard: {...}
      sections: [...]
```
#### 🧩 字段说明:
- 🔹 `app_label`: **采集目标应用的名称**
  - 用于报告展示中标记测试对象，也用于自动识别采集进程。
  - 示例值: `"com.example.app"`
- 🔹 `mem_speed`: **内存数据采样频率**
  - 表示每隔多少秒采集一次内存指标（如 RSS、PSS、USS）。
  - 示例值: `0.5` 表示每 0.5 秒采集一次，频率越高越精准，适用于瞬态波动检测。
- 🔹 `gfx_speed`: **图形帧数据持续采样频率**
  - 表示单次采集帧数据的时长，分多次采集。
  - 示例值: `30.0` 表示多次采集，每次采集30秒，用于计算 FPS、Jank 等指标。
- 🔹 `headline`
  - 类型: `字符串`
  - 含义: 当前模块或评估类别的标题，用于报告页签、概览名称等。
- 🔹 `standard`
  - 类型: `字典`
  - 含义: 定义每项评估指标，包括评判逻辑、专业描述、提示信息等。
  - 每个指标字段支持如下子字段:
    - `threshold`：数值阈值（用于比较）
    - `direction`：方向规则，`ge`（大于等于为优）或 `le`（小于等于为优）
    - `desc`：简明标题（通常用于提示或字段名称）
    - `tooltip`：详细解释（悬浮说明，展示在报告表格中）
- 🔹 `sections`
  - 类型: `列表`
  - 含义: 可配置的文本描述区块，用于报告文本输出，包括评估参考、准出标准等。
  - 每个 section 包含:
    - `title`：区块标题（如“准出标准”、“参考标准”）
    - `class`：展示样式类别，可设为 `refer`（参考标准）或 `criteria`（准出标准）
    - `enter`（可选）: 布尔值，表示是否默认展开
    - `value`：一个字符串数组，每条为一行内容（将渲染为列表）

```
如需拓展更多评估项，只需添加对应模块与标准块，结构保持一致即可。
此配置支持按模块分组、评分判定、文案展示一体，便于灵活维护和扩展。
```

---

### ⚜️ 星图凭证 (`--apply`)
#### 📔 功能描述:
- 使用激活码向远程授权中心发起请求，获取签名后的授权数据。  
- 授权数据将绑定当前设备指纹，并以 LIC 文件形式存储在本地。
#### 📔 参数说明: 
- `ACTIVATION CODE`: 一次性激活码，用于发起授权请求。  
- 支持命令行直接传参或留空后等待交互式输入。
#### 📔 实际应用: 
```
memrix --apply ACT-87K2-JQ91-XVZ3
```

## 🔰 环境桥接

### ⚜️ 数据魔方 (`--focus`)
#### 📔 功能描述:
- 传递应用包名。
#### 📔 参数说明:
- **字符串**，通常为 Android 应用的包名（如 `com.example.app`）。
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application>
```

### ⚜️ 宿主代号 (`--imply`)
#### 📔 功能描述:
- 指定目标设备的唯一序列号，当连接多个设备或自动识别失败时强制绑定目标设备。
#### 📔 参数说明: 
- **字符串**，为 ADB 设备的序列号（通过 `adb devices` 查看）。
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application> --imply <device.serial>
```

---

### ⚜️ 中枢节点 (`--scene`)
#### 📔 功能描述:
- 指定文件夹名称，作为任务的挂载目录或输出目录。数据的中转与聚合中心。
- 每次采集任务会将所有数据输出到一个对应的文件夹中，便于归档与后续生成报告。
#### 📔 参数说明: 
- **字符串**，用于指定输出目录名称。
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application> --scene <file.name>
```

---

### ⚜️ 星辰序列（`--title`）  
#### 📔 功能描述:  
- 设置报告主标题，便于区分不同测试任务的上下文。  
#### 📔 参数说明:  
- **字符串**，用于标记报告名称。  
#### 📔 实际应用:  
```
memrix --storm --focus <com.example.application> --title <name>
```

---

### ⚜️ 涟漪视界（`--atlas`）  
#### 📔 功能描述:  
- 任务完成后自动生成结构化图表报告，实现一体化流程。
#### 📔 参数说明: 
- **布尔值**，默认为 `False`  
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application> --atlas
```

---

### ⚜️ 极昼极夜（`--layer`）  
#### 📔 功能描述:  
- 在分析阶段区分 **前台** 与 **后台** 阶段内存数据。  
- 输出分段图表，提升可视化精度。  
#### 📔 参数说明: 
- **布尔值**，默认为 `False`  
#### 📔 实际应用:  
```
memrix --forge <file.name> --layer
```

---

## 🔰 观象引擎

### ⚜️ 洞察之镜 (`--watch`)
#### 📔 功能描述:
- 启动调试反射视角，用于观察系统运行轨迹与隐藏信息。
- 展示最详细的调试输出，追踪函数调用与变量变化。
#### 📔 参数说明:
- **布尔值** 默认为 `False`
#### 📔 实际应用: 
```
memrix --storm --focus <variable> --watch
```

---

## 🖥️ 使用示例
 
### 💾 持续监控 (`--storm --focus`)
```
memrix --storm --focus <com.example.application>
```

### 💾 生成报告 (`--forge`)
```
memrix --forge <file.name>
```

---

## Memrix｜记忆星核 编译 / Compile

![LOGO](https://raw.githubusercontent.com/PlaxtonFlarion/SoftwareCenter/main/Assets/MemrixSource/app_compile.png)

---

### 前提条件
#### 在开始之前，请确保已完成以下操作:
- 安装 **[Python](https://www.python.org/downloads/) 3.11** 或更高版本
- 安装 **[Nuitka](https://nuitka.net/)**
  - 导航到您的 **Python** 脚本所在的目录
    ```
    pip install nuitka==2.7
    ```

- 确保在项目根目录下有一个 `requirements.txt` 文件，其中列出了所有的依赖包
> **MemNova**
>> **requirements.txt**

- 确保您的 **Python** 环境中安装了所有依赖包
  - **海外** 导航到您的 **Python** 脚本所在的目录
    ```
    pip install -r requirements.txt
    ```
  - **大陆** 导航到您的 **Python** 脚本所在的目录
    ```
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```

- 在 **Python** 脚本所在的目录新建 `applications` 目录
> **MemNova**
>> **applications**

---

### 工具目录

#### 新建 `supports` 目录以及子目录，拷贝可执行文件至对应目录
- schematic
  - resources
  - supports
    - MacOS
    - Windows
      - npp_portable_mini
        - notepad++.exe
        - ...
  - templates
    - ...

---

### Windows 操作系统
#### 准备工作
- 打开命令提示符 **Command Prompt** 或 **PowerShell**
- 导航到您的 **Python** 脚本所在的目录

#### 运行根目录下 `build.py` 文件
> **MemNova**
>> **build.py**

#### 目录结构
- **applications**
  - **MemrixEngine**
    - **schematic**
    - **...**
  - **memrix.bat**
  - **Structure**
    - **Memrix_Mix**
    - **Memrix_Report**

---

### MacOS 操作系统
#### 准备工作
- 打开终端 **Terminal** 
- 导航到您的 **Python** 脚本所在的目录

#### 运行根目录下 `build.py` 文件
> **MemNova**
>> **build.py**

#### 目录结构
- **applications**
  - **Memrix.app**
    - **Contents**
      - **_CodeSignature**
      - **MacOS**
        - **schematic**
        - **memrix.sh**
        - **memrix**
        - **...**
      - **Resources**
        - **memrix_macos_bg.png**
        - ...
      - **Structure**
        - **Memrix_Mix**
        - **Memrix_Report**
      - **Info.plist**

---

## 🖐️ 技术支持
### ⭐️ 遇到任何问题，欢迎联系我们的技术支持团队。我们随时准备协助您解决问题。
- **[Welcome to issues!](https://github.com/PlaxtonFlarion/MemNova/issues)**

---

## 👥 社区协作
### ⭐️ 加入我们的行列！
- 无论是通过 **[Pull Request](https://github.com/PlaxtonFlarion/MemNova/pulls)** 还是 **[Issue](https://github.com/PlaxtonFlarion/MemNova/issues)**，您的智慧都是我们的财富。

---

## 📜 软件许可
### ⭐️ 我们遵循所有内置工具的开源许可和版权政策，并在应用中包含了原始许可证文本。
- **Memrix** 为专有软件（Proprietary Software），采用时间限制授权方式，禁止未经授权的复制、修改或传播。
- 若您希望申请授权，请联系 **[AceKeppel@outlook.com]**

---

## 📬 互动交流
### ⭐️ 有疑问？有灵感？我们期待您的来信: 
- **[AceKeppel@outlook.com]**
- **Memrix** - 洞察每一字节，唤醒每一段记忆 —— Memrix · 记忆星核。

---

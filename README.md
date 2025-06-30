# 🚀 Memrix :: 记忆星核

![LOGO](https://raw.githubusercontent.com/PlaxtonFlarion/SoftwareCenter/main/Assets/MemrixSource/app_readme.png)

---

## 🏆 项目简介 · Memrix :: 记忆星核

### ⭐️ 前沿技术
- **Memrix** 是一款跨平台的内存测试工具，专为硬件测试人员、开发者、售后工程师和技术爱好者设计。
- **Memrix** 运行于 **Windows** 与 **macOS** 平台，识别设备潜在的内存问题与性能瓶颈。
- **Memrix** 以专业的测试逻辑、清晰的报告输出和灵活的参数配置，为测试场景提供一个稳定可靠的解决方案。

### ⭐️ 命名灵感
- **Memrix** 来自 **Memory + Matrix** 的组合，中文名为 **记忆星核**。
- **Memrix** 象征内存世界中的逻辑结构、能量波动与智能探测，仿佛一颗潜入芯片深处的「星核」，洞察每一段正在闪烁的数据流动。

### ⭐️ 核心优势
- **即插即测** 无需额外驱动或环境配置，连接设备即可开始测试。
- **读写验证** 真实模拟负载，发现隐藏性内存异常与稳定性问题。
- **持续模式** 可进行无限循环拉取测试，捕捉瞬时错误。
- **扩展架构** 内核架构预留多平台适配能力，支持未来快速扩展。
- **报告输出** 测试完成后自动生成结构化报告，方便分析、归档与共享。

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
- **[Notepad++](https://notepad-plus-plus.org/downloads/)**: 纯文本编辑器。

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

### ⚜️ 记忆风暴 (`--storm`)
#### 📔 功能描述:
- 启动 **记忆风暴模式**，以持续的周期性方式拉取目标应用的内存使用情况，并将数据写入本地数据库中，供后续报告分析与可视化展示使用。
- 可指定目标应用包名，通过配置文件自定义拉取频率（默认 1 秒，可设定范围为 1~10 秒）。
- 适用于长时间稳定性监控、内存波动追踪、异常捕捉及前后台行为对比等复杂测试场景。
- 手动中断（Ctrl+C）。
#### 📔 参数说明: 
- **布尔值** 默认为 `False`
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application>
```

### ⚜️ 巡航引擎 (`--pulse`)
#### 📔 功能描述:
- 启动 **巡航引擎模式**，读取指定的 **JSON** 文件，根据其中定义的关键步骤，执行 **UI** 自动化操作。
- **Memrix** 会在执行过程中使用 **异步协程机制**，持续实时检测内存状态，确保测试流程与内存监控同步进行。
- **JSON** 脚本需符合自动化指令格式规范（如点击、滑动、输入、等待等），可结合 **UI** 控制引擎使用。
- 该命令适用于复杂场景模拟、自动化行为验证、压力场景下的内存异常捕捉等任务。
- 手动中断（Ctrl+C）。
#### 📔 参数说明: 
- **布尔值** 默认为 `False`
#### 📔 实际应用: 
```
memrix --pulse --focus <file.path>
```
#### 📔 脚本说明:
- `loopers` 脚本需要循环的次数
- `package` 应用程序包名
- `mission` 自动化指令集名称
  - `step1` 业务名称
    - `cmds` `u2`需要调用的自动化指令
    - `vals` `u2`自动化指令接收的参数
    - `args` `method`接收的不定长参数
    - `kwds` `method`接收的关键字参数
#### 📔 脚本示例:
```json
{
    "loopers": 10,
    "package": "com.example.application",
    "mission": {
        "step1": [
            {"cmds": "u2", "vals": [null, "method"], "args": ["arg"], "kwds": {"k": "v"}},
            {"cmds": "u2", "vals": [null, "method"], "args": ["arg"], "kwds": {"k": "v"}},
            {"cmds": "u2", "vals": [null, "method"], "args": ["arg"], "kwds": {"k": "v"}}
        ]
    }
}
```

### ⚜️ 真相快照 (`--forge`)
#### 📔 功能描述:
- 启动 **真相快照模式**，从测试过程中记录的本地数据库中提取原始数据，执行统计分析（如均值、峰值、波动区段）。
- 自动生成结构化、可视化的 **HTML** 格式报告，包含内存曲线图、异常区域标记、基本统计指标、测试元信息等。
- 支持限定输出指定批次的数据报告。
#### 📔 参数说明: 
- **布尔值** 默认为 `False`
#### 📔 实际应用: 
```
memrix --forge --focus <file.name>
```

### ⚜️ 星核蓝图 (`--align`)
#### 📔 功能描述:
- 启动 **星核蓝图模式**，**Memrix** 将自动调用系统内置的文本编辑器，打开主配置文件（YAML 格式）。
- 文件将以格式化、美观、带注释的方式呈现，便于修改参数行为、默认模式、报告设置等。
- 完成编辑并保存后，**Memrix** 会在下次启动时自动加载该配置。
- 配置文件是 **Memrix** 的“星核蓝图”，定义了程序的运行地图、参数注入与行为预设。
#### 📔 参数说明: 
- **布尔值** 默认为 `False`
#### 📔 实际应用: 
```
memrix --align
```
#### 📔 文件说明:
- `Memory`
  - `speed` 速率
  - `label` 应用名称
- `Script`
  - `group` 自动化指令集名称
- `Report`
  - `fg_max` 前台峰值标准
  - `fg_avg` 前台均值标准
  - `bg_max` 后台峰值标准
  - `bg_avg` 后台均值标准
  - `headline` 标题
  - `criteria` 标准
#### 📔 文件示例:
```yaml
Memory:
  speed: 1
  label: 应用名称
Script:
  group: mission
Report:
  fg_max: 0.0
  fg_avg: 0.0
  bg_max: 0.0
  bg_avg: 0.0
  headline: 标题
  criteria: 标准
```

---

### ⚜️ 星图凭证 (`--apply`)
#### 📔 功能描述:
- 使用激活码向远程授权中心发起请求，获取签名后的授权数据。  
- 授权数据将绑定当前设备指纹，并以 LIC 文件形式存储在本地。  
- 一旦激活成功，系统将进入已授权状态，具备完全运行权限。  
- 适用于首次部署、跨环境迁移、临时激活等场景。
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
- 用于传递关键上下文信息，根据核心操控命令的不同将自动转换为对应的上下文用途，提供结构化参数支持。
#### 📔 参数说明:
- **记忆风暴模式** 传递 -> **应用程序包名**
- **巡航引擎模式** 传递 -> **脚本文件路径**
- **真相快照模式** 传递 -> **指定报告编号**
#### 📔 实际应用: 
```
memrix --storm --focus <variable>
```

### ⚜️ 宿主代号 (`--imply`)
#### 📔 功能描述:
- 指定目标设备的唯一序列号，当连接多个设备或自动识别失败时强制绑定目标设备。
- 它是 **Memrix** 与设备之间的“精确信标”，确保测试任务落在指定设备之上，防止误测、多测或设备错位操作。
#### 📔 参数说明: 
- **字符串**
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application> --imply <device.serial>
```

### ⚜️ 中枢节点 (`--vault`)
#### 📔 功能描述:
- 指定文件夹名称，作为任务的挂载目录或输出目录。数据的中转与聚合中心。
- 每次内存采集任务会将所有数据输出到一个对应的文件夹中，便于归档与后续生成报告。
- 你可以手动传入一个自定义名称，例如 `20250410223015`。
- 如果未传递该参数，将默认生成一个以当前时间戳命名的目录，例如 `20250410223232`。
- 所有输出文件（日志、HTML 报告等）都会保存在该目录下。
#### 📔 参数说明: 
- **字符串**
#### 📔 实际应用: 
```
memrix --storm --focus <com.example.application> --vault <file.name>
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

### 💾 自动监控 (`--pulse --focus`)
```
memrix --pulse --focus <file.path>
```

### 💾 生成报告 (`--forge --focus`)
```
memrix --forge --focus <file.name>
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

# Memrix(记忆星核) 编译 / Compile

![LOGO](resources/images/illustration/Compile.png)

---

## 前提条件
### 在开始之前，请确保已完成以下操作:
- 安装 **[Python](https://www.python.org/downloads/) 3.11** 或更高版本
- 安装 **[Nuitka](https://nuitka.net/)**
  - 导航到您的 **Python** 脚本所在的目录
    ```
    pip install nuitka
    ```
- 确保在项目根目录下有一个 `requirements.txt` 文件，其中列出了所有的依赖包
> **MemNova**
>> **requirements.txt**
- 确保您的 **Python** 环境中安装了所有依赖包
  - 导航到您的 **Python** 脚本所在的目录
    ```
    pip install -r requirements.txt
    ```
- 在 **Python** 脚本所在的目录新建 `applications` 目录
> **MemNova**
>> **applications**

---

## 工具目录
### 拷贝 `resources` 目录
- schematic
  - resources

### 拷贝 `memnova/templates` 目录
- schematic
  - resources
  - templates
    - ...

---

## Windows 操作系统
### 准备工作
- 打开命令提示符 **Command Prompt** 或 **PowerShell**
- 导航到您的 **Python** 脚本所在的目录

### 运行 Nuitka 命令
```
python -m nuitka --standalone --windows-icon-from-ico=resources/icons/memrix_icn_1.ico --nofollow-import-to=uiautomator2 --include-module=deprecation,xmltodict --include-package=adbutils,apkutils2,cigam,pygments --show-progress --show-memory --output-dir=applications memcore/memrix.py
```

### 目录结构
- **applications**
  - **memrix.dist**
    - **schematic**
    - **...**
  - **memrix.bat**

---

## MacOS 操作系统
### 准备工作
- 打开终端 **Terminal** 
- 导航到您的 **Python** 脚本所在的目录

### 运行 Nuitka 命令
```
python -m nuitka --standalone --macos-create-app-bundle --macos-app-icon=resources/images/macos/memrix_macos_icn.png --nofollow-import-to=uiautomator2 --include-module=deprecation,xmltodict --include-package=adbutils,apkutils2,cigam,pygments --show-progress --show-memory --output-dir=applications memcore/memorix.py
```

### 目录结构
- **applications**
  - **memrix.app**
    - **Contents**
      - **_CodeSignature**
      - **MacOS**
        - **schematic**
        - **memrix.sh**
        - **...**
      - **Resources**
        - **memrix_macos_bg.png**
        - ...
      - **Info.plist**

### 修改 Info.plist 文件
```
<key>CFBundleExecutable</key>
<string>memrix.sh</string> <!-- 设置启动脚本 -->
```

### 赋予执行权限
#### memrix
```
chmod +x /Applications/memrix.app/Contents/MacOS/memrix
```

#### memrix.sh
```
chmod +x /Applications/memrix.app/Contents/MacOS/memrix.sh
```

---
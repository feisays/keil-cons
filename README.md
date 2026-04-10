# Keil uVision 命令行工具

通过 Keil UV4 命令行接口完成工程的编译、重编译、下载等操作，支持交互式和命令行两种使用方式。

## 前置要求

- Python 3.6+
- Keil MDK (uVision 5) 已安装
- **UV4.exe 已添加到系统 PATH 环境变量**

### 添加 UV4.exe 到 PATH

1. 找到 Keil 安装目录（通常为 `C:\Keil_v5\UV4`）
2. 右键"此电脑" -> 属性 -> 高级系统设置 -> 环境变量
3. 在"系统变量"中找到 `Path`，点击编辑
4. 添加 UV4.exe 所在目录路径（如 `C:\Keil_v5\UV4`）
5. 重启终端使配置生效

## 使用方法

### 交互模式（默认）

不带参数直接运行，进入交互式菜单：

```bash
python keil_cons.py
```

交互菜单提供以下操作：

| 选项 | 命令 | 说明 |
|------|------|------|
| 1 | Build (-b) | 仅编译修改过的文件 |
| 2 | Rebuild (-r) | 重新编译所有文件 |
| 3 | Flash (-f) | 下载程序到 Flash |
| 4 | Clean (-c) | 清理工程目标 |
| 5 | Clean + Rebuild (-cr) | 清理后重编译 |
| 6 | Build All (-b -z) | 编译所有目标 |

### 命令行模式

```bash
# 编译工程
python keil_cons.py -b

# 重编译工程
python keil_cons.py -r

# 下载到 Flash
python keil_cons.py -f

# 清理工程
python keil_cons.py -c

# 清理并重编译
python keil_cons.py --clean-rebuild

# 指定目标名称
python keil_cons.py -r -t "Target 1"

# 指定工程文件
python keil_cons.py -b -p D:/projects/demo/demo.uvprojx

# 指定搜索目录
python keil_cons.py -b -d D:/projects/demo

# 指定日志输出路径
python keil_cons.py -r -o build.log
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `-b`, `--build` | 编译工程（增量编译） |
| `-r`, `--rebuild` | 重编译工程（全量编译） |
| `-f`, `--flash` | 下载程序到 Flash |
| `-c`, `--clean` | 清理工程目标 |
| `--clean-rebuild` | 清理后重编译 |
| `-t`, `--target` | 指定目标名称 |
| `-p`, `--project` | 指定工程文件路径 |
| `-d`, `--dir` | 工程搜索目录（默认当前目录） |
| `-o`, `--output` | 指定日志输出路径 |

> 默认启用 `-j0` 隐藏 uVision GUI，无需手动指定。

## 编译日志

默认在工程所在目录下生成固定名称的编译日志：

```
BuildLog.log
```

可通过 `-o` 参数指定自定义日志路径。

## UV4 退出码

| 退出码 | 含义 | 脚本退出码 |
|--------|------|------------|
| 0 | 成功，无错误和警告 | 0 |
| 1 | 仅有警告 | 0（视为成功） |
| 2 | 存在错误（编译失败） | 2 |
| 3 | 致命错误 | 3 |
| 11 | 无法打开工程文件进行写入 | 11 |
| 12 | 数据库中未找到指定设备 | 12 |
| 13 | 写入工程文件出错 | 13 |
| 15 | 读取导入 XML 文件出错 | 15 |

警告（退出码 1）视为编译成功，仅当存在 error（退出码 >= 2）时才报失败。脚本退出码便于在 CI/CD 中判断编译结果。

## 工程文件查找

默认在当前目录**及其子目录**中递归搜索 `.uvprojx`（Keil v5）和 `.uvproj`（Keil v4）工程文件：
- 找到一个：自动使用
- 找到多个：列出相对路径，提示用户选择
- 未找到：报错退出

可通过 `-p` 直接指定工程文件路径，或通过 `-d` 指定搜索根目录。

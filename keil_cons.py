#!/usr/bin/env python3
"""
Keil uVision 命令行工具
通过 UV4.exe 完成对 Keil 工程的编译、下载等操作。
支持交互式运行，默认在当前目录查找 .uvprojx 工程文件。
"""

import os
import sys
import shutil
import subprocess
import argparse


def check_uv4() -> str:
    """检查 UV4.exe 是否在 PATH 环境变量中可用。

    Returns:
        UV4.exe 的完整路径。

    Raises:
        SystemExit: 如果 UV4.exe 不在 PATH 中。
    """
    uv4_path = shutil.which("UV4")
    if uv4_path:
        return uv4_path

    # 也检查常见安装位置
    common_paths = [
        os.path.join(os.environ.get("ProgramFiles", ""), "Keil_v5", "UV4", "UV4.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Keil_v5", "UV4", "UV4.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Keil", "UV4", "UV4.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Keil", "UV4", "UV4.exe"),
    ]
    for p in common_paths:
        if p and os.path.isfile(p):
            return p

    print("[错误] 未在 PATH 中找到 UV4.exe。")
    print("请将 UV4.exe 所在目录添加到系统 PATH 环境变量中。")
    print("常见路径示例: C:\\Keil_v5\\UV4")
    print("设置方法: 系统属性 -> 高级 -> 环境变量 -> Path -> 添加 UV4.exe 所在目录")
    sys.exit(1)


def find_project(search_dir: str = ".") -> str:
    """在指定目录及其子目录中查找 Keil 工程文件。

    Args:
        search_dir: 搜索目录，默认为当前目录。

    Returns:
        工程文件的完整路径。

    Raises:
        SystemExit: 如果未找到工程文件或找到多个。
    """
    projects = []

    for root, _dirs, files in os.walk(search_dir):
        for f in files:
            if f.endswith(".uvprojx") or f.endswith(".uvproj"):
                projects.append(os.path.join(root, f))

    if not projects:
        print(f"[错误] 在 {os.path.abspath(search_dir)} 及其子目录中未找到 Keil 工程文件 (.uvprojx / .uvproj)。")
        sys.exit(1)

    if len(projects) == 1:
        return os.path.abspath(projects[0])

    # 多个工程文件，让用户选择
    print(f"[提示] 找到 {len(projects)} 个工程文件：")
    for i, p in enumerate(projects, 1):
        rel = os.path.relpath(p, search_dir)
        print(f"  {i}. {rel}")

    while True:
        try:
            choice = input("请选择工程编号: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                return os.path.abspath(projects[idx])
            print(f"无效选择，请输入 1-{len(projects)} 之间的数字。")
        except (ValueError, EOFError):
            print(f"无效输入，请输入 1-{len(projects)} 之间的数字。")


def get_log_path(project_path: str, command: str = None) -> str:
    """在工程所在目录生成日志文件路径。

    Args:
        project_path: 工程文件路径。
        command: UV4 命令，用于区分日志文件名。

    Returns:
        日志文件完整路径。
    """
    project_dir = os.path.dirname(os.path.abspath(project_path))
    log_name_map = {
        "-b": "BuildLog.log",
        "-r": "RebuildLog.log",
        "-cr": "CleanRebuildLog.log",
        "-f": "FlashLog.log",
    }
    log_name = log_name_map.get(command, "KeilCommand.log")
    return os.path.join(project_dir, log_name)


def should_use_log(command: str) -> bool:
    """判断命令是否默认生成日志文件。"""
    return command in {"-b", "-r", "-cr", "-f"}


def run_uv4(uv4_path: str, project_path: str, command: str,
            target: str = None, log_path: str = None) -> int:
    """执行 UV4 命令。

    Args:
        uv4_path: UV4.exe 路径。
        project_path: 工程文件路径。
        command: UV4 命令 (-b/-r/-f/-c/-cr 等)。
        target: 目标名称（可选）。
        log_path: 日志输出路径（可选）。

    Returns:
        UV4 的退出码。
    """
    cmd = [uv4_path, command, project_path]

    if target:
        cmd.extend(["-t", target])

    if log_path:
        cmd.extend(["-o", log_path])

    print(f"[执行] {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
    except FileNotFoundError:
        print(f"[错误] 无法执行 UV4.exe: {uv4_path}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[中断] 用户取消操作。")
        sys.exit(130)


def print_result(action_desc: str, returncode: int, log_path: str = None):
    """打印执行结果。

    Args:
        action_desc: 当前执行动作描述。
        returncode: UV4 退出码。
        log_path: 日志文件路径。
    """
    error_levels = {
        0: "成功 - 无错误和警告",
        1: "警告 - 存在警告",
        2: "错误 - 编译失败",
        3: "致命错误",
        11: "无法打开工程文件进行写入",
        12: "数据库中未找到指定设备",
        13: "写入工程文件出错",
        15: "读取导入 XML 文件出错",
    }

    msg = error_levels.get(returncode, f"未知退出码: {returncode}")
    status = "成功" if returncode in (0, 1) else "失败"

    print(f"\n{'='*50}")
    print(f"{action_desc}结果: [{status}] {msg}")
    if log_path and os.path.isfile(log_path):
        print(f"日志文件: {log_path}")
    print(f"{'='*50}")


def interactive_mode(uv4_path: str):
    """交互式运行模式。

    Args:
        uv4_path: UV4.exe 路径。
    """
    print("=" * 50)
    print("  Keil uVision 命令行工具 (交互模式)")
    print("=" * 50)

    # 查找工程文件
    search_dir = input(f"\n搜索目录 (默认当前目录): ").strip() or "."
    project_path = find_project(search_dir)
    print(f"[工程] {project_path}")

    # 查询目标
    target = input("目标名称 (默认使用上次目标, 直接回车跳过): ").strip() or None

    while True:
        print("\n可用操作:")
        print("  1. 编译 (Build)         -b   仅编译修改过的文件")
        print("  2. 重编译 (Rebuild)     -r   重新编译所有文件")
        print("  3. 下载 (Flash)         -f   下载程序到 Flash")
        print("  4. 清理 (Clean)         -c   清理工程目标")
        print("  5. 清理并重编译 (Clean+Rebuild) -cr")
        print("  6. 编译所有目标         -b -z")
        print("  0. 退出")
        print()

        choice = input("请选择操作: ").strip()

        command_map = {
            "1": ("-b", "编译"),
            "2": ("-r", "重编译"),
            "3": ("-f", "下载"),
            "4": ("-c", "清理"),
            "5": ("-cr", "清理并重编译"),
            "6": ("-b", "编译所有目标"),
        }

        if choice == "0":
            print("再见！")
            break

        if choice not in command_map:
            print("[错误] 无效选择。")
            continue

        cmd, desc = command_map[choice]

        # 编译所有目标需要额外 -z 参数
        extra_args = ["-z"] if choice == "6" else []

        log_path = get_log_path(project_path, cmd) if should_use_log(cmd) else None
        full_cmd = [uv4_path, cmd, project_path, "-j0"]
        if target:
            full_cmd.extend(["-t", target])
        full_cmd.extend(extra_args)
        if log_path:
            full_cmd.extend(["-o", log_path])

        print(f"\n[执行] {desc}: {' '.join(full_cmd)}")
        try:
            result = subprocess.run(full_cmd)
            print_result(desc, result.returncode, log_path)
        except KeyboardInterrupt:
            print("\n[中断] 用户取消操作。")

        if input("\n是否继续? (Y/n): ").strip().lower() == "n":
            print("再见！")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Keil uVision 命令行工具 - 编译、下载 Keil 工程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                              交互模式
  %(prog)s -b                           编译工程
  %(prog)s -r                           重编译工程
  %(prog)s -f                           下载到 Flash
  %(prog)s -r -t "Target 1"            指定目标重编译
  %(prog)s -r -p D:/project/demo.uvprojx  指定工程文件

UV4 退出码:
  0  - 无错误或警告
  1  - 仅有警告
  2  - 存在错误
  3  - 致命错误
        """,
    )

    parser.add_argument(
        "-b", "--build",
        action="store_true",
        help="编译工程 (仅编译修改过的文件)",
    )
    parser.add_argument(
        "-r", "--rebuild",
        action="store_true",
        help="重编译工程 (重新编译所有文件)",
    )
    parser.add_argument(
        "-f", "--flash",
        action="store_true",
        help="下载程序到 Flash",
    )
    parser.add_argument(
        "-c", "--clean",
        action="store_true",
        help="清理工程目标",
    )
    parser.add_argument(
        "--clean-rebuild",
        action="store_true",
        help="清理后重编译工程",
    )
    parser.add_argument(
        "-t", "--target",
        type=str,
        default=None,
        help="指定目标名称 (多目标工程时使用)",
    )
    parser.add_argument(
        "-p", "--project",
        type=str,
        default=None,
        help="指定工程文件路径 (.uvprojx)",
    )
    parser.add_argument(
        "-d", "--dir",
        type=str,
        default=".",
        help="工程搜索目录 (默认: 当前目录)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="指定日志输出路径 (默认: 工程目录下自动生成)",
    )

    args = parser.parse_args()

    # 检查 UV4
    uv4_path = check_uv4()
    print(f"[UV4] {uv4_path}")

    # 如果没有任何操作参数，进入交互模式
    has_command = any([args.build, args.rebuild, args.flash, args.clean, args.clean_rebuild])
    if not has_command:
        interactive_mode(uv4_path)
        return

    # 查找工程文件
    if args.project:
        if not os.path.isfile(args.project):
            print(f"[错误] 工程文件不存在: {args.project}")
            sys.exit(1)
        project_path = os.path.abspath(args.project)
    else:
        project_path = find_project(args.dir)

    print(f"[工程] {project_path}")

    # 确定命令
    if args.clean_rebuild:
        cmd = "-cr"
        desc = "清理并重编译"
    elif args.rebuild:
        cmd = "-r"
        desc = "重编译"
    elif args.build:
        cmd = "-b"
        desc = "编译"
    elif args.flash:
        cmd = "-f"
        desc = "下载"
    elif args.clean:
        cmd = "-c"
        desc = "清理"
    else:
        cmd = "-b"
        desc = "编译"

    # 仅编译相关命令默认生成日志；下载/清理仅在显式指定 -o 时输出日志
    log_path = args.output
    if log_path is None and should_use_log(cmd):
        log_path = get_log_path(project_path, cmd)

    # 构建命令 (默认隐藏 GUI)
    full_cmd = [uv4_path, cmd, project_path, "-j0"]
    if args.target:
        full_cmd.extend(["-t", args.target])
    if log_path:
        full_cmd.extend(["-o", log_path])

    print(f"[执行] {desc}: {' '.join(full_cmd)}")
    returncode = subprocess.run(full_cmd).returncode
    print_result(desc, returncode, log_path)

    # 退出码 0 和 1 都视为成功
    sys.exit(0 if returncode in (0, 1) else returncode)


if __name__ == "__main__":
    main()

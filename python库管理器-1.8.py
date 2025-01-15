#禁止倒卖
#禁止倒卖
#禁止倒卖
#重要的事情说三遍！
import subprocess
import sys
import re
import json
import requests
from socket import gethostbyname, gaierror

print("作者: ikdxhz")
print("程序版本: 1.8")

pip_source = []

PIP_SOURCES = {
    "aliyun": "https://mirrors.aliyun.com/pypi/simple/",
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "douban": "https://pypi.douban.com/simple/",
    "ustc": "https://pypi.mirrors.ustc.edu.cn/simple/",
    "default": "https://pypi.org/simple/"
}

def check_python_version():
    major, minor, micro, releaselevel, serial = sys.version_info
    if major < 3 or (major == 3 and minor < 6) or (major == 3 and minor == 6 and micro < 1):
        print(f"当前Python版本为 {sys.version}, 脚本需要Python 3.6.1或更高版本.")
        sys.exit(1)
    else:
        print(f"当前Python版本为 {sys.version}, 符合要求.")

def check_pip_installed():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', '--version'])
        return True
    except subprocess.CalledProcessError:
        print("未找到pip，请确保pip已安装并添加到PATH中.")
        return False

def set_pip_source(source):
    global pip_source
    if source in PIP_SOURCES:
        pip_source = ["-i", PIP_SOURCES[source]]
        print(f"已切换到 {source} 源.")
    else:
        print("无效的源选择，请输入 aliyun, tsinghua, douban, ustc 或 default.")
        pip_source = []  # 清空 pip_source

def get_current_source():
    for key, value in PIP_SOURCES.items():
        if pip_source == ["-i", value]:
            return key
    return "default"

def get_pip_command():
    commands_to_try = ['pip', 'pip3']
    for cmd in commands_to_try:
        try:
            subprocess.check_call([cmd, '--version'])
            return [cmd]
        except FileNotFoundError:
            continue
    
    retries = 3
    while retries > 0:
        manual_input = input("未找到pip或pip3，请手动输入pip命令 (例如 'pip' 或 'pip3')，或输入 'exit' 退出: ").strip()
        if manual_input.lower() == 'exit':
            print("退出程序.")
            sys.exit(1)
        try:
            subprocess.check_call([manual_input, '--version'])
            return [manual_input]
        except FileNotFoundError:
            retries -= 1
            print(f"手动输入的pip命令无效，请重新输入 ({retries} 次尝试剩余).")
    
    print("多次尝试无效，请确保pip已安装并添加到PATH中。你可以通过以下命令安装pip:")
    print("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py")
    sys.exit(1)

def run_pip_command(pip_command, command, args=[], include_source=True):
    full_command = pip_command + command + args
    if include_source:
        full_command += pip_source
    try:
        result = subprocess.run(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n命令 {' '.join(full_command)} 失败:")
        print(e.stderr.strip())
        return False
    except FileNotFoundError:
        print(f"\n命令 {' '.join(full_command)} 找不到文件.")
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        return False

def install(pip_command, package):
    if run_pip_command(pip_command, ['install'], [package]):
        print(f"\n{package} 安装成功.")
    else:
        print(f"\n{package} 安装失败.")
        suggest_similar_packages(package)

def update_single(pip_command, package):
    if run_pip_command(pip_command, ['install', '--upgrade'], [package]):
        print(f"\n{package} 更新成功.")
    else:
        print(f"\n{package} 更新失败.")
        suggest_similar_packages(package)

def update_all(pip_command):
    try:
        result = subprocess.run(pip_command + ['list', '--outdated'] + pip_source, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        lines = result.stdout.splitlines()[2:]  # Skip header lines
        outdated_packages = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                package_name = parts[0]
                current_version = parts[1]
                latest_version = parts[2]
                outdated_packages.append((package_name, current_version, latest_version))
        
        if not outdated_packages:
            print("\n没有可更新的库.")
            list_all_packages(pip_command)
            return
        
        for package_name, current_version, latest_version in outdated_packages:
            if run_pip_command(pip_command, ['install', '--upgrade'], [package_name]):
                print(f"{package_name} 更新成功. 新版本: {latest_version}.")
            else:
                print(f"{package_name} 更新失败.")
    except subprocess.CalledProcessError as e:
        print(f"\n获取过时库列表失败: {e.stderr.strip()}")
    except Exception as e:
        print(f"发生未知错误: {e}")

def uninstall(pip_command, package):
    def check_dependencies(packages, checked=set()):
        dependencies = []
        for pkg in packages:
            if pkg in checked:
                continue
            checked.add(pkg)
            try:
                result = subprocess.run(pip_command + ['show', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
                deps = re.findall(r'Requires:\s*(.*)', result.stdout)
                if deps:
                    dep_list = [dep.strip() for dep in deps[0].split(',')]
                    dependencies.extend(dep_list)
                    additional_deps = check_dependencies(dep_list, checked)
                    dependencies.extend(additional_deps)
            except subprocess.CalledProcessError:
                pass
        return dependencies

    all_packages = []
    try:
        result = subprocess.run(pip_command + ['list', '--format=freeze'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        installed_packages = result.stdout.splitlines()
        installed_dict = {pkg.split('==')[0]: pkg for pkg in installed_packages}
        all_packages = list(installed_dict.keys())
    except subprocess.CalledProcessError as e:
        print(f"\n列出已安装库失败: {e.stderr.strip()}")
        return

    dependencies = check_dependencies([package])
    other_packages = [pkg for pkg in all_packages if pkg != package and any(dep in dependencies for dep in check_dependencies([pkg]))]

    if other_packages:
        print(f"\n警告: {package} 被以下包依赖: {', '.join(other_packages)}")
        confirm = input("确定要卸载吗? (y/n): ").strip().lower()
        if confirm != 'y':
            print("取消卸载.")
            return
    
    if run_pip_command(pip_command, ['uninstall', '-y'], [package], include_source=False):
        print(f"\n{package} 卸载成功.")
    else:
        print(f"\n{package} 卸载失败.")
        print("请检查以下几点:")
        print("1. 确保你有足够的权限来卸载该包.")
        print("2. 检查是否有其他包依赖于该包.")
        print("3. 尝试手动卸载该包，使用命令: pip uninstall -y {package}")

def list_all_packages(pip_command):
    try:
        result = subprocess.run(pip_command + ['list', '--format=columns'] + pip_source, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("\n已安装的库:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"\n列出已安装库失败: {e.stderr.strip()}")
    except Exception as e:
        print(f"发生未知错误: {e}")

def show_package_details(pip_command, package):
    try:
        result = subprocess.run(pip_command + ['show', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("\n包详细信息:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"\n获取包详细信息失败: {e.stderr.strip()}")
    except Exception as e:
        print(f"发生未知错误: {e}")

def suggest_similar_packages(package_name):
    print("\npip search 命令已被弃用，无法建议相似的包名.")

def get_random_hitokoto():
    url = "https://api.52vmy.cn/api/wl/yan/yiyan"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("code") == 200 and "data" in data and "hitokoto" in data["data"]:
            hitokoto = data["data"]["hitokoto"]
            print(hitokoto)
        else:
            print("\n获取随机一言失败，数据结构不正确.")
    except requests.HTTPError as http_err:
        print(f"\nHTTP 错误: {http_err}")
    except requests.ConnectionError as conn_err:
        print(f"\n连接错误: {conn_err}")
    except requests.Timeout as timeout_err:
        print(f"\n请求超时: {timeout_err}")
    except requests.RequestException as req_err:
        print(f"\n请求失败: {req_err}")
    except json.JSONDecodeError as json_err:
        print(f"\nJSON解码错误: {json_err}")
    except Exception as e:
        print(f"发生未知错误: {e}")

def fetch_announcement():
    url = "https://gg.ikdxhz.us.kg/"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        announcement = response.text.strip()
        if announcement:
            print("\n公告内容:")
            print(announcement)
        else:
            print("\n获取公告内容失败，数据为空.")
    except requests.HTTPError as http_err:
        print(f"\nHTTP 错误: {http_err}")
    except requests.ConnectionError as conn_err:
        print(f"\n连接错误: {conn_err}")
    except requests.Timeout as timeout_err:
        print(f"\n请求超时: {timeout_err}")
    except requests.RequestException as req_err:
        print(f"\n请求失败: {req_err}")
    except json.JSONDecodeError as json_err:
        print(f"\nJSON解码错误: {json_err}")
    except Exception as e:
        print(f"发生未知错误: {e}")

def check_network_connection():
    try:
        host = "360.com"
        gethostbyname(host)
        return True
    except gaierror:
        print("无法连接到互联网，请检查您的网络连接.")
        return False

def get_valid_package_name(prompt):
    while True:
        package_name = input(prompt).strip()
        if package_name:
            return package_name
        else:
            print("请输入有效的库名.")

def main():
    current_source = get_current_source()
    print(f"\n当前使用的pip源: {current_source}\n")
    
    if check_network_connection():
        get_random_hitokoto()
    
    print("\nikdxhz出品，必属精品")
    
    while True:
        print("\n请选择操作:")
        print("1. 切换pip源")
        print("2. 安装库")
        print("3. 更新单个库")
        print("4. 更新所有库")
        print("5. 卸载库")
        print("6. 列出所有库")
        print("7. 显示库详情")
        print("8. 获取公告")
        print("9. 退出")
        
        choice = input("请输入选项 (1/2/3/4/5/6/7/8/9): ").strip()
        
        if choice == "9":
            print("退出程序.")
            break
        
        if choice == "1":
            print("\n请选择pip源:")
            print("1. 阿里云")
            print("2. 清华大学")
            print("3. 豆瓣")
            print("4. 中国科学技术大学")
            print("5. 默认源")
            
            source_choice = input("请输入源编号 (1/2/3/4/5): ").strip()
            
            if source_choice == "1":
                set_pip_source("aliyun")
            elif source_choice == "2":
                set_pip_source("tsinghua")
            elif source_choice == "3":
                set_pip_source("douban")
            elif source_choice == "4":
                set_pip_source("ustc")
            elif source_choice == "5":
                set_pip_source("default")
            else:
                print("无效的选择，请输入 1, 2, 3, 4 或 5.")
        
        elif choice in ["2", "3", "5"]:
            package_name = get_valid_package_name("请输入库名: ")
            
            if choice == "2":
                install(pip_command, package_name)
            elif choice == "3":
                update_single(pip_command, package_name)
            elif choice == "5":
                uninstall(pip_command, package_name)
        
        elif choice == "4":
            update_all(pip_command)
        
        elif choice == "6":
            list_all_packages(pip_command)
        
        elif choice == "7":
            package_name = get_valid_package_name("请输入库名: ")
            show_package_details(pip_command, package_name)
        
        elif choice == "8":
            fetch_announcement()
        
        else:
            print("无效的选择，请输入 1, 2, 3, 4, 5, 6, 7, 8 或 9.")
        
        input("\n按回车键返回主菜单...")

if __name__ == "__main__":
    check_python_version()
    try:
        import requests
    except ImportError:
        print("缺少requests库，请先安装requests库: pip install requests")
        sys.exit(1)
    
    pip_command = get_pip_command()
    main()




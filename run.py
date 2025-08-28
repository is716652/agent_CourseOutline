import os
import sys
import socket
import configparser
import threading
import time
import webbrowser
from app import create_app

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包"""
    try:
        # PyInstaller 创建的临时文件夹路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    config_path = get_resource_path('config.ini')
    
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(config_path):
        create_default_config(config_path)
    
    config.read(config_path, encoding='utf-8')
    return config

def create_default_config(config_path):
    """创建默认配置文件"""
    config = configparser.ConfigParser()
    
    config['server'] = {
        'host': '127.0.0.1',
        'port': '5000',
        'debug': 'false',
        'backup_ports': '5001,5002,5003,5004,5005'
    }
    
    config['app'] = {
        'app_name': '教学大纲生成系统',
        'version': '1.0.0',
        'author': 'AI Assistant',
        'auto_open_browser': 'true',
        'default_page': '/teaching-outline'
    }
    
    config['paths'] = {
        'templates_dir': 'templates',
        'output_dir': 'output',
        'uploads_dir': 'uploads'
    }
    
    config['ai'] = {
        'default_positioning_length': '100',
        'default_objectives_length': '80',
        'default_module_content_length': '60',
        'default_temperature': '0.9'
    }
    
    config['logging'] = {
        'log_level': 'INFO',
        'log_file': 'app.log',
        'max_log_size': '10MB',
        'backup_count': '5'
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        config.write(f)
    
    print(f"✅ 已创建默认配置文件: {config_path}")

def check_port_available(host, port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def find_available_port(host, preferred_port, backup_ports):
    """找到可用的端口"""
    # 首先尝试首选端口
    if check_port_available(host, preferred_port):
        return preferred_port
    
    # 尝试备用端口
    for port in backup_ports:
        if check_port_available(host, port):
            print(f"⚠️  端口 {preferred_port} 被占用，使用备用端口 {port}")
            return port
    
    # 如果所有预设端口都被占用，尝试自动找一个
    for port in range(5006, 5020):
        if check_port_available(host, port):
            print(f"⚠️  预设端口都被占用，使用自动分配端口 {port}")
            return port
    
    raise Exception("无法找到可用端口")

def open_browser(host, port, default_page, delay=1.5):
    """延迟打开浏览器"""
    def _open():
        time.sleep(delay)
        url = f"http://{host}:{port}{default_page}"
        try:
            webbrowser.open(url)
            print(f"🌐 浏览器已打开: {url}")
        except Exception as e:
            print(f"⚠️  无法自动打开浏览器: {e}")
            print(f"请手动访问: {url}")
    
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()

def create_output_directories():
    """创建必要的输出目录"""
    directories = ['output', 'uploads', 'logs']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 已创建目录: {directory}")

app = create_app()

if __name__ == '__main__':
    try:
        # 加载配置
        print("🔧 加载配置文件...")
        config = load_config()
        
        # 创建必要目录
        create_output_directories()
        
        # 获取配置参数
        host = config.get('server', 'host', fallback='127.0.0.1')
        preferred_port = config.getint('server', 'port', fallback=5000)
        debug = config.getboolean('server', 'debug', fallback=False)
        auto_open_browser = config.getboolean('app', 'auto_open_browser', fallback=True)
        default_page = config.get('app', 'default_page', fallback='/teaching-outline')
        app_name = config.get('app', 'app_name', fallback='教学大纲生成系统')
        
        # 解析备用端口
        backup_ports_str = config.get('server', 'backup_ports', fallback='5001,5002,5003,5004,5005')
        backup_ports = [int(p.strip()) for p in backup_ports_str.split(',') if p.strip().isdigit()]
        
        # 找到可用端口
        print(f"🔍 检查端口可用性...")
        port = find_available_port(host, preferred_port, backup_ports)
        
        print("\n" + "="*50)
        print(f"🚀 {app_name} 启动中...")
        print("="*50)
        print(f"🌐 访问地址: http://{host}:{port}{default_page}")
        print(f"📊 运行模式: {'开发模式' if debug else '生产模式'}")
        print(f"🛑 停止服务: 按 Ctrl+C")
        print("="*50)
        print()
        
        # 自动打开浏览器
        if auto_open_browser:
            open_browser(host, port, default_page)
        
        # 启动Flask应用
        app.run(host=host, port=port, debug=debug, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭服务器...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")
        sys.exit(1)
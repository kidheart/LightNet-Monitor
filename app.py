from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Packet, Alert
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import subprocess
import atexit
import threading
from collections import deque

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-dev-key')

# 使用绝对路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'traffic_monitor.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Tshark 配置，优先从环境变量读取
TSHARK_PATH = os.environ.get('TSHARK_PATH', r"C:\Program Files\Wireshark\tshark.exe")
TSHARK_IFACE = os.environ.get('TSHARK_INTERFACE', "4")  # WLAN接口编号
TRAFFIC_THRESHOLD = 10 * 1024 * 1024  # 10MB/分钟

def tshark_realtime_import():
    cmd = [
        TSHARK_PATH, "-i", TSHARK_IFACE, "-l", "-T", "fields",
        "-e", "frame.time_epoch", "-e", "ip.src", "-e", "ip.dst",
        "-e", "_ws.col.Protocol", "-e", "frame.len",
        "-e", "tcp.srcport", "-e", "tcp.dstport",
        "-e", "udp.srcport", "-e", "udp.dstport",
        "-e", "tcp.flags", "-e", "ip.ttl", "-e", "eth.src", "-e", "eth.dst"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
    with app.app_context():
        current_minute = None
        current_minute_bytes = 0
        while True:
            for line in proc.stdout:
                fields = line.strip().split('\t')
                if len(fields) < 5 or not fields[1] or not fields[2]:
                    continue
                try:
                    timestamp = datetime.fromtimestamp(float(fields[0]))
                    src_ip = fields[1]
                    dst_ip = fields[2]
                    proto = fields[3]
                    length = int(fields[4])
                    src_port = int(fields[5]) if len(fields) > 5 and fields[5] else (int(fields[7]) if len(fields) > 7 and fields[7] else None)
                    dst_port = int(fields[6]) if len(fields) > 6 and fields[6] else (int(fields[8]) if len(fields) > 8 and fields[8] else None)
                    flags = fields[9] if len(fields) > 9 else None
                    ttl = int(fields[10]) if len(fields) > 10 and fields[10] else None
                    src_mac = fields[11] if len(fields) > 11 else None
                    dst_mac = fields[12] if len(fields) > 12 else None
                    # --- 自动流量阈值告警 ---
                    now_minute = timestamp.replace(second=0, microsecond=0)
                    if current_minute is None:
                        current_minute = now_minute
                    if now_minute != current_minute:
                        if current_minute_bytes > TRAFFIC_THRESHOLD:
                            alert = Alert(
                                alert_type='high_traffic',
                                description=f'一分钟内流量达到{current_minute_bytes}字节',
                                source_ip='*',
                                status='active',
                                timestamp=datetime.now(),
                                severity='warning',
                                category='traffic'
                            )
                            db.session.add(alert)
                            db.session.commit()
                        current_minute = now_minute
                        current_minute_bytes = 0
                    current_minute_bytes += length
                    # --- end ---
                    new_packet = Packet(
                        src_ip=src_ip,
                        dst_ip=dst_ip,
                        protocol=proto,
                        length=length,
                        timestamp=timestamp,
                        src_port=src_port,
                        dst_port=dst_port,
                        flags=flags,
                        ttl=ttl,
                        src_mac=src_mac,
                        dst_mac=dst_mac
                    )
                    db.session.add(new_packet)
                    db.session.commit()
                except Exception as e:
                    print(f"[tshark导入异常] {e}")
    proc.terminate()
    proc.wait()

def start_tshark_thread():
    t = threading.Thread(target=tshark_realtime_import, daemon=True)
    t.start()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('需要管理员权限', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    """Initialize the database"""
    # 确保instance目录存在
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    # 如果数据库文件存在，先删除
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"Error removing old database: {e}")
    
    # 创建新的数据库
    try:
        db.create_all()
        
        # 创建管理员用户
        admin = User.query.filter_by(name='admin').first()
        if not admin:
            admin = User(
                name='admin',
                role='admin',
                password=generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user with password: admin123")
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

@app.route('/')
@login_required
def index():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(5).all()
    packets = Packet.query.order_by(Packet.timestamp.desc()).limit(5).all()
    return render_template('index.html', alerts=alerts, packets=packets)

@app.route('/traffic')
@login_required
def traffic():
    packets = Packet.query.order_by(Packet.timestamp.desc()).limit(1000).all()
    return render_template('traffic.html', packets=packets)

@app.route('/alerts')
@login_required
def alerts():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(100).all()
    return render_template('alerts.html', alerts=alerts)

@app.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.status = 'resolved'
    alert.resolved_at = datetime.now()
    db.session.commit()
    flash('告警已标记为已解决', 'success')
    return redirect(url_for('alerts'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            return redirect(url_for('index'))
        flash('用户名或密码错误', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).limit(100).all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    name = request.form['name']
    password = request.form['password']
    
    if User.query.filter_by(name=name).first():
        flash('用户名已存在', 'danger')
        return redirect(url_for('users'))
    
    user = User(
        name=name,
        password=generate_password_hash(password),
        role='user'
    )
    db.session.add(user)
    db.session.commit()
    flash('用户添加成功', 'success')
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    password = request.form['password']
    
    user.password = generate_password_hash(password)
    db.session.commit()
    flash('密码重置成功', 'success')
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.name == 'admin':
        flash('不能删除管理员账户', 'danger')
        return redirect(url_for('users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功', 'success')
    return redirect(url_for('users'))

@app.route('/api/traffic_stats')
def traffic_stats():
    total_packets = Packet.query.count()
    total_bytes = db.session.query(db.func.sum(Packet.length)).scalar() or 0
    since = datetime.now() - timedelta(minutes=5)
    active_connections = db.session.query(Packet.src_ip, Packet.dst_ip).filter(Packet.timestamp > since).distinct().count()
    alert_count = Alert.query.count()
    return jsonify({
        'total_packets': total_packets,
        'total_bytes': total_bytes,
        'active_connections': active_connections,
        'alert_count': alert_count
    })

@app.route('/api/traffic_trend')
def traffic_trend():
    now = datetime.now()
    points = []
    for i in range(30, 0, -1):
        start = now - timedelta(minutes=i)
        end = now - timedelta(minutes=i-1)
        total = db.session.query(db.func.sum(Packet.length)).filter(Packet.timestamp >= start, Packet.timestamp < end).scalar() or 0
        points.append({
            'time': start.strftime('%H:%M'),
            'bytes': total
        })
    print(points)  # 调试输出
    return jsonify(points)

if __name__ == '__main__':
    with app.app_context():
        init_db()  # 先初始化数据库和表
        start_tshark_thread()  # 再启动 tshark 导入线程
    app.run(host='0.0.0.0', port=5000, debug=True)
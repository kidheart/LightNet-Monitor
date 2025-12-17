# 网络流量监控系统

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17959626.svg)](https://doi.org/10.5281/zenodo.17959626)

本系统是一个基于 Flask 和 SQLite 的网络流量监控与告警平台，支持实时数据包捕获、协议分析、异常检测、可视化统计和多用户管理。适用于校园、企业、实验室等场景的网络安全与运维监控。

---

## 功能特性

- **实时流量监控**
  - 支持 TCP/UDP/ICMP 等协议数据包捕获与解析
  - 记录源/目标 IP、端口、协议、包长、Flags、TTL、MAC 地址等详细信息
  - 实时流量趋势、活跃连接统计
  - 支持大流量分页与高效查询

- **智能告警管理**
  - 支持高流量、异常端口等多种告警类型
  - 告警记录包含类型、描述、源/目标 IP、端口、协议、级别、分类、状态等
  - 支持告警状态流转（活动/已解决）、历史追溯

- **数据可视化**
  - 仪表盘展示总包数、总流量、活跃连接、告警数量等核心指标
  - 流量趋势折线图、协议分布统计
  - 响应式前端，支持多终端访问

- **多用户与权限管理**
  - 支持管理员与普通用户角色
  - 用户注册、登录、密码加密存储、重置与删除
  - 管理员可管理所有用户

---

## 技术栈

- **后端框架**：Flask 2.0.1
- **数据库**：SQLite
- **ORM**：Flask-SQLAlchemy 2.5.1
- **前端**：Bootstrap 5.1.3、Chart.js、Bootstrap Icons
- **依赖管理**：Werkzeug
- **数据包采集**：tshark（Wireshark 命令行工具）

---

## 系统配置与依赖

- **操作系统**：Windows 10/11、Linux、macOS（推荐 Windows 10/11）
- **Python 版本**：3.7 及以上
- **依赖包**（见 requirements.txt）：
  ```
  Flask==2.0.1
  Flask-SQLAlchemy==2.5.1
  Werkzeug==2.0.1
  python-dateutil==2.8.2
  pytz==2021.1
  scapy==2.5.0
  psutil==5.9.0
  python-dotenv==0.19.0
  ```
- **第三方工具**：Wireshark（需安装并配置好 `tshark` 命令行工具）

---

## 安装与启动

1. **克隆项目**
   ```bash
   git clone [项目地址]
   cd [项目目录]
   ```

2. **创建虚拟环境并激活**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **安装 Wireshark 并确保 `tshark` 可用**
   - 下载地址：https://www.wireshark.org/download.html
   - 安装后确保 `C:\Program Files\Wireshark\` 在系统 PATH 中，或修改 `app.py` 里的 `TSHARK_PATH`。

5. **首次运行自动初始化数据库和管理员账号**
   ```bash
   python app.py
   ```
   > Windows 需管理员权限，Linux/Mac 需 root 权限运行。

6. **访问系统**
   - 浏览器访问 [http://localhost:5000](http://localhost:5000)

---

## 系统登录用户名及密码

- **默认管理员账号**：
  - 用户名：`admin`
  - 密码：`admin123`
- **安全建议**：首次登录后请及时修改管理员密码！

---

## 目录结构

```
├── app.py                # 主应用入口
├── models.py             # 数据模型定义
├── requirements.txt      # 依赖列表
├── capture.pcap          # 示例抓包文件
├── live_capture.pcap     # 实时抓包文件
├── instance/             # 数据库文件目录
│   └── traffic_monitor.db
├── static/               # 静态资源
│   └── js/
│       └── main.js       # 前端交互与可视化脚本
├── templates/            # 前端页面模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── traffic.html
│   ├── alerts.html
│   └── users.html
└── venv/                 # Python 虚拟环境
```

---

## 主要数据表结构

- **User（用户表）**
  | 字段         | 类型         | 说明         |
  | ------------ | ------------ | ------------ |
  | id           | Integer      | 主键         |
  | name         | String(80)   | 用户名，唯一 |
  | role         | String(20)   | 角色（admin/user）|
  | password     | String(120)  | 加密密码     |
  | created_at   | DateTime     | 创建时间     |
  | last_login   | DateTime     | 最后登录时间 |

- **Packet（数据包详情表）**
  | 字段         | 类型         | 说明         |
  | ------------ | ------------ | ------------ |
  | id           | Integer      | 主键         |
  | timestamp    | DateTime     | 捕获时间     |
  | src_ip       | String(45)   | 源 IP        |
  | dst_ip       | String(45)   | 目标 IP      |
  | protocol     | String(20)   | 协议         |
  | length       | Integer      | 包长度       |
  | src_port     | Integer      | 源端口       |
  | dst_port     | Integer      | 目标端口     |
  | flags        | String(20)   | TCP Flags    |
  | ttl          | Integer      | TTL          |
  | src_mac      | String(32)   | 源 MAC       |
  | dst_mac      | String(32)   | 目标 MAC     |

- **Alert（告警表）**
  | 字段         | 类型         | 说明         |
  | ------------ | ------------ | ------------ |
  | id           | Integer      | 主键         |
  | timestamp    | DateTime     | 告警时间     |
  | alert_type   | String(50)   | 告警类型     |
  | description  | Text         | 描述         |
  | source_ip    | String(45)   | 源 IP        |
  | status       | String(20)   | 状态（active/resolved）|
  | resolved_at  | DateTime     | 解决时间     |
  | dst_ip       | String(45)   | 目标 IP      |
  | src_port     | Integer      | 源端口       |
  | dst_port     | Integer      | 目标端口     |
  | protocol     | String(20)   | 协议         |
  | severity     | String(20)   | 严重级别     |
  | category     | String(50)   | 分类         |

- **NetworkInterface（网络接口表）** 和 **TrafficStats（流量统计表）**
  - 详见 `models.py`，如需接口流量统计和多网卡监控可扩展使用。

---

## 常用操作说明

- **仪表盘**：查看实时统计、最新告警、流量趋势
- **流量监控**：分页浏览详细数据包，支持协议/端口等多维度分析
- **告警管理**：查看、处理、追溯历史告警
- **用户管理**：添加、重置、删除用户（仅管理员）

---

## 注意事项

1. 生产环境请务必修改默认管理员密码
2. 建议定期备份数据库文件（`instance/traffic_monitor.db`）
3. 监控大流量时注意系统资源占用
4. Windows 需管理员权限，Linux/Mac 需 root 权限运行
5. 建议部署于专用服务器

---

## 常见问题

- **无法捕获数据包**：请检查管理员/root 权限、网络接口编号、tshark 路径或防火墙设置
- **性能瓶颈**：建议分页查询、定期清理历史数据、增加系统资源
- **数据库异常**：可删除数据库文件后重建（注意数据丢失风险）

---

## 贡献与许可

欢迎提交 Issue 和 Pull Request 参与改进。  
本项目采用 MIT License 开源。

---

如需更详细的开发文档或二次开发支持，请联系项目维护者。

---

如需英文版或更详细的开发者文档，请联系作者或提交 Issue。

---

**建议：将本 README.md 作为项目说明文件，便于后续维护和用户查阅。**

---

如需进一步细化或有特殊需求，请告知！ 
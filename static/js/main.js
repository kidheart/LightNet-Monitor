// 全局变量
let trafficChart = null;
let protocolChart = null;
let updateInterval = null;

// 初始化函数
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadAllData();
    setupEventListeners();
    
    // 每5秒更新一次数据
    updateInterval = setInterval(loadAllData, 5000);
});

// 初始化图表
function initializeCharts() {
    // 流量图表
    const trafficCtx = document.getElementById('trafficChart').getContext('2d');
    trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Incoming Traffic (bytes)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }, {
                label: 'Outgoing Traffic (bytes)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // 协议分布图表
    const protocolCtx = document.getElementById('protocolChart').getContext('2d');
    protocolChart = new Chart(protocolCtx, {
        type: 'doughnut',
        data: {
            labels: ['TCP', 'UDP', 'ICMP', 'Other'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)'
                ]
            }]
        },
        options: {
            responsive: true
        }
    });
}

// 加载所有数据
function loadAllData() {
    loadTrafficData();
    loadInterfaces();
    loadAlerts();
    loadPackets();
    loadUsers();
}

// 加载流量数据
function loadTrafficData() {
    fetch('/api/traffic')
        .then(response => response.json())
        .then(data => {
            updateTrafficChart(data);
            updateProtocolChart(data);
        })
        .catch(error => console.error('Error loading traffic data:', error));
}

// 更新流量图表
function updateTrafficChart(data) {
    const timestamps = data.map(item => new Date(item.timestamp).toLocaleTimeString());
    const incoming = data.map(item => item.incoming_bytes);
    const outgoing = data.map(item => item.outgoing_bytes);

    trafficChart.data.labels = timestamps;
    trafficChart.data.datasets[0].data = incoming;
    trafficChart.data.datasets[1].data = outgoing;
    trafficChart.update();
}

// 更新协议分布图表
function updateProtocolChart(data) {
    const protocolCounts = {
        tcp: 0,
        udp: 0,
        icmp: 0,
        other: 0
    };

    data.forEach(item => {
        switch(item.protocol) {
            case 'TCP': protocolCounts.tcp++; break;
            case 'UDP': protocolCounts.udp++; break;
            case 'ICMP': protocolCounts.icmp++; break;
            default: protocolCounts.other++; break;
        }
    });

    protocolChart.data.datasets[0].data = [
        protocolCounts.tcp,
        protocolCounts.udp,
        protocolCounts.icmp,
        protocolCounts.other
    ];
    protocolChart.update();
}

// 加载网络接口数据
function loadInterfaces() {
    fetch('/api/interfaces')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('interfacesTable');
            tableBody.innerHTML = data.map(interface => `
                <tr>
                    <td>${interface.name}</td>
                    <td>${interface.ip_address}</td>
                    <td>${interface.mac_address}</td>
                    <td>${interface.status}</td>
                    <td>${interface.is_monitored ? 'Yes' : 'No'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="toggleMonitoring(${interface.id})">
                            ${interface.is_monitored ? 'Stop' : 'Start'} Monitoring
                        </button>
                    </td>
                </tr>
            `).join('');
        })
        .catch(error => console.error('Error loading interfaces:', error));
}

// 加载告警数据
function loadAlerts() {
    fetch('/api/alerts')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('alertsTable');
            tableBody.innerHTML = data.map(alert => `
                <tr>
                    <td>${new Date(alert.timestamp).toLocaleString()}</td>
                    <td>${alert.alert_type}</td>
                    <td>${alert.severity}</td>
                    <td>${alert.description}</td>
                    <td>${alert.is_resolved ? 'Resolved' : 'Active'}</td>
                    <td>
                        ${!alert.is_resolved ? `
                            <button class="btn btn-sm btn-success" onclick="resolveAlert(${alert.id})">
                                Resolve
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `).join('');
        })
        .catch(error => console.error('Error loading alerts:', error));
}

// 加载数据包数据
function loadPackets() {
    fetch('/api/packets')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('packetsTable');
            tableBody.innerHTML = data.map(packet => `
                <tr>
                    <td>${new Date(packet.timestamp).toLocaleString()}</td>
                    <td>${packet.source_ip}:${packet.source_port}</td>
                    <td>${packet.destination_ip}:${packet.destination_port}</td>
                    <td>${packet.protocol}</td>
                    <td>${packet.length}</td>
                    <td>${packet.flags}</td>
                </tr>
            `).join('');
        })
        .catch(error => console.error('Error loading packets:', error));
}

// 加载用户数据
function loadUsers() {
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('usersTable');
            tableBody.innerHTML = data.map(user => `
                <tr>
                    <td>${user.name}</td>
                    <td>${user.role}</td>
                    <td>${new Date(user.created_at).toLocaleString()}</td>
                    <td>${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                            Delete
                        </button>
                    </td>
                </tr>
            `).join('');
        })
        .catch(error => console.error('Error loading users:', error));
}

// 切换接口监控状态
function toggleMonitoring(interfaceId) {
    fetch(`/api/interfaces/${interfaceId}/toggle`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(() => loadInterfaces())
    .catch(error => console.error('Error toggling interface monitoring:', error));
}

// 解决告警
function resolveAlert(alertId) {
    fetch(`/api/alerts/${alertId}/resolve`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(() => loadAlerts())
    .catch(error => console.error('Error resolving alert:', error));
}

// 删除用户
function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user?')) {
        fetch(`/api/users/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(() => loadUsers())
        .catch(error => console.error('Error deleting user:', error));
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 标签切换时重新加载数据
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            const tabId = this.getAttribute('href').substring(1);
            if (tabId === 'traffic') {
                loadTrafficData();
            } else if (tabId === 'interfaces') {
                loadInterfaces();
            } else if (tabId === 'alerts') {
                loadAlerts();
            } else if (tabId === 'packets') {
                loadPackets();
            } else if (tabId === 'users') {
                loadUsers();
            }
        });
    });
}

// 清理函数
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});

// 通用工具函数
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 时间格式化函数
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

// 处理表单提交
document.addEventListener('DOMContentLoaded', function() {
    // 处理所有表单提交
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
            }
        });
    });
    
    // 自动关闭警告消息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
}); 
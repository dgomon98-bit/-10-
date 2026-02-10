from flask import Flask, jsonify, render_template_string
import sqlite3
import os
import json

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect('parking_app.db')
    cursor = conn.cursor()
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parkings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            free_spots INTEGER DEFAULT 0,
            total_spots INTEGER DEFAULT 100,
            address TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    
    cursor.execute("SELECT COUNT(*) FROM parkings")
    count = cursor.fetchone()[0]
    
    if count == 0:
        
        moscow_parkings = [
            ('Кремля', 55.7520, 37.6175, 8, 150, 'Красная площадь'),
            ('ТЦ Афимолл Сити', 55.7490, 37.5398, 45, 200, 'Пресненская наб., 2'),
            ('Парк Горького', 55.7290, 37.6015, 85, 120, 'ул. Крымский Вал, 9'),
            ('ВДНХ ', 55.8252, 37.6381, 5, 80, 'пр. Мира, 119'),
            ('Москва-Сити', 55.7497, 37.5393, 12, 150, 'Пресненская наб., 8'),
            ('ТЦ Европейский', 55.7466, 37.5165, 35, 100, 'пл. Киевского Вокзала'),
            ('ТЦ Авиапарк', 55.8030, 37.5331, 60, 200, 'Ходынский бульвар, 4'),
            ('ЦУМ', 55.7606, 37.6194, 15, 50, 'ул. Петровка, 2'),
            ('ГУМ', 55.7547, 37.6216, 2, 30, 'Красная площадь, 3'),
            ('ТЦ Охотный ряд', 55.7578, 37.6175, 25, 70, 'Манежная площадь, 1'),
            ('Парк Зарядье', 55.7513, 37.6278, 40, 80, 'ул. Варварка'),
            ('Лужники', 55.7159, 37.5538, 70, 150, 'ул. Лужники, 24'),
            ('Воробьевы горы', 55.7108, 37.5532, 50, 80, 'Воробьевы горы'),
            ('Крокус Сити', 55.8258, 37.3903, 90, 300, '66 км МКАД'),
            ('Мега Химки', 55.8972, 37.4244, 120, 500, 'Ленинградское ш., 1'),
        ]
        
        cursor.executemany('''
            INSERT INTO parkings (name, lat, lon, free_spots, total_spots, address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', moscow_parkings)
        print(f"Добавлено {len(moscow_parkings)} тестовых парковок")
    
    conn.commit()
    conn.close()


init_db()


HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Карта парковок Москвы</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            animation: slideDown 0.5s ease;
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .header h1 i {
            color: #ff4757;
        }
        
        .auth-buttons {
            display: flex;
            gap: 15px;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #ff4757, #ff3838);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 15px rgba(255, 71, 87, 0.4);
        }
        
        .btn-secondary {
            background: transparent;
            color: #333;
            border: 2px solid #ddd;
        }
        
        .btn-secondary:hover {
            border-color: #ff4757;
            color: #ff4757;
        }
        
        #map {
            width: 100%;
            height: 70vh;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            overflow: hidden;
            animation: fadeIn 0.8s ease;
            background: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            color: #666;
            font-size: 18px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
        }
        
        .legend {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-top: 25px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 20px;
            border-radius: 10px;
            background: rgba(0,0,0,0.02);
            transition: transform 0.3s ease;
        }
        
        .legend-item:hover {
            transform: translateX(5px);
            background: rgba(0,0,0,0.05);
        }
        
        .status-dot {
            width: 20px;
            height: 20px;
            border-radius: 50%;
        }
        
        .status-green {
            background: linear-gradient(45deg, #00b894, #00a085);
            box-shadow: 0 0 10px rgba(0, 184, 148, 0.3);
        }
        
        .status-yellow {
            background: linear-gradient(45deg, #fdcb6e, #e17055);
            box-shadow: 0 0 10px rgba(253, 203, 110, 0.3);
        }
        
        .status-red {
            background: linear-gradient(45deg, #ff7675, #d63031);
            box-shadow: 0 0 10px rgba(255, 118, 117, 0.3);
        }
        
        .stats {
            display: flex;
            gap: 30px;
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
        }
        
        .stat-box {
            text-align: center;
            padding: 15px;
            flex: 1;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .stat-box:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }
        
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 20px;
                text-align: center;
            }
            
            .auth-buttons {
                flex-direction: column;
                width: 100%;
            }
            
            .btn {
                width: 100%;
                justify-content: center;
            }
            
            #map {
                height: 60vh;
            }
        }
        
        .map-error {
            color: #ff4757;
            font-weight: bold;
            text-align: center;
            padding: 20px;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-parking"></i>
                Парковки Москвы - Карта свободных мест
            </h1>
            <div class="auth-buttons">
                <button class="btn btn-primary" onclick="showLogin()">
                    <i class="fas fa-sign-in-alt"></i>
                    Войти
                </button>
                <button class="btn btn-secondary" onclick="showRegister()">
                    <i class="fas fa-user-plus"></i>
                    Регистрация
                </button>
            </div>
        </div>
        
        <div id="map">
            <div class="loading">
                <i class="fas fa-spinner fa-spin fa-2x"></i>
                <p>Загрузка карты...</p>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="status-dot status-green"></div>
                <div>
                    <strong>Много свободных мест</strong><br>
                    <small>≥ 30% свободно</small>
                </div>
            </div>
            <div class="legend-item">
                <div class="status-dot status-yellow"></div>
                <div>
                    <strong>Мало свободных мест</strong><br>
                    <small>10-30% свободно</small>
                </div>
            </div>
            <div class="legend-item">
                <div class="status-dot status-red"></div>
                <div>
                    <strong>Почти нет мест</strong><br>
                    <small>< 10% свободно</small>
                </div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-box" style="background: rgba(0, 184, 148, 0.1);">
                <i class="fas fa-check-circle" style="color: #00b894; font-size: 24px;"></i>
                <div id="free-count" class="stat-value">0</div>
                <div>Свободные парковки</div>
            </div>
            <div class="stat-box" style="background: rgba(253, 203, 110, 0.1);">
                <i class="fas fa-exclamation-triangle" style="color: #fdcb6e; font-size: 24px;"></i>
                <div id="medium-count" class="stat-value">0</div>
                <div>Почти заполнены</div>
            </div>
            <div class="stat-box" style="background: rgba(255, 118, 117, 0.1);">
                <i class="fas fa-times-circle" style="color: #ff7675; font-size: 24px;"></i>
                <div id="full-count" class="stat-value">0</div>
                <div>Заполнены</div>
            </div>
        </div>
    </div>
    
    <script>
        
        let freeParkings = 0;
        let mediumParkings = 0;
        let fullParkings = 0;
        
        
        function loadYandexMaps() {
            return new Promise((resolve, reject) => {
                
                if (typeof ymaps !== 'undefined') {
                    resolve();
                    return;
                }
                
                
                const script = document.createElement('script');
                script.src = 'https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=ваш_api_ключ'; 
                script.async = true;
                
                script.onload = function() {
                    console.log('Яндекс.Карты загружены');
                    resolve();
                };
                
                script.onerror = function() {
                    console.error('Ошибка загрузки Яндекс.Карт');
                    reject(new Error('Не удалось загрузить Яндекс.Карты'));
                };
                
                document.head.appendChild(script);
            });
        }
        
        
        async function init() {
            try {
              
                await loadYandexMaps();
                
              
                ymaps.ready(function() {
                
                    
                    const map = new ymaps.Map('map', {
                        center: [55.75, 37.61],
                        zoom: 11,
                        controls: ['zoomControl', 'fullscreenControl', 'typeSelector']
                    });
                    
                    
                    fetch('/api/parkings')
                        .then(response => response.json())
                        .then(parkings => {
                            
                            freeParkings = 0;
                            mediumParkings = 0;
                            fullParkings = 0;
                            
                            
                            parkings.forEach(parking => {
                                
                                let status, color, icon;
                                
                                if (parking.free_percent >= 30) {
                                    status = "Свободно";
                                    color = "#00b894";
                                    icon = "islands#greenIcon";
                                    freeParkings++;
                                } else if (parking.free_percent >= 10) {
                                    status = "Мало мест";
                                    color = "#fdcb6e";
                                    icon = "islands#yellowIcon";
                                    mediumParkings++;
                                } else {
                                    status = "Заполнена";
                                    color = "#ff7675";
                                    icon = "islands#redIcon";
                                    fullParkings++;
                                }
                                
                                
                                const placemark = new ymaps.Placemark(
                                    [parking.lat, parking.lon],
                                    {
                                        balloonContent: `
                                            <div style="padding: 15px; max-width: 300px;">
                                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                                                    <div style="width: 12px; height: 12px; border-radius: 50%; background: ${color};"></div>
                                                    <h3 style="margin: 0; color: #333;">${parking.name}</h3>
                                                </div>
                                                
                                                <div style="background: ${color}20; padding: 10px; border-radius: 8px; margin-bottom: 15px;">
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                                        <span>Статус:</span>
                                                        <strong style="color: ${color};">${status}</strong>
                                                    </div>
                                                    <div style="display: flex; justify-content: space-between;">
                                                        <span>Свободно:</span>
                                                        <strong>${parking.free_spots} из ${parking.total_spots}</strong>
                                                    </div>
                                                </div>
                                                
                                                <div style="margin-bottom: 15px;">
                                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                                        <span>Заполненность:</span>
                                                        <strong>${(100 - parking.free_percent).toFixed(1)}%</strong>
                                                    </div>
                                                    <div style="background: #eee; height: 8px; border-radius: 4px; overflow: hidden;">
                                                        <div style="width: ${100 - parking.free_percent}%; height: 100%; background: ${color};"></div>
                                                    </div>
                                                </div>
                                                
                                                ${parking.address ? `<div style="color: #666; font-size: 14px;">
                                                    <i class="fas fa-map-marker-alt"></i> ${parking.address}
                                                </div>` : ''}
                                            </div>
                                        `,
                                        iconCaption: parking.name,
                                        hintContent: `${parking.name} - ${status}`
                                    },
                                    {
                                        preset: icon,
                                        iconColor: color,
                                        balloonCloseButton: false,
                                        hideIconOnBalloonOpen: false
                                    }
                                );
                                
                                
                                map.geoObjects.add(placemark);
                            });
                            
                            
                            updateStats();
                            
                            console.log(`Загружено ${parkings.length} парковок`);
                        })
                        .catch(error => {
                            console.error('Ошибка загрузки парковок:', error);
                            showError('Ошибка загрузки данных с сервера');
                        });
                });
                
            } catch (error) {
                console.error('Ошибка инициализации карты:', error);
                showError('Не удалось загрузить карту. Проверьте подключение к интернету.');
            }
        }
        
        function showError(message) {
            const mapDiv = document.getElementById('map');
            mapDiv.innerHTML = `<div class="map-error"><i class="fas fa-exclamation-triangle"></i><p>${message}</p></div>`;
        }
        
        function updateStats() {
            document.getElementById('free-count').textContent = freeParkings;
            document.getElementById('medium-count').textContent = mediumParkings;
            document.getElementById('full-count').textContent = fullParkings;
        }
        
        function showRegister() {
            const login = prompt('Введите логин для регистрации:');
            if (login) {
                const password = prompt('Введите пароль:');
                if (password) {
                    alert(`Регистрация успешна!\\nЛогин: ${login}\\nПароль: ${password}\\n\\n(В демо-версии данные не сохраняются)`);
                }
            }
        }
        
        function showLogin() {
            const login = prompt('Введите логин:');
            if (login) {
                const password = prompt('Введите пароль:');
                if (password) {
                    if (login === 'admin' && password === 'admin') {
                        alert('Вход выполнен успешно!');
                    } else {
                        alert('Неверный логин или пароль\\nПопробуйте:\\nЛогин: admin\\nПароль: admin');
                    }
                }
            }
        }
        
        
        init();
        
        
        setInterval(() => {
            console.log('Автообновление данных...');
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''


@app.route('/api/parkings')
def get_parkings():
    conn = sqlite3.connect('parking_app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, lat, lon, free_spots, total_spots, address 
        FROM parkings 
        ORDER BY name
    ''')
    
    parkings = []
    for row in cursor.fetchall():
        parking = dict(row)
        
        
        free_spots = parking['free_spots']
        total_spots = parking['total_spots']
        free_percent = (free_spots / total_spots * 100) if total_spots > 0 else 0
        
        parking['free_percent'] = round(free_percent, 1)
        parkings.append(parking)
    
    conn.close()
    return jsonify(parkings)


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/add_parking', methods=['POST'])
def add_parking():
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('parking_app.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO parkings (name, lat, lon, free_spots, total_spots, address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['lat'],
            data['lon'],
            data['free_spots'],
            data['total_spots'],
            data.get('address', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Парковка добавлена'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print(" Откройте в браузере: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
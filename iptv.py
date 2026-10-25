<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamVue Pro - IPTV Player</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-sidebar: #111827;
            --bg-card: #1f2937;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --border: #374151;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-main); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        .sidebar { width: 380px; background-color: var(--bg-sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; height: 100%; }
        .sidebar-header { padding: 20px; border-bottom: 1px solid var(--border); }
        .logo-area { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
        .logo-icon { background: var(--accent); color: white; padding: 8px 12px; border-radius: 8px; font-weight: bold; }
        
        .tabs { display: flex; gap: 5px; background: var(--bg-card); padding: 5px; border-radius: 8px; margin-bottom: 15px; }
        .tab-btn { flex: 1; background: transparent; border: none; color: var(--text-muted); padding: 8px; cursor: pointer; border-radius: 6px; font-size: 13px; font-weight: 600; transition: 0.2s; }
        .tab-btn.active { background: var(--accent); color: white; }
        
        .search-box, .category-select, .url-input { width: 100%; padding: 10px 14px; background: var(--bg-main); border: 1px solid var(--border); color: white; border-radius: 8px; outline: none; margin-bottom: 10px; font-size: 14px; }
        .search-box:focus, .category-select:focus, .url-input:focus { border-color: var(--accent); }
        
        .channel-list { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 8px; }
        .channel-item { background: var(--bg-card); padding: 12px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; border: 1px solid transparent; transition: 0.2s; }
        .channel-item:hover { border-color: var(--accent); }
        .channel-info h4 { font-size: 14px; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 270px; }
        .channel-info span { font-size: 11px; color: var(--text-muted); background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; }
        
        /* Main Content */
        .main-content { flex: 1; display: flex; flex-direction: column; height: 100%; padding: 20px; overflow-y: auto; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .player-container { background: #000; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); aspect-ratio: 16/9; max-height: 65vh; display: flex; align-items: center; justify-content: center; position: relative; }
        video { width: 100%; height: 100%; outline: none; }
        .no-stream { color: var(--text-muted); text-align: center; }
        
        .upload-section { background: var(--bg-sidebar); padding: 15px; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 15px; }
        .btn { background: var(--accent); color: white; border: none; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: 0.2s; width: 100%; }
        .btn:hover { background: var(--accent-hover); }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <div class="logo-area">
                <div class="logo-icon">📺</div>
                <div>
                    <h3>StreamVue Pro</h3>
                    <small style="color:var(--text-muted);">M3U / VOD Web Player</small>
                </div>
            </div>
            
            <div class="upload-section">
                <input type="text" id="m3uUrl" class="url-input" placeholder="M3U URL Bağlantısını Yapıştır...">
                <button class="btn" onclick="loadM3UFromURL()">Listeyi Yükle</button>
            </div>

            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab('all', this)">Tümü</button>
                <button class="tab-btn" onclick="switchTab('live', this)">Canlı TV</button>
                <button class="tab-btn" onclick="switchTab('vod', this)">Filmler/Dizi</button>
            </div>

            <input type="text" id="searchBox" class="search-box" placeholder="Kanal veya içerik ara..." oninput="filterChannels()">
            <select id="categorySelect" class="category-select" onchange="filterChannels()">
                <option value="all">Tüm Kategoriler</option>
            </select>
        </div>

        <div class="channel-list" id="channelList">
            <div class="no-stream" style="padding:20px;">Lütfen M3U listesi yükleyin veya demo modunu kullanın.</div>
        </div>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <h2 id="currentTitle">Bir içerik seçin</h2>
            <button class="btn" style="width: auto;" onclick="loadDemoList()">✨ Demo Listesini Yükle</button>
        </div>
        <div class="player-container">
            <video id="videoPlayer" controls autoplay></video>
        </div>
    </div>

    <script>
        let allChannels = [];
        let currentTab = 'all';

        const DEMO_DATA = `#EXTM3U
#EXTINF:-1 group-title="Demo / Sinema", Big Buck Bunny (HLS Demo)
https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8
#EXTINF:-1 group-title="Demo / Sinema", Sintel Movie Trailer (MP4)
https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4
#EXTINF:-1 group-title="Doğa", Tears of Steel (HLS)
https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8`;

        window.onload = () => {
            parseM3U(DEMO_DATA);
        };

        function loadDemoList() {
            parseM3U(DEMO_DATA);
        }

        async function loadM3UFromURL() {
            const url = document.getElementById('m3uUrl').value.trim();
            if(!url) return alert("Lütfen geçerli bir M3U linki girin!");
            try {
                // CORS engeline karşı proxy kullanımı
                const proxyUrl = "https://api.allorigins.win/raw?url=" + encodeURIComponent(url);
                const res = await fetch(proxyUrl);
                const text = await res.text();
                parseM3U(text);
            } catch(e) {
                alert("M3U yüklenemedi! CORS engeli olabilir. Sunucu linkini kontrol edin.");
            }
        }

        function parseM3U(data) {
            allChannels = [];
            const lines = data.split('\n');
            let currentItem = {};

            for(let line of lines) {
                line = line.trim();
                if(line.startsWith('#EXTINF:')) {
                    currentItem = {};
                    let groupMatch = line.match(/group-title="([^"]+)"/);
                    currentItem.group = groupMatch ? groupMatch[1] : 'Genel';
                    let parts = line.split(',');
                    currentItem.name = parts[parts.length - 1].trim();
                } else if(line && !line.startsWith('#')) {
                    currentItem.url = line;
                    if(currentItem.name && currentItem.url) {
                        allChannels.push(currentItem);
                    }
                    currentItem = {};
                }
            }
            updateCategories();
            renderChannels(allChannels);
        }

        function updateCategories() {
            const select = document.getElementById('categorySelect');
            select.innerHTML = '<option value="all">Tüm Kategoriler</option>';
            const categories = [...new Set(allChannels.map(c => c.group))];
            categories.forEach(cat => {
                let opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                select.appendChild(opt);
            });
        }

        function switchTab(tab, btn) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterChannels();
        }

        function filterChannels() {
            const search = document.getElementById('searchBox').value.toLowerCase();
            const cat = document.getElementById('categorySelect').value;

            let filtered = allChannels.filter(c => {
                let matchesSearch = c.name.toLowerCase().includes(search);
                let matchesCat = (cat === 'all' || c.group === cat);
                return matchesSearch && matchesCat;
            });
            renderChannels(filtered);
        }

        function renderChannels(channels) {
            const list = document.getElementById('channelList');
            list.innerHTML = '';
            if(channels.length === 0) {
                list.innerHTML = '<div class="no-stream">İçerik bulunamadı.</div>';
                return;
            }
            channels.forEach(ch => {
                let div = document.createElement('div');
                div.className = 'channel-item';
                div.innerHTML = `
                    <div class="channel-info">
                        <h4>${ch.name}</h4>
                        <span>${ch.group}</span>
                    </div>
                `;
                div.onclick = () => playStream(ch.url, ch.name);
                list.appendChild(div);
            });
        }

        function playStream(url, name) {
            document.getElementById('currentTitle').textContent = "Şimdi Oynatılıyor: " + name;
            const video = document.getElementById('videoPlayer');
            
            if (Hls.isSupported() && url.includes('.m3u8')) {
                if(window.hlsInstance) window.hlsInstance.destroy();
                const hls = new Hls();
                hls.loadSource(url);
                hls.attachMedia(video);
                window.hlsInstance = hls;
                hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
            } else {
                video.src = url;
                video.play().catch(e => alert("Bu yayın tarayıcı tarafından doğrudan oynatılamıyor (CORS veya format kısıtı)."));
            }
        }
    </script>
</body>
</html>

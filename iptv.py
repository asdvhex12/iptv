import streamlit as st
import requests
import re
import streamlit.components.v1 as components

# Sayfa Yapılandırması
st.set_page_config(
    page_title="StreamVue Pro",
    page_icon="📺",
    layout="wide"
)

# Özel Modern Tema (Dark Mode)
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f9fafb; }
    .sidebar .stRadio label, .sidebar .stTextInput label { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

st.title("📺 StreamVue Pro - IPTV Player")
st.caption("M3U / M3U8 Canlı Yayın ve VOD Oynatıcı")

# M3U Parser Fonksiyonu
def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            current_channel = {}
            group_match = re.search(r'group-title="([^"]+)"', line)
            current_channel['group']  = group_match.group(1) if group_match else "Genel"
            
            name_parts = line.split(",")
            current_channel['name'] = name_parts[-1].strip() if len(name_parts) > 1 else "Bilinmeyen Kanal"
            
        elif line and not line.startswith("#"):
            if 'name' in current_channel:
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = {}
                
    return channels

# Demo Kanal Listesi
DEMO_M3U = """#EXTM3U
#EXTINF:-1 group-title="Demo / Sinema", Big Buck Bunny (HLS Demo)
https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8
#EXTINF:-1 group-title="Demo / Sinema", Sintel Movie Trailer
https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4
#EXTINF:-1 group-title="Doğa", Tears of Steel
https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8
"""

# Sol Menü
st.sidebar.header("⚙️ Yayın Kaynağı")
source_option = st.sidebar.radio("Kaynak Seç:", ["Demo Listesi", "M3U URL Bağlantısı"])

m3u_text = ""

if source_option == "Demo Listesi":
    m3u_text = DEMO_M3U
else:
    url_input = st.sidebar.text_input("M3U URL Adresi:", placeholder="http://...")
    if url_input:
        try:
            # Tarayıcı gibi görünmek için Headers ekledik (Zaman aşımı ve engellemeleri önler)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            with st.spinner('M3U listesi indiriliyor...'):
                res = requests.get(url_input, headers=headers, timeout=15)
                
            if res.status_code == 200:
                m3u_text = res.text
                st.sidebar.success("Liste başarıyla yüklendi!")
            else:
                st.sidebar.error(f"Bağlantı başarısız (Kod: {res.status_code})")
        except Exception as e:
            st.sidebar.error(f"Zaman aşımı veya bağlantı hatası: {e}")

channels = parse_m3u(m3u_text) if m3u_text else []

if channels:
    st.sidebar.markdown("---")
    categories = sorted(list(set([c['group'] for c in channels])))
    selected_cat = st.sidebar.selectbox("Kategori:", ["Tüm Kategoriler"] + categories)
    search = st.sidebar.text_input("Kanal Ara:", "")
    
    filtered = channels
    if selected_cat != "Tüm Kategoriler":
        filtered = [c for c in filtered if c['group'] == selected_cat]
    if search:
        filtered = [c for c in filtered if search.lower() in c['name'].lower()]
        
    st.sidebar.write(f"Bulunan Kanal: **{len(filtered)}**")
    
    channel_options = [f"{c['name']} ({c['group']})" for c in filtered]
    if channel_options:
        sel_idx = st.selectbox("🎯 Kanal Seçin:", range(len(channel_options)), format_func=lambda x: channel_options[x])
        ch = filtered[sel_idx]
        
        st.subheader(f"🔴 Şimdi Oynatılıyor: {ch['name']}")
        
        player_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <style>
                body {{ margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }}
                video {{ width: 100%; height: 100%; max-height: 480px; border-radius: 8px; outline: none; }}
            </style>
        </head>
        <body>
            <video id="v" controls autoplay></video>
            <script>
                const video = document.getElementById('v');
                const src = '{ch['url']}';
                if (Hls.isSupported() && src.includes('.m3u8')) {{
                    const hls = new Hls();
                    hls.loadSource(src);
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
                }} else {{
                    video.src = src;
                    video.play();
                }}
            </script>
        </body>
        </html>
        """
        components.html(player_html, height=500)
    else:
        st.warning("Bu kategoride/aramada kanal bulunamadı.")
else:
    st.info("Lütfen sol taraftan bir kaynak seçin veya M3U bağlantısı girin.")

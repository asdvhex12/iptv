import streamlit as st
import requests
import re
import streamlit.components.v1 as components

# Sayfa Yapılandırması
st.set_page_config(
    page_title="StreamVue IPTV Player",
    page_icon="📺",
    layout="wide"
)

# Stil (Dark Theme Enhancements)
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    stApp { color: #f8fafc; }
    .stSelectbox label, .stTextInput label { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

st.title("📺 StreamVue IPTV Web Player")
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
            # Kategori
            group_match = re.search(r'group-title="([^"]+)"', line)
            current_channel['group'] = group_match.group(1) if group_match else "Diğer"
            
            # Logo
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            current_channel['logo'] = logo_match.group(1) if logo_match else ""
            
            # İsim
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
#EXTINF:-1 tvg-logo="https://upload.wikimedia.org/wikipedia/commons/7/70/Big.Buck.Bunny.-.Full.Movie.ogv.jpg" group-title="Demo / Sinema", Big Buck Bunny (HLS Demo)
https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8
#EXTINF:-1 group-title="Demo / Sinema", Sintel Movie Trailer
https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8
#EXTINF:-1 group-title="Doğa", Nature Test Stream
https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8
"""

# Sol Menü (Sidebar) - M3U Yükleme
st.sidebar.header("⚙️ Yayın Kaynağı")
source_type = st.sidebar.radio("Kaynak Türü:", ["Demo Listesi", "M3U Bağlantısı (URL)", "M3U Dosyası Yükle"])

m3u_text = ""

if source_type == "Demo Listesi":
    m3u_text = DEMO_M3U
elif source_type == "M3U Bağlantısı (URL)":
    url = st.sidebar.text_input("M3U URL Girin:", placeholder="http://example.com/playlist.m3u")
    if url:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                m3u_text = res.text
                st.sidebar.success("M3U Başarıyla Çekildi!")
            else:
                st.sidebar.error("M3U Bağlantısı Alınamadı.")
        except Exception as e:
            st.sidebar.error(f"Hata: {e}")
elif source_type == "M3U Dosyası Yükle":
    uploaded_file = st.sidebar.file_uploader("M3U / M3U8 Dosyası Seç", type=["m3u", "m3u8", "txt"])
    if uploaded_file is not None:
        m3u_text = uploaded_file.read().decode("utf-8", errors="ignore")

# Kanalları İşle
channels = []
if m3u_text:
    channels = parse_m3u(m3u_text)

if channels:
    st.sidebar.hr()
    st.sidebar.subheader("🔍 Filtreleme")
    
    # Kategori Filtresi
    categories = sorted(list(set([c['group'] for c in channels])))
    selected_cat = st.sidebar.selectbox("Kategori Seç:", ["Tüm Kategoriler"] + categories)
    
    # Arama Filtresi
    search_query = st.sidebar.text_input("Kanal Ara:", "")
    
    # Filtreleme İşlemi
    filtered_channels = channels
    if selected_cat != "Tüm Kategoriler":
        filtered_channels = [c for c in filtered_channels if c['group'] == selected_cat]
    if search_query:
        filtered_channels = [c for c in filtered_channels if search_query.lower() in c['name'].lower()]
        
    st.sidebar.write(f"Bulunan Kanal Sayısı: **{len(filtered_channels)}**")
    
    # Kanal Seçimi
    channel_names = [f"{c['name']} ({c['group']})" for c in filtered_channels]
    
    if channel_names:
        selected_index = st.selectbox("🎯 İzlemek İstediğiniz Kanalı Seçin:", range(len(channel_names)), format_func=lambda x: channel_names[x])
        selected_channel = filtered_channels[selected_index]
        
        # Oynatıcı Alanı (HLS.js Entegre Video Player)
        st.subheader(f"🔴 Şimdi İzleniyor: {selected_channel['name']}")
        st.caption(f"Kategori: {selected_channel['group']}")
        
        hls_player_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <style>
                body {{ margin: 0; background-color: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }}
                video {{ width: 100%; height: 100%; max-height: 500px; border-radius: 8px; outline: none; }}
            </style>
        </head>
        <body>
            <video id="video" controls autoplay></video>
            <script>
                var video = document.getElementById('video');
                var videoSrc = '{selected_channel['url']}';
                if (Hls.isSupported()) {{
                    var hls = new Hls();
                    hls.loadSource(videoSrc);
                    hls.attachMedia(video);
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{ video.play(); }});
                }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                    video.src = videoSrc;
                    video.addEventListener('loadedmetadata', function() {{ video.play(); }});
                }}
            </script>
        </body>
        </html>
        """
        components.html(hls_player_html, height=520)
    else:
        st.warning("Aramanıza uygun kanal bulunamadı.")
else:
    st.info("Lütfen sol menüden bir M3U dosyası yükleyin veya URL bağlantısı girin.")

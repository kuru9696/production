    let map;
    const markersLayer = L.layerGroup();
    const userLayer = L.layerGroup();

    const redIcon = new L.Icon({
      iconUrl: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
      iconSize: [32,32], iconAnchor: [16,32], popupAnchor: [0,-28]
    });
    const greenIcon = new L.Icon({
      iconUrl: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
      iconSize: [32,32], iconAnchor: [16,32], popupAnchor: [0,-28]
    });

    let userMarker = null;
    let userWatchId = null;
    let userShown = false;

    function toast(msg, timeout=2200){
      const el = document.getElementById('toast');
      el.textContent = msg;
      el.style.display = 'block';
      clearTimeout(el._t);
      el._t = setTimeout(()=> el.style.display = 'none', timeout);
    }

    function initMap(){
      map = L.map('map', {zoomControl:true, attributionControl:false}).setView([35.7,139.49], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19}).addTo(map);
      markersLayer.addTo(map);
      userLayer.addTo(map);
      loadMarkers();
      let t;
      map.on('moveend', ()=>{ clearTimeout(t); t=setTimeout(loadMarkers,400); });
      const userToggle = document.getElementById('userToggle');
      userToggle.addEventListener('click', toggleUserLocation);
    }

    function clearMarkers(){ markersLayer.clearLayers(); }

    function loadMarkers(){
      fetch('/list').then(r=>r.json()).then(data=>{
        clearMarkers();
        data.forEach((item, index)=>{
          const icon = item.approved ? greenIcon : redIcon;
          const marker = L.marker([item.lat, item.lng], {icon});
          const naiyoEsc = item.naiyo ? escapeHtml(item.naiyo) : '';
          const pop = document.createElement('div');
          pop.className = 'popup-content';
          const t = document.createElement('p'); t.className='popup-title'; t.textContent = item.title || '（タイトルなし）';
          const s = document.createElement('p'); s.className='popup-sub'; s.textContent = `${item.age || '年齢不明'} ・ ${item.gender || '性別不明'}`;
          const d = document.createElement('p'); d.style.marginTop='8px'; d.style.marginBottom='0'; d.textContent = naiyoEsc || '(詳細なし)';
          pop.appendChild(t);
          pop.appendChild(s);
          pop.appendChild(d);
          marker.bindPopup(pop);
          marker.addTo(markersLayer);
        });
      }).catch(err=>{
        console.error('loadMarkers error', err);
      });
    }

    function escapeHtml(s){ if(!s) return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

    // ---------- 修正ポイント：buttonClick() ----------
    function buttonClick(){
      const old = document.getElementById('old').value;
      const gender = document.getElementById('gender').value;
      const title = document.getElementById('title').value;
      const naiyo = document.getElementById('naiyo').value;

      if(!title){ toast('タイトルを選んでください'); return; }

      // もし「自分の位置表示がON」かつ userMarker が存在するなら、それを使う（余分な getCurrentPosition を呼ばない）
      if(userShown && userMarker){
        const latlng = userMarker.getLatLng();
        const payload = { lat: latlng.lat, lng: latlng.lng, age: old, gender: gender, title: title, naiyo: naiyo };
        fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
          .then(r=>r.json()).then(()=>{ toast('募集を投稿しました'); loadMarkers(); })
          .catch(()=>toast('投稿に失敗しました'));
        return;
      }

      // それ以外は通常通り getCurrentPosition で位置を取得する
      if(navigator.geolocation){
        navigator.geolocation.getCurrentPosition(pos=>{
          const payload = { lat: pos.coords.latitude, lng: pos.coords.longitude, age: old, gender: gender, title: title, naiyo: naiyo };
          fetch('/add', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
            .then(r=>r.json()).then(()=>{ toast('募集を投稿しました'); loadMarkers(); })
            .catch(()=>toast('投稿に失敗しました'));
        }, ()=>{
          toast('位置情報を取得できませんでした（ブラウザの設定を確認）');
        }, {timeout:5000});
      } else {
        toast('このブラウザは位置情報に対応していません');
      }
    }
    // ---------- 修正ここまで ----------

    function complete(index){
      fetch('/delete', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({index})})
        .then(r=>r.json()).then(()=>{ toast('募集を完了しました'); loadMarkers(); })
        .catch(()=>toast('削除に失敗しました'));
    }

    function updateToggleUI(shown){
      const btn = document.getElementById('userToggle');
      const lbl = document.getElementById('userToggleLabel');
      const sub = document.getElementById('userToggleSub');
      if(shown){
        btn.classList.add('active');
        btn.setAttribute('aria-pressed','true');
        lbl.textContent = '自分の位置を非表示';
        sub.textContent = 'オン';
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed','false');
        lbl.textContent = '自分の位置を表示';
        sub.textContent = 'オフ';
      }
    }

    function toggleUserLocation(){
      if(!userShown){
        showUserLocation();
      } else {
        hideUserLocation();
      }
    }

    function showUserLocation(){
      if(!navigator.geolocation){
        toast('このブラウザは位置情報に対応していません');
        return;
      }

      navigator.geolocation.getCurrentPosition(pos => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        if(!userMarker){
          userMarker = L.circleMarker([lat, lng], {
            radius: 8,
            color: '#ffffff',
            weight: 2,
            fillColor: getComputedStyle(document.documentElement).getPropertyValue('--accent') || '#2563eb',
            fillOpacity: 0.95
          }).addTo(userLayer);

          userMarker.bindPopup('あなたの現在地');
        } else {
          userMarker.setLatLng([lat,lng]);
        }

        map.setView([lat, lng], Math.max(map.getZoom(), 15));

        if(userWatchId === null){
          userWatchId = navigator.geolocation.watchPosition(p => {
            const la = p.coords.latitude;
            const ln = p.coords.longitude;
            if(userMarker) userMarker.setLatLng([la, ln]);
          }, err => {
            console.warn('watchPosition error', err);
          }, {enableHighAccuracy:true, maximumAge:5000, timeout:7000});
        }

        userShown = true;
        updateToggleUI(true);
        toast('自分の位置を表示しました');
      }, err => {
        console.warn('getCurrentPosition error', err);
        toast('位置情報を取得できませんでした（許可や端末設定を確認してください）');
      }, {enableHighAccuracy:true, timeout:7000});
    }

    function hideUserLocation(){
      if(userWatchId !== null){
        navigator.geolocation.clearWatch(userWatchId);
        userWatchId = null;
      }
      userLayer.clearLayers();
      userMarker = null;
      userShown = false;
      updateToggleUI(false);
      toast('自分の位置を非表示にしました');
    }

    // 初期表示をONにする場合は次の行を有効化（既にONが要る場合）
    // window.addEventListener('load', () => { initMap(); showUserLocation(); });

    // 通常：初期はOFFで読み込み
    window.addEventListener('load', initMap);

#pragma once

static const char WEB_UI_HTML[] PROGMEM = R"WINDOWUI(
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#171a1f">
  <title>Окна и двери</title>
  <style>
    :root{color-scheme:dark;--bg:#111317;--band:#171a1f;--panel:#1d2127;--line:#343a43;--text:#f3f5f7;--muted:#aab1ba;--blue:#2f81c1;--green:#23865f;--red:#b54148;--amber:#c58a31;--focus:#78b9e8}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,sans-serif;font-size:15px;letter-spacing:0}button,input,select{font:inherit}button{border:1px solid var(--line);background:#262b32;color:var(--text);min-height:42px;padding:8px 13px;border-radius:6px;cursor:pointer}button:hover{background:#30363e}button:disabled{opacity:.45;cursor:not-allowed}button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--focus);outline-offset:2px}.icon{font-size:18px;line-height:1}.topbar{height:58px;display:flex;align-items:center;gap:16px;padding:0 18px;background:var(--band);border-bottom:1px solid var(--line)}.brand{font-size:19px;font-weight:700}.top-state{margin-left:auto;color:var(--muted);display:flex;align-items:center;gap:8px}.dot{width:9px;height:9px;border-radius:50%;background:var(--red)}.dot.ok{background:var(--green)}.tabs{display:flex;gap:2px;padding:8px 18px;background:var(--band);border-bottom:1px solid var(--line);overflow:auto}.tabs button{border-color:transparent;background:transparent;color:var(--muted);white-space:nowrap}.tabs button.active{background:#292e35;color:var(--text);border-color:var(--line)}main{max-width:1440px;margin:auto;padding:16px}.view{display:none}.view.active{display:block}.workspace{display:grid;grid-template-columns:minmax(270px,340px) minmax(0,1fr);gap:16px}.workspace>*{min-width:0}.section{background:var(--panel);border:1px solid var(--line);border-radius:7px}.section-head{min-height:48px;padding:11px 14px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--line)}.section-head h2,.section-head h3{margin:0;font-size:16px}.grow{flex:1}.object-list{min-height:480px}.object-row{width:100%;border:0;border-bottom:1px solid var(--line);border-radius:0;background:transparent;text-align:left;padding:12px 14px;display:grid;grid-template-columns:1fr auto;gap:4px 10px}.object-row:last-child{border-bottom:0}.object-row.selected{background:#29313a}.object-name{font-weight:700}.object-meta{font-size:13px;color:var(--muted)}.badge{font-size:12px;border:1px solid var(--line);border-radius:10px;padding:2px 7px;align-self:start}.badge.ok{color:#7fdbb5;border-color:#357a61}.badge.move{color:#8ccbf1;border-color:#326b8d}.badge.fault{color:#ff9ba0;border-color:#8d383d}.badge.offline{color:#c2c6cc}.detail{min-height:480px}.detail-body{padding:14px}.summary{display:grid;grid-template-columns:repeat(4,minmax(100px,1fr));border:1px solid var(--line);border-radius:6px;margin-bottom:14px}.metric{padding:11px;border-right:1px solid var(--line)}.metric:last-child{border-right:0}.metric-label{display:block;color:var(--muted);font-size:12px;margin-bottom:5px}.metric-value{font-size:17px;font-weight:700}.commands{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}.commands .open{background:#1f6f53;border-color:#3a9273}.commands .close{background:#285f91;border-color:#3b79ae}.commands .stop{background:#86353a;border-color:#b54b52;margin-left:auto}.sensor-strip{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.sensor{border:1px solid var(--line);border-radius:6px;padding:7px 10px;color:var(--muted)}.sensor.on{color:#8ce0bb;border-color:#3f8669;background:#203b31}.sensor.warn{color:#ffd18a;border-color:#856530}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:650px}th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left}th{color:var(--muted);font-size:12px;font-weight:600}tr:last-child td{border-bottom:0}.empty{padding:44px 20px;text-align:center;color:var(--muted)}.calibration{margin-top:16px;border-top:1px solid var(--line);padding-top:14px}.calibration h3{font-size:15px;margin:0 0 10px}.calibration-actions{display:flex;gap:8px;flex-wrap:wrap}.notice{padding:10px 12px;border-left:3px solid var(--amber);background:#29251e;color:#e5d4b6;margin-top:12px}.toolbar{display:flex;gap:8px;flex-wrap:wrap}.form-grid{display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:12px;padding:14px}.field label{display:block;color:var(--muted);font-size:12px;margin-bottom:5px}.field input,.field select,.remote-row input,.remote-row select{width:100%;height:42px;border:1px solid var(--line);border-radius:6px;background:#12151a;color:var(--text);padding:8px 10px}.backup-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.backup-actions input[type=file]{max-width:310px;color:var(--muted)}.log{padding:0;margin:0;list-style:none}.log li{padding:10px 14px;border-bottom:1px solid var(--line);display:grid;grid-template-columns:90px 1fr;gap:12px}.log time{color:var(--muted)}.remote-row{display:grid;grid-template-columns:110px minmax(150px,1fr) minmax(150px,1fr) 150px auto auto;gap:10px;padding:10px 14px;border-bottom:1px solid var(--line);align-items:center}.muted{color:var(--muted)}.danger{color:#ff9ba0}.hidden{display:none!important}@media(max-width:800px){.topbar{padding:0 12px}.tabs{padding:7px 10px}main{padding:10px}.workspace{grid-template-columns:1fr}.object-list{min-height:0}.summary{grid-template-columns:1fr 1fr}.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--line)}.commands .stop{margin-left:0}.form-grid{grid-template-columns:1fr}.remote-row{grid-template-columns:1fr 1fr}.remote-row>*{grid-column:auto!important}.remote-row code,.remote-row input{grid-column:1/-1!important}.top-state span:last-child{display:none}.backup-actions{align-items:stretch}.backup-actions>*{width:100%;max-width:none!important}}
  </style>
  <style>
    .cap-config{margin-top:16px;border-top:1px solid var(--line);padding-top:14px}.cap-config h3{font-size:15px;margin:0 0 10px}.cap-channel-grid{display:grid;grid-template-columns:repeat(4,minmax(110px,1fr));gap:8px;margin:10px 0}.cap-channel{display:flex;align-items:center;gap:8px;min-height:40px;padding:7px 9px;border:1px solid var(--line);border-radius:6px}.cap-channel input{width:18px;height:18px}.cap-summary{color:var(--muted);font-size:13px}.cap-noise{color:#ffd18a}@media(max-width:800px){.cap-channel-grid{grid-template-columns:1fr 1fr}}
  </style>
</head>
<body>
  <header class="topbar"><div class="brand">Окна и двери</div><div class="top-state"><i id="systemDot" class="dot"></i><span id="systemText">Подключение...</span></div></header>
  <nav class="tabs">
    <button data-view="control" class="active">Управление</button>
    <button data-view="remotes">Пульты</button>
    <button data-view="events">События</button>
    <button data-view="settings">Настройки</button>
  </nav>
  <main>
    <section id="control" class="view active">
      <div class="workspace">
        <div class="section object-list">
          <div class="section-head"><h2>Объекты</h2><span class="grow"></span><button id="stopAll" title="Остановить все объекты"><span class="icon">■</span> Все</button></div>
          <div id="objectList"><div class="empty">Загрузка...</div></div>
        </div>
        <div class="section detail">
          <div class="section-head"><h2 id="detailName">Выберите объект</h2><span class="grow"></span><span id="detailBadge" class="badge offline">нет данных</span></div>
          <div id="detailBody" class="detail-body"><div class="empty">Выберите дверь или окно слева</div></div>
        </div>
      </div>
    </section>

    <section id="remotes" class="view section">
      <div class="section-head"><h2>Пульты 433 МГц</h2><span class="grow"></span><button id="learnRemote">Начать обучение</button></div>
      <div id="remoteStatus" class="notice hidden"></div><div id="remoteList"><div class="empty">Нет сохранённых кнопок</div></div>
    </section>

    <section id="events" class="view section">
      <div class="section-head"><h2>Журнал событий</h2><span class="grow"></span><button id="clearEvents">Очистить</button></div>
      <ul id="eventList" class="log"><li><span></span><span class="muted">Событий пока нет</span></li></ul>
    </section>

    <section id="settings" class="view section">
      <div class="section-head"><h2>Настройки системы</h2><span class="grow"></span><button id="discover">Найти шкафы CAN</button><button id="saveSettings">Сохранить</button></div>
      <div class="form-grid">
        <div class="field"><label>Имя системы</label><input id="systemName" maxlength="31"></div>
        <div class="field"><label>Частота CAN</label><select id="canRate" disabled><option value="500000">500 кбит/с</option></select></div>
        <div class="field"><label>Максимум объектов</label><input value="64" disabled></div>
      </div>
      <div class="section-head"><h3>Обнаруженные контроллеры</h3></div>
      <div id="discoveryList"><div class="empty">Нажмите «Найти шкафы CAN»</div></div>
      <div class="section-head">
        <h3>Резервная копия</h3><span class="grow"></span>
        <div class="backup-actions">
          <button id="downloadBackup">Скачать</button>
          <input id="backupFile" type="file" accept=".wbackup,application/octet-stream">
          <button id="restoreBackup">Восстановить</button>
        </div>
      </div>
    </section>
  </main>
  <script>
  const $=id=>document.getElementById(id);let objects=[],selected=-1,busy=false;
  const labels={state:{0:"загрузка",1:"безопасный режим",2:"готов",3:"движение",4:"калибровка",5:"авария",6:"восстановление"},position:{0:"неизвестно",1:"открыто",2:"закрыто",3:"промежуточное",4:"проветривание"},fault:{0:"нет",1:"нет конфигурации",2:"таймаут связи",3:"перегрузка",4:"нет тока",5:"таймаут движения",6:"ошибка VNH",7:"защитная кромка",8:"конфликт датчиков",9:"низкое питание",10:"нет ведомой STM",11:"ошибка калибровки",12:"восстановление питания",13:"нет CAP1188"}};
  async function api(url,opt={}){const c=new AbortController(),t=setTimeout(()=>c.abort(),1600);try{const r=await fetch(url,{...opt,signal:c.signal,cache:"no-store"});if(!r.ok){let message=String(r.status);try{const body=await r.clone().json();if(body.error)message=body.error}catch(e){}throw Error(message)}return r}finally{clearTimeout(t)}}
  function capConfigurationHtml(o){const mask=Number(o.capEnabledMask||0),count=Array.from({length:8},(_,i)=>(mask>>i)&1).reduce((a,b)=>a+b,0),channels=Array.from({length:8},(_,i)=>`<label class="cap-channel"><input type="checkbox" data-cap-channel="${i}" ${(mask&(1<<i))?'checked':''}><span>CS${i+1}</span></label>`).join("");return `<div class="cap-config"><h3>CAP1188</h3><div class="cap-summary">Активно каналов: <b data-cap-count>${count}</b> из 8${o.capNoise?' <span class="cap-noise">Обнаружены помехи</span>':''}</div><div class="cap-channel-grid">${channels}</div><button data-cap-save>Сохранить каналы</button></div>`}
  function bindCapConfiguration(){const boxes=[...document.querySelectorAll("[data-cap-channel]")],count=document.querySelector("[data-cap-count]"),save=document.querySelector("[data-cap-save]");boxes.forEach(box=>box.onchange=()=>{if(count)count.textContent=boxes.filter(x=>x.checked).length});if(save)save.onclick=async()=>{const mask=boxes.reduce((value,box)=>value|(box.checked?(1<<Number(box.dataset.capChannel)):0),0);await post("/api/object/cap",{id:selected,mask});await loadDetail()}}
  function stateClass(o){if(!o.online)return"offline";if(o.fault)return"fault";if(o.state===3||o.state===4)return"move";return"ok"}
  function stateText(o){if(!o.online)return"нет связи";if(o.fault)return labels.fault[o.fault]||"авария";return labels.state[o.state]||"неизвестно"}
  function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
  function renderObjects(){if(!objects.length){$("objectList").innerHTML='<div class="empty">Объекты не настроены</div>';return}$("objectList").innerHTML=objects.map(o=>`<button class="object-row ${o.id===selected?'selected':''}" data-id="${o.id}"><span class="object-name">${esc(o.name)}</span><span class="badge ${stateClass(o)}">${esc(stateText(o))}</span><span class="object-meta">${labels.position[o.position]||'неизвестно'} · ${o.actuatorCount} прив.</span><span class="object-meta">CAN ${o.cabinetId}</span></button>`).join("");document.querySelectorAll(".object-row").forEach(b=>b.onclick=()=>selectObject(+b.dataset.id))}
  function sensorsHtml(o){const r=o.reeds||0,c=o.cap||0;return `<div class="sensor-strip"><span class="sensor ${r&1?'on':''}">Открыто</span><span class="sensor ${r&2?'on':''}">Закрыто</span><span class="sensor ${r&4?'on':''}">Выдвижение</span><span class="sensor ${c?'warn':''}">Кромка: ${c?'касание':'свободна'}</span><span class="sensor ${o.powerGood?'on':'warn'}">12 В: ${o.powerGood?'норма':'ошибка'}</span></div>`}
  function renderDetail(o){$("detailName").textContent=o.name;$("detailBadge").className=`badge ${stateClass(o)}`;$("detailBadge").textContent=stateText(o);const rows=(o.actuators||[]).map((a,i)=>`<tr><td>${i+1}</td><td>${a.online?'готов':'нет связи'}</td><td>${a.current} мА</td><td>${a.pwm} %</td><td>${a.direction||'стоп'}</td><td>${a.calibrated?'да':'нет'}</td></tr>`).join("");const fullAllowed=o.position===1||o.position===2;$("detailBody").innerHTML=`<div class="summary"><div class="metric"><span class="metric-label">Положение</span><span class="metric-value">${labels.position[o.position]||'неизвестно'}</span></div><div class="metric"><span class="metric-label">Состояние</span><span class="metric-value">${stateText(o)}</span></div><div class="metric"><span class="metric-label">Макс. ток</span><span class="metric-value">${o.maxCurrent||0} мА</span></div><div class="metric"><span class="metric-label">Связь</span><span class="metric-value">${o.online?'CAN':'нет'}</span></div></div><div class="commands"><button class="open" data-cmd="open"><span class="icon">↑</span> Открыть</button><button class="close" data-cmd="close"><span class="icon">↓</span> Закрыть</button><button class="stop" data-cmd="stop"><span class="icon">■</span> Стоп</button></div>${sensorsHtml(o)}<div class="table-wrap"><table><thead><tr><th>Актуатор</th><th>STM32</th><th>Ток</th><th>PWM</th><th>Направление</th><th>Калиброван</th></tr></thead><tbody>${rows||'<tr><td colspan="6">Нет телеметрии</td></tr>'}</tbody></table></div><div class="calibration"><h3>Синхронизация скорости</h3><div class="calibration-actions"><button data-cal="open">Калибровать открытие</button><button data-cal="close">Калибровать закрытие</button><button data-cal="full" ${fullAllowed?'':'disabled title="Сначала доведите объект до конечного положения"'}>Полный цикл</button><button data-cal="reset">Сбросить</button></div><div class="notice">Калибровка запускает все приводы. Зона движения должна быть свободна.</div></div>`;document.querySelectorAll("[data-cmd]").forEach(b=>b.onclick=()=>command(b.dataset.cmd));document.querySelectorAll("[data-cal]").forEach(b=>b.onclick=()=>calibrate(b.dataset.cal))}
  async function loadObjects(){try{const j=await(await api("/api/objects")).json();objects=j.objects||[];$("systemDot").classList.add("ok");$("systemText").textContent="ESP32 подключена";if(selected<0&&objects.length)selected=objects[0].id;renderObjects();if(selected>=0)loadDetail()}catch(e){$("systemDot").classList.remove("ok");$("systemText").textContent="Нет связи"}}
  async function selectObject(id){selected=id;renderObjects();await loadDetail()}
  async function loadDetail(){try{const o=await(await api(`/api/object?id=${selected}`)).json();renderDetail(o)}catch(e){$("detailBadge").className="badge offline";$("detailBadge").textContent="нет связи"}}
  async function post(path,data){const body=new URLSearchParams(data);return api(path,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body})}
  async function command(cmd){if(busy)return;busy=true;try{await post("/api/object/command",{id:selected,command:cmd});setTimeout(loadDetail,150)}finally{busy=false}}
  async function calibrate(mode){if(!confirm("Убедитесь, что зона движения свободна. Запустить калибровку?"))return;try{await post("/api/object/calibrate",{id:selected,mode});setTimeout(loadDetail,150)}catch(e){alert("Калибровку нельзя начать из текущего положения")}}
  async function stopAll(){await post("/api/stop-all",{})}
  async function loadEvents(){try{const j=await(await api("/api/events")).json();$("eventList").innerHTML=(j.events||[]).map(e=>`<li><time>${esc(e.time)}</time><span><b>${esc(e.object)}</b> ${esc(e.text)}</span></li>`).join("")||'<li><span></span><span class="muted">Событий пока нет</span></li>'}catch(e){}}
  function objectOptions(mask){let current=-1;try{const m=BigInt(`0x${mask}`);objects.forEach((_,i)=>{if(m&(1n<<BigInt(i)))current=i})}catch(e){}return objects.map((o,i)=>`<option value="${i}" ${i===current?'selected':''}>${esc(o.name)}</option>`).join("")}
  async function loadRemotes(){try{const j=await(await api("/api/remotes")).json();$("remoteStatus").classList.toggle("hidden",!j.learning);$("remoteStatus").textContent=j.learning?"Нажмите нужную кнопку пульта...":"";$("remoteList").innerHTML=(j.remotes||[]).map(r=>`<div class="remote-row" data-remote="${r.index}"><code>${esc(r.code)}</code><input data-name value="${esc(r.name)}" maxlength="31"><select data-target>${objectOptions(r.targetMask)}</select><select data-action><option value="open" ${r.action==='open'?'selected':''}>Открыть</option><option value="close" ${r.action==='close'?'selected':''}>Закрыть</option><option value="stop" ${r.action==='stop'?'selected':''}>Стоп</option></select><button data-save>Сохранить</button><button data-del>Удалить</button></div>`).join("")||'<div class="empty">Нет сохранённых кнопок</div>';document.querySelectorAll("[data-remote]").forEach(row=>{row.querySelector("[data-save]").onclick=async()=>{const target=+row.querySelector("[data-target]").value,mask=(1n<<BigInt(target)).toString(16);await post("/api/remotes/save",{index:row.dataset.remote,name:row.querySelector("[data-name]").value,targetMask:mask,command:row.querySelector("[data-action]").value});loadRemotes()};row.querySelector("[data-del]").onclick=async()=>{await post("/api/remotes/delete",{index:row.dataset.remote});loadRemotes()}})}catch(e){}}
  const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  function provisionFailureText(status){if(status.state==="timeout")return"STM32 не подтвердила запись EEPROM";if(status.result===1)return"STM32 отклонила параметры";if(status.result===2)return"Нельзя перенастраивать плату во время движения";if(status.result===3)return"Ошибка записи или проверки EEPROM";return"Перенастройка не выполнена"}
  async function waitProvision(token){for(let attempt=0;attempt<16;attempt++){await wait(250);const status=await(await api(`/api/provision/status?token=${token}`)).json();if(status.token!==token)throw Error("transaction_replaced");if(status.state==="success")return status;if(status.state!=="pending")throw Error(provisionFailureText(status))}throw Error("Нет подтверждения записи EEPROM")}
  async function provisionNode(node){
    const current=objects.find(o=>o.cabinetId===node.cabinetId),reconfigure=Boolean(node.configured);
    if(reconfigure&&!confirm(`Перенастроить шкаф CAN ${node.cabinetId}? Все актуаторы должны быть остановлены.`))return;
    const cabinetId=prompt("Номер CAN-шкафа (0-63)",String(reconfigure?node.cabinetId:1));if(cabinetId===null)return;
    const numericCabinet=Number(cabinetId);if(!Number.isInteger(numericCabinet)||numericCabinet<0||numericCabinet>63){alert("Номер шкафа должен быть от 0 до 63");return}
    const name=prompt("Название окна или двери",current?.name||`CAN ${numericCabinet}`);if(name===null)return;
    const type=prompt("Тип: 0=окно, 1=одинарная дверь, 2=двойная дверь",String(current?.type??0));if(type===null)return;
    const numericType=Number(type);if(![0,1,2].includes(numericType)){alert("Допустимый тип: 0, 1 или 2");return}
    const actuatorCount=prompt("Количество актуаторов: 2, 4, 6 или 8",String(current?.actuatorCount??2));if(actuatorCount===null)return;
    const numericCount=Number(actuatorCount);if(![2,4,6,8].includes(numericCount)){alert("Допустимо 2, 4, 6 или 8 актуаторов");return}
    const mask=prompt("Маска D-M9P: 0=все D-M9N, 63=все D-M9P",String(current?.reedPolarityMask??0));if(mask===null)return;const numericMask=Number(mask);if(!Number.isInteger(numericMask)||numericMask<0||numericMask>63){alert("Маска D-M9P должна быть от 0 до 63");return}
    const button=document.querySelector(`[data-provision-uid="${node.uid}"]`);if(button){button.disabled=true;button.textContent="Запись..."}
    try{
      const started=await(await post("/api/provision",{uid:node.uid,cabinetId:numericCabinet,name,type:numericType,actuatorCount:numericCount,reedPolarityMask:numericMask})).json();
      const status=await waitProvision(started.token);
      alert(`EEPROM записана и проверена. CAN ${status.cabinetId}, ревизия ${status.configRevision}.`);
      await loadObjects();await discover();
    }catch(error){const messages={cabinet_id_in_use:"Этот CAN-номер уже занят другим шкафом",object_moving:"Сначала остановите все актуаторы",provision_busy:"Другая EEPROM уже программируется",uid_not_discovered:"Контроллер больше не отвечает",stm32_update_required:"Сначала установите на STM32 универсальную прошивку alpha.9 или новее",can_send_failed:"Не удалось отправить команду по CAN"};alert(messages[error.message]||error.message||"Ошибка перенастройки");if(button){button.disabled=false;button.textContent=reconfigure?"Перенастроить":"Настроить"}}
  }
  async function restoreNode(node,backups){
    if(!backups.length){alert("В ESP32 пока нет резервных копий EEPROM");return}
    const choices=backups.map(b=>`${b.cabinetId}: ${b.name} (${b.actuatorCount} прив.)`).join("\n");
    const selected=prompt(`Введите номер старой платы:\n${choices}`,String(backups[0].cabinetId));if(selected===null)return;
    const cabinetId=Number(selected),backup=backups.find(b=>b.cabinetId===cabinetId);
    if(!backup){alert("Резервная копия этого номера не найдена");return}
    if(!confirm(`Записать конфигурацию «${backup.name}» из платы №${cabinetId} в новую EEPROM?`))return;
    try{
      const started=await(await post("/api/eeprom/restore",{uid:node.uid,cabinetId})).json();
      const status=await waitProvision(started.token);
      alert(`EEPROM восстановлена. Плата №${status.cabinetId}, ревизия ${status.configRevision}.`);
      await loadObjects();await discover();
    }catch(error){
      const messages={backup_not_found:"Резервная копия не найдена",target_already_configured:"Выбранная новая плата уже настроена",backup_object_online:"Старая плата с этим номером сейчас работает",cabinet_id_in_use:"Этот номер уже отвечает в CAN",stm32_update_required:"Обновите прошивку STM32 новой платы",can_send_failed:"Не удалось отправить резерв по CAN"};
      alert(messages[error.message]||error.message||"Восстановление не выполнено");
    }
  }
  async function discover(){await post("/api/discover",{});await wait(700);const [nodeResponse,backupResponse]=await Promise.all([api("/api/discovery"),api("/api/eeprom/backups")]);const nodes=(await nodeResponse.json()).nodes||[],backups=(await backupResponse.json()).backups||[];$("discoveryList").innerHTML=nodes.map(n=>`<div class="remote-row"><code>${esc(n.uid)}</code><span>${n.configured?'CAN '+n.cabinetId:'Не настроен'}</span><span>FW ${n.firmware}</span><button data-provision-uid="${esc(n.uid)}">${n.configured?'Перенастроить':'Настроить'}</button>${!n.configured&&backups.length?`<button data-restore-uid="${esc(n.uid)}">Восстановить</button>`:''}</div>`).join("")||'<div class="empty">Контроллеры не ответили</div>';document.querySelectorAll("[data-provision-uid]").forEach(button=>{const node=nodes.find(n=>n.uid===button.dataset.provisionUid);button.onclick=()=>provisionNode(node)});document.querySelectorAll("[data-restore-uid]").forEach(button=>{const node=nodes.find(n=>n.uid===button.dataset.restoreUid);button.onclick=()=>restoreNode(node,backups)})}
  async function restoreSystemBackup(){
    const file=$("backupFile").files[0];if(!file){alert("Выберите файл резервной копии");return}
    if(!confirm("Заменить все настройки ESP32 и резервные копии EEPROM данными из файла? Все актуаторы должны быть остановлены."))return;
    const button=$("restoreBackup");button.disabled=true;button.textContent="Проверка...";
    try{
      const form=new FormData();form.append("backup",file);
      const response=await fetch("/api/backup/import",{method:"POST",body:form,cache:"no-store"});
      let result={};try{result=await response.json()}catch(e){}
      if(!response.ok)throw Error(result.error||String(response.status));
      alert("Настройки и резервные копии EEPROM восстановлены. ESP32 перезагружается.");
      setTimeout(()=>location.reload(),4000);
    }catch(error){
      const messages={system_busy:"Сначала остановите все актуаторы",backup_size:"Неверный размер файла резервной копии",backup_invalid:"Файл повреждён, имеет неверную версию или не принадлежит этой системе"};
      alert(messages[error.message]||error.message||"Восстановление не выполнено");
      button.disabled=false;button.textContent="Восстановить";
    }
  }
  async function loadSettings(){try{const j=await(await api("/api/settings")).json();$("systemName").value=j.systemName||"";$("canRate").value=String(j.canRate||500000)}catch(e){}}
  async function saveSettings(){await post("/api/settings",{systemName:$("systemName").value});$("systemText").textContent="Настройки сохранены"}
  const renderDetailBase=renderDetail;renderDetail=o=>{renderDetailBase(o);$("detailBody").insertAdjacentHTML("beforeend",capConfigurationHtml(o));bindCapConfiguration()};
  document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tabs button").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll(".view").forEach(x=>x.classList.toggle("active",x.id===b.dataset.view));if(b.dataset.view==="events")loadEvents();if(b.dataset.view==="remotes")loadRemotes();if(b.dataset.view==="settings")loadSettings()});
  $("stopAll").onclick=stopAll;$("learnRemote").onclick=async()=>{await post("/api/remotes/learn",{});loadRemotes()};$("clearEvents").onclick=async()=>{await post("/api/events/clear",{});loadEvents()};$("discover").onclick=discover;$("saveSettings").onclick=saveSettings;$("downloadBackup").onclick=()=>{location.href="/api/backup/export"};$("restoreBackup").onclick=restoreSystemBackup;
  loadObjects();setInterval(loadObjects,1000);
  </script>
</body>
</html>

)WINDOWUI";

/**
 * SANJEEVINI - Voice-First Snakebite Emergency Assistance Platform
 * Interactive Channel Simulators & Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initChannelTabs();
  initFlutterSimulator();
  initIvrSimulator();
  initWhatsAppSimulator();
  initFacilitySearchDemo();
  initApiTabs();
});

/* ==========================================================================
   1. CHANNEL TABS SWITCHER
   ========================================================================== */
function initChannelTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }
    });
  });
}

/* ==========================================================================
   2. FLUTTER MOBILE APP SIMULATOR
   ========================================================================== */
function initFlutterSimulator() {
  const patientBtn = document.getElementById('flutter-tab-patient');
  const ashaBtn = document.getElementById('flutter-tab-asha');
  const patientView = document.getElementById('flutter-patient-view');
  const ashaView = document.getElementById('flutter-asha-view');
  const gpsTriggerBtn = document.getElementById('flutter-gps-btn');
  const gpsStatusText = document.getElementById('flutter-gps-status');
  const facilityContainer = document.getElementById('flutter-facility-list');
  const ashaUpdateForm = document.getElementById('asha-readiness-form');
  const ashaSyncStatus = document.getElementById('asha-sync-msg');

  // Toggle Patient vs ASHA View
  if (patientBtn && ashaBtn && patientView && ashaView) {
    patientBtn.addEventListener('click', () => {
      patientBtn.classList.add('active');
      ashaBtn.classList.remove('active');
      patientView.style.display = 'flex';
      ashaView.style.display = 'none';
    });

    ashaBtn.addEventListener('click', () => {
      ashaBtn.classList.add('active');
      patientBtn.classList.remove('active');
      patientView.style.display = 'none';
      ashaView.style.display = 'flex';
    });
  }

  // GPS Simulation in Flutter
  if (gpsTriggerBtn) {
    gpsTriggerBtn.addEventListener('click', () => {
      gpsStatusText.innerHTML = '<span style="color:#00e5a3;">📡 Requesting phone GPS fix...</span>';
      gpsTriggerBtn.disabled = true;

      setTimeout(() => {
        const simulatedLat = 26.8467;
        const simulatedLon = 80.9462;
        gpsStatusText.innerHTML = `<span style="color:#00e5a3;">✓ Location locked: ${simulatedLat}°N, ${simulatedLon}°E (±12m)</span>`;
        gpsTriggerBtn.disabled = false;

        // Render mock facilities calculated from BallTree
        if (facilityContainer) {
          facilityContainer.innerHTML = `
            <div class="facility-card-mini">
              <div class="facility-card-header">
                <span class="facility-title">CHC Mohanlalganj</span>
                <span class="facility-badge-unknown">ASV UNKNOWN</span>
              </div>
              <div class="facility-meta">Community Health Centre • Lucknow, UP</div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.3rem;">
                <span style="font-weight:700; color:#38bdf8; font-size:0.8rem;">📍 4.2 km away</span>
                <a href="#map" class="directions-link">Get Directions ↗</a>
              </div>
            </div>

            <div class="facility-card-mini">
              <div class="facility-card-header">
                <span class="facility-title">PHC Gosainganj</span>
                <span class="facility-badge-unknown">ASV UNKNOWN</span>
              </div>
              <div class="facility-meta">Primary Health Centre • Lucknow, UP</div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.3rem;">
                <span style="font-weight:700; color:#38bdf8; font-size:0.8rem;">📍 8.7 km away</span>
                <a href="#map" class="directions-link">Get Directions ↗</a>
              </div>
            </div>

            <div class="facility-card-mini">
              <div class="facility-card-header">
                <span class="facility-title">CHC Sarojini Nagar</span>
                <span class="facility-badge-verified">ASV VERIFIED</span>
              </div>
              <div class="facility-meta">Verified 45m ago by ASHA Sunita D.</div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.3rem;">
                <span style="font-weight:700; color:#38bdf8; font-size:0.8rem;">📍 14.1 km away</span>
                <a href="#map" class="directions-link">Get Directions ↗</a>
              </div>
            </div>
          `;
        }
      }, 900);
    });
  }

  // ASHA Form Submission Simulation
  if (ashaUpdateForm) {
    ashaUpdateForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const statusVal = document.getElementById('asha-asv-status').value;
      const vialsVal = document.getElementById('asha-vials-count').value || '0';

      ashaSyncStatus.innerHTML = `<span style="color:#00e5a3;">✓ Syncing to FastAPI Backend...</span>`;

      setTimeout(() => {
        ashaSyncStatus.innerHTML = `
          <div style="background:rgba(0,229,163,0.15); border:1px solid #00e5a3; padding:0.6rem; border-radius:6px; color:#00e5a3; font-size:0.75rem;">
            ✓ Facility record updated! Status: <strong>${statusVal}</strong> (${vialsVal} vials recorded). Timestamp: Just now.
          </div>
        `;
      }, 700);
    });
  }
}

/* ==========================================================================
   3. IVR VOICE TELEPHONY CALL SIMULATOR (WITH WEB SPEECH SYNTHESIS)
   ========================================================================== */
function initIvrSimulator() {
  const callStartBtn = document.getElementById('ivr-start-call');
  const callEndBtn = document.getElementById('ivr-end-call');
  const callStatusBadge = document.getElementById('ivr-status-badge');
  const transcriptBox = document.getElementById('ivr-transcript');
  const waveBars = document.querySelectorAll('.wave-bar');
  const dialBtns = document.querySelectorAll('.dialpad-btn');

  let callActive = false;
  let callStep = 0;

  function speakText(text, callback) {
    // Animate waveform
    waveBars.forEach(b => b.classList.add('speaking'));

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.onend = () => {
        waveBars.forEach(b => b.classList.remove('speaking'));
        if (callback) callback();
      };
      utterance.onerror = () => {
        waveBars.forEach(b => b.classList.remove('speaking'));
        if (callback) callback();
      };
      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => {
        waveBars.forEach(b => b.classList.remove('speaking'));
        if (callback) callback();
      }, 2500);
    }
  }

  function addTranscript(sender, text, isIvr = false) {
    if (!transcriptBox) return;
    const line = document.createElement('div');
    line.className = 'transcript-line ' + (isIvr ? 'transcript-ivr' : 'transcript-caller');
    line.innerHTML = `<strong>${sender}:</strong> ${text}`;
    transcriptBox.appendChild(line);
    transcriptBox.scrollTop = transcriptBox.scrollHeight;
  }

  if (callStartBtn) {
    callStartBtn.addEventListener('click', () => {
      if (callActive) return;
      callActive = true;
      callStep = 1;
      callStatusBadge.innerHTML = '<span class="pulse-dot" style="background:#00e5a3;"></span> CALL CONNECTED (00:04)';
      callStatusBadge.style.color = '#00e5a3';
      transcriptBox.innerHTML = '';

      const greeting = "Namaste. Welcome to Sanjeevini Snakebite Emergency Assistance. For Hindi press 1. For English press 2.";
      addTranscript("IVR System", greeting, true);
      speakText(greeting);
    });
  }

  if (callEndBtn) {
    callEndBtn.addEventListener('click', () => {
      if (!callActive) return;
      callActive = false;
      callStep = 0;
      callStatusBadge.innerHTML = '<span class="pulse-dot" style="background:#ffaa00;"></span> CALL ENDED';
      callStatusBadge.style.color = '#ffaa00';
      waveBars.forEach(b => b.classList.remove('speaking'));
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      addTranscript("System", "Call disconnected by caller.");
    });
  }

  // Dialpad handling
  dialBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (!callActive) {
        alert("Please tap the Green Call Button first to simulate dialing in.");
        return;
      }
      const num = btn.getAttribute('data-num');
      addTranscript("Caller Keypad", `Pressed [${num}]`);

      handleIvrDialInput(num);
    });
  });

  function handleIvrDialInput(key) {
    if (callStep === 1) {
      if (key === '1') {
        callStep = 2;
        const msg = "Hindi chuni gayi. Kripya dhyan dein: Mareez ko shant rakhein, daudein nahi. Kaate hue ang ko hilayein nahi. Press 1 for nearby hospital, Press 2 for first aid.";
        addTranscript("IVR System (Hindi)", msg, true);
        speakText("Hindi chuni gayi. Mareez ko shant rakhein. Kaate hue ang ko na hilayein.");
      } else {
        callStep = 2;
        const msg = "English selected. Emergency Protocol: Keep patient completely still. Do NOT tie tourniquet or cut wound. Press 1 to find nearest hospital, Press 2 to listen to first aid steps.";
        addTranscript("IVR System", msg, true);
        speakText(msg);
      }
    } else if (callStep === 2) {
      if (key === '1') {
        callStep = 3;
        const msg = "Searching facilities near your registered cell tower. Nearest is CHC Mohanlalganj, 4 kilometers away. Emergency alert has been dispatched to local ASHA worker.";
        addTranscript("IVR System", msg, true);
        speakText(msg);
      } else {
        const msg = "First Aid Warning: Do NOT cut, suck, or apply ice. Immobilize bitten limb with a splint. Reach nearest health centre immediately.";
        addTranscript("IVR System", msg, true);
        speakText(msg);
      }
    }
  }
}

/* ==========================================================================
   4. WHATSAPP CHATBOT SIMULATOR
   ========================================================================== */
function initWhatsAppSimulator() {
  const chatCanvas = document.getElementById('wa-chat-canvas');
  const inputEl = document.getElementById('wa-user-input');
  const sendBtn = document.getElementById('wa-send-btn');
  const actionBtns = document.querySelectorAll('.wa-action-btn');

  function appendMessage(text, isUser = false) {
    if (!chatCanvas) return;
    const bubble = document.createElement('div');
    bubble.className = `wa-bubble ${isUser ? 'wa-bubble-user' : 'wa-bubble-bot'}`;
    bubble.innerHTML = text;
    chatCanvas.appendChild(bubble);
    chatCanvas.scrollTop = chatCanvas.scrollHeight;
  }

  function handleBotResponse(query) {
    const q = query.toLowerCase();

    // Typing simulation delay
    setTimeout(() => {
      if (q.includes('location') || q.includes('gps') || q.includes('nearby') || q.includes('hospital')) {
        appendMessage(`
          🏥 <strong>Nearby Facilities Identified (Lucknow Sector)</strong><br><br>
          1. <strong>CHC Mohanlalganj</strong> (4.2 km)<br>
          • Type: Community Health Centre<br>
          • ASV Status: <em>UNKNOWN / UNVERIFIED</em><br>
          • Emergency Contact: 0522-2970101<br>
          <a href="#map" style="color:#25d366; text-decoration:underline;">[📍 Open Directions in Maps]</a><br><br>
          2. <strong>PHC Gosainganj</strong> (8.7 km)<br>
          • Type: Primary Health Centre<br>
          • ASV Status: <em>UNKNOWN</em><br><br>
          ⚠️ <em>Note: Always call ahead or dial 108 Ambulance while in transit.</em>
        `);
      } else if (q.includes('first aid') || q.includes('help') || q.includes('bitten')) {
        appendMessage(`
          🆘 <strong>CRITICAL FIRST AID PROTOCOL (WHO / NAPSE)</strong><br><br>
          ✅ <strong>DO:</strong><br>
          • Keep the person calm & still. Movement spreads venom faster.<br>
          • Immobilize the bitten limb using a cloth/splint.<br>
          • Remove rings, watches, or tight shoes before swelling begins.<br>
          • Transport immediately to nearest PHC/CHC.<br><br>
          ❌ <strong>NEVER:</strong><br>
          • DO NOT cut or incise the wound.<br>
          • DO NOT suck venom out.<br>
          • DO NOT tie tight tourniquets or ropes.<br>
          • DO NOT apply ice or herbal pastes.
        `);
      } else if (q.includes('asha') || q.includes('worker') || q.includes('contact')) {
        appendMessage(`
          👩‍⚕️ <strong>Local ASHA Emergency Coordination</strong><br><br>
          Assigned Area: Sector 4, Mohanlalganj<br>
          • ASHA Worker: Smt. Sunita Devi<br>
          • Status: On-call for snakebite transit assistance<br>
          • Notification ping dispatched with your location pin!
        `);
      } else {
        appendMessage(`
          Sanjeevini Emergency Bot received: "${query}"<br><br>
          Please select an emergency option below:<br>
          1. 📍 Send Location for Nearby Hospital<br>
          2. 🆘 Safe First Aid Guide<br>
          3. 📞 Call 108 Ambulance Dispatch
        `);
      }
    }, 500);
  }

  if (sendBtn && inputEl) {
    sendBtn.addEventListener('click', () => {
      const val = inputEl.value.trim();
      if (!val) return;
      appendMessage(val, true);
      inputEl.value = '';
      handleBotResponse(val);
    });

    inputEl.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendBtn.click();
      }
    });
  }

  actionBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      appendMessage(prompt, true);
      handleBotResponse(prompt);
    });
  });
}

/* ==========================================================================
   5. FACILITY SEARCH DEMO (HAVERSINE BALLTREE CONCEPT)
   ========================================================================== */
function initFacilitySearchDemo() {
  const searchInput = document.getElementById('demo-location-input');
  const searchBtn = document.getElementById('demo-search-btn');
  const resultsContainer = document.getElementById('demo-search-results');

  const facilityDatabase = [
    { name: "CHC Mohanlalganj", state: "Uttar Pradesh", district: "Lucknow", type: "CHC", lat: 26.671, lon: 80.982, dist: "4.2 km", status: "UNKNOWN" },
    { name: "PHC Gosainganj", state: "Uttar Pradesh", district: "Lucknow", type: "PHC", lat: 26.772, lon: 81.121, dist: "8.7 km", status: "UNKNOWN" },
    { name: "CHC Nancowry", state: "A & N Islands", district: "Nicobars", type: "CHC", lat: 8.012, lon: 93.524, dist: "12.4 km", status: "UNKNOWN" },
    { name: "CHC Keshod", state: "Gujarat", district: "Junagadh", type: "CHC", lat: 21.303, lon: 70.252, dist: "6.1 km", status: "UNKNOWN" },
    { name: "PHC Aland", state: "Karnataka", district: "Kalaburagi", type: "PHC", lat: 17.561, lon: 76.568, dist: "9.3 km", status: "UNKNOWN" },
    { name: "CHC Baramati", state: "Maharashtra", district: "Pune", type: "CHC", lat: 18.152, lon: 74.577, dist: "5.8 km", status: "UNKNOWN" },
    { name: "PHC Cheyyar", state: "Tamil Nadu", district: "Tiruvannamalai", type: "PHC", lat: 12.658, lon: 79.542, dist: "7.4 km", status: "UNKNOWN" }
  ];

  function renderFacilities(list) {
    if (!resultsContainer) return;
    if (list.length === 0) {
      resultsContainer.innerHTML = '<div style="padding:1rem; text-align:center; color:#94a3b8;">No facilities matching your filter. Try "Lucknow", "Gujarat", "Pune", or "PHC".</div>';
      return;
    }

    resultsContainer.innerHTML = list.map(fac => `
      <div class="demo-result-item">
        <div>
          <div class="demo-res-title">${fac.name} (${fac.type})</div>
          <div class="demo-res-location">${fac.district}, ${fac.state} • Coordinates: ${fac.lat}°N, ${fac.lon}°E</div>
          <div style="margin-top:0.3rem;">
            <span class="facility-badge-unknown">ASV STOCK: ${fac.status} (UNVERIFIED)</span>
          </div>
        </div>
        <div class="demo-res-right">
          <div class="demo-res-dist">${fac.dist}</div>
          <span style="font-size:0.75rem; color:#64748b;">Direct Haversine</span>
        </div>
      </div>
    `).join('');
  }

  if (searchBtn && searchInput) {
    searchBtn.addEventListener('click', () => {
      const q = searchInput.value.trim().toLowerCase();
      if (!q) {
        renderFacilities(facilityDatabase);
        return;
      }
      const filtered = facilityDatabase.filter(f => 
        f.name.toLowerCase().includes(q) ||
        f.state.toLowerCase().includes(q) ||
        f.district.toLowerCase().includes(q) ||
        f.type.toLowerCase().includes(q)
      );
      renderFacilities(filtered);
    });

    searchInput.addEventListener('input', () => {
      searchBtn.click();
    });
  }
}

/* ==========================================================================
   6. API SPECIFICATION TABS
   ========================================================================== */
function initApiTabs() {
  const apiTabs = document.querySelectorAll('.api-tab-item');
  const codeBlocks = {
    nearby: `{
  <span class="token-key">"query_latitude"</span>: <span class="token-num">26.8467</span>,
  <span class="token-key">"query_longitude"</span>: <span class="token-num">80.9462</span>,
  <span class="token-key">"search_radius_km"</span>: <span class="token-num">30.0</span>,
  <span class="token-key">"total_found"</span>: <span class="token-num">1</span>,
  <span class="token-key">"facilities"</span>: [
    {
      <span class="token-key">"facility_id"</span>: <span class="token-str">"HCF-014923"</span>,
      <span class="token-key">"facility_name"</span>: <span class="token-str">"CHC Mohanlalganj"</span>,
      <span class="token-key">"facility_type"</span>: <span class="token-str">"CHC"</span>,
      <span class="token-key">"distance_km"</span>: <span class="token-num">4.2</span>,
      <span class="token-key">"asv_stock_status"</span>: <span class="token-str">"UNKNOWN"</span>,
      <span class="token-key">"asv_quantity_vials"</span>: <span class="token-bool">null</span>,
      <span class="token-key">"asv_verification_source"</span>: <span class="token-str">"NOT_VERIFIED"</span>
    }
  ],
  <span class="token-key">"safety_disclaimer"</span>: <span class="token-str">"ASV availability is unverified in baseline facility directories. Always confirm directly or through 108 emergency ambulance dispatch."</span>
}`,
    asvStatus: `{
  <span class="token-key">"facility_id"</span>: <span class="token-str">"HCF-014923"</span>,
  <span class="token-key">"facility_name"</span>: <span class="token-str">"CHC Mohanlalganj"</span>,
  <span class="token-key">"asv_stock_status"</span>: <span class="token-str">"AVAILABLE"</span>,
  <span class="token-key">"asv_quantity_vials"</span>: <span class="token-num">14</span>,
  <span class="token-key">"verification_source"</span>: <span class="token-str">"TELEPHONE_CALL"</span>,
  <span class="token-key">"last_verification_timestamp"</span>: <span class="token-str">"2026-10-18T04:15:00Z"</span>,
  <span class="token-key">"safety_disclaimer"</span>: <span class="token-str">"Anti-Snake Venom (ASV) availability is NOT GUARANTEED unless confirmed by live operational update. Do not delay transport."</span>
}`,
    emergencyLocation: `{
  <span class="token-key">"emergency_id"</span>: <span class="token-str">"EMG-20261018-0921"</span>,
  <span class="token-key">"caller_channel"</span>: <span class="token-str">"FLUTTER_GPS"</span>,
  <span class="token-key">"latitude"</span>: <span class="token-num">26.846712</span>,
  <span class="token-key">"longitude"</span>: <span class="token-num">80.946288</span>,
  <span class="token-key">"accuracy_meters"</span>: <span class="token-num">12.5</span>,
  <span class="token-key">"patient_status"</span>: <span class="token-str">"SUSPECTED_ENVENOMATION"</span>,
  <span class="token-key">"asha_notified"</span>: <span class="token-bool">true</span>
}`
  };

  const codeDisplay = document.getElementById('api-code-content');

  apiTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      apiTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const key = tab.getAttribute('data-endpoint');
      if (codeDisplay && codeBlocks[key]) {
        codeDisplay.innerHTML = `<pre><code>${codeBlocks[key]}</code></pre>`;
      }
    });
  });
}

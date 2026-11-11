/* ============================================================
   Proyecto Lenguajes Formales — Lógica del frontend
   ============================================================ */

const API = '/api';
let GRAMMATICAS = [];
let SELECCIONADA = null;

// ---------------------------------------------------------------------------
// InicializaciÃ³n
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    await cargarGramaticas();
    inicializarSelector();

    const btnRefresh = document.getElementById('btn-refresh-grammars');
    if (btnRefresh) btnRefresh.addEventListener('click', async () => {
        await cargarGramaticas();
        inicializarSelector();
    });

    // Rutas por pÃ¡gina
    const path = window.location.pathname;
    if (path === '/item1') initItem1();
    else if (path === '/item2') initItem2();
    else if (path === '/item3') initItem3();
});

// ---------------------------------------------------------------------------
// GramÃ¡ticas (carga automÃ¡tica desde backend)
// ---------------------------------------------------------------------------
async function cargarGramaticas() {
    try {
        const res = await fetch(`${API}/grammars`);
        const data = await res.json();
        GRAMMATICAS = data.gramaticas || [];
        if (GRAMMATICAS.length > 0 && !SELECCIONADA) {
            SELECCIONADA = GRAMMATICAS[0].id;
        }
    } catch (e) {
        console.error('Error cargando gramÃ¡ticas:', e);
        mostrarError('No se pudieron cargar las gramÃ¡ticas desde el servidor.');
    }
}

function inicializarSelector() {
    const sel = document.getElementById('grammar-select');
    const info = document.getElementById('grammar-info');
    if (!sel) return;

    sel.innerHTML = '';
    GRAMMATICAS.forEach(g => {
        const o = document.createElement('option');
        o.value = g.id;
        o.textContent = g.nombre + ' (inicial: ' + g.simbolo_inicial + ')';
        sel.appendChild(o);
    });

    if (SELECCIONADA) sel.value = SELECCIONADA;
    actualizarInfoSelector();

    sel.addEventListener('change', (e) => {
        SELECCIONADA = e.target.value;
        actualizarInfoSelector();
    });
}

function actualizarInfoSelector() {
    const info = document.getElementById('grammar-info');
    const sel = document.getElementById('grammar-select');
    if (!info || !sel) return;
    const g = GRAMMATICAS.find(x => x.id === sel.value);
    if (!g) { info.textContent = ''; return; }
    const ll1 = g.es_ll1 === true ? 'sí' : (g.es_ll1 === false ? 'no' : '?');
    const slr = g.es_slr1 === true ? 'sí' : (g.es_slr1 === false ? 'no' : '?');
    info.textContent = `Terminales: ${g.terminales.join(', ')} | No terminales: ${g.no_terminales.join(', ')} | LL(1): ${ll1} | SLR(1): ${slr}`;
}

function getSeleccionada() {
    return GRAMMATICAS.find(g => g.id === SELECCIONADA) || null;
}

// ---------------------------------------------------------------------------
// Utilidades UI
// ---------------------------------------------------------------------------
function mostrar(id, mostrar) {
    const el = document.getElementById(id);
    if (el) el.style.display = mostrar ? '' : 'none';
}

function mostrarError(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.style.display = '';
}

function ocultarError(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

function escapeHtml(t) {
    if (t == null) return '';
    return String(t)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// ---------------------------------------------------------------------------
// ÍTEM 1 — FIRST y FOLLOW
// ---------------------------------------------------------------------------
function initItem1() {
    const btn = document.getElementById('btn-load-ff');
    if (!btn) return;
    btn.addEventListener('click', async () => {
        const g = getSeleccionada();
        if (!g) { mostrarError('ff-error', 'Selecciona una gramÃ¡tica.'); return; }
        ocultarError('ff-error');
        mostrar('ff-loading', true);
        mostrar('ff-result', false);

        try {
            const res = await fetch(`${API}/first-follow`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grammar_id: g.id })
            });
            const data = await res.json();
            if (!res.ok) { mostrarError('ff-error', data.error || 'Error'); mostrar('ff-loading', false); return; }
            renderItem1(data);
            mostrar('ff-loading', false);
            mostrar('ff-result', true);
        } catch (e) {
            mostrarError('ff-error', 'Error de red: ' + e.message);
            mostrar('ff-loading', false);
        }
    });
}

function renderItem1(data) {
    document.getElementById('ff-grammar-summary').innerHTML =
        `<strong>GramÃ¡tica:</strong> ${escapeHtml(data.gramatica)} &nbsp;|&nbsp; <strong>Símbolo inicial:</strong> ${escapeHtml(data.simbolo_inicial)}`;

    // Producciones
    const tbody = document.getElementById('ff-producciones-body');
    tbody.innerHTML = '';
    (data.producciones || []).forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${escapeHtml(p.cabeza)}</strong></td><td>${escapeHtml(p.cuerpo)}</td>`;
        tbody.appendChild(tr);
    });

    // FIRST
    const fbody = document.getElementById('ff-first-body');
    fbody.innerHTML = '';
    for (const nt of data.no_terminales || []) {
        const vals = data.first[nt] || [];
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${escapeHtml(nt)}</strong></td><td>{${vals.map(v => escapeHtml(v)).join(', ') || '&epsilon;'}}</td>`;
        fbody.appendChild(tr);
    }

    // FOLLOW
    const fbdy = document.getElementById('ff-follow-body');
    fbdy.innerHTML = '';
    for (const nt of data.no_terminales || []) {
        const vals = data.follow[nt] || [];
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><strong>${escapeHtml(nt)}</strong></td><td>{${vals.map(v => escapeHtml(v)).join(', ') || '&epsilon;'}}</td>`;
        fbdy.appendChild(tr);
    }
}

// ---------------------------------------------------------------------------
// ÍTEM 2 — LL(1) y SLR(1)
// ---------------------------------------------------------------------------
function initItem2() {
    const btnLL1 = document.getElementById('btn-load-ll1');
    const btnSLR = document.getElementById('btn-load-slr1');

    if (btnLL1) btnLL1.addEventListener('click', async () => {
        await cargarModulo('ll1');
    });
    if (btnSLR) btnSLR.addEventListener('click', async () => {
        await cargarModulo('slr1');
    });

    const btnSimLL1 = document.getElementById('btn-sim-ll1');
    if (btnSimLL1) btnSimLL1.addEventListener('click', async () => {
        const inp = document.getElementById('ll1-input').value.trim();
        const g = getSeleccionada();
        if (!g) return;
        ocultarError('i2-error');
        mostrar('i2-loading', true);
        try {
            const res = await fetch(`${API}/ll1`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grammar_id: g.id, input: inp })
            });
            const data = await res.json();
            if (!res.ok) { mostrarError('i2-error', data.error || 'Error'); mostrar('i2-loading', false); return; }
            renderSimLL1(data.simulacion);
            mostrar('i2-loading', false);
        } catch (e) {
            mostrarError('i2-error', 'Error de red: ' + e.message);
            mostrar('i2-loading', false);
        }
    });

    const btnSimSLR = document.getElementById('btn-sim-slr1');
    if (btnSimSLR) btnSimSLR.addEventListener('click', async () => {
        const inp = document.getElementById('slr1-input').value.trim();
        const g = getSeleccionada();
        if (!g) return;
        ocultarError('i2-error');
        mostrar('i2-loading', true);
        try {
            const res = await fetch(`${API}/slr1`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grammar_id: g.id, input: inp })
            });
            const data = await res.json();
            if (!res.ok) { mostrarError('i2-error', data.error || 'Error'); mostrar('i2-loading', false); return; }
            renderSimSLR(data.simulacion);
            mostrar('i2-loading', false);
        } catch (e) {
            mostrarError('i2-error', 'Error de red: ' + e.message);
            mostrar('i2-loading', false);
        }
    });
}

async function cargarModulo(tipo) {
    const g = getSeleccionada();
    if (!g) { mostrarError('i2-error', 'Selecciona una gramÃ¡tica.'); return; }
    ocultarError('i2-error');
    mostrar('i2-loading', true);

    try {
        const res = await fetch(`${API}/${tipo === 'll1' ? 'll1' : 'slr1'}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grammar_id: g.id })
        });
        const data = await res.json();
        if (!res.ok) { mostrarError('i2-error', data.error || 'Error'); mostrar('i2-loading', false); return; }

        if (tipo === 'll1') {
            mostrar('i2-ll1', true);
            mostrar('i2-slr1', false);
            renderLL1(data);
        } else {
            mostrar('i2-slr1', true);
            mostrar('i2-ll1', false);
            renderSLR1(data);
        }
        mostrar('i2-loading', false);
    } catch (e) {
        mostrarError('i2-error', 'Error de red: ' + e.message);
        mostrar('i2-loading', false);
    }
}

function renderLL1(data) {
    // Clasificación
    const cl = document.getElementById('ll1-clasificacion');
    cl.innerHTML = `
        <div class="kv-item"><span class="k">Es LL(1)</span><span class="v">${data.es_ll1 === true ? 'SÍ' : 'NO'}</span></div>
        <div class="kv-item"><span class="k">Gramática</span><span class="v">${escapeHtml(data.gramatica)}</span></div>
    `;

    // Conflictos
    const conf = document.getElementById('ll1-conflictos');
    if (!data.conflictos || data.conflictos.length === 0) {
        conf.innerHTML = '<span style="color:var(--success); font-weight:700;">Sin conflictos LL(1).</span>';
    } else {
        conf.innerHTML = '<ul style="margin-left:1.2rem;">' +
            data.conflictos.map(c => `<li>${escapeHtml(c.non_terminal)}: ${escapeHtml(c.type)} en sÃ­mbolos {${c.symbols.map(escapeHtml).join(', ')}}</li>`).join('') +
            '</ul>';
    }

    // Tabla predictiva
    const wrapper = document.getElementById('ll1-tabla-wrapper');
    const terminals = data.terminales || [];
    const nts = data.no_terminales || [];
    const tabla = data.tabla || {};

    let html = '<table class="data-table"><thead><tr><th>A \\ a</th>';
    terminals.forEach(t => html += `<th>${escapeHtml(t)}</th>`);
    html += '</tr></thead><tbody>';
    nts.forEach(A => {
        html += `<tr><td><strong>${escapeHtml(A)}</strong></td>`;
        terminals.forEach(a => {
            const celdas = tabla[A] && tabla[A][a] ? tabla[A][a] : [];
            let contenido = '';
            if (celdas.length === 0) contenido = '&mdash;';
            else if (celdas.length === 1) contenido = escapeHtml(celdas[0]);
            else {
                contenido = celdas.map(c => escapeHtml(c)).join('; ');
                contenido += ' <span style="color:var(--error); font-weight:700;">[CONFLICTO]</span>';
            }
            html += `<td>${contenido}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    wrapper.innerHTML = html;
}

function renderSimLL1(sim) {
    const cont = document.getElementById('ll1-sim-result');
    if (!sim) { cont.style.display = 'none'; return; }
    cont.style.display = '';
    let html = `<p><strong>Entrada:</strong> ${escapeHtml(sim.entrada)} &nbsp;|&nbsp; <strong>Resultado:</strong> <span style="color:${sim.aceptado ? 'var(--success)' : 'var(--error)'}; font-weight:700;">${sim.aceptado ? 'ACEPTADA' : 'RECHAZADA'}</span></p>`;
    html += '<table class="data-table"><thead><tr><th>Paso</th><th>Pila</th><th>Entrada restante</th><th>Acción</th></tr></thead><tbody>';
    (sim.pasos || []).forEach(p => {
        const accion = escapeHtml(p.action || '');
        let cls = '';
        if (accion.includes('ACEPTAR')) cls = 'style="color:var(--success);font-weight:700"';
        else if (accion.includes('ERROR')) cls = 'style="color:var(--error);font-weight:700"';
        html += `<tr><td>${p.step}</td><td>${escapeHtml((p.stack||[]).join(' '))}</td><td>${escapeHtml((p.remaining||[]).join(' '))}</td><td ${cls}>${accion}</td></tr>`;
    });
    html += '</tbody></table>';
    cont.innerHTML = html;
}

// ---------------- SLR(1) ----------------
function renderSLR1(data) {
    // Clasificación
    const cl = document.getElementById('slr1-clasificacion');
    cl.innerHTML = `
        <div class="kv-item"><span class="k">Es SLR(1)</span><span class="v">${data.es_slr1 === true ? 'SÍ' : 'NO'}</span></div>
        <div class="kv-item"><span class="k">Símbolo aumentado</span><span class="v">${escapeHtml(data.simbolo_aumento)}</span></div>
        <div class="kv-item"><span class="k">Estados</span><span class="v">${data.num_estados}</span></div>
    `;
    document.getElementById('slr1-aug-start').textContent = data.simbolo_aumento;

    // Conflictos
    const conf = document.getElementById('slr1-conflictos');
    if (!data.conflictos || data.conflictos.length === 0) {
        conf.innerHTML = '<span style="color:var(--success); font-weight:700;">Sin conflictos SLR(1).</span>';
    } else {
        conf.innerHTML = '<ul style="margin-left:1.2rem;">' +
            data.conflictos.map(c => `<li>Estado ${c.state}, sÃ­mbolo '${escapeHtml(c.symbol)}': ${escapeHtml(c.type)}</li>`).join('') +
            '</ul>';
    }

    // Estados e ítems LR(0)
    const ew = document.getElementById('slr1-estados-wrapper');
    let html = '<table class="data-table"><thead><tr><th>Estado</th><th>Ítems LR(0)</th><th>Transiciones</th></tr></thead><tbody>';
    (data.estados || []).forEach(es => {
        const itemsHtml = es.items.map(it => escapeHtml(it)).join('<br>');
        const transHtml = Object.entries(es.transiciones || {}).map(([sym, j]) => `${escapeHtml(sym)} → I${j}`).join('<br>') || '&mdash;';
        html += `<tr><td><strong>I${es.indice}</strong></td><td>${itemsHtml}</td><td>${transHtml}</td></tr>`;
    });
    html += '</tbody></table>';
    ew.innerHTML = html;

    // Tablas ACTION y GOTO
    const tw = document.getElementById('slr1-tablas-wrapper');
    // Reconstruir columnas ACTION y GOTO desde ACTION/GOTO serializados
    const actionRaw = data.ACTION || {};
    const gotoRaw = data.GOTO || {};

    // Obtener terminales y no terminales
    const terminalsSet = new Set();
    const nonTerminalsSet = new Set();
    Object.keys(actionRaw).forEach(k => {
        const [estado, simbolo] = k.split('|');
        terminalsSet.add(simbolo);
    });
    Object.keys(gotoRaw).forEach(k => {
        const [estado, nt] = k.split('|');
        nonTerminalsSet.add(nt);
    });
    const terminals = Array.from(terminalsSet).sort();
    const nonTerminals = Array.from(nonTerminalsSet).sort();

    // Estados ordenados
    const estadosIdx = new Set();
    Object.keys(actionRaw).forEach(k => estadosIdx.add(Number(k.split('|')[0])));
    Object.keys(gotoRaw).forEach(k => estadosIdx.add(Number(k.split('|')[0])));
    const estadosOrd = Array.from(estadosIdx).sort((a, b) => a - b);

    html = `
        <div style="overflow-x:auto;">
        <table class="data-table">
        <thead><tr><th>Estado</th>
        ${terminals.map(t => `<th>ACTION<br>${escapeHtml(t)}</th>`).join('')}
        ${nonTerminals.map(nt => `<th>GOTO<br>${escapeHtml(nt)}</th>`).join('')}
        </tr></thead><tbody>
    `;

    estadosOrd.forEach(i => {
        html += `<tr><td><strong>I${i}</strong></td>`;
        terminals.forEach(t => {
            const key = `${i}|${t}`;
            const accs = actionRaw[key] || [];
            let c = '';
            if (accs.length === 0) c = '&mdash;';
            else if (accs.length === 1) c = renderAccion(accs[0]);
            else c = accs.map(renderAccion).join('; ') + ' <span style="color:var(--error);font-weight:700">[CONFLICTO]</span>';
            html += `<td>${c}</td>`;
        });
        nonTerminals.forEach(nt => {
            const key = `${i}|${nt}`;
            const j = gotoRaw[key];
            html += `<td>${j != null ? j : '&mdash;'}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    tw.innerHTML = html;

    // Autómata LR(0) SVG
    renderAutomataLR0(data);
}

function renderAccion(a) {
    if (a.tipo === 'shift') return `<span style="color:var(--primary); font-weight:700;">s${a.estado}</span>`;
    if (a.tipo === 'reduce') return `<span style="color:var(--warning); font-weight:700;">r${escapeHtml(a.produccion)}</span>`;
    if (a.tipo === 'accept') return `<span style="color:var(--success); font-weight:700;">acc</span>`;
    return escapeHtml(String(a.tipo));
}

function renderAutomataLR0(data) {
    const cont = document.getElementById('slr1-automata');
    const estados = data.estados || [];
    const trans = data.transiciones || {};
    const n = estados.length;
    if (n === 0) { cont.innerHTML = '<p style="color:var(--muted)">Sin estados.</p>'; return; }

    const r = 260;
    const cx = 400, cy = 300;
    let svg = `<svg width="900" height="620" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 620">
        <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#6b7a8d"/></marker></defs>`;

    // Aristas primero (detrÃ¡s de nodos)
    Object.entries(trans).forEach(([key, j]) => {
        const [iStr, sym] = key.split('|');
        const i = Number(iStr);
        const a1 = (i / n) * 2 * Math.PI;
        const a2 = (j / n) * 2 * Math.PI;
        const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
        const x2 = cx + r * Math.cos(a2), y2 = cy + r * Math.sin(a2);
        svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="edge-line" stroke="#6b7a8d" stroke-width="1.6"/>`;
        // Etiqueta de transiciÃ³n en el punto medio
        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
        svg += `<text x="${mx}" y="${my}" font-size="10" fill="#2e75b6" text-anchor="middle" dominant-baseline="middle" font-weight="700">${escapeHtml(sym)}</text>`;
    });

    // Nodos
    estados.forEach(es => {
        const a = (es.indice / n) * 2 * Math.PI;
        const x = cx + r * Math.cos(a);
        const y = cy + r * Math.sin(a);
        const esInicial = es.indice === 0;
        svg += `<circle cx="${x}" cy="${y}" r="30" fill="#fff" stroke="#1f4e79" stroke-width="${esInicial ? 3 : 2}"/>`;
        svg += `<text x="${x}" y="${y+4}" font-size="13" fill="#1f4e79" text-anchor="middle" font-weight="700">I${es.indice}</text>`;
        if (esInicial) {
            svg += `<circle cx="${x}" cy="${y}" r="34" fill="none" stroke="#1f4e79" stroke-width="2" stroke-dasharray="6,4"/>`;
        }
    });

    svg += `</svg>`;
    cont.innerHTML = svg;
}

function renderSimSLR(sim) {
    const cont = document.getElementById('slr1-sim-result');
    if (!sim) { cont.style.display = 'none'; return; }
    cont.style.display = '';
    let html = `<p><strong>Entrada:</strong> ${escapeHtml(sim.entrada)} &nbsp;|&nbsp; <strong>Resultado:</strong> <span style="color:${sim.aceptado ? 'var(--success)' : 'var(--error)'}; font-weight:700;">${sim.aceptado ? 'ACEPTADA' : 'RECHAZADA'}</span></p>`;
    html += '<table class="data-table"><thead><tr><th>Paso</th><th>Pila de estados</th><th>Entrada restante</th><th>Acción</th></tr></thead><tbody>';
    (sim.pasos || []).forEach(p => {
        const accion = escapeHtml(p.action || '');
        let cls = '';
        if (accion.includes('ACEPTAR')) cls = 'style="color:var(--success);font-weight:700"';
        else if (accion.includes('ERROR')) cls = 'style="color:var(--error);font-weight:700"';
        html += `<tr><td>${p.step}</td><td>${escapeHtml((p.stack||[]).join(' '))}</td><td>${escapeHtml((p.remaining||[]).join(' '))}</td><td ${cls}>${accion}</td></tr>`;
    });
    html += '</tbody></table>';
    cont.innerHTML = html;
}

// ---------------------------------------------------------------------------
// ÍTEM 3 — SDD
// ---------------------------------------------------------------------------
function initItem3() {
    const btn = document.getElementById('btn-run-sdd');
    if (!btn) return;
    btn.addEventListener('click', async () => {
        const inp = document.getElementById('sdd-input').value.trim();
        const g = getSeleccionada();
        if (!g) { mostrarError('sdd-error', 'Selecciona una gramÃ¡tica.'); return; }
        ocultarError('sdd-error');
        mostrar('sdd-alert', false);
        mostrar('sdd-loading', true);
        mostrar('sdd-result', false);

        try {
            const res = await fetch(`${API}/sdd`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grammar_id: g.id, input: inp })
            });
            const data = await res.json();
            if (!res.ok) { mostrarError('sdd-error', data.error || 'Error'); mostrar('sdd-loading', false); return; }
            renderSDD(data);
            mostrar('sdd-loading', false);
            mostrar('sdd-result', true);
        } catch (e) {
            mostrarError('sdd-error', 'Error de red: ' + e.message);
            mostrar('sdd-loading', false);
        }
    });
}

function renderSDD(data) {
    // Gramática
    const gt = document.querySelector('#sdd-grammar-table tbody');
    gt.innerHTML = '';
    // Usar producciones del reporte si vienen, si no, del tree
    const producciones = new Set();
    function colectarProducciones(nodo) {
        if (!nodo) return;
        if (nodo.production && nodo.production.text) producciones.add(nodo.production.text);
        (nodo.children || []).forEach(colectarProducciones);
    }
    if (data.tree) colectarProducciones(data.tree);
    producciones.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${escapeHtml(p)}</td>`;
        gt.appendChild(tr);
    });

    // Tabla de atributos
    const ab = document.getElementById('sdd-attr-body');
    ab.innerHTML = '';
    (data.tabla_atributos || []).forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${escapeHtml(row.symbol)}</td><td>${escapeHtml(row.attribute)}</td><td>${escapeHtml(row.type)}</td><td>${escapeHtml(row.nature)}</td><td>${escapeHtml(row.meaning)}</td>`;
        ab.appendChild(tr);
    });

    // Reglas semánticas
    const rs = document.getElementById('sdd-rules');
    let html = '';
    (data.reglas_semanticas || []).forEach(rule => {
        html += `<div style="margin-bottom:0.9rem; padding:0.8rem; background:#f7fafc; border:1px solid var(--border); border-radius:6px;">`;
        html += `<div style="font-weight:700; color:var(--primary); margin-bottom:0.4rem;">${escapeHtml(rule.production)}</div>`;
        (rule.rules || []).forEach(r => {
            const define = r.define;
            const uses = (r.uses || []).map(u => `${escapeHtml(u.symbol)}.${escapeHtml(u.attribute)}`).join(', ');
            html += `<div style="margin-left:1rem; font-size:0.92rem;">${escapeHtml(define.symbol)}.${escapeHtml(define.attribute)} (${define.nature}) ${uses ? 'usa: ' + uses : ''} ${r.expression ? '— ' + escapeHtml(r.expression) : ''}</div>`;
        });
        html += `</div>`;
    });
    rs.innerHTML = html || '<p style="color:var(--muted)">Sin reglas semánticas.</p>';

    // Árbol y árbol anotado
    if (data.tree) {
        renderArbol(data.tree, 'sdd-tree', false);
        renderArbol(data.tree, 'sdd-tree-annotated', true);
    } else {
        document.getElementById('sdd-tree').innerHTML = '<p style="color:var(--muted)">Árbol no disponible (cadena no aceptada).</p>';
        document.getElementById('sdd-tree-annotated').innerHTML = '<p style="color:var(--muted)">Árbol no disponible.</p>';
    }

    // Grafo de dependencias
    renderGrafo(data.graph, 'sdd-graph');

    // Orden topológico
    const topo = document.getElementById('sdd-topo');
    topo.innerHTML = '';
    (data.topoOrder || []).forEach((item, idx) => {
        const div = document.createElement('div');
        div.className = `topo-step ${item.defined ? '' : 'undef'}`;
        div.title = `${item.symbol}#${item.nodeId}.${item.attributeName} (${item.nature})`;
        div.textContent = `Paso ${item.evaluationStep != null ? item.evaluationStep : '—'}: ${item.symbol}#${item.nodeId}.${item.attributeName}`;
        topo.appendChild(div);
    });

    // Traza de evaluaciÃ³n
    const tbody = document.getElementById('sdd-trace-body');
    tbody.innerHTML = '';
    (data.trace || []).forEach(t => {
        const tr = document.createElement('tr');
        const usados = (t.dependsOn || []).map(d => `${d.symbol}#${d.nodeId}.${d.attributeName}=${d.value != null ? escapeHtml(d.value) : '—'}`).join(', ');
        tr.innerHTML = `<td>${t.step}</td><td>${escapeHtml(t.symbol)}#${t.nodeId}.${escapeHtml(t.attributeName)}</td><td>${t.nodeId}</td><td>${usados || '—'}</td><td><strong>${escapeHtml(t.result)}</strong></td>`;
        tbody.appendChild(tr);
    });

    // Resultado final y alertas
    const finalBox = document.getElementById('sdd-final');
    const alertBox = document.getElementById('sdd-alert');
    if (data.circular) {
        mostrar('sdd-alert', true);
        alertBox.className = 'alert alert-warning';
        alertBox.textContent = data.cycleMessage ? `DefiniciÃ³n circular detectada: ${data.cycleMessage}` : data.message;
        finalBox.innerHTML = `<span style="color:var(--error); font-weight:700;">EvaluaciÃ³n detenida por ciclo.</span>`;
    } else if (!data.accepted) {
        mostrar('sdd-alert', true);
        alertBox.className = 'alert alert-error';
        alertBox.textContent = data.message;
        finalBox.innerHTML = `<span style="color:var(--error); font-weight:700;">Cadena no aceptada.</span>`;
    } else {
        ocultarError('sdd-error');
        finalBox.innerHTML = `<strong>${escapeHtml(data.finalAttribute || 'S.val')} =</strong> <span style="font-weight:700; color:var(--primary);">${escapeHtml(data.finalValue)}</span>`;
    }
}

// ---------- Árbol SVG ----------
function renderArbol(tree, containerId, annotated) {
    const cont = document.getElementById(containerId);
    if (!tree) { cont.innerHTML = '<p style="color:var(--muted)">Sin árbol.</p>'; return; }

    // Recopilar nodos con niveles
    const nodos = [];
    const aristas = [];
    function dfs(nodo, x, y, nivel, indiceX) {
        const id = 'n' + (nodos.length);
        nodos.push({ id, simbolo: nodo.simbolo, indice: nodo.indice, nivel, x: indiceX * 220, y: nivel * 130, atributos: nodo.attributes || {}, produccion: nodo.production });
        if (nodo.children && nodo.children.length > 0) {
            const childXs = [];
            nodo.children.forEach((c, ci) => {
                const cx = indiceX * 220 + (ci - (nodo.children.length - 1) / 2) * 150;
                const cid = dfs(c, cx, y + 130, nivel + 1, indiceX * 10 + ci);
                aristas.push([id, cid]);
            });
        }
        return id;
    }
    dfs(tree, 0, 0, 0, 0);

    // Ajustar X para evitar solapamiento simple: usar índice de visita en orden
    // Recalcular X basado en posición en el array (inorden aproximado)
    nodos.forEach((n, i) => { n.x = i * 200 + 150; });

    const ancho = 900;
    const alto = Math.max(200, (Math.max(...nodos.map(n => n.nivel)) + 1) * 140 + 100);
    let svg = `<svg width="${ancho}" height="${alto}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}">
        <defs><marker id="arrow-tree" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L0,9 L9,4.5 z" fill="#1f4e79"/></marker></defs>`;

    // Aristas
    aristas.forEach(([p, c]) => {
        const np = nodos.find(n => n.id === p);
        const nc = nodos.find(n => n.id === c);
        svg += `<line x1="${np.x + 60}" y1="${np.y + 22}" x2="${nc.x + 60}" y2="${nc.y - 6}" class="edge-line" stroke="#6b7a8d" stroke-width="1.8" marker-end="url(#arrow-tree)"/>`;
    });

    // Nodos
    nodos.forEach(n => {
        const esHoja = n.simbolo === 'e' || (n.produccion === null || n.produccion === undefined);
        const fill = esHoja ? '#eef6fd' : '#fff';
        const attrs = annotated ? n.atributos : {};
        const attrStr = Object.entries(attrs).map(([k, v]) => `${k}=${escapeHtml(v)}`).join(', ');
        const label = annotated && attrStr ? `${n.simbolo}#${n.indice}\n[${attrStr}]` : `${n.simbolo}#${n.indice}`;
        svg += `<rect x="${n.x}" y="${n.y}" width="120" height="44" class="node-box"/>`;
        svg += `<text x="${n.x + 60}" y="${n.y + 18}" class="node-text" text-anchor="middle" font-weight="700">${escapeHtml(n.simbolo)}#${n.indice}</text>`;
        if (attrStr) svg += `<text x="${n.x + 60}" y="${n.y + 34}" class="node-text" text-anchor="middle" font-size="11" fill="#6b7a8d">[${attrStr}]</text>`;
    });
    svg += `</svg>`;
    cont.innerHTML = svg;
}

// ---------- Grafo de dependencias SVG ----------
function renderGrafo(graph, containerId) {
    const cont = document.getElementById(containerId);
    const nodes = graph.nodes || [];
    const edges = graph.edges || [];
    if (nodes.length === 0) { cont.innerHTML = '<p style="color:var(--muted)">Sin grafo de dependencias.</p>'; return; }

    // Layout circular simple
    const cx = 450, cy = 300, r = 230;
    const pos = {};
    nodes.forEach((node, i) => {
        const a = (i / nodes.length) * 2 * Math.PI;
        pos[node.id] = { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
    });

    let svg = `<svg width="900" height="620" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 620">
        <defs><marker id="arrow-graph" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0,0 L0,9 L9,4.5 z" fill="#94a3b8"/></marker></defs>`;

    // Aristas
    edges.forEach(e => {
        const o = pos[e.from];
        const d = pos[e.to];
        if (!o || !d) return;
        svg += `<line x1="${o.x}" y1="${o.y}" x2="${d.x}" y2="${d.y}" class="graph-edge" marker-end="url(#arrow-graph)"/>`;
    });

    // Nodos
    nodes.forEach(node => {
        const p = pos[node.id];
        const cls = 'graph-node ' + (node.nature || 'sintetizado').replace(/\s+/g, '-');
        const label = node.id;
        const val = node.value != null ? ` = ${escapeHtml(node.value)}` : '';
        svg += `<circle cx="${p.x}" cy="${p.y}" r="24" class="${cls}"/>`;
        svg += `<text x="${p.x}" y="${p.y + 4}" class="graph-node-label" font-weight="700">${escapeHtml(node.symbol)}#${node.nodeId}</text>`;
        svg += `<text x="${p.x}" y="${p.y + 16}" class="graph-node-label" font-size="10" fill="#6b7a8d">${escapeHtml(node.attribute)}${val}</text>`;
    });
    svg += `</svg>`;
    cont.innerHTML = svg;
}

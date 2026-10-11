// Compiler Construction Studio Frontend Logic

const EXAMPLES = {
    arithmetic: `a = 10;\nb = 20;\nc = a + b * 2;`,

    parentheses: `a = 10;\nb = 20;\nc = (a + b) * 2;`,

    if_else: `a = 10;\nb = 20;\nc = a + b;\n\nif (c > 30) {\n    d = c - 5;\n} else {\n    d = c + 5;\n}`,

    while_loop: `a = 0;\n\nwhile (a < 5) {\n    a = a + 1;\n}`,

    optimization: `a = 10 + 20;\nb = a * 1;\nc = b + 0;`,

    complex: `a = 10;\nb = 20;\nc = a + b * 2;\n\nif (c > 30) {\n    d = c - 5;\n} else {\n    d = c + 5;\n}\n\nwhile (d < 50) {\n    d = d + 1;\n}`
};

let currentTokens = [];

// DOM Elements
const codeEditor = document.getElementById('code-editor');
const lineNumbers = document.getElementById('line-numbers');
const lineCountSpan = document.getElementById('line-count');
const presetSelect = document.getElementById('code-presets');
const compileBtn = document.getElementById('compile-btn');
const resetBtn = document.getElementById('reset-code-btn');
const clearBtn = document.getElementById('clear-code-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const errorBanner = document.getElementById('error-banner');
const errorMessage = document.getElementById('error-message');

document.addEventListener('DOMContentLoaded', () => {
    // Initial Code
    codeEditor.value = EXAMPLES.if_else;
    updateLineNumbers();

    // Event Listeners
    codeEditor.addEventListener('input', () => {
        updateLineNumbers();
        dismissError();
    });

    codeEditor.addEventListener('scroll', () => {
        lineNumbers.scrollTop = codeEditor.scrollTop;
    });

    codeEditor.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = codeEditor.selectionStart;
            const end = codeEditor.selectionEnd;
            codeEditor.value = codeEditor.value.substring(0, start) + "    " + codeEditor.value.substring(end);
            codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
            updateLineNumbers();
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            compileCode();
        }
    });

    presetSelect.addEventListener('change', (e) => {
        const key = e.target.value;
        if (EXAMPLES[key]) {
            codeEditor.value = EXAMPLES[key];
            updateLineNumbers();
            dismissError();
            compileCode();
        }
    });

    resetBtn.addEventListener('click', () => {
        codeEditor.value = EXAMPLES.if_else;
        presetSelect.value = 'if_else';
        updateLineNumbers();
        dismissError();
        compileCode();
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            codeEditor.value = '';
            updateLineNumbers();
            dismissError();
        });
    }

    compileBtn.addEventListener('click', compileCode);

    // Pipeline Click Navigation
    document.querySelectorAll('.pipeline-step').forEach(step => {
        step.addEventListener('click', () => {
            const targetTab = step.getAttribute('data-target');
            if (targetTab) switchTab(targetTab);
        });
    });

    // Tab Navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');
            switchTab(targetId);
        });
    });

    // Sub-tab Navigation (Quadruples vs Triples)
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.sub-pane').forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-sub');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');
        });
    });

    // Token Filter
    const tokenSearchInput = document.getElementById('token-search');
    if (tokenSearchInput) {
        tokenSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            renderTokensTable(currentTokens.filter(t => 
                t.value.toLowerCase().includes(query) || 
                t.type.toLowerCase().includes(query)
            ));
        });
    }

    // Initial compile
    compileCode();
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tab') === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.toggle('active', p.id === tabId);
    });
}

function updateLineNumbers() {
    const lines = codeEditor.value.split('\n');
    lineCountSpan.textContent = `Lines: ${lines.length}`;
    lineNumbers.innerHTML = lines.map((_, i) => `<div>${i + 1}</div>`).join('');
}

function dismissError() {
    if (errorBanner) errorBanner.style.display = 'none';
}

function showError(msg) {
    if (errorBanner && errorMessage) {
        errorMessage.textContent = msg;
        errorBanner.style.display = 'flex';
    }
}

function getSelectedPasses() {
    const passes = [];
    if (document.getElementById('opt-const-prop').checked) passes.push('constant_propagation');
    if (document.getElementById('opt-const-fold').checked) passes.push('constant_folding');
    if (document.getElementById('opt-alg-simp').checked) passes.push('algebraic_simplification');
    if (document.getElementById('opt-cse').checked) passes.push('common_subexpression');
    if (document.getElementById('opt-dce').checked) passes.push('dead_code_elimination');
    return passes;
}

function updatePipelineStatus(success, errorStage = null) {
    const stages = ['lexer', 'parser', 'ast', 'tac', 'quads', 'triples', 'blocks', 'cfg', 'opt', 'target'];
    stages.forEach(s => {
        const el = document.getElementById(`status-${s}`);
        if (!el) return;
        if (success) {
            el.textContent = '✓ Completed';
            el.style.color = 'var(--accent-green)';
        } else {
            if (s === errorStage) {
                el.textContent = '✕ Error';
                el.style.color = 'var(--accent-red)';
            } else {
                el.textContent = '-';
                el.style.color = 'var(--text-muted)';
            }
        }
    });
}

async function compileCode() {
    const code = codeEditor.value;
    const passes = getSelectedPasses();

    dismissError();
    statusDot.className = 'status-dot compiling';
    statusText.textContent = 'Compiling...';

    try {
        const response = await fetch('/api/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, passes })
        });

        const data = await response.json();

        if (!response.ok) {
            const errStr = data.error || 'Compilation error';
            showError(errStr);
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Error';

            const stage = errStr.includes('Lexical') ? 'lexer' : 'parser';
            updatePipelineStatus(false, stage);
            return;
        }

        statusDot.className = 'status-dot ready';
        statusText.textContent = 'Compiled & Optimized';
        updatePipelineStatus(true);

        renderResults(data);

    } catch (err) {
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Server error';
        showError(`Network/Server Error: ${err.message}`);
        updatePipelineStatus(false, 'lexer');
    }
}

function renderResults(data) {
    currentTokens = data.tokens || [];

    // 1. Statistics Bar
    const stats = data.statistics || {};
    document.getElementById('stat-tokens').textContent = stats.tokens_count || 0;
    document.getElementById('stat-ast').textContent = stats.ast_nodes_count || 0;
    document.getElementById('stat-tac').textContent = stats.tac_instructions_count || 0;
    document.getElementById('stat-temps').textContent = stats.temporaries_count || 0;
    document.getElementById('stat-quads').textContent = stats.quadruples_count || 0;
    document.getElementById('stat-triples').textContent = stats.triples_count || 0;
    document.getElementById('stat-blocks').textContent = stats.basic_blocks_count || 0;
    document.getElementById('stat-opt-lines').textContent = stats.opt_instructions_count || 0;
    document.getElementById('stat-removed').textContent = stats.instructions_removed || 0;

    // 2. TAC Display
    const unoptTac = data.intermediate.unoptimized.tac || [];
    const optTac = data.intermediate.optimized.tac || [];
    document.getElementById('unopt-tac-code').textContent = unoptTac.join('\n') || '// No instructions';
    document.getElementById('opt-tac-code').textContent = optTac.join('\n') || '// No instructions';

    // "Why This Instruction?" Table
    renderWhyTable(data.intermediate.optimized.detailed_tac || data.intermediate.unoptimized.detailed_tac || []);

    // 3. Optimization Report & Metrics
    document.getElementById('count-unopt').textContent = unoptTac.length;
    document.getElementById('count-opt').textContent = optTac.length;
    const diff = unoptTac.length - optTac.length;
    document.getElementById('diff-count').textContent = diff > 0 ? `-${diff}` : '0';

    const pct = unoptTac.length > 0 ? Math.max(0, Math.round((diff / unoptTac.length) * 100)) : 0;
    document.getElementById('reduction-pct').textContent = `${pct}%`;

    // Passes Applied Badges
    const passesContainer = document.getElementById('passes-applied-container');
    const applied = stats.passes_applied || [];
    if (applied.length === 0) {
        passesContainer.innerHTML = '<span class="badge-empty">No optimizations triggered for this program</span>';
    } else {
        passesContainer.innerHTML = applied.map(p => `
            <span class="pass-badge-applied">✓ ${escapeHtml(p)}</span>
        `).join('');
    }

    // Optimization Transformation Logs
    const logsContainer = document.getElementById('optimization-logs');
    const logs = data.optimization_logs || [];
    document.getElementById('log-count-badge').textContent = `${logs.length} transforms`;
    if (logs.length === 0) {
        logsContainer.innerHTML = '<div class="empty-state">Code is already in minimal optimal form (0 transforms applied).</div>';
    } else {
        logsContainer.innerHTML = logs.map(l => `
            <div class="log-entry">
                <span class="log-pass-badge">${escapeHtml(l.pass)}</span>
                <span class="log-detail">${escapeHtml(l.detail)}</span>
            </div>
        `).join('');
    }

    // 4. Target Pseudo-Assembly Code
    const targetCodeDisplay = document.getElementById('target-code-display');
    targetCodeDisplay.textContent = data.target_code || '; No target code generated';

    // 5. Quadruples & Triples Tables
    renderQuadruples(data.intermediate.optimized.quadruples || []);
    renderTriples(data.intermediate.optimized.triples || []);

    // 6. AST Visualizer
    renderAST(data.ast);

    // 7. Directed Control Flow Graph (CFG)
    renderCFG(data.intermediate.optimized.blocks || []);

    // 8. Lexical Tokens
    renderTokensTable(currentTokens);

    // 9. Execution & Memory Store
    renderExecution(data.execution || {});
}

function renderWhyTable(detailedTac) {
    const tbody = document.querySelector('#why-table tbody');
    document.getElementById('why-count-badge').textContent = `${detailedTac.length} instructions`;

    if (!detailedTac || detailedTac.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-cell">No instructions available</td></tr>';
        return;
    }

    tbody.innerHTML = detailedTac.map(item => `
        <tr>
            <td><strong style="color: var(--accent-blue);">${item.index}</strong></td>
            <td><code style="color: #6ee7b7; font-weight: 600;">${escapeHtml(item.tac)}</code></td>
            <td style="color: var(--text-secondary); font-size: 0.82rem;">${escapeHtml(item.why)}</td>
        </tr>
    `).join('');
}

function renderQuadruples(quads) {
    const tbody = document.querySelector('#quadruples-table tbody');
    if (!quads || quads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No quadruples generated</td></tr>';
        return;
    }

    tbody.innerHTML = quads.map((q, idx) => `
        <tr>
            <td>${idx}</td>
            <td><strong style="color: var(--accent-blue);">${escapeHtml(q.op)}</strong></td>
            <td>${escapeHtml(q.arg1)}</td>
            <td>${escapeHtml(q.arg2)}</td>
            <td><span style="color: var(--accent-green); font-weight: 600;">${escapeHtml(q.result)}</span></td>
        </tr>
    `).join('');
}

function renderTriples(triples) {
    const tbody = document.querySelector('#triples-table tbody');
    if (!triples || triples.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-cell">No triples generated</td></tr>';
        return;
    }

    tbody.innerHTML = triples.map((t) => `
        <tr>
            <td><strong style="color: var(--accent-blue);">${escapeHtml(t.index)}</strong></td>
            <td>${escapeHtml(t.op)}</td>
            <td>${escapeHtml(t.arg1)}</td>
            <td>${escapeHtml(t.arg2)}</td>
        </tr>
    `).join('');
}

function renderAST(astNode) {
    const container = document.getElementById('ast-container');
    if (!astNode) {
        container.innerHTML = '<div class="empty-state">No AST available</div>';
        return;
    }
    container.innerHTML = buildASTHtml(astNode);
}

function buildASTHtml(node) {
    if (!node) return '';

    const typeClass = getNodeColorClass(node.type);
    let html = `
        <div class="ast-tree-node">
            <div class="ast-node-card">
                <span class="ast-node-badge ${typeClass}">${node.type || 'Node'}</span>
                <span>${escapeHtml(node.name || '')}</span>
            </div>
    `;

    if (node.children && node.children.length > 0) {
        html += '<div class="ast-children">';
        for (const child of node.children) {
            html += buildASTHtml(child);
        }
        html += '</div>';
    }

    html += '</div>';
    return html;
}

function getNodeColorClass(type) {
    switch (type) {
        case 'Program': return 'type-program';
        case 'Assignment': return 'type-assign';
        case 'If': case 'While': return 'type-if';
        case 'BinOp': return 'type-binop';
        case 'Identifier': return 'type-id';
        case 'Number': return 'type-num';
        default: return 'type-program';
    }
}

function renderCFG(blocks) {
    const container = document.getElementById('cfg-container');
    document.getElementById('cfg-blocks-badge').textContent = `${blocks.length} blocks`;

    if (!blocks || blocks.length === 0) {
        container.innerHTML = '<div class="empty-state">No Basic Blocks generated</div>';
        return;
    }

    let html = '<div class="cfg-graph-layout">';
    blocks.forEach((block, idx) => {
        html += `
            <div class="cfg-node-card">
                <div class="cfg-node-header">
                    <span>Basic Block ${block.id}</span>
                    <span>${block.instructions.length} statements</span>
                </div>
                <div class="cfg-node-code">
                    ${block.instructions.map(i => `<div>${escapeHtml(i)}</div>`).join('')}
                </div>
            </div>
        `;

        if (block.successors && block.successors.length > 0) {
            html += `
                <div class="cfg-edge-svg">
                    <svg width="100%" height="38" style="overflow: visible;">
                        <defs>
                            <marker id="arrow-${idx}" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto">
                                <polygon points="0 0, 6 3, 0 6" fill="#38bdf8" />
                            </marker>
                        </defs>
                        <line x1="50%" y1="0" x2="50%" y2="28" stroke="#38bdf8" stroke-width="2" marker-end="url(#arrow-${idx})" />
                        <text x="54%" y="18" fill="#94a3b8" font-size="11" font-family="monospace">
                            branch to: ${block.successors.join(', ')}
                        </text>
                    </svg>
                </div>
            `;
        } else if (idx < blocks.length - 1) {
            html += `
                <div class="cfg-edge-svg">
                    <svg width="100%" height="38" style="overflow: visible;">
                        <defs>
                            <marker id="arrow-fall-${idx}" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto">
                                <polygon points="0 0, 6 3, 0 6" fill="#10b981" />
                            </marker>
                        </defs>
                        <line x1="50%" y1="0" x2="50%" y2="28" stroke="#10b981" stroke-width="2" marker-end="url(#arrow-fall-${idx})" />
                        <text x="54%" y="18" fill="#94a3b8" font-size="11" font-family="monospace">fallthrough</text>
                    </svg>
                </div>
            `;
        }
    });
    html += '</div>';

    container.innerHTML = html;
}

function renderTokensTable(tokens) {
    const tbody = document.querySelector('#tokens-table tbody');
    const badge = document.getElementById('token-count-badge');
    badge.textContent = `${tokens.length} tokens`;

    if (!tokens || tokens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No tokens found</td></tr>';
        return;
    }

    tbody.innerHTML = tokens.map((t, idx) => `
        <tr>
            <td>${idx + 1}</td>
            <td><span class="badge">${escapeHtml(t.type)}</span></td>
            <td><code>${escapeHtml(t.lexeme || t.value)}</code></td>
            <td>${t.line}</td>
            <td>${t.column}</td>
        </tr>
    `).join('');
}

function renderExecution(execData) {
    const varsGrid = document.getElementById('variables-grid');
    const traceContainer = document.getElementById('trace-container');

    const vars = execData.final_variables || {};
    const varKeys = Object.keys(vars);

    if (varKeys.length === 0) {
        varsGrid.innerHTML = '<div class="empty-state">No user variables recorded in memory</div>';
    } else {
        varsGrid.innerHTML = varKeys.map(k => `
            <div class="var-card">
                <span class="var-name">${escapeHtml(k)}</span>
                <span class="var-val">${vars[k]}</span>
            </div>
        `).join('');
    }

    const trace = execData.trace || [];
    if (trace.length === 0) {
        traceContainer.innerHTML = '<div class="empty-state">No execution trace available</div>';
    } else {
        traceContainer.innerHTML = trace.map(step => `
            <div class="trace-step">
                <span class="trace-num">#${step.step}</span>
                <span class="trace-action">${escapeHtml(step.action || step.tac)}</span>
                <span class="trace-state">${JSON.stringify(step.variables)}</span>
            </div>
        `).join('');
    }
}

function copyText(elemId) {
    const text = document.getElementById(elemId).textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied to clipboard!");
    });
}

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

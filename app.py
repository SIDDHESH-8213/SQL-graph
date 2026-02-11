import sqlglot
from sqlglot import exp
import networkx as nx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

def get_production_lineage(sql):
    try:
        # 1. Parse into AST
        parsed = sqlglot.parse_one(sql)
        G = nx.DiGraph()
        
        # 2. Registry: Identify all CTEs defined in the query
        cte_registry = {cte.alias: cte for cte in parsed.find_all(exp.CTE)}
        
        # 3. Destination: Find the Final Target (INSERT/CREATE)
        target_name = None
        for statement in parsed.find_all((exp.Create, exp.Insert)):
            table = statement.find(exp.Table)
            if table:
                target_name = table.this.sql()

        # 4. Helper: Trace dependencies for a specific scope
        def trace_dependencies(expression, node_name):
            for table in expression.find_all(exp.Table):
                source = table.this.sql()
                if source != node_name:
                    G.add_edge(source, node_name)

        # 5. Build CTE-to-CTE and Raw-to-CTE links
        for alias, expression in cte_registry.items():
            G.add_node(alias, label=f"CTE: {alias}", type="CTE", color="#4da6ff")
            trace_dependencies(expression, alias)

        # 6. Build final link to Target
        if target_name:
            G.add_node(target_name, label=target_name, type="TARGET", color="#4dff88")
            main_select = parsed.find(exp.Select)
            if main_select:
                trace_dependencies(main_select, target_name)

        # 7. Format for Vis.js
        nodes = []
        for node in G.nodes:
            # If node has no inputs, it's a Raw Source
            is_raw = G.in_degree(node) == 0 and node != target_name
            color = "#ff4d4d" if is_raw else G.nodes[node].get('color', "#4da6ff")
            label = f"RAW: {node}" if is_raw else G.nodes[node].get('label', node)
            nodes.append({"id": node, "label": label, "color": color})

        edges = [{"from": u, "to": v} for u, v in G.edges()]
        return {"nodes": nodes, "edges": edges}
    
    except Exception as e:
        return {"nodes": [], "edges": []}

# --- THE UI (Cyber-Grid Theme) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html class="dark">
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #mynetwork { background-image: radial-gradient(#1e293b 1px, transparent 1px); background-size: 24px 24px; }
    </style>
</head>
<body class="bg-[#020617] text-slate-300 min-h-screen">
    <div class="max-w-screen-2xl mx-auto p-8">
        <header class="flex justify-between items-end mb-12 border-b border-slate-800 pb-8">
            <div>
                <h1 class="text-3xl font-black text-white tracking-tight italic">BIGEYE <span class="text-blue-500 not-italic">L_PILOT</span></h1>
                <p class="text-xs font-mono text-slate-500 mt-2 uppercase tracking-widest">Advanced AST Lineage Resolver</p>
            </div>
            <div class="hidden md:flex gap-6">
                <div class="text-right"><p class="text-[10px] text-slate-500 uppercase">Engine</p><p class="text-sm font-bold text-blue-400">SQLGlot 23.x</p></div>
                <div class="text-right"><p class="text-[10px] text-slate-500 uppercase">Latency</p><p class="text-sm font-bold text-green-400">< 12ms</p></div>
            </div>
        </header>

        <div class="grid lg:grid-cols-12 gap-10">
            <div class="lg:col-span-4 space-y-6">
                <div class="bg-[#0f172a] border border-slate-800 p-6 rounded-3xl shadow-2xl">
                    <div class="flex items-center gap-2 mb-4">
                        <div class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                        <h3 class="text-xs font-bold text-slate-400 uppercase">SQL Input</h3>
                    </div>
                    <textarea id="sqlInput" class="w-full h-[550px] bg-[#020617] border border-slate-800 rounded-2xl p-5 font-mono text-sm text-blue-300 focus:border-blue-500 transition-all outline-none resize-none shadow-inner" placeholder="Paste SQL logic..."></textarea>
                    <button onclick="solve()" class="w-full mt-6 bg-blue-600 hover:bg-blue-500 text-white font-black py-5 rounded-2xl transition-all active:scale-[0.97] shadow-xl shadow-blue-900/20 uppercase tracking-tighter">Execute Trace</button>
                </div>
            </div>

            <div class="lg:col-span-8">
                <div class="bg-[#0f172a] border border-slate-800 rounded-3xl relative h-[720px] shadow-2xl overflow-hidden">
                    <div id="mynetwork" class="w-full h-full"></div>
                    <div class="absolute bottom-8 left-8 flex gap-8 bg-black/40 backdrop-blur-xl px-8 py-4 rounded-2xl border border-white/5">
                        <div class="flex items-center gap-3"><div class="w-3 h-3 rounded-full bg-[#ff4d4d]"></div><span class="text-[10px] font-black uppercase tracking-widest">Raw Source</span></div>
                        <div class="flex items-center gap-3"><div class="w-3 h-3 rounded-full bg-[#4da6ff]"></div><span class="text-[10px] font-black uppercase tracking-widest">CTE logic</span></div>
                        <div class="flex items-center gap-3"><div class="w-3 h-3 rounded-full bg-[#4dff88]"></div><span class="text-[10px] font-black uppercase tracking-widest">Final Sink</span></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function solve() {
            const sql = document.getElementById('sqlInput').value;
            fetch('/map', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sql: sql})
            })
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById('mynetwork');
                const options = {
                    nodes: { 
                        shape: 'dot', 
                        size: 32, 
                        font: { color: '#f8fafc', size: 12, face: 'JetBrains Mono, monospace', weight: 'bold' },
                        borderWidth: 0,
                        shadow: { enabled: true, color: 'rgba(0,0,0,0.5)', size: 10 }
                    },
                    edges: { 
                        arrows: 'to', 
                        color: { color: '#334155', highlight: '#3b82f6' }, 
                        width: 3,
                        smooth: { type: 'curvedCW', roundness: 0.2 }
                    },
                    physics: {
                        enabled: true,
                        barnesHut: { gravitationalConstant: -3000, springLength: 180, springConstant: 0.04 },
                        stabilization: { iterations: 150 }
                    }
                };
                new vis.Network(container, data, options);
            });
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index(): return HTML_CONTENT

@app.post("/map")
async def map_sql(request: Request):
    data = await request.json()
    return get_production_lineage(data['sql'])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
# 📊 SQL Lineage Explorer: AST-Based Dependency Mapping

<img width="1600" height="798" alt="image" src="https://github.com/user-attachments/assets/91d15a02-481d-4f12-8c11-54c7fd36af3b" />

---

## 🎯 The Problem

In modern data observability (like the challenges tackled at Bigeye), identifying the **Root Cause** of a data failure is the primary bottleneck.

Traditional lineage tools often rely on brittle regex patterns that fail when faced with:

- Complex "spaghetti" SQL  
- Deeply nested Common Table Expressions (CTEs)  
- Multi-stage Joins and Aliases  

---

## 🚀 The Solution

This project implements a **Static Analysis** approach to data lineage.

Instead of simple text matching, the algorithm converts raw SQL into an **Abstract Syntax Tree (AST)**. It programmatically traverses the tree to build a high-fidelity **Directed Acyclic Graph (DAG)**.

This allows engineers to:

- **Trace Upstream:** Pinpoint the exact raw sources contributing to a downstream failure.  
- **Analyze Impact:** Visualize the "Blast Radius" of a broken table before it hits production.  
- **Deduplicate Logic:** Map complex `WITH` clauses to see exactly how data is transformed.  

---

## 🧠 The Algorithm (Workflow)

The engine follows a 4-step execution pipeline:

### 1️⃣ Parsing (The X-Ray)
Uses `sqlglot` to transform SQL into a structured AST, ensuring the engine understands the grammar of the query, not just keywords.

### 2️⃣ Target Identification
Scans the tree root for `CREATE` or `INSERT` nodes to define the **Final Sink (Green Node)**.

### 3️⃣ CTE Resolution
Iterates through `WITH` branches to map temporary workspaces, linking them to their respective **Raw Tables (Red Nodes)**.

### 4️⃣ DAG Generation
Uses `NetworkX` to manage the graph hierarchy and `PyVis` to generate an interactive, physics-based UI.

---

## 🛠️ Tech Stack

- **Language:** Python 3.9+  
- **Parser:** sqlglot (Abstract Syntax Tree generation)  
- **Graph Theory:** NetworkX (DAG management and In-Degree analysis)  
- **Visualization:** PyVis (Interactive HTML/JS graph rendering)  

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sql-lineage-explorer.git
cd sql-lineage-explorer

# Install dependencies
pip install sqlglot networkx pyvis

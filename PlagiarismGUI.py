# TO RUN THIS PROGRAM, YOU NEED TO INSTALL THE FOLLOWING PACKAGES:
# RUN THIS COMMAND IN YOUR TERMINAL
# pip install sentence-transformers scikit-learn networkx python-docx PyMuPDF numpy

# TO RUN THIS PROGRAM, YOU NEED TO INSTALL THE FOLLOWING PACKAGES:
# pip install sentence-transformers scikit-learn networkx python-docx PyMuPDF numpy

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

# === Load model once ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Cache detailed chunk results for popup ===
detailed_results = {}

# === Helper functions ===
def chunk_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def ngram_similarity(text1, text2, n=5):
    def get_ngrams(words, n):
        return {" ".join(words[i:i+n]) for i in range(len(words)-n+1)}
    words1, words2 = text1.split(), text2.split()
    ngrams1, ngrams2 = get_ngrams(words1, n), get_ngrams(words2, n)
    if not ngrams1 or not ngrams2:
        return 0.0
    return len(ngrams1 & ngrams2) / len(ngrams1 | ngrams2)

def read_file(filepath):
    if filepath.lower().endswith(".txt"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif filepath.lower().endswith(".docx"):
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    elif filepath.lower().endswith(".pdf"):
        import fitz
        doc = fitz.open(filepath)
        return "\n".join(page.get_text() for page in doc)
    return ""

# === Main plagiarism detection ===
def detect_plagiarism(folder_path, threshold):
    global detailed_results
    detailed_results.clear()

    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if f.lower().endswith((".txt", ".docx", ".pdf"))]

    texts = {f: read_file(f).strip() for f in files}

    results = []
    summary = []
    G = nx.Graph()

    for f in files:
        if not texts[f]:
            results.append((f, "", "EMPTY", "", "EMPTY", ""))
            continue

    for i in range(len(files)):
        for j in range(i+1, len(files)):
            f1, f2 = files[i], files[j]
            if not texts[f1] or not texts[f2]:
                continue

            chunks1, chunks2 = chunk_text(texts[f1]), chunk_text(texts[f2])
            chunk_matches = []
            sims = []

            for c1 in chunks1:
                for c2 in chunks2:
                    sbert_score = cosine_similarity(
                        [model.encode(c1)], [model.encode(c2)]
                    )[0][0]
                    ngram_score = ngram_similarity(c1, c2)
                    final_score = 0.7 * sbert_score + 0.3 * ngram_score
                    sims.append(final_score)
                    chunk_matches.append({
                        "chunk1": c1[:60] + "...",
                        "chunk2": c2[:60] + "...",
                        "sbert": sbert_score,
                        "ngram": ngram_score,
                        "final": final_score
                    })

            avg_sim = sum(sims) / len(sims) if sims else 0
            results.append((f1, f2, avg_sim*100, "", "", ""))

            detailed_results[(f1, f2)] = chunk_matches

            if avg_sim*100 >= threshold:
                G.add_edge(f1, f2, weight=avg_sim*100)

    # === Summary (max similarity for each file) ===
    for f in files:
        if not texts[f]:
            summary.append((f, "EMPTY", "EMPTY"))
            continue

        best_file, best_sim = None, 0
        for (a, b, sim, *_ ) in results:
            if sim == "EMPTY":
                continue
            if a == f and sim > best_sim:
                best_file, best_sim = b, sim
            elif b == f and sim > best_sim:
                best_file, best_sim = a, sim

        if best_file:
            summary.append((f, os.path.basename(best_file), f"{best_sim:.2f}%"))
        else:
            summary.append((f, "-", "0.00%"))

    # === Clusters ===
    clusters = []
    for comp in nx.connected_components(G):
        clusters.append([os.path.basename(f) for f in comp])

    return results, summary, clusters

# === GUI functions ===
def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def run_detection():
    folder = folder_var.get()
    if not folder:
        messagebox.showerror("Error", "Please select a folder.")
        return
    try:
        threshold = float(threshold_var.get())
    except ValueError:
        messagebox.showerror("Error", "Invalid threshold value.")
        return

    results, summary, clusters = detect_plagiarism(folder, threshold)

    # populate Results tab
    for row in results_tree.get_children():
        results_tree.delete(row)
    for f1, f2, sim, *_ in results:
        if sim == "EMPTY":
            results_tree.insert("", "end", values=(os.path.basename(f1), "EMPTY", "EMPTY"), tags=("empty",))
        else:
            tag = "high" if sim >= threshold else "low"
            results_tree.insert("", "end", values=(os.path.basename(f1), os.path.basename(f2), f"{sim:.2f}%"), tags=(tag,))

    # populate Summary tab
        # Summary tab (sorted)
    for row in summary_tree.get_children():
        summary_tree.delete(row)

    def sim_value(sim_str):
        if sim_str == "EMPTY":
            return -1.0
        try:
            return float(sim_str.strip().strip('%'))
        except Exception:
            return -1.0

    sorted_summary = sorted(summary, key=lambda item: sim_value(item[2]), reverse=True)

    for f, match, max_sim in sorted_summary:
        if max_sim == "EMPTY":
            summary_tree.insert("", "end", values=(os.path.basename(f), "EMPTY", "EMPTY"), tags=("empty",))
        else:
            val = float(max_sim.strip("%"))
            tag = "high" if val >= threshold*100 else "low"
            summary_tree.insert("", "end", values=(os.path.basename(f), match, max_sim), tags=(tag,))
    summary_tree.tag_configure("high", background="#ff9999")
    summary_tree.tag_configure("low", background="#b3ffb3")
    summary_tree.tag_configure("empty", background="#e0e0e0")

    # populate Clustering tab
    for row in cluster_tree.get_children():
        cluster_tree.delete(row)
    for idx, comp in enumerate(clusters, start=1):
        cluster_tree.insert("", "end", values=(f"Group {idx}", ", ".join(comp)))

def show_detailed_popup(file1, file2):
    key = (file1, file2)
    if key not in detailed_results:
        key = (file2, file1)
    if key not in detailed_results:
        messagebox.showinfo("No Data", "No detailed results available.")
        return

    popup = tk.Toplevel(root)
    popup.title(f"Detailed View: {os.path.basename(file1)} vs {os.path.basename(file2)}")
    popup.geometry("900x500")

    tree = ttk.Treeview(popup, columns=("c1", "c2", "sbert", "ngram", "final"), show="headings")
    tree.heading("c1", text="Chunk A")
    tree.heading("c2", text="Chunk B")
    tree.heading("sbert", text="SBERT Sim")
    tree.heading("ngram", text="N-gram Sim")
    tree.heading("final", text="Weighted Final")
    tree.pack(expand=True, fill="both")

    for match in detailed_results[key]:
        values = (
            match["chunk1"], match["chunk2"],
            f"{match['sbert']:.2f}", f"{match['ngram']:.2f}", f"{match['final']:.2f}"
        )
        row_id = tree.insert("", "end", values=values)
        if match["final"] >= 0.8:
            tree.item(row_id, tags=("high",))
        elif match["final"] >= 0.5:
            tree.item(row_id, tags=("medium",))
        else:
            tree.item(row_id, tags=("low",))

    tree.tag_configure("high", background="#ff9999")
    tree.tag_configure("medium", background="#fff599")
    tree.tag_configure("low", background="#b3ffb3")

def on_result_double_click(event):
    item = results_tree.selection()
    if not item:
        return
    vals = results_tree.item(item[0], "values")
    if len(vals) < 3 or vals[1] == "EMPTY":
        return
    file1, file2 = vals[0], vals[1]
    folder = folder_var.get()
    show_detailed_popup(os.path.join(folder, file1), os.path.join(folder, file2))

# === GUI setup ===
root = tk.Tk()
root.title("Plagiarism Detector")
root.geometry("900x600")

frame_top = tk.Frame(root)
frame_top.pack(fill="x", pady=5)

folder_var = tk.StringVar()
threshold_var = tk.StringVar(value="70")

tk.Label(frame_top, text="Folder:").pack(side="left")
tk.Entry(frame_top, textvariable=folder_var, width=50).pack(side="left", padx=5)
tk.Button(frame_top, text="Browse", command=browse_folder).pack(side="left", padx=5)

tk.Label(frame_top, text="Threshold (%):").pack(side="left", padx=5)
tk.Entry(frame_top, textvariable=threshold_var, width=5).pack(side="left")
tk.Button(frame_top, text="Run Detection", command=run_detection).pack(side="left", padx=10)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Results tab
results_frame = ttk.Frame(notebook)
notebook.add(results_frame, text="Results")
results_tree = ttk.Treeview(results_frame, columns=("f1", "f2", "sim"), show="headings")
results_tree.heading("f1", text="File 1")
results_tree.heading("f2", text="File 2")
results_tree.heading("sim", text="Similarity")
results_tree.pack(expand=True, fill="both")
results_tree.bind("<Double-1>", on_result_double_click)

# Summary tab
summary_frame = ttk.Frame(notebook)
notebook.add(summary_frame, text="Summary")
summary_tree = ttk.Treeview(summary_frame, columns=("f", "match", "maxsim"), show="headings")
summary_tree.heading("f", text="File")
summary_tree.heading("match", text="Highest Match")
summary_tree.heading("maxsim", text="Max Similarity")
summary_tree.pack(expand=True, fill="both")

# Clustering tab
cluster_frame = ttk.Frame(notebook)
notebook.add(cluster_frame, text="Clustering")
cluster_tree = ttk.Treeview(cluster_frame, columns=("group", "files"), show="headings")
cluster_tree.heading("group", text="Group")
cluster_tree.heading("files", text="Files")
cluster_tree.pack(expand=True, fill="both")

# Color coding
for tree in (results_tree, summary_tree):
    tree.tag_configure("high", background="#ff9999")
    tree.tag_configure("low", background="#b3ffb3")
    tree.tag_configure("empty", background="#d9d9d9")

root.mainloop()

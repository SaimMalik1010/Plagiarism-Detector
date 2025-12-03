#Plagiarism Detection System (Sentence-BERT + N-Gram + Tkinter GUI)

A complete plagiarism detection application combining semantic similarity, N-gram overlap, chunk-based analysis, and a multi-tab graphical user interface.
Designed for academic evaluation, content verification, and document similarity analysis.

Key Features:
1. Hybrid Plagiarism Detection Engine
* Sentence-BERT semantic embeddings. 
* N-gram similarity for verbatim detection. 
* Chunk-based processing for long documents. 
* Detects paraphrased, restructured, and copy-paste plagiarism.
2. Multi-Tab Tkinter GUI
* Results Tab: All pairwise similarities (color-coded & sortable)
* Summary Tab: Highest match per file with severity indicators
* Clustering Tab: Groups similar files using NetworkX
* Interactive Pop-Ups: Detailed chunk-level similarity view
3. File Format Support
* .txt, 
* .docx, 
* .pdf
4. Intelligent Handling:
* Skips empty files automatically, 
* Adjustable similarity threshold, 
* Clear indicators for flagged/acceptable matches

How It Works:

Documents are split into chunks.  
Each chunk pair is compared using:
* Sentence-BERT cosine similarity
* N-gram overlap

Final similarity = average of both metrics.
All pairwise similarities are aggregated into:
1. Tabular results
2. Summaries
3. Clusters
4. Detailed chunk match reports

Technology Stack:
* Python
* Sentence-Transformers (SBERT)
* Scikit-Learn
* PyMuPDF
* python-docx
* NetworkX
* Tkinter (GUI)

Clustering:
Uses similarity graph + connected components to find plagiarism groups or "collaboration rings".

Use Cases:
* Universities checking student assignments
* Content teams detecting article reuse
* Researchers verifying paper originality
* QA teams monitoring internal documentation reuse

Status: 
Fully functional, production-ready local application.

Next planned features:
CSV export,
Report generation (PDF)

import streamlit as st
from pathlib import Path

from security import extract_zip_safely, MAX_ARCHIVE_BYTES
from parser import analyze_project, analyze_pasted_python
from graph import build_import_graph, graph_figure
from redaction import redact_secrets
from llm import explain_code, generate_review, generate_tests, generate_roadmap

st.set_page_config(page_title="RepoRadar", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1400px; padding-top: 1.5rem;}
.code-card {border:1px solid #30364d; border-radius:12px; padding:14px; margin:8px 0;}
.metric-card {border:1px solid #30364d; border-radius:12px; padding:12px;}
</style>
""", unsafe_allow_html=True)

st.title("💻🧠 RepoRadar")
st.caption("Codebase Learning Companion — understand unfamiliar projects without executing uploaded code.")

with st.sidebar:
    st.header("Input")
    mode = st.radio("Source", ["ZIP archive", "Paste Python code"])
    provider = st.selectbox("LLM provider", ["None", "Groq", "Mistral", "OpenRouter"])
    depth = st.selectbox("Learning depth", ["Beginner", "Intermediate", "Advanced"])
    st.caption(f"Archive limit: {MAX_ARCHIVE_BYTES // (1024*1024)} MB. Uploaded code is never executed.")

project_root = None
analysis = None

if mode == "ZIP archive":
    upload = st.file_uploader("Upload a small source ZIP", type=["zip"])
    if upload:
        if upload.size > MAX_ARCHIVE_BYTES:
            st.error("Archive exceeds the configured size limit.")
        else:
            try:
                project_root = extract_zip_safely(upload)
                analysis = analyze_project(project_root)
            except Exception as exc:
                st.error(f"Could not safely analyze archive: {exc}")
else:
    pasted = st.text_area("Paste Python code", height=350, placeholder="import os\n\ndef hello():\n    return 'world'")
    if pasted.strip():
        analysis = analyze_pasted_python(pasted)
        project_root = None

if analysis:
    tabs = st.tabs(["📊 Overview", "🕸️ Architecture", "📖 Learning Mode", "🔎 Review", "🧪 Tests", "🗺️ Roadmap"])

    with tabs[0]:
        cols = st.columns(5)
        cols[0].metric("Files", analysis["file_count"])
        cols[1].metric("Python", analysis["python_files"])
        cols[2].metric("Dependencies", len(analysis["dependencies"]))
        cols[3].metric("Entry candidates", len(analysis["entry_points"]))
        cols[4].metric("Tests", "Yes" if analysis["has_tests"] else "No")

        st.subheader("Languages")
        st.write(analysis["languages"])
        st.subheader("Entry-point candidates")
        st.write(analysis["entry_points"] or ["None detected"])
        st.subheader("Documentation coverage")
        st.progress(analysis["documentation_coverage"] / 100)
        st.caption(f'{analysis["documentation_coverage"]:.0f}% of analyzed source files contain useful documentation.')

        st.subheader("Dependencies")
        st.write(analysis["dependencies"] or ["No external-looking dependencies detected."])

        st.subheader("Large files")
        st.write(analysis["large_files"] or ["None"])

        st.subheader("File tree")
        for item in analysis["files"]:
            st.code(item, language="text")

    with tabs[1]:
        st.subheader("Folder / module architecture")
        if analysis.get("modules"):
            st.dataframe(analysis["modules"], use_container_width=True, hide_index=True)
        else:
            st.info("No Python modules were parsed.")

        graph = build_import_graph(analysis.get("python_sources", {}))
        if graph.number_of_edges():
            st.plotly_chart(graph_figure(graph), use_container_width=True)
        else:
            st.info("No Python import relationships were detected.")

        st.subheader("Select a file")
        options = list(analysis.get("python_sources", {}).keys())
        if options:
            selected = st.selectbox("File", options)
            source = analysis["python_sources"][selected]
            st.code(source, language="python", line_numbers=True)

    with tabs[2]:
        options = list(analysis.get("python_sources", {}).keys())
        if not options:
            st.info("Learning Mode currently supports Python source.")
        else:
            selected = st.selectbox("Code to explain", options, key="learn_file")
            source = analysis["python_sources"][selected]
            safe_source = redact_secrets(source)
            st.code(safe_source, language="python", line_numbers=True)
            if provider == "None":
                st.info("Choose an LLM provider to generate an explanation.")
            elif st.button("Explain selected code", type="primary"):
                with st.spinner("Analyzing code..."):
                    result = explain_code(provider, depth, selected, safe_source)
                st.markdown(result)

    with tabs[3]:
        if provider == "None":
            st.info("Choose an LLM provider to generate review suggestions.")
        elif st.button("Generate review suggestions", type="primary"):
            with st.spinner("Generating suggestions..."):
                result = generate_review(provider, analysis)
            st.markdown(result)
        st.caption("Review items are suggestions/questions, not confirmed defects.")

    with tabs[4]:
        if provider == "None":
            st.info("Choose an LLM provider to generate test ideas.")
        elif st.button("Generate test ideas", type="primary"):
            with st.spinner("Generating tests..."):
                result = generate_tests(provider, analysis)
            st.markdown(result)

    with tabs[5]:
        if provider == "None":
            st.info("Choose an LLM provider to generate a roadmap.")
        elif st.button("Generate learning roadmap", type="primary"):
            with st.spinner("Building roadmap..."):
                result = generate_roadmap(provider, analysis, depth)
            st.markdown(result)
else:
    st.info("Upload a ZIP or paste Python code to begin.")

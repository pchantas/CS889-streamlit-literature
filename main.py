import streamlit as st
import json

from google import genai

client = genai.Client()

MODEL_NAME = "gemini-2.5-flash"#"meta-llama/Llama-3.1-8B-Instruct"
MAX_PAPERS = 5


with open("example-bib.json") as f:
        data = json.load(f)

st.title("Literature Lookup")

papers = data["references"]
query = st.text_input("Search by keyword")

if "log" not in st.session_state:
    st.session_state.log = []

if "ai_overview" not in st.session_state:
    st.session_state.ai_overview = None 

def matches(p, q):
    q = q.lower()
    return (
        q in p["title"].lower()
        or q in p["abstract"].lower()
        or any(q in k.lower() for k in p["keywords"])
    )

def score(p, q):
    q = q.lower()
    s = 0
    if q in p["title"].lower():
        s += 3
    if any(q in k.lower() for k in p["keywords"]):
        s += 2
    if q in p["abstract"].lower():
        s += 1
    return s

def ai_overview(papers):
    papers = papers[:MAX_PAPERS]

    text = ""
    for i, p in enumerate(papers, 1):
        text += f"Paper {i} Title: {p['title']}. Abstract: {p['abstract']} "

    prompt = f"""
You are assisting with a literature review.

Compare the following papers:
1. Identify common themes across the papers.
2. Highlight key differences in methods or approaches.
3. Note differences in assumptions or scope.

Do not rank the papers or recommend which to read.

{text}
"""

    response = client.models.generate_content(
        model=MODEL_NAME, 
        contents=prompt, 
    )
    print("1 Gemini Query")
    return response.candidates[0].content.parts[0].text


if query:
    shown = [p for p in papers if score(p, query) > 0]
    shown.sort(key=lambda p: score(p, query), reverse=True)
else:
    shown = papers

# for p in shown:
#     with st.expander(f"{p['title']} ({p['year']})"):

#         st.write("**Authors:**", ", ".join(p["authors"]))
#         st.write("**Journal:**", p["journal"])
#         st.write("**Abstract:**")
#         st.write(p["abstract"])
#         st.write("**Keywords:**", ", ".join(p["keywords"]))

#         relevant = st.checkbox("Mark as relevant", key=f"rel_{p['id']}")

#         if relevant:
#             st.session_state.log.append({
#                 "paper_id": p["id"],
#             })
col_checkbox, col_info = st.columns([2, 10])
with col_checkbox:
    st.markdown("**Mark as Relevant**")
with col_info:
    st.markdown("**Search Result**")

for p in shown:
    col_checkbox, col_info = st.columns([2, 10])
    with col_checkbox:
        relevant = st.checkbox("Relevant", key=f"rel_{p['id']}", label_visibility="collapsed")

        if "log" not in st.session_state:
            st.session_state.log = []
        if relevant and not any(log["paper_id"] == p["id"] for log in st.session_state.log):
            st.session_state.log.append({"paper_id": p["id"]})
        elif not relevant:
            # Remove if unchecked
            st.session_state.log = [log for log in st.session_state.log if log["paper_id"] != p["id"]]


    with col_info:
        with st.expander(f"{p['title']} ({p['year']})"):
            st.write("**Authors:**", ", ".join(p["authors"]))
            st.write("**Journal:**", p["journal"])
            st.write("**Abstract:**")
            st.write(p["abstract"])
            st.write("**Keywords:**", ", ".join(p["keywords"]))


st.markdown("---")
st.subheader("AI Overview")
st.caption(
    f"Summarizes themes and differences across the papers marked as relevant.\nCurrent underlying model: {MODEL_NAME}"
)

if st.button("Generate AI Overview for Relevant Papers"):
    selected_ids = [log["paper_id"] for log in st.session_state.log]
    selected_papers = [p for p in papers if p["id"] in selected_ids]

    if selected_papers:
        with st.spinner("Analyzing relevant papers with ..."):
            overview = ai_overview(selected_papers)
            st.session_state.ai_overview = overview
            st.session_state.show_ai = True 
    else:
        st.warning("No papers marked as relevant")

def toggle_ai():
    st.session_state.show_ai = not st.session_state.show_ai

if st.session_state.get("ai_overview") and st.session_state.show_ai:
    st.write(st.session_state.ai_overview)
    st.button("Collapse AI Summary", on_click=toggle_ai)

elif st.session_state.get("ai_overview") and not st.session_state.show_ai:
    st.button("Expand AI Summary", on_click=toggle_ai)

st.markdown("---")
st.subheader("Save Marked Paper")
selected_ids = [log["paper_id"] for log in st.session_state.log]
selected_papers = [p for p in papers if p["id"] in selected_ids]

save_dict = {
    "selected_papers": selected_papers,
    "ai_overview": st.session_state.ai_overview
}

json_str = json.dumps(save_dict, indent=2)

if selected_papers:
    st.download_button(
        label=f"Download {len(selected_papers)} Selected Papers JSON",
        data=json_str,
        file_name="selected_papers.json",
        mime="application/json"
    )

else:
    st.info("No papers marked as relevant")

# st.markdown("---")
# st.subheader("Interaction Log")
# st.write(st.session_state.log)





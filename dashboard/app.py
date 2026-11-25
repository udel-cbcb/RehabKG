#!/usr/bin/env python3
"""
RehabKG Dashboard - Rehabilitation Knowledge Graph Analytics

Prototype for data analytics and knowledge discovery.
Run: streamlit run dashboard/app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import logging
from dotenv import load_dotenv
import html
from db import get_driver as db_get_driver

load_dotenv()

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="RehabKG Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Neo4j connection
@st.cache_resource
def get_driver():
    return db_get_driver()

def run_query(query, params=None):
    """Run a read-only query; surface failures instead of hiding them."""
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run(query, params or {}, timeout=30)
            return [record.data() for record in result]
    except Exception:
        logger.exception("Dashboard query failed")
        st.error("Query failed — see the server log for details.")
        return []

def render_link_table(dataframe, link_column, height=400):
    """Render a dataframe as HTML table with clickable links in specified column."""
    html = f"""
    <div style="max-height: {height}px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 4px;">
    <table style="width:100%; border-collapse: collapse;">
    <thead style="position: sticky; top: 0; background: #f8f9fa;">
    <tr style="border-bottom: 2px solid #ddd; text-align: left;">
    """
    for col in dataframe.columns:
        html += f'<th style="padding: 8px; font-weight: 600;">{col}</th>'
    html += """
    </tr>
    </thead>
    <tbody>
    """
    for _, row in dataframe.iterrows():
        html += '<tr style="border-bottom: 1px solid #ddd;">'
        for col in dataframe.columns:
            value = row[col]
            if col == link_column and pd.notna(value) and isinstance(value, str) and value.startswith('http'):
                html += f'<td style="padding: 8px;"><a href="{value}" target="_blank">{value}</a></td>'
            else:
                html += f'<td style="padding: 8px;">{value}</td>'
        html += '</tr>'
    html += """
    </tbody>
    </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🏥 RehabKG Dashboard")
    st.markdown("""
    **Rehabilitation Knowledge Graph**
    
    A comprehensive graph database integrating rehabilitation ontologies, 
    clinical datasets, and therapeutic exercises for physical therapy research.
    """)
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📊 Overview", "🏋️ Exercises", "🔬 Clinical Trials", 
         "👤 Patients", "🧬 Ontologies", "🔍 Knowledge Discovery",
         "✅ Evidence & Review"]
    )
    st.markdown("---")
    
    # Graph stats with explanations
    st.markdown("**📊 Graph Statistics**")
    st.caption("Total nodes (entities) and relationships in the knowledge graph")
    stats_nodes = run_query("MATCH (n) RETURN count(n) AS nodes")
    stats_rels = run_query("MATCH ()-[r]->() RETURN count(r) AS rels")
    st.metric("Nodes", f"{stats_nodes[0]['nodes']:,}", help="Entities like exercises, patients, trials, ontology concepts")
    st.metric("Relationships", f"{stats_rels[0]['rels']:,}", help="Connections between entities (e.g., Exercise → Muscle)")

# Main content
if page == "📊 Overview":
    st.title("📊 Rehabilitation Knowledge Graph (RehabKG)")
    
    st.markdown("""
    ### Knowledge Graph Summary
    
    The RehabKG integrates data from multiple sources into a unified graph structure:
    - **Clinical Data**: Exercises, patients, clinical trials, outcomes
    - **Ontologies**: ICF, HPO, Uberon, Mondo, PMR, COPPER (standardized medical vocabularies)
    - **Bridges**: Connections between ontologies to enable cross-domain queries
    """)
    
    # Key metrics with explanations
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        exercises_count = run_query("MATCH (n:Exercise) RETURN count(n) AS c")
        st.metric("Exercises", f"{exercises_count[0]['c']:,}", help="Therapeutic exercises from FreeExerciseDB")
    with col2:
        trials_count = run_query("MATCH (n:ClinicalTrial) RETURN count(n) AS c")
        st.metric("Clinical Trials", f"{trials_count[0]['c']:,}", help="Rehabilitation trials from ClinicalTrials.gov")
    with col3:
        patients_count = run_query("MATCH (n:Patient) RETURN count(n) AS c")
        st.metric("Patients", f"{patients_count[0]['c']:,}", help="Amputation patients from MOTU dataset")
    with col4:
        ontology_count = run_query("""
            MATCH (n)
            WHERE n:ICFConcept OR n:HPOConcept OR n:UberonConcept OR n:MondoDisease
               OR n:ICD10Code OR n:EXMOConcept OR n:REHABOConcept OR n:OntologyClass
               OR n:OntologyProperty OR n:PAINConcept OR n:OntologyIndividual
               OR n:NodeType OR n:RelType
            RETURN count(n) AS c
        """)
        st.metric("Ontology Concepts", f"{ontology_count[0]['c']:,}", help="Medical concepts from all integrated ontologies + schema nodes")
    
    # Additional metrics row
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        sessions_count = run_query("MATCH (n:Session) RETURN count(n) AS c")
        st.metric("Sessions", f"{sessions_count[0]['c']:,}", help="Hospital stay sessions from MOTU dataset")
    with col6:
        outcomes_count = run_query("MATCH (n:Outcome) RETURN count(n) AS c")
        st.metric("Outcomes", f"{outcomes_count[0]['c']:,}", help="Patient outcome measurements from MOTU dataset")
    with col7:
        adverse_count = run_query("MATCH (n:AdverseEvent) RETURN count(n) AS c")
        st.metric("Adverse Events", f"{adverse_count[0]['c']:,}", help="Adverse events from MOTU dataset")
    with col8:
        scales_count = run_query("MATCH (n:AssessmentScale) RETURN count(n) AS c")
        st.metric("Assessment Scales", f"{scales_count[0]['c']:,}", help="Rehabilitation assessment scales")
    
    # Third row - anatomy and equipment
    col9, col10, col11, col12 = st.columns(4)
    with col9:
        muscle_count = run_query("MATCH (n:Muscle) RETURN count(n) AS c")
        st.metric("Muscles", f"{muscle_count[0]['c']:,}", help="Muscle anatomy targets from Exercise DB")
    with col10:
        equipment_count = run_query("MATCH (n:Equipment) RETURN count(n) AS c")
        st.metric("Equipment", f"{equipment_count[0]['c']:,}", help="Exercise equipment from Exercise DB")
    with col11:
        # Empty for balance
        pass
    with col12:
        # Empty for balance
        pass
    
    # Data sources with links
    st.subheader("📁 Data Sources")
    st.caption("Where each piece of data comes from")
    
    sources_query = """
        MATCH (n)
        WHERE n.source IS NOT NULL
        WITH n.source AS source, labels(n)[0] AS label, count(n) AS count
        RETURN source, label, count
        ORDER BY count DESC
    """
    sources_raw = run_query(sources_query)
    # Build a label-type mapping for each source
    source_types = {}
    ontology_labels = {'ICD10Code','HPOConcept','UberonConcept','MondoDisease',
                       'ICFConcept','EXMOConcept','REHABOConcept','PAINConcept',
                       'OntologyClass','OntologyProperty','OntologyIndividual'}
    for row in sources_raw:
        t = 'Ontology' if row['label'] in ontology_labels else 'Clinical'
        source_types[row['source']] = t

    sources_data = pd.DataFrame({
        "#": [str(i) for i in range(1, len(sources_raw) + 1)],
        "Dataset": [row['source'] for row in sources_raw],
        "Type": [source_types.get(row['source'], '?') for row in sources_raw],
        "Count": [f"{row['count']:,}" for row in sources_raw],
    })
    st.dataframe(sources_data, use_container_width=True, height=400, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small"),
                                "Count": st.column_config.TextColumn("Count", width="small"),
                                "Type": st.column_config.TextColumn("Type", width="small")})
    
    st.caption("🔗 **Quick Links:** [CDC ICD-10-CM](https://www.cms.gov/medicare/coding-billing/icd-10-codes) | [HPO](https://hpo.jax.org/) | [Uberon](https://uberon.github.io/) | [Mondo](https://monarch-initiative.github.io/mondo/) | [MOTU](https://zenodo.org/records/6649435) | [ClinicalTrials.gov](https://clinicaltrials.gov/) | [ICF](https://bioportal.bioontology.org/ontologies/ICF) | [Free Exercise DB](https://github.com/BasiliusCyclop/FreeExerciseDB) | [Open Rehab](https://github.com/openrehab/open-rehab-exercises)")
    
    # Entity types with counts
    st.subheader("📊 Entity Types")
    st.caption("Types of nodes in the knowledge graph")
    
    entities_query = """
        MATCH (n)
        WHERE n.source IS NOT NULL
        WITH labels(n)[0] AS label, n.source AS source, count(n) AS count
        RETURN label AS entity_type, source AS source, count AS count
        ORDER BY count DESC
    """
    entities = run_query(entities_query)
    entities_df = pd.DataFrame(entities)
    entities_df.insert(0, '#', [str(i) for i in range(1, len(entities_df) + 1)])
    entities_df['count'] = entities_df['count'].apply(lambda x: f"{x:,}")
    entities_df = entities_df[['#', 'entity_type', 'source', 'count']]
    st.dataframe(entities_df, use_container_width=True, height=400, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small"),
                                "count": st.column_config.TextColumn("Count", width="small")})
    
    # Relationship types with explanations
    st.subheader("🔗 Relationship Types")
    st.caption("How entities are connected to each other")
    
    # Query to get relationship counts with source information
    rels_query = """
        MATCH (a)-[r]->(b)
        WHERE a.source IS NOT NULL OR b.source IS NOT NULL
        WITH type(r) AS rel_type, count(r) AS count,
             collect(DISTINCT coalesce(a.source, '')) AS sources_a,
             collect(DISTINCT coalesce(b.source, '')) AS sources_b
        RETURN rel_type AS relationship, count AS count,
               sources_a + sources_b AS all_sources
        ORDER BY count DESC
    """
    rels = run_query(rels_query)
    
    # Format sources as string (deduplicate in Python since APOC not available)
    for rel in rels:
        sources = list(set([s for s in rel['all_sources'] if s]))
        rel['Sources'] = ', '.join(sorted(sources))
        del rel['all_sources']
    
    rels_df = pd.DataFrame(rels)
    rels_df.insert(0, '#', [str(i) for i in range(1, len(rels_df) + 1)])
    rels_df['count'] = rels_df['count'].apply(lambda x: f"{x:,}")
    rels_df = rels_df[['#', 'relationship', 'Sources', 'count']]
    st.dataframe(rels_df, use_container_width=True, height=400, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small"),
                                "count": st.column_config.TextColumn("Count", width="small"),
                                "Sources": st.column_config.TextColumn("Sources", width="max")})

elif page == "🏋️ Exercises":
    st.title("🏋️ Exercise Explorer")
    
    exercise_count = run_query("MATCH (n:Exercise) RETURN count(n) AS c")[0]['c']
    st.markdown(f"""
    ### Therapeutic Exercises
    
    Browse the exercise database containing **{exercise_count:,} therapeutic exercises** used in physical therapy.
    
    **Properties:**
    - **Name**: Exercise name (e.g., "Barbell Squat")
    - **Category**: Type of exercise (strength, stretching, cardio, balance)
    - **Level**: Difficulty level (beginner, intermediate, advanced)
    - **Muscles**: Target muscles (primary and secondary)
    - **Equipment**: Required equipment (if any)
    
    **Relationships:**
    - `TARGETS_PRIMARY` → Muscle (main muscle worked)
    - `TARGETS_SECONDARY` → Muscle (secondary muscles)
    - `REQUIRES` → Equipment (equipment needed)
    - `TARGETS_BODY_PART` → BodyPart (body region)
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category", 
            ["All", "strength", "stretching", "cardio", "balance"],
            help="Filter by exercise type")
    with col2:
        level = st.selectbox("Level", 
            ["All", "beginner", "intermediate", "advanced"],
            help="Filter by difficulty level")
    
    query = "MATCH (e:Exercise) WHERE 1=1"
    params = {}
    
    if category != "All":
        query += " AND e.category = $category"
        params["category"] = category
    if level != "All":
        query += " AND e.level = $level"
        params["level"] = level
    
    query += """
        OPTIONAL MATCH (e)-[:TARGETS_PRIMARY]->(pm:Muscle)
        OPTIONAL MATCH (e)-[:TARGETS_SECONDARY]->(sm:Muscle)
        RETURN e.name AS name, e.category AS category, e.level AS level, 
               e.equipment AS equipment, e.source AS source,
               collect(DISTINCT pm.name) AS primary_muscles,
               collect(DISTINCT sm.name) AS secondary_muscles
    """
    
    exercises = run_query(query, params)
    
    # Format muscles as comma-separated strings
    for ex in exercises:
        ex['primary_muscles'] = ', '.join(ex['primary_muscles']) if ex['primary_muscles'] else '-'
        ex['secondary_muscles'] = ', '.join(ex['secondary_muscles']) if ex['secondary_muscles'] else '-'
    
    exercises_df = pd.DataFrame(exercises)
    exercises_df.insert(0, '#', [str(i) for i in range(1, len(exercises_df) + 1)])
    st.dataframe(exercises_df, use_container_width=True, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small")})
    
    st.subheader("💪 Exercise → Muscle Connections")
    st.caption("Which muscles are targeted by the most exercises")
    muscle_query = """
        MATCH (e:Exercise)-[:TARGETS_PRIMARY]->(m:Muscle)
        RETURN m.name AS muscle, count(e) AS exercises
        ORDER BY exercises DESC
        LIMIT 20
    """
    muscles = run_query(muscle_query)
    st.bar_chart(pd.DataFrame(muscles).set_index("muscle"))

elif page == "🔬 Clinical Trials":
    st.title("🔬 Clinical Trial Finder")
    
    st.markdown("""
    ### Clinical Trials Database
    
    Search **1,387 rehabilitation clinical trials** from ClinicalTrials.gov.
    
    **Properties:**
    - **NCT ID**: Unique trial identifier (e.g., NCT04142177)
    - **Title**: Trial title
    - **Status**: Current status (RECRUITING, COMPLETED, etc.)
    - **Enrollment**: Number of participants
    
    **Relationships:**
    - `STUDIES_CONDITION` → Condition (medical condition being studied)
    
    **Usage:**
    - Find active trials for specific conditions
    - Compare enrollment sizes
    - Track trial status and timelines
    """)
    
    condition = st.text_input("Search Condition", "low back pain", 
                              help="Enter a medical condition to search for trials")
    status = st.selectbox("Status", 
        ["All", "RECRUITING", "COMPLETED", "ACTIVE_NOT_RECRUITING"],
        help="Filter by trial status")
    
    query = """
        MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
        WHERE toLower(c.name) CONTAINS toLower($condition)
    """
    params = {"condition": condition}
    
    if status != "All":
        query += " AND t.status = $status"
        params["status"] = status
    
    query += """
        RETURN t.nct_id AS nct_id, t.title AS title, 
               t.status AS status, t.enrollment AS enrollment,
               c.name AS condition
        ORDER BY t.enrollment DESC
        LIMIT 50
    """
    
    trials = run_query(query, params)
    trials_df = pd.DataFrame(trials)
    trials_df.insert(0, '#', [str(i) for i in range(1, len(trials_df) + 1)])
    if 'enrollment' in trials_df.columns:
        # Bulk-imported graphs type properties as strings; Cypher-path as ints.
        def _fmt_enroll(x):
            if pd.isna(x) or str(x).strip() == "":
                return "-"
            try:
                return f"{int(float(x)):,}"
            except (TypeError, ValueError):
                return str(x)
        trials_df['enrollment'] = trials_df['enrollment'].apply(_fmt_enroll)
    st.dataframe(trials_df, use_container_width=True, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small"),
                                "enrollment": st.column_config.TextColumn("enrollment", width="small")})
    
    st.subheader("📊 Trial Status Distribution")
    st.caption("How many trials are in each status category")
    status_query = """
        MATCH (t:ClinicalTrial)
        RETURN t.status AS status, count(t) AS count
    """
    statuses = run_query(status_query)
    st.bar_chart(pd.DataFrame(statuses).set_index("status"))

elif page == "👤 Patients":
    st.title("👤 Patient Outcomes (MOTU)")
    
    st.markdown("""
    ### MOTU Amputation Dataset
    
    Analyze outcomes from **1,006 amputation patients** in the MOTU dataset.
    
    **Patient Properties:**
    - **Patient ID**: Unique identifier (e.g., MOTU-1)
    - **Sex**: Gender (M/F)
    - **Birth Year**: Year of birth
    
    **Session Properties:**
    - **Amputation Side**: Left (L) or Right (R)
    - **Amputation Cause**: vascular, traumatic, cancer, etc.
    - **Length of Stay**: Days in rehabilitation
    - **K-Level**: Functional classification (K0-K4)
    
    **Outcome Properties:**
    - **Phase**: admission or discharge
    - **Value**: Score on assessment scale (e.g., Barthel Index)
    
    **Assessment Scales:**
    - **Barthel Index (BARTEL)**: Activities of daily living (0-100)
    - **FIM**: Functional Independence Measure
    - **Berg Balance Scale**: Balance assessment (0-56)
    """)
    
    st.subheader("📊 Amputation Side Distribution")
    st.caption("Patients by amputation side (Left/Right)")
    side_query = """
        MATCH (s:Session)
        RETURN s.amputation_side AS side, count(s) AS count
    """
    sides = run_query(side_query)
    st.bar_chart(pd.DataFrame(sides).set_index("side"))
    
    st.subheader("📈 Outcome Improvement by Cause")
    st.caption("Average Barthel Index scores at admission vs discharge by amputation cause")
    improvement_query = """
        MATCH (p:Patient)-[:HAS_STAY]->(s:Session)-[:HAS_OUTCOME]->(o:Outcome)
        WHERE o.outcome_id CONTAINS 'BARTEL'
        WITH s.amputation_cause AS cause, 
             o.phase AS phase, 
             avg(coalesce(o.value_numeric, toFloat(o.value))) AS avg_score,
             count(DISTINCT p) AS patients
        RETURN cause,
               max(CASE WHEN phase = 'admission' THEN avg_score END) AS avg_admission,
               max(CASE WHEN phase = 'discharge' THEN avg_score END) AS avg_discharge,
               patients
        ORDER BY patients DESC
    """
    improvements = run_query(improvement_query)
    improvements_df = pd.DataFrame(improvements)
    improvements_df.insert(0, '#', [str(i) for i in range(1, len(improvements_df) + 1)])
    for col in ['avg_admission', 'avg_discharge', 'patients']:
        if col in improvements_df.columns:
            improvements_df[col] = improvements_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    st.dataframe(improvements_df, use_container_width=True, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small")})

elif page == "🧬 Ontologies":
    st.title("🧬 Ontology Explorer")
    
    st.markdown("""
    ### Medical Ontologies
    
    Browse standardized medical vocabularies integrated into the RehabKG.
    
    **Available Ontologies:**
    
    | Ontology | Description | Concepts |
    |----------|-------------|----------|
    | **ICF** | WHO International Classification of Functioning | 1,509 |
    | **HPO** | Human Phenotype Ontology | 32,772 |
    | **Uberon** | Cross-species anatomy ontology | 10,000 |
    | **Mondo** | Disease ontology | 5,000 |
    | **ICD10** | ICD-10-CM disease codes | 92,694 |
    | **PAIN** | The Pain Ontology (IASP) | 623 |
    | **EXMO** | Exercise medicine ontology | 220 |
    | **REHABO** | Rehabilitation ontology | 63 |

    The focused graph excludes COPPER, KHMO, CBHA, and other flagged ontology
    families.
    
    **Why Ontologies Matter:**
    - Enable standardized terminology across datasets
    - Allow cross-referencing between different data sources
    - Support semantic queries (e.g., "find all mobility-related concepts")
    """)
    
    ontology = st.selectbox("Select Ontology", 
        ["ICF", "HPO", "Uberon", "Mondo", "ICD10", "PAIN", "EXMO", "REHABO"],
        help="Select an ontology to browse its concepts")
    params = None
    
    if ontology == "ICF":
        st.info("**ICF (International Classification of Functioning)** - WHO standard for describing health and health-related states. Codes: b* = Body Functions, s* = Body Structure, d* = Activity/Participation, e* = Environmental Factors")
        query = """
            MATCH (i:ICFConcept)
            WHERE i.code STARTS WITH 'b' OR i.code STARTS WITH 'd' OR i.code STARTS WITH 's'
            RETURN i.code AS code, i.name AS name, 
                   labels(i)[0] AS type
            LIMIT 100
        """
    elif ontology == "HPO":
        st.info("**HPO (Human Phenotype Ontology)** - Standard vocabulary for abnormal phenotypes. Used to link diseases to symptoms and clinical features.")
        query = """
            MATCH (h:HPOConcept)
            RETURN h.code AS code, h.name AS name
            LIMIT 100
        """
    elif ontology == "Uberon":
        st.info("**Uberon** - Cross-species anatomy ontology. Provides standardized names for anatomical structures across organisms.")
        query = """
            MATCH (u:UberonConcept)
            RETURN u.uri AS code, u.name AS name
            LIMIT 100
        """
    elif ontology == "Mondo":
        st.info("**Mondo** - Disease ontology that integrates multiple disease vocabularies. Links to ICD-10 codes for clinical classification.")
        query = """
            MATCH (m:MondoDisease)
            RETURN m.uri AS code, m.name AS name
            LIMIT 100
        """
    elif ontology == "ICD10":
        st.info("**ICD-10-CM** - International Classification of Diseases, 10th Revision. Clinical modification used for disease coding and billing.")
        query = """
            MATCH (i:ICD10Code)
            RETURN i.code AS code, i.description AS name
            LIMIT 100
        """
    elif ontology == "PAIN":
        st.info("**PAIN (The Pain Ontology, IASP)** - Standard vocabulary for pain sensations, qualities, and related clinical concepts.")
        query = """
            MATCH (p:PAINConcept)
            RETURN coalesce(p.code, p.uri) AS code, p.name AS name
            ORDER BY name
            LIMIT 100
        """
    elif ontology == "EXMO":
        st.info("**EXMO (Exercise Medicine Ontology)** - Standard vocabulary for exercise tests, equipment, and activity concepts.")
        query = """
            MATCH (e:EXMOConcept)
            RETURN coalesce(e.code, e.uri) AS code, e.name AS name
            ORDER BY name
            LIMIT 100
        """
    elif ontology == "REHABO":
        st.info("**REHABO (Rehabilitation Ontology)** - Rehabilitation processes, exercises, and assistive-device concepts.")
        query = """
            MATCH (r:REHABOConcept)
            RETURN coalesce(r.code, r.uri) AS code, r.name AS name
            ORDER BY name
            LIMIT 100
        """
    else:
        # Future sources can use a parameterized label match.
        st.info(f"**{ontology}** - Specialized ontology for physical therapy and rehabilitation.")
        query = """
            MATCH (n)
            WHERE $ontology IN labels(n)
            RETURN n.code AS code, n.name AS name
            LIMIT 100
        """
        params = {"ontology": f"{ontology}Concept"}
    
    concepts = run_query(query, params) if params else run_query(query)
    
    concepts_df = pd.DataFrame(concepts)
    concepts_df.insert(0, '#', [str(i) for i in range(1, len(concepts_df) + 1)])
    st.dataframe(concepts_df, use_container_width=True, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small")})
    
    st.subheader("🔗 ICF → Exercise Connections")
    st.caption("How ICF functioning concepts connect to therapeutic exercises")
    icf_query = """
        MATCH (i:ICFConcept)<-[:MAPS_TO_ICF]-(m)
        MATCH (m)<-[:TARGETS_PRIMARY]-(e:Exercise)
        RETURN i.code AS icf_code, i.name AS icf_name, 
               count(e) AS exercises
        LIMIT 20
    """
    icf_data = run_query(icf_query)
    # columns= keeps the frame well-formed when the query returns no rows
    # (e.g. a bulk-loaded graph without MAPS_TO_ICF→TARGETS_PRIMARY chains)
    icf_df = pd.DataFrame(icf_data, columns=["icf_code", "icf_name", "exercises"])
    icf_df.insert(0, '#', [str(i) for i in range(1, len(icf_df) + 1)])
    if 'exercises' in icf_df.columns:
        icf_df['exercises'] = icf_df['exercises'].apply(lambda x: f"{x:,}")
    icf_df = icf_df[['#', 'icf_code', 'icf_name', 'exercises']]
    st.dataframe(icf_df, use_container_width=True, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small"),
                                "exercises": st.column_config.TextColumn("exercises", width="small")})

elif page == "🔍 Knowledge Discovery":
    st.title("🔍 Knowledge Discovery")
    
    st.markdown("""
    ### Explore Graph Connectivity
    
    Use this tool to discover relationships and paths in the knowledge graph.
    
    **Features:**
    - **Path Finding**: Find connections between any two concepts
    - **Disconnected Components**: Identify isolated nodes that need bridging
    - **Relationship Analysis**: Understand how different entity types connect
    
    **Tips:**
    - Start with entity types like "Exercise", "Patient", "ClinicalTrial"
    - End with ontology types like "ICFConcept", "HPOConcept"
    - Paths show how clinical data connects to standardized ontologies
    """)
    
    st.subheader("📊 Disconnected Components")
    st.caption("Nodes that have no relationships - potential candidates for new bridges")
    disconnected_query = """
        MATCH (n)
        WHERE NOT (n)--()
        UNWIND labels(n) AS label
        RETURN label, count(n) AS count
        ORDER BY count DESC
    """
    disconnected = run_query(disconnected_query)
    disconnected_df = pd.DataFrame(disconnected)
    disconnected_df.insert(0, '#', [str(i) for i in range(1, len(disconnected_df) + 1)])
    if 'count' in disconnected_df.columns:
        disconnected_df['count'] = disconnected_df['count'].apply(lambda x: f"{x:,}")
    if 'label' in disconnected_df.columns:
        disconnected_df = disconnected_df.rename(columns={'label': 'entity type'})
    st.dataframe(disconnected_df, use_container_width=True, hide_index=True,
                 column_config={"#": st.column_config.TextColumn("#", width="small"),
                                "count": st.column_config.TextColumn("count", width="small")})
    
    st.subheader("🛤️ Find Paths Between Concepts")
    
    # Get available entity types for autocomplete
    entity_types = run_query("""
        MATCH (n)
        UNWIND labels(n) AS label
        WITH label, count(n) AS count
        RETURN label AS entity_type, count
        ORDER BY count DESC
    """)
    entity_options = [e['entity_type'] for e in entity_types]
    
    # Categorize entity types for better UX
    clinical_types = [e for e in entity_options if e in ['Exercise', 'Patient', 'Session', 'Outcome', 'ClinicalTrial', 'Condition', 'AdverseEvent', 'AssessmentScale', 'BodyPart', 'Muscle', 'Equipment']]
    ontology_types = [e for e in entity_options if 'Concept' in e or 'ICF' in e or 'Disease' in e or 'Code' in e]
    schema_types = [e for e in entity_options if e in ['BodyFunction', 'Activity', 'BodyStructure', 'EnvironmentalFactor', 'RelType', 'NodeType', 'OntologyClass', 'OntologyProperty', 'OntologyIndividual']]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Start Concept**")
        start_category = st.selectbox("Category", 
            ["Clinical Data", "Ontology", "Schema"],
            key="start_category",
            help="Select the category of the starting entity")
        
        if start_category == "Clinical Data":
            concept1 = st.selectbox("Entity Type", clinical_types, key="start_entity",
                                   help="Select the starting entity type")
        elif start_category == "Ontology":
            concept1 = st.selectbox("Entity Type", ontology_types, key="start_entity",
                                   help="Select the starting ontology type")
        else:
            concept1 = st.selectbox("Entity Type", schema_types, key="start_entity",
                                   help="Select the starting schema type")
    
    with col2:
        st.markdown("**End Concept**")
        end_category = st.selectbox("Category", 
            ["Ontology", "Clinical Data", "Schema"],
            key="end_category",
            help="Select the category of the ending entity")
        
        if end_category == "Clinical Data":
            concept2 = st.selectbox("Entity Type", clinical_types, key="end_entity",
                                   help="Select the ending entity type")
        elif end_category == "Ontology":
            concept2 = st.selectbox("Entity Type", ontology_types, key="end_entity",
                                   help="Select the ending ontology type")
        else:
            concept2 = st.selectbox("Entity Type", schema_types, key="end_entity",
                                   help="Select the ending schema type")
    
    if st.button("Find Paths", help="Search for paths between the two concepts"):
        with st.spinner("Searching for paths..."):
            paths = run_query(f"""
                MATCH (start:{concept1})-[*1..3]-(end:{concept2})
                WITH DISTINCT start, end
                MATCH path = shortestPath((start)-[*1..3]-(end))
                RETURN [n IN nodes(path) | {{
                    label: labels(n)[0],
                    name: coalesce(n.name, n.title, n.nct_id, n.code, n.cui, n.concept_id, n.patient_id, n.session_id, n.outcome_id, 'unknown')
                }}] AS node_data,
                       length(path) AS length,
                       [r IN relationships(path) | type(r)] AS rels
                LIMIT 10
            """, params=None)
        st.session_state['paths'] = paths
        st.session_state['concept1'] = concept1
        st.session_state['concept2'] = concept2
    
    paths = st.session_state.get('paths', [])
    if paths:
        # ── Path summary ──
        concept1 = st.session_state.get('concept1', '')
        concept2 = st.session_state.get('concept2', '')
        lengths = [p['length'] for p in paths]

        st.success(f"**Found {len(paths)} path{'s' if len(paths) != 1 else ''} between {concept1} and {concept2}**")

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total Paths", f"{len(paths)}")
        mcol2.metric("Min Length", f"{min(lengths)}")
        mcol3.metric("Avg Length", f"{sum(lengths) / len(lengths):.1f}")
        mcol4.metric("Max Length", f"{max(lengths)}")

        # Compact per-path table with clickable rows (click to jump to the path canvas)
        st.caption("Click a path number to jump to its visualization; use '↑ Back to summary' to return")
        html_rows = ""
        for i, p in enumerate(paths):
            node_types = ', '.join(sorted({nd['label'] for nd in p['node_data']}))
            rel_types = ', '.join(sorted(set(p['rels'])))
            start_name = html.escape(p['node_data'][0]['name'])
            end_name = html.escape(p['node_data'][-1]['name'])
            html_rows += (
                f"<tr>"
                f"<td><a href='#path-{i+1}' style='text-decoration:none; color:inherit; "
                f"display:block; padding:8px;'>{i+1}</a></td>"
                f"<td>{p['length']}</td>"
                f"<td>{start_name} → {end_name}</td>"
                f"<td>{node_types}</td><td>{rel_types}</td></tr>"
            )
        summary_html = f"""
        <div id="path-summary" style="max-height: 400px; overflow-y: auto; border: 1px solid #e0e0e0; border-radius: 4px;">
        <table style="width:100%; border-collapse: collapse;">
        <thead style="position: sticky; top: 0; background: #f8f9fa;">
        <tr style="border-bottom: 2px solid #ddd; text-align: left;">
            <th style="padding: 8px; font-weight: 600;">Path Number</th>
            <th style="padding: 8px; font-weight: 600;">Length</th>
            <th style="padding: 8px; font-weight: 600;">Start → End</th>
            <th style="padding: 8px; font-weight: 600;">Node Types</th>
            <th style="padding: 8px; font-weight: 600;">Relationship Types</th>
        </tr>
        </thead>
        <tbody>
        {html_rows}
        </tbody>
        </table>
        </div>
        """
        st.markdown(summary_html, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 1.5rem'></div>", unsafe_allow_html=True)

        # Color map for node types
        color_map = {
            'Exercise': '#4CAF50',
            'Patient': '#2196F3',
            'Session': '#03A9F4',
            'Outcome': '#00BCD4',
            'ClinicalTrial': '#FF9800',
            'Condition': '#F44336',
            'ICFConcept': '#9C27B0',
            'HPOConcept': '#E91E63',
            'UberonConcept': '#673AB7',
            'MondoDisease': '#795548',
            'ICD10Code': '#607D8B',
            'MELLODConcept': '#8BC34A',
            'KHMOConcept': '#CDDC39',
            'PMRConcept': '#FFEB3B',
            'COPPERConcept': '#FFC107',
            'OPEConcept': '#FF5722',
            'ONTOLOCOConcept': '#9E9E9E',
            'BodyFunction': '#009688',
            'Activity': '#00ACC1',
            'BodyStructure': '#039BE5',
            'EnvironmentalFactor': '#3F51B5',
        }
        
        # Show all paths in Cytoscape
        for i, p in enumerate(paths):
            st.markdown(
                f"<div id='path-{i+1}'><strong>Path {i+1}</strong> (length {p['length']})</div>",
                unsafe_allow_html=True
            )
            
            # Build Cytoscape elements
            elements = []
            node_set = set()
            
            # Get node names for display
            for idx, node_data in enumerate(p['node_data']):
                label = node_data['label']
                name = node_data['name']
                node_id = f"n{idx}"
                node_set.add(node_id)
                color = color_map.get(label, '#9E9E9E')
                
                elements.append({
                    'data': {'id': node_id, 'label': f"{label}\n{name}", 'type': label, 'color': color}
                })
            
            # Add edges
            for idx, rel in enumerate(p['rels']):
                source_id = f"n{idx}"
                target_id = f"n{idx + 1}"
                elements.append({
                    'data': {'source': source_id, 'target': target_id, 'label': rel}
                })
            
            # Build legend HTML
            used_types = set()
            for node_data in p['node_data']:
                used_types.add(node_data['label'])
            
            legend_items = ''
            for node_type in sorted(used_types):
                color = color_map.get(node_type, '#9E9E9E')
                legend_items += f'<span class="legend-item"><span class="legend-color" style="background-color: {color};"></span>{node_type}</span>'
            
            # Build colored path text: (Label: name) -[REL] → (Label: name)
            path_text_parts = []
            for j, nd in enumerate(p['node_data']):
                color = color_map.get(nd['label'], '#9E9E9E')
                node_str = f"<span style='color:{color}; font-weight:bold'>({nd['label']}: {nd['name']})</span>"
                path_text_parts.append(node_str)
                if j < len(p['rels']):
                    rel = p['rels'][j]
                    path_text_parts.append(f" -[<span style='color:#555; font-weight:bold'>{rel}</span>]-> ")
            path_text = ''.join(path_text_parts)
            
            # Cytoscape controls
            ctrl_cols = st.columns([0.5, 1.2, 1, 1, 0.5])
            with ctrl_cols[0]:
                st.markdown("**Graph Layout**")
            with ctrl_cols[1]:
                layout = st.selectbox("Layout", ["cose", "circle", "breadthfirst", "grid"], key=f"layout_{i}", label_visibility="collapsed")
            with ctrl_cols[2]:
                show_labels = st.checkbox("Node Labels", value=True, key=f"labels_{i}")
            with ctrl_cols[3]:
                show_edge_labels = st.checkbox("Edge Labels", value=True, key=f"edge_labels_{i}")
            with ctrl_cols[4]:
                fit_clicked = st.button("Fit", key=f"fit_{i}", help="Fit graph to viewport")
            
            # Cytoscape HTML with Cytoscape.js, legend, and path text
            node_label_display = "'data(label)'" if show_labels else "''"
            edge_label_display = "'data(label)'" if show_edge_labels else "''"
            
            # Layout config based on selection
            if layout == "cose":
                layout_config = """{
                    name: 'cose',
                    idealEdgeLength: function(edge) { return 60; },
                    nodeOverlap: 15,
                    nodeRepulsion: function(node) { return 2000; },
                    edgeElasticity: function(edge) { return 150; },
                    nestingFactor: 1.2,
                    gravity: 0.35,
                    numIter: 1000,
                    padding: 30,
                    fit: true,
                    nodeDimensionsIncludeLabels: true,
                    animate: false
                }"""
            elif layout == "circle":
                layout_config = """{
                    name: 'circle',
                    padding: 30,
                    fit: true,
                    nodeDimensionsIncludeLabels: true,
                    animate: false
                }"""
            elif layout == "breadthfirst":
                layout_config = """{
                    name: 'breadthfirst',
                    directed: true,
                    padding: 30,
                    fit: true,
                    nodeDimensionsIncludeLabels: true,
                    animate: false,
                    spacingFactor: 1.2
                }"""
            else:  # grid
                layout_config = """{
                    name: 'grid',
                    padding: 30,
                    fit: true,
                    nodeDimensionsIncludeLabels: true,
                    animate: false,
                    condense: true,
                    rows: undefined
                }"""
            
            html = f"""
            <html>
            <head>
                <script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
                <style>
                    #cy {{
                        width: 100%;
                        height: 450px;
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                    }}
                    .legend {{
                        font-size: 11px;
                        padding: 8px 5px;
                        text-align: center;
                    }}
                    .legend-item {{
                        display: inline-block;
                        margin: 3px 6px;
                    }}
                    .legend-color {{
                        display: inline-block;
                        width: 10px;
                        height: 10px;
                        border-radius: 50%;
                        margin-right: 3px;
                        vertical-align: middle;
                    }}
                    .path-text {{
                        font-size: 14px;
                        padding: 8px;
                        text-align: center;
                        color: #333333;
                        border-top: 1px solid #e0e0e0;
                        margin-top: 5px;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                    }}
                    .node-info {{
                        font-size: 11px;
                        padding: 5px;
                        text-align: center;
                        color: #666666;
                        font-style: italic;
                        min-height: 20px;
                    }}
                </style>
            </head>
            <body>
                <div id="cy"></div>
                <div class="node-info" id="nodeInfo">Click a node to see details</div>
                <div class="legend">
                    {legend_items}
                </div>
                <div class="path-text">
                    {path_text}
                </div>
                <script>
                    var cy = cytoscape({{
                        container: document.getElementById('cy'),
                        elements: {elements},
                        style: [
                            {{
                                selector: 'node',
                                style: {{
                                    'label': {node_label_display},
                                    'background-color': 'data(color)',
                                    'text-wrap': 'wrap',
                                    'text-max-width': '80px',
                                    'font-size': '10px',
                                    'color': '#000000',
                                    'text-outline-color': '#ffffff',
                                    'text-outline-width': 2,
                                    'shape': 'ellipse',
                                    'width': 50,
                                    'height': 50
                                }}
                            }},
                            {{
                                selector: 'edge',
                                style: {{
                                    'label': {edge_label_display},
                                    'width': 2,
                                    'line-color': '#888888',
                                    'target-arrow-color': '#888888',
                                    'target-arrow-shape': 'triangle',
                                    'curve-style': 'bezier',
                                    'font-size': '8px',
                                    'color': '#333333',
                                    'text-outline-color': '#ffffff',
                                    'text-outline-width': 2
                                }}
                            }},
                            {{
                                selector: 'node:selected',
                                style: {{
                                    'border-width': 3,
                                    'border-color': '#FFD700',
                                    'border-opacity': 1
                                }}
                            }},
                            {{
                                selector: '.highlighted',
                                style: {{
                                    'background-color': '#FFD700',
                                    'line-color': '#FFD700',
                                    'target-arrow-color': '#FFD700',
                                    'transition-property': 'background-color, line-color, target-arrow-color',
                                    'transition-duration': '0.5s'
                                }}
                            }},
                            {{
                                selector: '.faded',
                                style: {{
                                    'opacity': 0.3
                                }}
                            }}
                        ],
                        layout: {layout_config},
                        userZoomingEnabled: true,
                        userPanningEnabled: true
                    }});
                    
                    // Node click handler - highlight connected nodes
                    cy.on('tap', 'node', function(evt) {{
                        var node = evt.target;
                        // Reset all nodes
                        cy.elements().removeClass('highlighted faded');
                        // Highlight clicked node and its neighborhood
                        var neighborhood = node.neighborhood().add(node);
                        neighborhood.addClass('highlighted');
                        cy.elements().not(neighborhood).addClass('faded');
                        // Show node info
                        var data = node.data();
                        document.getElementById('nodeInfo').innerHTML = '<b>' + data.type + '</b>: ' + data.label.replace('\\n', ' - ');
                    }});
                    
                    // Edge click handler
                    cy.on('tap', 'edge', function(evt) {{
                        var edge = evt.target;
                        var data = edge.data();
                        document.getElementById('nodeInfo').innerHTML = '<b>Relationship:</b> ' + data.label + ' (' + data.source + ' → ' + data.target + ')';
                    }});
                    
                    // Click on background to reset
                    cy.on('tap', function(evt) {{
                        if (evt.target === cy) {{
                            cy.elements().removeClass('highlighted faded');
                            document.getElementById('nodeInfo').innerHTML = 'Click a node to see details';
                        }}
                    }});
                    // Fit and center graph to viewport if Fit button was clicked
                    {'cy.ready(function() { cy.center(); cy.fit(undefined, 20); });' if fit_clicked else ''}
                </script>
            </body>
            </html>
            """
            
            components.html(html, height=800)
            st.markdown(
                "<div style='text-align: center; margin: 0.5rem 0 2rem;'>"
                "<a href='#path-summary' style='font-size: 12px; text-decoration: none;'>↑ Back to summary</a>"
                "</div>",
                unsafe_allow_html=True
            )
    else:
        st.warning("No paths found between these concepts. Try different entity types.")

# ── Evidence & Review (clinician review loop) ────────────────────────────
if page == "✅ Evidence & Review":
    from pathlib import Path
    import csv as _csv

    CURATED = Path(__file__).resolve().parent.parent / "curated"
    CONDITION_CSV = CURATED / "condition_exercise.csv"
    SAFETY_CSV = CURATED / "safety_contraindications.csv"

    st.title("✅ Evidence & Review")
    st.markdown("""
    Curated edges (recommendations, precautions, contraindications) are
    **candidates until a clinician reviews them**. The review unit is the
    CSV row in `curated/` — Git stays the system of record; you never
    need to touch Git.

    **Workflow**
    1. Review the unreviewed tables below (or the CSVs directly).
    2. Download the decisions template, fill `decision`
       (`approved`/`rejected`), `reviewed_by`, `reviewed_on`; a citation
       (or DOI) is **required for approvals**.
    3. Apply: `python curated/apply_decisions.py decisions.csv --update-graph`
    4. Reloading the graph (`python import_bulk.py --skip-export`) is not
       needed if you pass `--update-graph`.
    """)
    st.info(
        "Unreviewed rows are research candidates, not clinical advice. "
        "Do not use this data for patient care without local validation."
    )

    st.subheader("📊 Unreviewed edges in the graph")
    unrev = run_query("""
        MATCH ()-[r]->()
        WHERE r.review_status = 'unreviewed'
        RETURN type(r) AS rel_type, count(r) AS edges
        ORDER BY edges DESC
    """)
    if unrev:
        st.dataframe(pd.DataFrame(unrev), use_container_width=True)
    else:
        st.write("No edges with review_status='unreviewed' — load the graph "
                 "with a recent provenance-aware postload first.")

    st.subheader("📋 Unreviewed curated edges (from the graph)")
    for rel_type, title in [
        ("RECOMMENDS_EXERCISE", "Recommendations"),
        ("PRECAUTION", "Precautions"),
        ("CONTRAINDICATION", "Contraindications"),
    ]:
        rows = run_query(f"""
            MATCH (c:Condition)-[r:{rel_type}]->(e:Exercise)
            WHERE r.review_status = 'unreviewed'
            RETURN c.name AS condition, e.name AS exercise,
                   r.rationale AS rationale, r.method AS method,
                   r.match_type AS match_type, r.confidence AS confidence,
                   r.source AS source
            ORDER BY c.name, e.name
            LIMIT 200
        """)
        with st.expander(f"{title} ({len(rows)} shown, cap 200)", expanded=False):
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, height=300)
            else:
                st.write("None matching (graph may predate the provenance postload).")

    st.subheader("⬇️ Decisions template")
    st.caption(
        "One row per curated CSV row. Fill decision/reviewed_by/reviewed_on; "
        "approvals require citation or citation_doi. Rows you leave as "
        "'unreviewed' (or blank) are skipped."
    )

    def _decisions_template(path):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
        out = []
        for row in rows:
            rec = {
                "file": path.name,
                "match_type": row["match_type"],
                "rel_type": row.get("rel_type", ""),
                "condition_key": row["condition_key"],
                "exercise_name": row["exercise_name"],
                "current_status": row["status"],
                "decision": "",
                "reviewed_by": "",
                "reviewed_on": "",
                "citation": "",
                "comment": "",
            }
            out.append(rec)
        return out

    tmpl = _decisions_template(CONDITION_CSV) + _decisions_template(SAFETY_CSV)
    tmpl_df = pd.DataFrame(tmpl)
    st.dataframe(tmpl_df.head(15), use_container_width=True)
    st.download_button(
        "Download decisions template (CSV)",
        data=tmpl_df.to_csv(index=False),
        file_name="review_decisions.csv",
        mime="text/csv",
    )

    st.subheader("▶️ Apply decisions")
    st.code("python curated/apply_decisions.py review_decisions.csv --update-graph",
            language="bash")
    st.caption(
        "--update-graph re-runs the idempotent curated loaders against the "
        "live database so approved edges reflect immediately; without it, "
        "decisions take effect at the next full load."
    )

# Footer
st.markdown("---")
st.markdown("""
**RehabKG Dashboard v0.1** - Prototype | 
[GitHub](https://github.com/udel-cbcb/RehabKG) | 
Built with Streamlit + Neo4j
""")

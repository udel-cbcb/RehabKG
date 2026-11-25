"""
End-to-end tests for the RehabKG Dashboard using Playwright.

Run: python3 -m pytest tests/test_e2e.py -v
Requires: pip install playwright pytest-playwright && playwright install chromium
Requires: Dashboard running on http://localhost:8501
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"

SIDEBAR = "[data-testid='stSidebar']"
METRIC = "[data-testid='stMetric']"
DATAFRAME = "[data-testid='stDataFrame']"
SELECTBOX = "[data-testid='stSelectbox']"
CHECKBOX = "[data-testid='stCheckbox']"
# st.info testid: stNotificationContentInfo on Streamlit <1.46, stAlert on newer
INFO_ALERT = "[data-testid='stNotificationContentInfo'], [data-testid='stAlert']"


@pytest.fixture(scope="session")
def browser_context_args():
    return {"viewport": {"width": 1440, "height": 900}}


def goto_page(page: Page, nav_label: str):
    """Load the dashboard and navigate to a page via the sidebar radio."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    if nav_label:
        page.locator(SIDEBAR).locator("label").filter(has_text=nav_label).click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)


# ───────────────────── Overview Page ─────────────────────

class TestOverviewPage:
    """Tests for the Overview page (default landing page)."""

    def test_page_loads(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page).to_have_title("RehabKG Dashboard")

    def test_sidebar_visible(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.locator(SIDEBAR)).to_be_visible()
        expect(page.locator(SIDEBAR)).to_contain_text("RehabKG Dashboard")

    def test_graph_statistics_visible(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        sidebar = page.locator(SIDEBAR)
        expect(sidebar).to_contain_text("Graph Statistics")
        expect(sidebar).to_contain_text("Nodes")
        expect(sidebar).to_contain_text("Relationships")

    def test_overview_title(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Rehabilitation Knowledge Graph (RehabKG)")).to_be_visible()

    def test_key_metrics_displayed(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        metrics = page.locator(METRIC)
        expect(metrics).to_have_count(12)
        # Sidebar: Nodes, Relationships; Main: Exercises, Clinical Trials, Patients, Ontology Concepts,
        # Sessions, Outcomes, Adverse Events, Assessment Scales, Muscles, Equipment
        expect(metrics.nth(2)).to_contain_text("Exercises")
        expect(metrics.nth(3)).to_contain_text("Clinical Trials")
        expect(metrics.nth(4)).to_contain_text("Patients")
        expect(metrics.nth(5)).to_contain_text("Ontology Concepts")

    def test_data_sources_section(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Data Sources")).to_be_visible()
        expect(page.get_by_text("Where each piece of data comes from")).to_be_visible()

    def test_quick_links_visible(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Quick Links")).to_be_visible()

    def test_entity_types_section(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Entity Types")).to_be_visible()
        expect(page.get_by_text("Types of nodes in the knowledge graph")).to_be_visible()

    def test_relationship_types_section(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Relationship Types")).to_be_visible()
        expect(page.get_by_text("How entities are connected to each other")).to_be_visible()

    def test_dataframes_render(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        # Data Sources, Entity Types, Relationship Types tables
        expect(page.locator(DATAFRAME)).to_have_count(3)

    def test_footer_visible(self, page: Page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("RehabKG Dashboard v0.1")).to_be_visible()


# ───────────────────── Navigation ─────────────────────

class TestNavigation:
    """Tests for sidebar navigation between pages."""

    def test_navigate_to_exercises(self, page: Page):
        goto_page(page, "Exercises")
        expect(page.get_by_text("Exercise Explorer")).to_be_visible()

    def test_navigate_to_clinical_trials(self, page: Page):
        goto_page(page, "Clinical Trials")
        expect(page.get_by_text("Clinical Trial Finder")).to_be_visible()

    def test_navigate_to_patients(self, page: Page):
        goto_page(page, "Patients")
        expect(page.get_by_text("Patient Outcomes")).to_be_visible()

    def test_navigate_to_ontologies(self, page: Page):
        goto_page(page, "Ontologies")
        expect(page.get_by_text("Ontology Explorer")).to_be_visible()

    def test_navigate_to_knowledge_discovery(self, page: Page):
        goto_page(page, "Knowledge Discovery")
        expect(page.get_by_text("Explore Graph Connectivity")).to_be_visible()

    def test_navigate_back_to_overview(self, page: Page):
        goto_page(page, "Knowledge Discovery")
        page.locator(SIDEBAR).locator("label").filter(has_text="Overview").click()
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Rehabilitation Knowledge Graph (RehabKG)")).to_be_visible()


# ───────────────────── Exercise Explorer ─────────────────────

class TestExerciseExplorer:
    """Tests for the Exercise Explorer page."""

    def test_page_loads(self, page: Page):
        goto_page(page, "Exercises")
        expect(page.get_by_role("heading", name="Therapeutic Exercises")).to_be_visible()
        expect(page.get_by_text("949 therapeutic exercises")).to_be_visible()

    def test_category_filter(self, page: Page):
        goto_page(page, "Exercises")
        expect(page.get_by_text("Category", exact=True).first).to_be_visible()

    def test_level_filter(self, page: Page):
        goto_page(page, "Exercises")
        expect(page.get_by_text("Level", exact=True).first).to_be_visible()

    def test_exercise_table_renders(self, page: Page):
        goto_page(page, "Exercises")
        expect(page.locator(DATAFRAME).first).to_be_visible()

    def test_exercise_muscle_chart(self, page: Page):
        goto_page(page, "Exercises")
        expect(page.get_by_text("Exercise → Muscle Connections")).to_be_visible()


# ───────────────────── Clinical Trials ─────────────────────

class TestClinicalTrials:
    """Tests for the Clinical Trial Finder page."""

    def test_page_loads(self, page: Page):
        goto_page(page, "Clinical Trials")
        expect(page.get_by_text("Clinical Trial Finder")).to_be_visible()
        expect(page.get_by_text("1,387 rehabilitation clinical trials")).to_be_visible()

    def test_search_condition_input(self, page: Page):
        goto_page(page, "Clinical Trials")
        expect(page.get_by_text("Search Condition")).to_be_visible()

    def test_status_filter(self, page: Page):
        goto_page(page, "Clinical Trials")
        expect(page.get_by_text("Status", exact=True).first).to_be_visible()

    def test_trials_table_renders(self, page: Page):
        goto_page(page, "Clinical Trials")
        expect(page.locator(DATAFRAME).first).to_be_visible()

    def test_status_distribution_chart(self, page: Page):
        goto_page(page, "Clinical Trials")
        expect(page.get_by_text("Trial Status Distribution")).to_be_visible()


# ───────────────────── Patients ─────────────────────

class TestPatients:
    """Tests for the Patient Outcomes page."""

    def test_page_loads(self, page: Page):
        goto_page(page, "Patients")
        expect(page.get_by_text("Patient Outcomes")).to_be_visible()
        expect(page.get_by_text("1,006 amputation patients")).to_be_visible()

    def test_amputation_side_chart(self, page: Page):
        goto_page(page, "Patients")
        expect(page.get_by_text("Amputation Side Distribution")).to_be_visible()

    def test_outcome_improvement_chart(self, page: Page):
        goto_page(page, "Patients")
        expect(page.get_by_text("Outcome Improvement by Cause")).to_be_visible()

    def test_improvement_table_renders(self, page: Page):
        goto_page(page, "Patients")
        expect(page.locator(DATAFRAME).first).to_be_visible()


# ───────────────────── Ontology Explorer ─────────────────────

class TestOntologyExplorer:
    """Tests for the Ontology Explorer page."""

    def test_page_loads(self, page: Page):
        goto_page(page, "Ontologies")
        expect(page.get_by_text("Ontology Explorer")).to_be_visible()
        expect(page.get_by_text("Medical Ontologies")).to_be_visible()

    def test_ontology_selector(self, page: Page):
        goto_page(page, "Ontologies")
        expect(page.get_by_text("Select Ontology")).to_be_visible()
        expect(page.locator(SELECTBOX).first).to_be_visible()

    def test_icf_default_selected(self, page: Page):
        goto_page(page, "Ontologies")
        expect(page.get_by_text("ICF (International Classification of Functioning)")).to_be_visible()

    def test_icf_exercise_connections(self, page: Page):
        goto_page(page, "Ontologies")
        expect(page.get_by_text("ICF → Exercise Connections")).to_be_visible()

    def test_concepts_table_renders(self, page: Page):
        goto_page(page, "Ontologies")
        expect(page.locator(DATAFRAME).first).to_be_visible()

    def test_switch_ontology_hpo(self, page: Page):
        goto_page(page, "Ontologies")
        # Open the selectbox and choose HPO
        page.locator(SELECTBOX).first.click()
        page.wait_for_timeout(500)
        page.locator("[role='option']", has_text="HPO").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        expect(page.locator(INFO_ALERT).first).to_contain_text("Human Phenotype Ontology")

    def test_switch_ontology_icd10(self, page: Page):
        goto_page(page, "Ontologies")
        page.locator(SELECTBOX).first.click()
        page.wait_for_timeout(500)
        page.locator("[role='option']", has_text="ICD10").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        expect(page.locator(INFO_ALERT).first).to_contain_text("ICD-10-CM")

    def test_switch_ontology_pain(self, page: Page):
        """PAIN browser shows pain concepts from the focused graph."""
        goto_page(page, "Ontologies")
        page.locator(SELECTBOX).first.click()
        page.wait_for_timeout(500)
        page.locator("[role='option']", has_text="PAIN").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        expect(page.locator(INFO_ALERT).first).to_contain_text("The Pain Ontology")
        expect(page.locator(DATAFRAME).first).to_contain_text("abdominal pain")


# ───────────────────── Knowledge Discovery ─────────────────────

class TestKnowledgeDiscovery:
    """Tests for the Knowledge Discovery page."""

    def test_page_loads(self, page: Page):
        goto_page(page, "Knowledge Discovery")
        expect(page.get_by_text("Explore Graph Connectivity")).to_be_visible()
        expect(page.get_by_text("Find Paths Between Concepts")).to_be_visible()

    def test_entity_selectors(self, page: Page):
        goto_page(page, "Knowledge Discovery")
        expect(page.get_by_text("Start Concept")).to_be_visible()
        expect(page.get_by_text("End Concept")).to_be_visible()

    def test_find_paths_button(self, page: Page):
        goto_page(page, "Knowledge Discovery")
        expect(page.get_by_role("button", name="Find Paths")).to_be_visible()

    def test_disconnected_components(self, page: Page):
        goto_page(page, "Knowledge Discovery")
        expect(page.get_by_text("Disconnected Components").first).to_be_visible()
        expect(page.get_by_text("candidates for new bridges")).to_be_visible()

    def test_find_paths_flow(self, page: Page):
        """End-to-end: select Exercise → ICFConcept and find paths."""
        goto_page(page, "Knowledge Discovery")

        # Start category selectbox (first selectbox on page)
        page.locator(SELECTBOX).nth(0).click()
        page.wait_for_timeout(500)
        page.locator("[role='option']", has_text="Clinical Data").click()
        page.wait_for_timeout(500)

        # Start entity: Exercise
        page.locator(SELECTBOX).nth(1).click()
        page.wait_for_timeout(500)
        page.locator("[role='option']", has_text="Exercise").click()
        page.wait_for_timeout(500)

        # End category: Ontology (default) - end entity: ICFConcept.
        # Type to filter: with many ontology labels in the graph the dropdown
        # virtualizes its options, so ICFConcept may not be in the initial DOM.
        page.locator(SELECTBOX).nth(3).click()
        page.wait_for_timeout(500)
        page.keyboard.type("ICFConcept", delay=25)
        page.wait_for_timeout(500)
        page.locator("[role='option']", has_text="ICFConcept").click()
        page.wait_for_timeout(500)

        # Click Find Paths
        page.get_by_role("button", name="Find Paths").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000)

        # Either paths found or warning shown
        paths_found = page.get_by_text("Path 1").count() > 0
        warning_shown = page.get_by_text("No paths found").count() > 0
        assert paths_found or warning_shown, "Expected paths or a no-paths warning"

        # If paths were found, the summary block must be present
        if paths_found:
            expect(page.get_by_text("Found", exact=False).first).to_be_visible()
            expect(page.get_by_text("Total Paths")).to_be_visible()
            # Click a summary row link and verify it scrolls to the path canvas
            page.locator("table tbody tr a[href^='#path-']").first.click()
            page.wait_for_timeout(2000)
            # Path canvas should exist (may need scroll to be in viewport)
            assert page.locator("#path-1").count() > 0, "Path canvas should exist after clicking summary row"

            # Click "Back to summary" and verify the summary table exists
            page.locator("a[href='#path-summary']").first.click()
            page.wait_for_timeout(1500)
            assert page.locator("#path-summary").count() > 0, "Summary table should exist"
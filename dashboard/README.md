# RehabKG Dashboard

Prototype dashboard for Rehabilitation Knowledge Graph analytics.

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r dashboard/requirements.txt

# Run dashboard
streamlit run dashboard/app.py
```

## Features

### 📊 Overview
- Graph statistics (nodes, relationships)
- Data source distribution
- Relationship type breakdown

### 🏋️ Exercises
- Search exercises by category and level
- View exercise → muscle connections
- Filter by equipment

### 🔬 Clinical Trials
- Search trials by condition
- Filter by trial status
- View enrollment statistics

### 👤 Patients
- MOTU patient outcomes
- Amputation side distribution
- Outcome improvement by cause

### 🧬 Ontologies
- Browse ICF, HPO, Uberon, Mondo concepts
- View ICF → exercise connections
- Explore ontology hierarchies

### 🔍 Knowledge Discovery
- Find paths between concepts
- Identify disconnected components
- Explore graph connectivity

## Production Considerations

For production deployment, consider:

1. **Frontend**: Migrate to React/Next.js for better UX
2. **Backend**: Use FastAPI for REST API
3. **Authentication**: Add user authentication
4. **Caching**: Implement Redis caching
5. **Deployment**: Docker + Kubernetes

## Architecture (Production)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React/Next.js │────▶│   FastAPI       │────▶│   Neo4j         │
│   Frontend      │     │   Backend       │     │   Database      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   User Interface        REST API              Graph Database
   - Dashboard           - /exercises          - Queries
   - Filters             - /trials             - Transactions
   - Visualizations      - /patients           - Analytics
```

## File Structure

```
dashboard/
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

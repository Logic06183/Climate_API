"""
🏥 Climate-Health Analysis Web Application
===========================================

Upload your health data, extract climate data, run analysis, and create maps!

NO SYNTHETIC DATA - Only uses your real uploaded data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import io
import base64
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from climate_toolkit import ClimateDataExtractor, ClimateDataExporter
from climate_toolkit.health import ClimateHealthIntegrator
from climate_toolkit.core import DataQualityValidator
from climate_toolkit.config import ClimateToolkitConfig, GEEConfig

# Page config
st.set_page_config(
    page_title="Climate-Health Analysis Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    </style>
""", unsafe_allow_html=True)


def create_template_csv():
    """Create template health data CSV."""
    template_data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03', '...'],
        'total_births': [150, 148, 152, '...'],
        'preterm_births': [12, 11, 13, '...'],
        'cvd_events': [25, 23, 27, '...'],
        'notes': ['Required', 'Required', 'Required', 'Optional']
    }
    return pd.DataFrame(template_data)


def validate_health_data(df):
    """Validate uploaded health data format."""
    errors = []
    warnings = []

    # Check required column
    if 'date' not in df.columns:
        errors.append("❌ Missing required 'date' column")
        return errors, warnings

    # Try to convert date
    try:
        df['date'] = pd.to_datetime(df['date'])
    except:
        errors.append("❌ 'date' column contains invalid dates. Use YYYY-MM-DD format")
        return errors, warnings

    # Check for at least one health outcome column
    health_cols = [col for col in df.columns if col != 'date']
    if len(health_cols) == 0:
        errors.append("❌ No health outcome columns found. Add at least one outcome variable")

    # Check for negative values
    for col in health_cols:
        if df[col].dtype in [np.int64, np.float64]:
            if (df[col] < 0).any():
                warnings.append(f"⚠️ Column '{col}' contains negative values")

    # Check for missing values
    missing_pct = df.isnull().sum() / len(df) * 100
    for col, pct in missing_pct.items():
        if pct > 20:
            warnings.append(f"⚠️ Column '{col}' has {pct:.1f}% missing values")

    return errors, warnings


def download_link(df, filename, text):
    """Generate download link for dataframe."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def main():
    # Header
    st.markdown('<div class="main-header">🏥 Climate-Health Analysis Platform</div>',
                unsafe_allow_html=True)

    st.markdown("""
    **Upload your health data, extract climate data, analyze relationships, and create maps!**

    ✅ No synthetic data - uses only your real data
    ✅ Automatic climate data extraction from Google Earth Engine
    ✅ Statistical analysis with temporal lags
    ✅ Publication-ready figures and tables
    ✅ Interactive maps
    """)

    # Sidebar
    st.sidebar.title("⚙️ Configuration")

    # GEE Project ID
    gee_project = st.sidebar.text_input(
        "Google Earth Engine Project ID",
        value="joburg-hvi",
        help="Your GEE project ID. Get one at https://earthengine.google.com"
    )

    # Study Location
    st.sidebar.subheader("📍 Study Location")
    location_name = st.sidebar.text_input("Location Name", "Johannesburg, South Africa")

    col1, col2 = st.sidebar.columns(2)
    latitude = col1.number_input("Latitude", value=-26.2041, format="%.4f")
    longitude = col2.number_input("Longitude", value=28.0473, format="%.4f")

    # Date Range
    st.sidebar.subheader("📅 Study Period")
    start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
    end_date = st.sidebar.date_input("End Date", datetime(2023, 12, 31))

    # Analysis Options
    st.sidebar.subheader("🔬 Analysis Options")
    lag_days_str = st.sidebar.text_input(
        "Lag Periods (days, comma-separated)",
        "0,7,14,21,30",
        help="Test these lag periods between exposure and outcome"
    )
    lag_days = [int(x.strip()) for x in lag_days_str.split(',')]

    thresholds_str = st.sidebar.text_input(
        "Heat Thresholds (°C, comma-separated)",
        "25,28,30,32,35",
        help="Temperature thresholds for analysis"
    )
    thresholds = [float(x.strip()) for x in thresholds_str.split(',')]

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Data",
        "🌡️ Extract Climate",
        "📊 Run Analysis",
        "🗺️ Create Maps"
    ])

    # ===================================================================
    # TAB 1: Upload Health Data
    # ===================================================================
    with tab1:
        st.header("📤 Upload Your Health Data")

        st.markdown("""
        ### Data Format Requirements

        Your CSV file must include:
        - **`date`** column (YYYY-MM-DD format) - **REQUIRED**
        - At least one health outcome column (e.g., `preterm_births`, `cvd_events`, etc.)

        Optional columns:
        - `total_births`, `population`, demographic variables, etc.
        """)

        # Download template
        st.subheader("📥 Download Template")
        template_df = create_template_csv()

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(template_df, use_container_width=True)
        with col2:
            st.download_button(
                label="⬇️ Download Template CSV",
                data=template_df.to_csv(index=False),
                file_name="health_data_template.csv",
                mime="text/csv"
            )

        # File upload
        st.subheader("📁 Upload Your Data")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload your health data in CSV format"
        )

        if uploaded_file is not None:
            try:
                # Read the file
                health_df = pd.read_csv(uploaded_file)

                st.success(f"✅ File uploaded: {uploaded_file.name}")

                # Validate
                errors, warnings = validate_health_data(health_df)

                if errors:
                    st.error("**Data Validation Failed:**")
                    for error in errors:
                        st.markdown(error)
                    st.session_state.health_data = None
                else:
                    if warnings:
                        st.warning("**Warnings:**")
                        for warning in warnings:
                            st.markdown(warning)

                    st.success("✅ **Data validation passed!**")

                    # Store in session state
                    health_df['date'] = pd.to_datetime(health_df['date'])
                    st.session_state.health_data = health_df

                    # Preview
                    st.subheader("📋 Data Preview")
                    st.dataframe(health_df.head(10), use_container_width=True)

                    # Summary
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Records", len(health_df))
                    col2.metric("Date Range",
                               f"{health_df['date'].min().date()} to {health_df['date'].max().date()}")
                    col3.metric("Columns", health_df.shape[1])

            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
                st.session_state.health_data = None
        else:
            st.info("👆 Please upload your health data CSV file to begin")

    # ===================================================================
    # TAB 2: Extract Climate Data
    # ===================================================================
    with tab2:
        st.header("🌡️ Extract Climate Data")

        st.markdown(f"""
        ### Settings
        - **Location**: {location_name}
        - **Coordinates**: {latitude}, {longitude}
        - **Period**: {start_date} to {end_date}
        - **GEE Project**: {gee_project}
        """)

        if st.button("🚀 Extract Climate Data", type="primary", use_container_width=True):
            with st.spinner("Extracting climate data from Google Earth Engine..."):
                try:
                    config = ClimateToolkitConfig(
                        gee=GEEConfig(project_id=gee_project)
                    )

                    extractor = ClimateDataExtractor(config)

                    result = extractor.extract_climate_data(
                        lat=latitude,
                        lon=longitude,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        location_name=location_name,
                        calculate_monthly=True
                    )

                    st.session_state.climate_data = result['daily']
                    st.session_state.monthly_data = result['monthly']

                    st.success("✅ **Climate data extracted successfully!**")

                    # Display summary
                    climate_df = result['daily']

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Days", len(climate_df))
                    col2.metric("Mean Max Temp", f"{climate_df['tmax_celsius'].mean():.1f}°C")
                    col3.metric("Max Temp", f"{climate_df['tmax_celsius'].max():.1f}°C")
                    col4.metric("Days >30°C", (climate_df['tmax_celsius'] > 30).sum())

                    # Preview
                    st.subheader("📋 Climate Data Preview")
                    st.dataframe(climate_df.head(10), use_container_width=True)

                    # Download option
                    st.download_button(
                        label="⬇️ Download Climate Data",
                        data=climate_df.to_csv(index=False),
                        file_name=f"climate_data_{location_name.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )

                except Exception as e:
                    st.error(f"❌ Error extracting climate data: {e}")
                    st.info("""
                    **Troubleshooting:**
                    - Ensure you're authenticated with Google Earth Engine
                    - Check your GEE project ID is correct
                    - Verify your internet connection
                    """)

        # Show if already extracted
        if hasattr(st.session_state, 'climate_data'):
            st.success("✅ Climate data ready for analysis!")

    # ===================================================================
    # TAB 3: Run Analysis
    # ===================================================================
    with tab3:
        st.header("📊 Climate-Health Analysis")

        # Check prerequisites
        has_health = hasattr(st.session_state, 'health_data') and st.session_state.health_data is not None
        has_climate = hasattr(st.session_state, 'climate_data') and st.session_state.climate_data is not None

        if not has_health:
            st.warning("⚠️ Please upload health data in Tab 1")
        if not has_climate:
            st.warning("⚠️ Please extract climate data in Tab 2")

        if has_health and has_climate:
            st.success("✅ Both health and climate data are ready!")

            health_df = st.session_state.health_data
            climate_df = st.session_state.climate_data

            # Select outcome variable
            health_cols = [col for col in health_df.columns if col != 'date']
            outcome_col = st.selectbox(
                "Select Health Outcome Variable",
                health_cols,
                help="Choose the health outcome to analyze"
            )

            if st.button("🔬 Run Analysis", type="primary", use_container_width=True):
                with st.spinner("Running climate-health analysis..."):
                    try:
                        integrator = ClimateHealthIntegrator()

                        # Merge data
                        merged = integrator.merge_climate_health(
                            climate_df=climate_df,
                            health_df=health_df,
                            lag_days=lag_days
                        )

                        st.session_state.merged_data = merged

                        # Run analysis
                        report = integrator.generate_research_report(
                            merged_df=merged,
                            temperature_col='tmax_celsius',
                            health_outcome_col=outcome_col,
                            output_path=None
                        )

                        st.session_state.analysis_report = report

                        # Display results
                        st.success("✅ **Analysis Complete!**")

                        # Correlation results
                        st.subheader("🔗 Correlation Analysis")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Correlation (r)", f"{report['correlation']['pearson_r']:.3f}")
                        col2.metric("P-value", f"{report['correlation']['p_value']:.4f}")

                        if report['correlation']['significant']:
                            col3.markdown("**✅ Significant**")
                        else:
                            col3.markdown("**❌ Not Significant**")

                        # Heat threshold analysis
                        st.subheader("🌡️ Heat Threshold Analysis")
                        threshold_df = report['threshold_analysis']
                        st.dataframe(threshold_df, use_container_width=True)

                        # Visualization
                        st.subheader("📈 Exposure-Response Curve")
                        fig = integrator.plot_exposure_response(
                            merged_df=merged,
                            exposure_col='tmax_celsius',
                            outcome_col=outcome_col
                        )
                        st.pyplot(fig)

                        # Distributed lag
                        st.subheader("⏰ Distributed Lag Analysis")
                        lag_df = report['distributed_lag']
                        significant_lags = lag_df[lag_df['significant']]

                        if len(significant_lags) > 0:
                            st.success(f"Found {len(significant_lags)} significant lag periods:")
                            st.dataframe(significant_lags, use_container_width=True)
                        else:
                            st.info("No statistically significant lag periods found")

                        # Download results
                        st.subheader("⬇️ Download Results")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.download_button(
                                "📊 Merged Data",
                                merged.to_csv(index=False),
                                "merged_climate_health.csv",
                                mime="text/csv"
                            )

                        with col2:
                            st.download_button(
                                "📈 Threshold Analysis",
                                threshold_df.to_csv(index=False),
                                "heat_threshold_analysis.csv",
                                mime="text/csv"
                            )

                        with col3:
                            st.download_button(
                                "⏰ Lag Analysis",
                                lag_df.to_csv(index=False),
                                "distributed_lag_results.csv",
                                mime="text/csv"
                            )

                    except Exception as e:
                        st.error(f"❌ Analysis error: {e}")
                        import traceback
                        st.code(traceback.format_exc())

    # ===================================================================
    # TAB 4: Create Maps
    # ===================================================================
    with tab4:
        st.header("🗺️ Interactive Maps")

        has_merged = hasattr(st.session_state, 'merged_data')

        if not has_merged:
            st.warning("⚠️ Please run analysis in Tab 3 first")
        else:
            st.success("✅ Data ready for mapping!")

            merged = st.session_state.merged_data

            st.info("""
            **Map Features Coming Soon:**
            - Interactive heat maps
            - Vulnerability zones
            - Risk stratification
            - Temporal animation

            For now, use the analysis outputs from Tab 3!
            """)

            # Show location on map
            st.subheader("📍 Study Location")
            map_data = pd.DataFrame({
                'lat': [latitude],
                'lon': [longitude]
            })
            st.map(map_data, zoom=10)


if __name__ == "__main__":
    # Initialize session state
    if 'health_data' not in st.session_state:
        st.session_state.health_data = None
    if 'climate_data' not in st.session_state:
        st.session_state.climate_data = None

    main()

#!/usr/bin/env python3
"""
🏥 WORKING MVP: Johannesburg Heat-Health Analysis
==================================================

This script demonstrates the COMPLETE climate-health analysis workflow:
1. Extract real climate data for Johannesburg (2023)
2. Generate realistic health outcome data
3. Merge with temporal lags
4. Perform statistical analysis
5. Generate publication-ready outputs

RUN THIS NOW: python johannesburg_heat_health_mvp.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from climate_toolkit import ClimateDataExtractor, ClimateDataExporter
from climate_toolkit.health import ClimateHealthIntegrator
from climate_toolkit.config import ClimateToolkitConfig, GEEConfig
from climate_toolkit.logger import setup_logger


def generate_realistic_health_data(climate_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate realistic health outcome data.

    In real research, this would be replaced with actual hospital/clinic data.
    This creates synthetic data that responds to temperature.
    """
    print("\n📊 Generating realistic health outcome data...")

    np.random.seed(42)  # Reproducible

    health_data = []

    for idx, row in climate_df.iterrows():
        date = row['date']
        temp = row['tmax_celsius']

        # Base rates per 1000 births/population
        base_preterm_rate = 8.0  # 8 per 1000 births
        base_cvd_rate = 2.5  # 2.5 cardiovascular events per 1000 population/day

        # Temperature effect (increases with heat)
        # Every 1°C above 28°C increases risk by 3%
        temp_excess = max(0, temp - 28)
        temp_effect = 1 + (temp_excess * 0.03)

        # Add random variation
        preterm_rate = base_preterm_rate * temp_effect * np.random.normal(1, 0.15)
        cvd_rate = base_cvd_rate * temp_effect * np.random.normal(1, 0.20)

        # Population denominators
        daily_births = np.random.poisson(150)  # ~150 births/day in Johannesburg
        population_at_risk = 50000  # Population segment at risk

        # Calculate outcomes
        preterm_births = int(np.random.poisson(daily_births * preterm_rate / 1000))
        cvd_events = int(np.random.poisson(population_at_risk * cvd_rate / 1000))

        health_data.append({
            'date': date,
            'daily_births': daily_births,
            'preterm_births': preterm_births,
            'preterm_rate': (preterm_births / daily_births * 1000) if daily_births > 0 else 0,
            'cvd_events': cvd_events,
            'cvd_rate': cvd_events / population_at_risk * 1000,
        })

    health_df = pd.DataFrame(health_data)

    print(f"  ✓ Generated {len(health_df)} days of health data")
    print(f"  ✓ Mean preterm birth rate: {health_df['preterm_rate'].mean():.2f} per 1000")
    print(f"  ✓ Mean CVD event rate: {health_df['cvd_rate'].mean():.2f} per 1000")

    return health_df


def main():
    """Run complete heat-health analysis MVP."""

    print("\n" + "="*70)
    print("🏥 JOHANNESBURG HEAT-HEALTH ANALYSIS MVP")
    print("="*70)

    # Setup
    logger = setup_logger()
    output_dir = Path("./mvp_outputs")
    output_dir.mkdir(exist_ok=True)

    # Configuration
    config = ClimateToolkitConfig(
        gee=GEEConfig(project_id="joburg-hvi")  # Replace with your project
    )

    # Study parameters
    location_name = "Johannesburg, South Africa"
    lat = -26.2041
    lon = 28.0473
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    print(f"\n📍 Study Location: {location_name}")
    print(f"📅 Study Period: {start_date} to {end_date}")
    print(f"📂 Output Directory: {output_dir}")

    # ============================================================
    # STEP 1: Extract Climate Data
    # ============================================================
    print("\n" + "-"*70)
    print("STEP 1: EXTRACTING CLIMATE DATA FROM GOOGLE EARTH ENGINE")
    print("-"*70)

    try:
        extractor = ClimateDataExtractor(config)

        result = extractor.extract_climate_data(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            location_name=location_name,
            calculate_monthly=True
        )

        climate_df = result['daily']
        monthly_df = result['monthly']

        print(f"\n✅ Extracted {len(climate_df)} days of temperature data")
        print(f"\nTemperature Summary:")
        print(f"  • Mean max temp: {climate_df['tmax_celsius'].mean():.1f}°C")
        print(f"  • Max temp recorded: {climate_df['tmax_celsius'].max():.1f}°C")
        print(f"  • Days >30°C: {(climate_df['tmax_celsius'] > 30).sum()}")
        print(f"  • Days >35°C: {(climate_df['tmax_celsius'] > 35).sum()}")

    except Exception as e:
        print(f"\n❌ Error extracting climate data: {e}")
        print("\nNote: This requires Google Earth Engine authentication.")
        print("If you get an error, you can use the pre-extracted sample data instead.")
        print("\nFor now, creating sample climate data for demonstration...")

        # Create sample data for demonstration
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        np.random.seed(42)

        # Realistic Johannesburg temperatures
        seasonal = 10 * np.sin(np.linspace(0, 2*np.pi, len(dates)))
        daily_var = np.random.normal(0, 3, len(dates))

        climate_df = pd.DataFrame({
            'date': dates,
            'tmax_celsius': 28 + seasonal + daily_var,
            'tmean_celsius': 23 + seasonal + daily_var,
        })

        print(f"✓ Created sample climate data: {len(climate_df)} days")

    # ============================================================
    # STEP 2: Generate Health Data
    # ============================================================
    print("\n" + "-"*70)
    print("STEP 2: GENERATING HEALTH OUTCOME DATA")
    print("-"*70)

    health_df = generate_realistic_health_data(climate_df)

    # ============================================================
    # STEP 3: Integrate Climate and Health Data
    # ============================================================
    print("\n" + "-"*70)
    print("STEP 3: INTEGRATING CLIMATE-HEALTH DATA")
    print("-"*70)

    integrator = ClimateHealthIntegrator()

    # Merge with temporal lags (critical for climate-health research!)
    merged_df = integrator.merge_climate_health(
        climate_df=climate_df,
        health_df=health_df,
        time_column='date',
        lag_days=[0, 7, 14, 21, 30]  # Test different exposure windows
    )

    print(f"\n✅ Merged dataset created:")
    print(f"  • Observations: {len(merged_df)}")
    print(f"  • Variables: {merged_df.shape[1]}")
    print(f"  • Includes 5 lag periods: 0, 7, 14, 21, 30 days")

    # ============================================================
    # STEP 4: Statistical Analysis
    # ============================================================
    print("\n" + "-"*70)
    print("STEP 4: STATISTICAL ANALYSIS")
    print("-"*70)

    # Analyze preterm births
    print("\n📊 PRETERM BIRTHS AND HEAT EXPOSURE:")
    print("-"*70)

    report = integrator.generate_research_report(
        merged_df=merged_df,
        temperature_col='tmax_celsius',
        health_outcome_col='preterm_rate',
        output_path=output_dir / 'preterm_births_analysis.txt'
    )

    print(f"\n  Correlation: r = {report['correlation']['pearson_r']:.3f}")
    print(f"  P-value: {report['correlation']['p_value']:.4f}")
    print(f"  Significant: {'YES ✓' if report['correlation']['significant'] else 'NO'}")

    # Heat threshold analysis
    print("\n📈 HEAT THRESHOLD ANALYSIS:")
    print("-"*70)
    threshold_df = report['threshold_analysis']

    for _, row in threshold_df.iterrows():
        sig = "***" if row['p_value'] < 0.001 else ("**" if row['p_value'] < 0.01 else ("*" if row['p_value'] < 0.05 else ""))
        print(f"  ≥{row['threshold_celsius']}°C: RR = {row['relative_risk']:.2f} "
              f"(p={row['p_value']:.4f}) {sig}")

    # Distributed lag analysis
    print("\n⏰ DISTRIBUTED LAG ANALYSIS:")
    print("-"*70)
    lag_df = report['distributed_lag']
    significant_lags = lag_df[lag_df['significant']].sort_values('correlation', ascending=False)

    if len(significant_lags) > 0:
        print(f"  Significant lag periods found: {len(significant_lags)}")
        print("\n  Strongest effects:")
        for _, row in significant_lags.head(3).iterrows():
            print(f"    Lag {row['lag_days']} days: r = {row['correlation']:.3f} (p={row['p_value']:.4f})")
    else:
        print("  No statistically significant lag periods found")

    # ============================================================
    # STEP 5: Create Visualizations
    # ============================================================
    print("\n" + "-"*70)
    print("STEP 5: CREATING PUBLICATION-READY VISUALIZATIONS")
    print("-"*70)

    # Plot 1: Exposure-response curve
    fig1 = integrator.plot_exposure_response(
        merged_df=merged_df,
        exposure_col='tmax_celsius',
        outcome_col='preterm_rate',
        bins=15
    )
    fig1.savefig(output_dir / 'exposure_response_curve.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: exposure_response_curve.png")
    plt.close(fig1)

    # Plot 2: Time series
    fig2, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Temperature over time
    axes[0].plot(merged_df['date'], merged_df['tmax_celsius'], 'r-', alpha=0.7, linewidth=1)
    axes[0].axhline(y=30, color='orange', linestyle='--', label='30°C threshold')
    axes[0].axhline(y=35, color='red', linestyle='--', label='35°C threshold')
    axes[0].set_ylabel('Max Temperature (°C)', fontsize=12)
    axes[0].set_title('Temperature and Preterm Birth Rate - Johannesburg 2023',
                     fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Health outcomes over time
    axes[1].plot(merged_df['date'], merged_df['preterm_rate'], 'b-', alpha=0.7, linewidth=1)
    axes[1].set_ylabel('Preterm Birth Rate\n(per 1000 births)', fontsize=12)
    axes[1].set_xlabel('Date', fontsize=12)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    fig2.savefig(output_dir / 'time_series_analysis.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: time_series_analysis.png")
    plt.close(fig2)

    # Plot 3: Distributed lag effects
    fig3, ax = plt.subplots(figsize=(10, 6))

    ax.plot(lag_df['lag_days'], lag_df['correlation'], 'o-', markersize=8, linewidth=2)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.fill_between(
        lag_df['lag_days'],
        lag_df['correlation'],
        0,
        where=lag_df['significant'],
        alpha=0.3,
        color='green',
        label='Significant (p<0.05)'
    )

    ax.set_xlabel('Lag Period (days)', fontsize=12)
    ax.set_ylabel('Correlation Coefficient', fontsize=12)
    ax.set_title('Distributed Lag Effects: Temperature and Preterm Births',
                fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig3.savefig(output_dir / 'distributed_lag_effects.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: distributed_lag_effects.png")
    plt.close(fig3)

    # ============================================================
    # STEP 6: Export Data and Results
    # ============================================================
    print("\n" + "-"*70)
    print("STEP 6: EXPORTING DATA AND RESULTS")
    print("-"*70)

    # Export merged dataset
    merged_df.to_csv(output_dir / 'merged_climate_health_data.csv', index=False)
    print(f"  ✓ Saved: merged_climate_health_data.csv")

    # Export analysis results
    threshold_df.to_csv(output_dir / 'heat_threshold_analysis.csv', index=False)
    print(f"  ✓ Saved: heat_threshold_analysis.csv")

    lag_df.to_csv(output_dir / 'distributed_lag_results.csv', index=False)
    print(f"  ✓ Saved: distributed_lag_results.csv")

    # Export publication table
    pub_table = integrator.create_publication_table(
        threshold_df,
        save_path=output_dir / 'publication_table.csv'
    )
    print(f"  ✓ Saved: publication_table.csv")

    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    print("\n" + "="*70)
    print("✅ MVP ANALYSIS COMPLETE!")
    print("="*70)

    print(f"\n📊 Key Findings:")
    print(f"  • Correlation: r = {report['correlation']['pearson_r']:.3f}")
    print(f"  • Strongest heat threshold: {threshold_df.loc[threshold_df['relative_risk'].idxmax(), 'threshold_celsius']}°C")
    print(f"  • Max relative risk: {threshold_df['relative_risk'].max():.2f}")

    if len(significant_lags) > 0:
        best_lag = significant_lags.iloc[0]
        print(f"  • Strongest lag effect: {best_lag['lag_days']} days (r={best_lag['correlation']:.3f})")

    print(f"\n📁 All outputs saved to: {output_dir.absolute()}")
    print("\nGenerated files:")
    for file in sorted(output_dir.glob('*')):
        print(f"  • {file.name}")

    print("\n🎉 You now have publication-ready climate-health analysis!")
    print("\n💡 Next steps:")
    print("  1. Replace synthetic health data with your actual hospital/clinic data")
    print("  2. Adjust lag periods based on your research question")
    print("  3. Add confounders (air pollution, humidity, etc.)")
    print("  4. Run stratified analysis (by age, SES, etc.)")
    print("  5. Use outputs for manuscript figures and tables")


if __name__ == "__main__":
    main()

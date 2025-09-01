"""Example usage of the DataVizTest package.

This script demonstrates the main features of the modernized DataVizTest
package, including data loading, filtering, and visualization.
"""

import pandas as pd
import numpy as np

# Import the main DataVizTest package
import sys
sys.path.append('src')
import dataviztest as dvt

# Create sample data
def create_sample_data():
    """Create sample data for demonstration."""
    np.random.seed(42)
    
    data = {
        'id': range(1, 101),
        'category': np.random.choice(['Electronics', 'Books', 'Clothing', 'Home'], 100),
        'price': np.random.uniform(10, 500, 100),
        'rating': np.random.uniform(1, 5, 100),
        'sales': np.random.randint(1, 1000, 100),
        'in_stock': np.random.choice([True, False], 100),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
        'date_added': pd.date_range('2023-01-01', periods=100, freq='D')
    }
    
    return pd.DataFrame(data)


def main():
    """Main demonstration function."""
    print("DataVizTest 2.0 - Example Usage")
    print("=" * 40)
    
    # Create sample data
    print("\n1. Creating sample data...")
    sample_data = create_sample_data()
    print(f"Created dataset with shape: {sample_data.shape}")
    print(f"Columns: {list(sample_data.columns)}")
    
    # Initialize DataVizTest session
    print("\n2. Initializing DataVizTest session...")
    session = dvt.run(sample_data)
    print("Session initialized successfully!")
    
    # Get data summary
    print("\n3. Getting data summary...")
    summary = session.get_data_summary()
    print(f"Data validation: {'PASSED' if summary.validation_result.is_valid else 'FAILED'}")
    print(f"Total rows: {summary.summary_stats.total_rows}")
    print(f"Total columns: {summary.summary_stats.total_columns}")
    print(f"Memory usage: {summary.summary_stats.memory_usage_mb:.2f} MB")
    
    # Demonstrate filtering
    print("\n4. Creating and applying filters...")
    
    # Create a numeric filter
    price_filter = dvt.NumericFilter(
        name="Price Range Filter",
        column="price",
        operator=dvt.FilterOperator.BETWEEN,
        min_value=50.0,
        max_value=300.0
    )
    
    # Create a categorical filter
    category_filter = dvt.CategoricalFilter(
        name="Category Filter",
        column="category",
        operator=dvt.FilterOperator.IN,
        selected_values=["Electronics", "Books"]
    )
    
    # Create filter set
    filter_set = dvt.FilterSet(name="Demo Filters")
    filter_set.add_filter(price_filter)
    filter_set.add_filter(category_filter)
    
    # Add to filter engine
    session.filters.add_filter_set(filter_set)
    
    # Apply filters
    filter_result = session.apply_filters()
    print(f"Original rows: {filter_result.original_row_count}")
    print(f"Filtered rows: {filter_result.filtered_row_count}")
    print(f"Retention rate: {filter_result.retention_percentage:.1f}%")
    
    # Demonstrate visualization
    print("\n5. Creating visualizations...")
    
    # Create a scatter plot configuration
    scatter_config = dvt.PlotConfig(
        title="Price vs Rating Scatter Plot",
        plot_type=dvt.PlotType.SCATTER,
        x_column="price",
        y_column="rating",
        color_column="category"
    )
    
    # Generate plot
    plot_result = session.create_plot(scatter_config)
    print(f"Plot creation: {'SUCCESS' if plot_result.success else 'FAILED'}")
    print(f"Data points plotted: {plot_result.data_points}")
    print(f"Generation time: {plot_result.generation_time_ms:.2f}ms")
    
    if plot_result.warnings:
        print(f"Warnings: {plot_result.warnings}")
    
    # Demonstrate different plot types
    plot_types = [
        (dvt.PlotType.BAR, "category", "sales"),
        (dvt.PlotType.HISTOGRAM, "price", None),
        (dvt.PlotType.BOX, None, "rating"),
    ]
    
    for plot_type, x_col, y_col in plot_types:
        config = dvt.PlotConfig(
            title=f"{plot_type.value.title()} Plot",
            plot_type=plot_type,
            x_column=x_col,
            y_column=y_col
        )
        
        result = session.create_plot(config)
        print(f"{plot_type.value} plot: {'SUCCESS' if result.success else 'FAILED'}")
    
    # Show available plot types
    print(f"\n6. Available plot types: {[pt.value for pt in dvt.PlotType]}")
    
    # Display column information
    print(f"\n7. Column information:")
    if session.metadata:
        for col in session.metadata.columns:
            print(f"  - {col.name}: {col.data_type.value} "
                  f"(unique: {col.unique_count}, nulls: {col.null_count})")
    
    print("\n" + "=" * 40)
    print("DataVizTest 2.0 demonstration completed!")
    

if __name__ == "__main__":
    main()
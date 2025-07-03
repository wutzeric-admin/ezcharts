# Following libraries are imported in the backend automatically

# import numpy as np
# import plotly
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import pyecharts

# The dataframe is called "df" by default
# The structure of the dataframe is identical to the CSV in this folder

df_filtered = df.copy()

# Define zone mappings for titles
zone_titles = [
    'Front Left', 'Front Mid', 'Front Right',
    'Center Left', 'Center Mid', 'Center Right',
    'Back Left', 'Back Mid', 'Back Right'
]

# Define zones for Player A and Player B
zones_a = [f"Player A Zone {i}" for i in range(1, 10)]
zones_b = [f"Player B Zone {i}" for i in range(1, 10)]

# Add a new column 'Shot Played By' to indicate whether the shot was played by Player A or Player B
def determine_shot_played_by(primary_category):
    if isinstance(primary_category, str):
        if 'player a' in primary_category.lower():
            return 'Player A'
        elif 'player b' in primary_category.lower():
            return 'Player B'
    return None

globals()['determine_shot_played_by'] = determine_shot_played_by  # Add to global scope

df_filtered['Shot Played By'] = df_filtered['Primary category'].apply(determine_shot_played_by)

# Define colors for the stacked bars
colors = {
    'no result': '#3E5879',
    'won point': '#5CB338',
    'lost point': '#FB4141'
}

# Order of shot results
shot_result_order = ['no result', 'won point', 'lost point']

# Function to determine the shot result
def determine_shot_result(row, player_name):
    if row['Shot Played By'] == player_name:
        if pd.isna(row['Won By']):
            return 'no result'
        elif player_name.lower() in str(row['Won By']).lower():
            return 'won point'
        else:
            return 'lost point'
    return None  # Exclude shots not belonging to this player

globals()['determine_shot_result'] = determine_shot_result  # Add to global scope

# Calculate shot results for each player
df_filtered['Shot Result Player A'] = df_filtered.apply(lambda row: determine_shot_result(row, 'Player A'), axis=1)
df_filtered['Shot Result Player B'] = df_filtered.apply(lambda row: determine_shot_result(row, 'Player B'), axis=1)

# Prepare plot data for each player
def prepare_plot_data(df_filtered, shot_result_column, shot_result_order, group_by_column):
    plot_data = df_filtered.groupby([group_by_column, shot_result_column]).agg(
        Count=('event_uuid', 'size'),  # Count the occurrences
        event_uuid_list=('event_uuid', lambda x: [str(uuid) for uuid in x])  # Collect event_uuids
    ).reset_index()
    plot_data.rename(columns={shot_result_column: 'Shot Result'}, inplace=True)
    plot_data['Shot Result'] = pd.Categorical(plot_data['Shot Result'], categories=shot_result_order, ordered=True)
    return plot_data

player_a_data = prepare_plot_data(df_filtered, 'Shot Result Player A', shot_result_order, 'Primary category')
player_b_data = prepare_plot_data(df_filtered, 'Shot Result Player B', shot_result_order, 'Primary category')

# Ensure consistent categories across both players
all_categories = pd.DataFrame({'Primary category': pd.concat([player_a_data['Primary category'], player_b_data['Primary category']]).unique()})
all_categories['Primary category'] = all_categories['Primary category'].astype(str)

# Merge with all_categories and fill missing values
player_a_data = pd.merge(all_categories, player_a_data, on='Primary category', how='left')
player_a_data['Count'] = player_a_data['Count'].fillna(0).astype(int)  # Ensure 'Count' is filled with 0
player_a_data['Shot Result'] = player_a_data['Shot Result'].astype(str)  # Convert to string before filling
player_a_data['Shot Result'] = pd.Categorical(player_a_data['Shot Result'], categories=shot_result_order, ordered=True)  # Recreate as Categorical

player_b_data = pd.merge(all_categories, player_b_data, on='Primary category', how='left')
player_b_data['Count'] = player_b_data['Count'].fillna(0).astype(int)  # Ensure 'Count' is filled with 0
player_b_data['Shot Result'] = player_b_data['Shot Result'].astype(str)  # Convert to string before filling
player_b_data['Shot Result'] = pd.Categorical(player_b_data['Shot Result'], categories=shot_result_order, ordered=True)  # Recreate as Categoricals

# Find the maximum count across all grids for consistent axis limits
max_count_a = player_a_data['Count'].max()
max_count_b = player_b_data['Count'].max()
max_count = max(max_count_a, max_count_b) + 5

# Create a 3x3 grid of pie charts for Player A
fig = make_subplots(
    rows=3, cols=3,
    specs=[[{'type': 'domain'}] * 3] * 3,  # Pie charts in all cells
    subplot_titles=[
        f"<b>{title}</b>" for title, zone in zip(zone_titles, zones_a)
    ]
)

globals()['make_subplots'] = make_subplots  # Add to global scope

# Add Player A's zones
for i, (zone, title) in enumerate(zip(zones_a, zone_titles)):
    row, col = divmod(i, 3)
    row += 1
    subset = player_a_data[player_a_data['Primary category'] == zone]
    
    # Compute radius as a fraction of max_total_shots
    total_count = subset['Count'].sum()

    # Predefine colors for the current subset
    pie_colors = []
    for result in subset['Shot Result']:
        pie_colors.append(colors[result])  # Add the color for the shot result

    # Prepare customdata without list comprehension
    customdata = []
    for _, subset_row in subset.iterrows():
        customdata.append({
            'event_list': subset_row['event_uuid_list']
        })

    # Add pie chart for this zone
    fig.add_trace(
        go.Pie(
            labels=subset['Shot Result'], 
            values=subset['Count'], 
            textinfo='value',
            textfont=dict(color='white', size=16, family='Arial'),
            marker=dict(colors=pie_colors),  # Use predefined list to avoid list comprehension errors in SPAN Charts environment
            hole=0.2,  # Donut chart style
            domain=dict(x=[0.33 * col, 0.33 * (col + 1)], y=[1 - 0.33 * row, 1 - 0.33 * (row - 1)]),
            scalegroup='pies',  # Ensures scaling consistency
            pull=[0.05 if count > 0 else 0 for count in subset['Count']],  # Highlight non-zero slices
            customdata=customdata
        ),
        row=row,
        col=col + 1
    )

# Update layout
fig.update_layout(
    height=800,  # Adjust height for 3x3 layout
    width=1200,   # Adjust width for 3 columns
    barmode='relative',  # Ensure consistency for grouping (if needed for legends)
    title=dict(
        text='Player A Hitting "From" Zones (Radius Scaled by Total Shots)',
        font=dict(color='white', size=20, family='Arial'),
        x=0.5,  # Centered title
        y=0.98,
        xanchor='center',
        yanchor='top'
    ),
    paper_bgcolor='black',  # Background outside the plot
    plot_bgcolor='black',   # Background inside the plot
    legend=dict(font=dict(color='white'))  # White legend text
)

# Fix title positioning above each pie chart
for annotation in fig['layout']['annotations']:
    annotation['y'] += 0.05  # Shift the title above each chart
    annotation['font'] = dict(color='white', size=16, family='Arial')  # Set title text to white and font size to 12px

result = fig.to_json()
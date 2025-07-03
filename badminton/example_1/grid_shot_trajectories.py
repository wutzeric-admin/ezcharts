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

# Group zones into subsets for multiple charts
zone_groups = {
    'Player A hitting from front court': ['zone 1', 'zone 2', 'zone 3'],
    'Player A hitting from mid court': ['zone 4', 'zone 5', 'zone 6'],
    'Player A hitting from back court': ['zone 7', 'zone 8', 'zone 9'],
    'Player B hitting from front court': ['zone 1', 'zone 2', 'zone 3'],
    'Player B hitting from mid court': ['zone 4', 'zone 5', 'zone 6'],
    'Player B hitting from back court': ['zone 7', 'zone 8', 'zone 9']
}

# Define zone mappings for Player A (left) and Player B (right)
zone_mapping_left_side = {
    'zone 1': (2.5, 2), 'zone 2': (2.5, 1.2), 'zone 3': (2.5, 0.4),
    'zone 4': (1.5, 2), 'zone 5': (1.5, 1.2), 'zone 6': (1.5, 0.4),
    'zone 7': (0.5, 2), 'zone 8': (0.5, 1.2), 'zone 9': (0.5, 0.4),
    'net': (3, 1.2),  # Centered between Player A and Player B
    'out': (-0.25, 1.2)  # Beyond the chart for out
}
globals()['zone_mapping_left_side'] = zone_mapping_left_side # Add to global scope

zone_mapping_right_side = {
    'zone 1': (3.5, 0.4), 'zone 2': (3.5, 1.2), 'zone 3': (3.5, 2),
    'zone 4': (4.5, 0.4), 'zone 5': (4.5, 1.2), 'zone 6': (4.5, 2),
    'zone 7': (5.5, 0.4), 'zone 8': (5.5, 1.2), 'zone 9': (5.5, 2),
    'net': (3, 1.2),  # Centered between Player A and Player B
    'out': (6.25, 1.2)  # Beyond Player B's grid for out
}
globals()['zone_mapping_right_side'] = zone_mapping_right_side # Add to global scope

def get_coordinates(zone, zone_mapping_left_side, zone_mapping_right_side, is_player_a):
    mapping = zone_mapping_left_side if is_player_a else zone_mapping_right_side
    return mapping.get(zone, (None, None))  # Default to None if zone is invalid

# Classify outcomes
def classify_outcome(row):
    if pd.isna(row['Won By']):
        return 'no-result'
    if row['Shot Played By'] in row['Won By']:
        return 'won point'
    return 'lost point'

globals()['classify_outcome'] = classify_outcome # Add get_def to global scope

# Add a new column 'Shot Played By' to indicate whether the shot was played by Player A or Player B
def determine_shot_played_by(primary_category):
    if isinstance(primary_category, str):
        if 'player a' in primary_category.lower():
            return 'Player A'
        elif 'player b' in primary_category.lower():
            return 'Player B'
    return None

globals()['determine_shot_played_by'] = determine_shot_played_by # Add get_def to global scope

# Apply classification
df_filtered['Shot Played By'] = df_filtered['Primary category'].apply(determine_shot_played_by)

# Function to determine the zone
def determine_zone(location, mapping):
    if isinstance(location, str):
        return next((zone for zone in mapping if zone in location.lower()), 'Unknown')
    return 'Unknown'

globals()['determine_zone'] = determine_zone # Add get_def to global scope

# Add a column to determine the applicable mapping for "From Zone" and "To Zone"
df_filtered['From Mapping'] = df_filtered['Shot Played By'].apply(
    lambda player: zone_mapping_left_side if player == 'Player A' else zone_mapping_right_side
)
df_filtered['To Mapping'] = df_filtered['Shot Played By'].apply(
    lambda player: zone_mapping_right_side if player == 'Player A' else zone_mapping_left_side
)

# Apply the function using the preprocessed mapping columns
df_filtered['From Zone'] = df_filtered.apply(
    lambda row: determine_zone(row['Primary category'], row['From Mapping']), axis=1
)
df_filtered['To Zone'] = df_filtered.apply(
    lambda row: determine_zone(row['Receiving Location'], row['To Mapping']), axis=1
)

# Drop the temporary mapping columns if no longer needed
df_filtered.drop(['From Mapping', 'To Mapping'], axis=1, inplace=True)

# Classify outcomes
df_filtered['Outcome'] = df_filtered.apply(classify_outcome, axis=1)

# Include Shot Played By and event_uuid in grouping to identify direction
line_data = df_filtered.groupby(['From Zone', 'To Zone', 'Outcome', 'Shot Played By']).agg(
    Count=('event_uuid', 'size'),  # Count the occurrences
    event_uuid_list=('event_uuid', lambda x: [str(uuid) for uuid in x])  # Collect event_uuids
).reset_index()

# Define colors for outcomes
colors = {
    'no-result': '#3E5879',
    'won point': '#5CB338',
    'lost point': '#FB4141'
}

# Create the 3x2 grid layout for all charts
fig = make_subplots(
    rows=2, cols=3,
    subplot_titles=list(zone_groups.keys()),
    vertical_spacing=0.2,  # Reduced vertical spacing
    horizontal_spacing=0.00001,  # Reduced horizontal spacing
    specs=[[{}, {}, {}], [{}, {}, {}]]
)

# Iterate over each group to create charts
for i, (chart_title, zones) in enumerate(zone_groups.items()):

    row = i // 3 + 1
    col = i % 3 + 1
    is_player_a = 'Player A' in chart_title

    # Add gray lines for custom coordinates
    boundary_lines = [
        ((0,0), (6,0)), #horizontal line 1
        ((0,0.8), (6,0.8)), #horizontal line 2
        ((0,1.6), (6,1.6)), #horizontal line 3
        ((0,2.4), (6,2.4)), #horizontal line 4
        ((0,0), (0,2.4)), #vertical line 1
        ((1,0), (1,2.4)), #vertical line 2
        ((2,0), (2,2.4)), #vertical line 3
        ((3,0), (3,2.4)), #vertical line 4
        ((4,0), (4,2.4)), #vertical line 5
        ((5,0), (5,2.4)), #vertical line 6
        ((6,0), (6,2.4)), #vertical line 7
    ]   

    for (x1, y1), (x2, y2) in boundary_lines:
        # Check if the current line is the solid line
        if (x1, y1) == (3, 0) and (x2, y2) == (3, 2.4):
            line_style = dict(color="gray", width=5)  # Solid line for net
        else:
            line_style = dict(color="gray", width=1, dash="dash")  # Dashed line

        fig.add_shape(
            type="line",
            x0=x1, y0=y1, x1=x2, y1=y2,
            line=line_style,
            xref=f"x{col + (3 * (row - 1))}",  # Reference subplot's x-axis
            yref=f"y{col + (3 * (row - 1))}"   # Reference subplot's y-axis
        )

    # Filter data for the selected zones
    filtered_data = line_data[
        (line_data['From Zone'].isin(zones)) &
        (line_data['Shot Played By'] == ('Player A' if is_player_a else 'Player B')) &
        (line_data['From Zone'].str.contains('zone', case=False)) &
        (
            (line_data['To Zone'].str.contains('zone', case=False)) |
            (line_data['To Zone'].isin(['net', 'out']))
        )
    ]

    # Aggregate counts grouped by 'From Zone', 'To Zone', and 'Outcome'
    total_counts = filtered_data.groupby(['From Zone', 'To Zone', 'Outcome'])['Count'].sum().reset_index()

    # Add grid points and zone labels for all zones (full court visualization)
    for zone, (x, y) in zone_mapping_left_side.items():
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                # mode='markers+text',
                marker=dict(size=0, color='black'),
                text=f"{zone.title()}",
                textposition='top center',
                textfont=dict(color='white', family='Arial'),
                showlegend=False
            ),
            row=row,
            col=col
        )

    for zone, (x, y) in zone_mapping_right_side.items():
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                # mode='markers+text',
                marker=dict(size=0, color='black'),
                text=f"{zone.title()}",
                textposition='top center',
                textfont=dict(color='white', family='Arial'),
                showlegend=False
            ),
            row=row,
            col=col
        )

    # Add lines for each combination of From Zone, To Zone, and Outcome
    for _, row_data in total_counts.iterrows():
        x1, y1 = get_coordinates(row_data['From Zone'], zone_mapping_left_side, zone_mapping_right_side, is_player_a=is_player_a)
        x2, y2 = get_coordinates(row_data['To Zone'], zone_mapping_left_side, zone_mapping_right_side, is_player_a=not is_player_a)

        if x1 is None or x2 is None:
            continue

        # Control points for Bezier curves
        control_x1 = x1 + (x2 - x1) * 0.2
        control_y1 = y1 + (y2 - y1) * 0.1 + 0.1
        control_x2 = x1 + (x2 - x1) * 0.8
        control_y2 = y2 + (y2 - y1) * 0.1 + 0.1

        # Get event_uuid_list for this combination
        matching_rows = filtered_data[
            (filtered_data['From Zone'] == row_data['From Zone']) & 
            (filtered_data['To Zone'] == row_data['To Zone']) & 
            (filtered_data['Outcome'] == row_data['Outcome'])
        ]
        if not matching_rows.empty:
            event_list = matching_rows['event_uuid_list'].iloc[0]
        else:
            event_list = []

        # Prepare customdata without list comprehension
        customdata = []
        customdata.append({
            'event_list': event_list
        })
        # Add the line for this outcome
        fig.add_trace(
            go.Scatter(
                x=[x1, control_x1, control_x2, x2],
                y=[y1, control_y1, control_y2, y2],
                mode='lines',  # Only lines, no markers
                line=dict(
                    shape='spline',
                    width=row_data['Count'],  # Line thickness reflects count
                    color=colors[row_data['Outcome']]
                ),
                opacity=0.75,  # Apply transparency
                hovertemplate=f"Shots: {row_data['Count']}<br>Click on arrowheads to see related video clips<extra></extra>",
                showlegend=False
            ),
            row=row,
            col=col
        )

        # Add an arrow marker at the end of the line
        fig.add_trace(
            go.Scatter(
                x=[control_x2],  # End of the line
                y=[control_y2],  # End of the line
                mode='markers',
                marker=dict(
                    size=max(8, row_data['Count']),
                    symbol='triangle-right' if is_player_a else 'triangle-left',  # Arrowhead based on player
                    color=colors[row_data['Outcome']]  # Same color as the line
                ),
                hovertemplate=f"Shots: {row_data['Count']}<br>Click on arrowheads to view related video clips<extra></extra>",
                customdata=customdata,
                showlegend=False
            ),
            row=row,
            col=col
        )

# Update layout
fig.update_layout(
    height=700,  # Adjust height to fit plots
    width=1600,   # Adjust width to fit plots
    title=dict(
        text="Trajectory of Shots",
        font=dict(color='white', size=18, family='Arial'),
        x=0.5, y=0.98, xanchor='center', yanchor='top'
    ),
    paper_bgcolor='black',
    plot_bgcolor='black',
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False),
    legend=dict(font=dict(color='white', family='Arial'))
)
# Fix subplot title font color to white
for annotation in fig['layout']['annotations']:
    annotation['font']['color'] = 'white'

# Explicitly remove axis labels for all subplots
for axis in fig['layout']:
    if axis.startswith('xaxis') or axis.startswith('yaxis'):
        fig['layout'][axis].update(showgrid=False, visible=False)

result = fig.to_json()
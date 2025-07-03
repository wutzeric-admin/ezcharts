# Following libraries are imported in the backend automatically

# import numpy as np
# import plotly
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import pyecharts

# The dataframe is called "df" by default
# The structure of the dataframe is identical to the CSV in this folder

df_full = df.copy()  # Keep unfiltered copy
    
# Filter df1 for Player B's shots
df1 = df[
    df['Primary category'].str.contains('Player B', na=False) &
    (df['Rally Shot Type'].str.lower() != 'serve')
].copy()
df1['event_uuid'] = df1['event_uuid'].astype(str)

# Zone label mapping
zone_labels = {
    'Zone 1': 'Front Left',
    'Zone 2': 'Front Center',
    'Zone 3': 'Front Right',
    'Zone 4': 'Mid Left',
    'Zone 5': 'Mid Center',
    'Zone 6': 'Mid Right',
    'Zone 7': 'Back Left',
    'Zone 8': 'Back Center',
    'Zone 9': 'Back Right'
}

zones = sorted(zone_labels.keys(), key=lambda x: int(x.split()[-1]))
shot_types = sorted(df1['Rally Shot Type'].dropna().unique())

# Prepare data grid
z_values = []
customdata = []
text_labels = []

for shot_type in shot_types:
    row_counts = []
    row_custom = []
    row_text = []
    for zone in zones:
        # Get all shots of this type in this zone from Player B's shots
        mask = df1['Rally Shot Type'].eq(shot_type) & df1['Primary category'].str.contains(zone, na=False)
        shots_df = df1[mask].copy()
        count = len(shots_df)
        event_list = shots_df['event_uuid'].tolist()

        if count > 0:
            # Count immediate winners (won by player B)
            winners = sum(shots_df['Won By'].str.contains('player b', case=False, na=False))
            
            # Count immediate errors (won by opponent)
            errors = sum(shots_df['Won By'].str.contains('player a', case=False, na=False))
            
            # Get indices of shots that didn't end the rally
            continuing_shot_indices = shots_df[shots_df['Won By'].isna()].index
            
            winner_setup = 0
            weak_shots = 0
            
            for idx in continuing_shot_indices:
                next_idx = idx + 1
                if next_idx in df_full.index:
                    next_shot = df_full.loc[next_idx]
                    if pd.notna(next_shot['Won By']):
                        if 'player b' in str(next_shot['Won By']).lower():
                            winner_setup += 1
                        elif 'player a' in str(next_shot['Won By']).lower():
                            weak_shots += 1

            # Create a four-line text label
            line1 = str(count)  # Just the number
            
            # Winners (immediate + setups) with correct grammar
            total_winners = winners + winner_setup
            line2 = f"{total_winners} {'winners' if total_winners > 1 else 'winner'}" if total_winners > 0 else ""
            
            # Errors with correct grammar
            line3 = f"{errors} {'errors' if errors > 1 else 'error'}" if errors > 0 else ""
            
            # Weak shots with correct grammar
            line4 = f"{weak_shots} {'weak shots' if weak_shots > 1 else 'weak shot'}" if weak_shots > 0 else ""
            
            # Combine the lines, filtering out empty ones
            text = "<br>".join(line for line in [line1, line2, line3, line4] if line)
        else:
            text = ""

        row_counts.append(count)
        row_custom.append({'event_list': event_list})
        row_text.append(text)
        
    z_values.append(row_counts)
    customdata.append(row_custom)
    text_labels.append(row_text)

x_list = []
for z in zones:
    x_list.append(zone_labels[z])

# Build the heatmap with agsunset colorscale
fig = go.Figure(data=go.Heatmap(
    z=z_values,
    x=x_list,
    y=shot_types,
    colorscale='agsunset',  # Changed to agsunset colorscale
    text=text_labels,
    texttemplate="%{text}",
    textfont={"color": "white"},
    customdata=customdata,
    hovertemplate='Zone: %{x}<br>Shot Type: %{y}<br>Count: %{z}<br>🎥 Click to view events<extra></extra>',
    colorbar=dict(title='Count', titleside='right')
))

# Layout updates
fig.update_layout(
    title="Player B: Shot Types by Court Zone (Heatmap, Serves Removed)",
    xaxis=dict(title='Court Zone'),
    yaxis=dict(title='Shot Type'),
    plot_bgcolor='black',
    paper_bgcolor='black',
    font=dict(color='white', family='Helvetica'),
    height=600,
    width=1000,
    margin=dict(t=60, l=100, r=50, b=60)
)
result = fig.to_json()
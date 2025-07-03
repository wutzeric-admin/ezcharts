# Following libraries are imported in the backend automatically

# import numpy as np
# import plotly
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import pyecharts

# The dataframe is called "df" by default
# The structure of the dataframe is identical to the CSV in this folder

df1 = df.copy()
def determine_shot_played_by(primary_category):
    if isinstance(primary_category, str):
        if 'player a' in primary_category.lower():
            return 'Player A'
        elif 'player b' in primary_category.lower():
            return 'Player B'
    return None
globals()['determine_shot_played_by'] = determine_shot_played_by

df1['Shot Played By'] = df1['Primary category'].apply(determine_shot_played_by)
colors = {
    'no result': '#3E5879',
    'won point': '#5CB338',
    'lost point': '#FB4141'
}
shot_result_order = ['no result', 'won point', 'lost point']
def determine_shot_result(row, player_name):
    if row['Shot Played By'] == player_name:
        if pd.isna(row['Won By']):
            return 'no result'
        elif player_name.lower() in str(row['Won By']).lower():
            return 'won point'
        else:
            return 'lost point'
    return None
globals()['determine_shot_result'] = determine_shot_result

df1['Shot Result Player B'] = df1.apply(lambda row: determine_shot_result(row, 'Player B'), axis=1)
def prepare_plot_data(df_filtered, shot_result_column, shot_result_order):
    plot_data = df_filtered.groupby(['Rally Shot Type', shot_result_column]).agg(
        Count=('event_uuid', 'size'),
        event_uuid_list=('event_uuid', lambda x: [str(uuid) for uuid in x])
    ).reset_index()
    plot_data.rename(columns={shot_result_column: 'Shot Result'}, inplace=True)
    plot_data['Shot Result'] = pd.Categorical(plot_data['Shot Result'], categories=shot_result_order, ordered=True)
    return plot_data
globals()['prepare_plot_data'] = prepare_plot_data

player_b_data = prepare_plot_data(df1, 'Shot Result Player B', shot_result_order)
all_categories = pd.DataFrame({'Rally Shot Type': player_b_data['Rally Shot Type'].unique()})
all_categories['Rally Shot Type'] = all_categories['Rally Shot Type'].astype(str)
player_b_data = pd.merge(all_categories, player_b_data, on='Rally Shot Type', how='left')
player_b_data['Count'] = player_b_data['Count'].fillna(0).astype(int)
player_b_data['Shot Result'] = player_b_data['Shot Result'].astype(str)
player_b_data['Shot Result'] = pd.Categorical(player_b_data['Shot Result'], categories=shot_result_order, ordered=True)
player_b_data = player_b_data.sort_values(by='Rally Shot Type', ascending=True)
bar = (
    pyecharts.charts.Bar(init_opts=pyecharts.options.InitOpts(width="100%", height="100vh", bg_color="black"))
    .add_xaxis(all_categories['Rally Shot Type'].tolist())
)
for result in shot_result_order:
    y_data = []
    for cat in all_categories['Rally Shot Type']:
        row = player_b_data[(player_b_data['Rally Shot Type'] == cat) & (player_b_data['Shot Result'] == result)]
        if not row.empty:
            y_data.append({
                "value": int(row['Count'].values[0]),
                "event_list": row['event_uuid_list'].values[0]
            })
        else:
            y_data.append({
                "value": 0,
                "event_list": []
            })
    bar.add_yaxis(
        f"Player B ({result})",
        y_data,
        stack="player_b",
        itemstyle_opts=pyecharts.options.ItemStyleOpts(color=colors[result]),
        label_opts=pyecharts.options.LabelOpts(is_show=False)
    )
bar.set_global_opts(
    title_opts=pyecharts.options.TitleOpts(
        title="Shot Types: Player B",
        title_textstyle_opts=pyecharts.options.TextStyleOpts(color="white")
    ),
    tooltip_opts=pyecharts.options.TooltipOpts(
        trigger="item",
        formatter=r'''
        <div style="font-family:Arial,sans-serif;">
            <span style="font-size:18px; color:#fff;"><strong>{b}</strong></span><br/>
            <span style="font-size:13px; color:#fff;">{a}</span><br/>
            <span style="font-size:13px; color:#ffb347;">Count: {c}</span><br/>
            <span style="font-size:12px; color:#ccc;">🎥 Click to see video clips</span>
        </div>
        ''',
        background_color="rgba(0, 0, 0, 0.5)",
        border_color="#ff9800",
        border_width=2,
        textstyle_opts=pyecharts.options.TextStyleOpts(color="#fff", font_size=13),
        extra_css_text="box-shadow: 0 2px 12px rgba(0,0,0,0.3); border-radius: 10px;"
    ),
    legend_opts=pyecharts.options.LegendOpts(
        is_show=True,
        orient="horizontal",
        pos_top="2%",
        pos_left="center",
        textstyle_opts=pyecharts.options.TextStyleOpts(color="white")
    ),
    xaxis_opts=pyecharts.options.AxisOpts(
        name="Rally Shot Type",
        name_location="middle",
        name_gap=50,
        name_textstyle_opts=pyecharts.options.TextStyleOpts(color="white", font_size=16),
        axislabel_opts=pyecharts.options.LabelOpts(
            color="white",
            rotate=25,
            font_size=12,
            interval=0
        ),
        axisline_opts=pyecharts.options.AxisLineOpts(
            linestyle_opts=pyecharts.options.LineStyleOpts(color="white")
        ),
        splitline_opts=pyecharts.options.SplitLineOpts(is_show=False),
        boundary_gap=True
    ),
    yaxis_opts=pyecharts.options.AxisOpts(
        name="Count",
        name_location="middle",
        name_gap=50,
        name_rotate=90,
        name_textstyle_opts=pyecharts.options.TextStyleOpts(color="white", font_size=16),
        axislabel_opts=pyecharts.options.LabelOpts(color="white"),
        axisline_opts=pyecharts.options.AxisLineOpts(
            linestyle_opts=pyecharts.options.LineStyleOpts(color="white")
        ),
        splitline_opts=pyecharts.options.SplitLineOpts(
            is_show=True,
            linestyle_opts=pyecharts.options.LineStyleOpts(color="gray", type_='dotted', width=1)
        )
    ),
)
bar.options["grid"] = {
    "top": "10%",
    "bottom": "10%",
    "left": "8%",
    "right": "8%",
    "height": "75%"
}

result = bar.dump_options()
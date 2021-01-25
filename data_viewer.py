import os
import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime
import sys
import configparser
from utils import (
load_las,
compare_clouds,
extract_area,
random_subsample,
compare_clouds,
view_cloud_plotly
)
config = configparser.ConfigParser()
config.read('config.ini')
config_dict = config['2016-2020']
dir_1 = config_dict['dir_1']
dir_2 = config_dict['dir_2']
class_labels = ['nochange','removed',"added",'change',"color_change","unfit"]
classified_dir = config_dict['classified_dir']

point_list_dir = classified_dir
clearance = 3
point_size = 1.5

classified_point_list_files = [os.path.join(classified_dir,f) for f in os.listdir(classified_dir) if os.path.isfile(os.path.join(classified_dir, f))]
scene_numbers = [int(os.path.basename(x).split('_')[0]) for x in classified_point_list_files]
sample_size = 100000


classified_point_list_dfs = {scene_num:pd.read_csv(path) for scene_num,path in zip(scene_numbers,classified_point_list_files)}

files_dir_1 = [os.path.join(dir_1,f) for f in os.listdir(dir_1) if os.path.isfile(os.path.join(dir_1, f)) and f.split(".")[-1]=='las']
files_dir_2 = [os.path.join(dir_2,f) for f in os.listdir(dir_2) if os.path.isfile(os.path.join(dir_2, f))and f.split(".")[-1]=='las']


files_dir_1 = {int(os.path.basename(x).split("_")[0]):x for x in files_dir_1}
files_dir_2 = {int(os.path.basename(x).split("_")[0]):x for x in files_dir_2}





classified_point_list_files = {int(os.path.basename(x).split("_")[0]):x for x in classified_point_list_files}


def create_plots(point_list_df,file_1,file_2,sample_size=2048,clearance=2,shape='cylinder'):
    points1 = load_las(file_1)
    points2 = load_las(file_2)
    current_figure_tuples = []
    for index, row in point_list_df.iterrows():
        center = np.array([row['x'],row['y']])
        #Remove ground
        # points1 = points1[points1[:,2]>0.43]
        # points2 = points2[points2[:,2]>0.43]
        extraction_1 = random_subsample(extract_area(points1,center,clearance,shape),sample_size)
        extraction_2 = random_subsample(extract_area(points2,center,clearance,shape),sample_size)
        fig_1 = view_cloud_plotly(extraction_1[:,:3],extraction_1[:,3:],show=False,point_size=point_size)
        fig_2 = view_cloud_plotly(extraction_2[:,:3],extraction_2[:,3:],show=False,point_size=point_size)
        current_figure_tuples.append((fig_1,fig_2))
    return current_figure_tuples





external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__,external_stylesheets=external_stylesheets,suppress_callback_exceptions = True) 


drop_options_scene = [{'label':key,'value':key} for key in scene_numbers]
drop_options_scene = sorted(drop_options_scene,key=lambda x:x['label'])

current_classifications = {}

# for scene_number,classified_point_list_file in classified_point_list_files.items():
#     classified_point_list_df = pd.read_csv(classified_point_list_file)

#     current_classifications[scene_number] = classified_point_list_df['classification'].tolist()
current_classifications = {key:val['classification'].tolist() for key,val in classified_point_list_dfs.items()}
app.layout = html.Div([
dcc.Dropdown(id= 'scene_number',
options=drop_options_scene,
multi=False,
value = '0',
style ={'width':'20%'},
searchable = False),
html.Div(id='once_chosen_scene_div'),

html.Div(id='placeholder', style={"display":"none"}),
html.Div(id="placeholder2", style={"display":"none"}),


])

@app.callback(
    Output(component_id='once_chosen_scene_div', component_property='children'),
    Input(component_id='scene_number', component_property='value'),prevent_initial_call=True
)


def scene_changer(scene_number):
    global sample_size
    global clearance
    global current_figure_tuples
    global n_points
    global current_classifications 
    global current_point_number
    global current_scene_number
    global drop_options_classifiation

    #Start at first point for all scenes
    current_point_number=0
    current_scene_number = i =  int(scene_number)
    
    n_points = classified_point_list_dfs[i].shape[0]

    if not scene_number in current_classifications.keys():
        current_classifications[i] = ['UNSET']*n_points

    
    #Update plot list
    current_figure_tuples = create_plots(classified_point_list_dfs[i],files_dir_1[i],files_dir_2[i],sample_size=sample_size,clearance=clearance)


    
    drop_options_classifiation = [{'label':key,'value':key} for key in class_labels]
    
    drop_options_point_number = [{'label':key,'value':key} for key in range(classified_point_list_dfs[i].shape[0])]
    
    once_chosen_scene_div = html.Div([

    
    dcc.Dropdown(id= 'point_number',
    options=drop_options_point_number,
    multi=False,
    value = '0',
    style ={'width':'20%'},
    searchable = False
    ),

    html.Div(id='specific_point',children=[html.Div([
    html.H3(current_classifications[i][current_point_number],id = 'classification'),


        
            html.H3('Time 1'),
            dcc.Graph(id='g1', figure=current_figure_tuples[0][0])
        ], className="six columns"),

        html.Div([
            html.H3('Time 2'),
            dcc.Graph(id='g2', figure=current_figure_tuples[0][1])
        ], className="six columns"),
    ], className="row")
    ])


    return once_chosen_scene_div


@app.callback(
    # Output(component_id='specific_point', component_property='children'),
    Output(component_id='g1', component_property='figure'),
    Output(component_id='g2', component_property='figure'),
    Output(component_id='classification', component_property='children'),
    Input(component_id='point_number', component_property='value'),prevent_initial_call=True
)


def point_changer(point_number):
    
    


    global current_point_number
    global current_scene_number
    global drop_options_classifiation

    assert point_number in range(classified_point_list_dfs[current_scene_number].shape[0]), "Invalid drop option"
    current_point_number = int(point_number)
     
    fig_1 = current_figure_tuples[current_point_number][0]
    fig_2 = current_figure_tuples[current_point_number][1]
    classification_of_new_points = current_classifications[current_scene_number][current_point_number]
   
    
    return fig_1,fig_2,classification_of_new_points










    
    

app.run_server(debug=False)











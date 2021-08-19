# Bilbiotecas necessÃ¡rias

import numpy as np
import pandas as pd
import streamlit as st
import re
import plotly.graph_objects as go
import plotly.express as px

@st.cache(suppress_st_warning=True)
def load_dataframe(file_name):
  df = pd.read_csv(file_name,              # nome do arquivo .csv que serÃ¡ carregado
                  delimiter=';',           # esses arquivos .csv possuem os dados serparados por ponto e vÃ­rgula (semicolon)
                  decimal=",",             # esses arquivos .csv possuem o ponto decimal como uma vÃ­rgula, necessitando trocar para o ponto decimal
                  encoding='utf-8',        # a codificaÃ§Ã£o serÃ¡ em utf-8
                  skiprows=0,              # skip default rows depending in dataframe configuration header
                  )
  return df

def coordinates_to_horary(x,y):
  day = 0
  shift = 'A'
  hour = 0
  if(y>=0 and y<=5): day = y+2
  if(x>=0 and x<=5): # M
    shift = 'M'
    hour = x+1
  elif(x>=6 and x<=11): # T
    shift = 'T'
    hour = x+1-6
  elif(x>=12 and x<=15): # N
    shift = 'N'
    hour = x+1-12
  return str(day) + shift + str(hour)

def map_period_tuple(tuple_, array_):
        # first index:  day of the week - {'2':0, '3':1, '4':2, '5':3, '6':4, '7':5}
        # second index: shift           - {'M':M, 'T':A, 'N':N}
        # third index:  hour            - {'1':0, '2':1, '3':2, '4':3, '5':4, '6':5}
        list_days = []
        list_hours = []
        dict_shift = {'M':0, 'T':6, 'N':12} # deslocadores da linha
        [list_days.append(int(x)-2) for x in tuple_[0]] # -2 para converter do formato 234567 para 012345
        [list_hours.append(int(x)-1) for x in tuple_[2]] # -1 para converter do formato 123456 para 012345

        for i in list_hours: # linhas com base nos horÃ¡rios
            for j in list_days: # colunas com base nos dias da semana
                try: array_[i+dict_shift[tuple_[1]]][j] = True # preencher matriz onde foi identificado um horÃ¡rio
                except: pass
        return array_

def extract_numeric_period(list_):
        M = np.zeros((6,6), dtype=np.int) # morning
        A = np.zeros((6,6), dtype=np.int) # afternoon
        N = np.zeros((4,6), dtype=np.int) # night
        array_ = np.concatenate((M,A,N), axis=0)
        for str_ in list_: # iterando sobre todos os horÃ¡rios disponÃ­veis, e.g: [6T23456, 7T123456, 6N12345]
            match = re.match(r"([0-9]+)([a-z]+)([0-9]+)", str_, re.I) # identificar padrÃ£o da string NÃºmeroLetraNÃºmero, separando 6T23456 em (6, T, 23456)
            if match: array_ = map_period_tuple(match.groups(), array_) # se identificar padrÃ£o anterior, deverÃ¡ converte-lo em matriz
        return array_

df_matriculas = {'2018.1': pd.DataFrame(), '2018.2': pd.DataFrame(), '2019.1': pd.DataFrame(), '2019.2': pd.DataFrame()}
df_matriculas['2018.1'] = load_dataframe('matricula-componente-20181.csv')
df_matriculas['2018.2'] = load_dataframe('matricula-componente-20182.csv')
df_matriculas['2019.1'] = load_dataframe('matricula-componente-20191.csv')
df_matriculas['2019.2'] = load_dataframe('matricula-componente-20192.csv')

df_turmas = {'2018.1': pd.DataFrame(), '2018.2': pd.DataFrame(), '2019.1': pd.DataFrame(), '2019.2': pd.DataFrame()}
df_turmas['2018.1'] = load_dataframe('turmas-2018.1.csv')
df_turmas['2018.2'] = load_dataframe('turmas-2018.2.csv')
df_turmas['2019.1'] = load_dataframe('turmas-2019.1.csv')
df_turmas['2019.2'] = load_dataframe('turmas-2019.2.csv')

df_componentes = load_dataframe('componentes-curriculares-presenciais.csv')

semestres = list(df_turmas.keys())

colunas_turmas = ['id_turma', 'id_componente_curricular', 'descricao_horario']
colunas_componentes = ['id_componente', 'unidade_responsavel', 'nome']
colunas_matriculas = ['id_turma', 'discente']

df_componentes = df_componentes.filter(colunas_componentes).reset_index() # manter colunas essenciais

for semestre in semestres:
  df_matriculas[semestre] = df_matriculas[semestre].filter(colunas_matriculas).reset_index() # manter colunas essenciais
  df_turmas[semestre] = df_turmas[semestre].filter(colunas_turmas).reset_index() # manter colunas essenciais
  df_turmas[semestre] = df_turmas[semestre].dropna(subset=['descricao_horario']) # descricao_horario deve ser nÃ£o nula, qualquer entrada NaN deve ser descartada                   

columns_to_drop = ['id_componente_curricular', 'id_componente']
for semestre in semestres: 
  df_turmas[semestre] = pd.merge(df_turmas[semestre], df_componentes, 
                                 how='inner', left_on='id_componente_curricular',
                                 right_on='id_componente').drop(columns_to_drop, axis=1) # nomeando turmas com base na sua ID de componente curricular
  df_turmas[semestre] = df_turmas[semestre].rename(columns= {'nome': 'disciplina'}, inplace=False) # renomear coluna para que fique claro o nome da disciplina
st.title("Melhor HorÃ¡rio para Monitoria")
with st.sidebar:
    st.title("Filtros")
    semestre_dd = st.selectbox('Semestre:',semestres)
    unidade_dd = st.selectbox('Unidade ResponsÃ¡vel:',df_turmas[semestre]['unidade_responsavel'].sort_values().unique())
    disciplinas = st.multiselect('Disciplinas:',df_turmas[semestre]['disciplina'][df_turmas[semestre]['unidade_responsavel']==unidade_dd].sort_values().unique())

if(disciplinas):
    id_turmas_selecionadas = list(df_turmas[semestre][df_turmas[semestre]['disciplina'].isin(disciplinas)].id_turma) # id das turmas referentes Ã s disciplinas selecionadas
    discentes_selecionados = df_matriculas[semestre][(df_matriculas[semestre].id_turma).isin(id_turmas_selecionadas)]['discente'].unique() # discentes que estÃ£o matriculados nas turmas buscadas
    total_discentes_selecionados = discentes_selecionados.size # quantidade de discentes_selecionados 
    turmas_discentes_selecionados = df_matriculas[semestre][df_matriculas[semestre]['discente'].isin(discentes_selecionados)].drop_duplicates().groupby(['id_turma'])['discente'].describe()[['count']].reset_index() # todas as turmas que os discentes selecionados estÃ£o matriculados

    horarios = df_turmas[semestre][df_turmas[semestre]['id_turma'].isin(turmas_discentes_selecionados['id_turma'])][['descricao_horario','id_turma']].reset_index()
    horarios = horarios.join(turmas_discentes_selecionados.set_index('id_turma'),on='id_turma').drop(columns=['index', 'id_turma']).rename(columns={"count": "peso"})

    horarios_modificando = horarios['descricao_horario'].str.replace("[(@*&?].*[)@*&?]", "", regex=True) # remover conteÃºdo entre parenthesis das strings e.g: 4T456 (22/07/2019 - 07/12/2019) -> 4T456 
    horarios_listas = horarios_modificando.str.split(' ').dropna() # dividir string '6T23456 7T123456 6N12345' em lista [6T23456, 7T123456, 6N12345]
    horarios_matrix = horarios_listas.apply(extract_numeric_period) # aplicar conversÃ£o de horÃ¡rio formato UFRN para matriz
    horarios_matrix_pesos = horarios_matrix*horarios['peso'] # aplicando os pesos aos horÃ¡rios existentes

    piores_horarios_monitoria = horarios_matrix_pesos.sum() # quanto maior o valor, mais discentes (dos escolhidos) estÃ£o ocupados
    total_discentes_selecionados = np.max(piores_horarios_monitoria)
    melhores_horarios_monitoria = total_discentes_selecionados-piores_horarios_monitoria # quanto maior o valor, mais discentes (dos escolhidos) estÃ£o desocupados

    labels_dia_semana = ['SEG','TER','QUA','QUI','SEX','SAB']
    labels_horario = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 
                    'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 
                    'N1', 'N2', 'N3', 'N4']
    labels_horario_r = ['N4', 'N3', 'N2', 'N1', 'T6', 'T5', 
                    'T4', 'T3', 'T2', 'T1', 'M6', 'M5', 
                    'M4', 'M3', 'M2', 'M1']                    
    colorscale = [[0, 'red'], [1, 'green']]
    
    fig = go.Figure(data=go.Heatmap(
                   z=np.flipud(melhores_horarios_monitoria),
                   x=labels_dia_semana,
                   y=labels_horario_r,
                   hoverongaps = False,
                   hovertemplate = "Dia:%{x}<br>HorÃ¡rio:%{y}<br>Alunos Livres:%{z}",
                   colorscale='darkmint'))
    st.markdown("## HorÃ¡rios Livres")
    st.write(fig)

    st.markdown("## HorÃ¡rios x Alunos Livres")

    dia_dd = st.selectbox('Dia:',labels_dia_semana)
    dia_arr = [row[labels_dia_semana.index(dia_dd)] for row in melhores_horarios_monitoria]
    maxDia = max(dia_arr)
    fig = px.bar(pd.DataFrame ({'HorÃ¡rios':labels_horario,'Alunos Livres':dia_arr}, columns = ['HorÃ¡rios','Alunos Livres']), x='HorÃ¡rios', y='Alunos Livres', color_discrete_sequence =['darkseagreen']*maxDia)
    
    st.write(fig)

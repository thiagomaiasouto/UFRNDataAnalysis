# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import pandas as pd
import gdown as gd
import re
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots



@st.cache(suppress_st_warning=True)
def load_dataframe():
  
  url = 'https://drive.google.com/file/d/1-34MNU3QuKplfPI-_BqDXx7SeZoAzEEE/view?usp=sharing'
  output = 'df.csv'
  gd.download(url,output)
  df = pd.read_csv('df.csv', sep=';')
  
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


df_final = load_dataframe('df.csv')

st.session_state.caminho = st.sidebar.selectbox('Navegar:',['Monitoria','Analise'])

if st.session_state.caminho == 'Monitoria':
  df_test = df_final.filter(['semestre','unidade_responsavel','disciplina','descricao_horario', 'discente'])

  st.title("Melhor Horário para Monitoria")
  with st.sidebar:
      st.title("Filtros")
      semestre = st.selectbox('Semestre:',df_test['semestre'].sort_values().unique())
      df_test = df_test[df_test['semestre']==semestre]
      unidade = st.selectbox('Unidade Responsável:',df_test.unidade_responsavel.sort_values().unique())
      disciplinas = st.multiselect('Disciplinas:',df_test[df_test['unidade_responsavel']==unidade].disciplina.sort_values().unique())

  if(disciplinas):
      discentes = df_test[df_test['disciplina'].isin(disciplinas)].discente
      horarios = df_test[df_test['discente'].isin(discentes)].drop_duplicates().filter(['descricao_horario','discente']).groupby(['descricao_horario']).count().rename(columns={"discente": "peso"}).reset_index()
      
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
elif st.session_state.caminho == 'Analise':
  st.title('Analise')
  
  with st.sidebar:
      st.title("Filtros")
      
      df_test = df_final.filter(['semestre','nome_docente','disciplina','descricao_horario', 'discente'])
      
      semestre_sel = st.selectbox('Semestre:',df_test['semestre'].sort_values().unique())
      
      df_test = df_test[df_test['semestre']==semestre_sel]
      
      docente_sel = st.selectbox('Docente:',df_test.nome_docente.sort_values().unique())
      
      disciplina_sel = st.selectbox('Disciplina:',df_test[df_test['nome_docente']==docente_sel].disciplina.sort_values().unique())
      
      df_query = df_final.query('disciplina == @disciplina_sel & nome_docente == @docente_sel & semestre == @semestre_sel ')
     
  fig = px.histogram(data_frame = df_query, 
                   x = 'nota', nbins=10, color='unidade', 
                   title = 'Distribuição de notas na matéria de ' + disciplina_sel + " em cada unidade", 
                   hover_data= ['nota'], barmode = 'overlay', opacity = 0.75)
  
  st.plotly_chart(fig)
     
  #st.header("Novo grafico")
  
  df_query_move = df_final[(df_final['disciplina'] == disciplina_sel) & (df_final['nome_docente'] == docente_sel)]
  
  fig2 = px.scatter(df_query_move , x= 'media_final',  animation_frame= 'semestre', animation_group='discente',
           size='media_final', hover_name='media_final')

  fig2.update_layout(title = 'Distribuições da média final de cada discente por semestre')
  
  st.plotly_chart(fig2)
  
  notas_medias = df_final.groupby(by = ['id_turma', 'nome_docente'])['media_final'].mean().reset_index()
  notas_medias = notas_medias.drop('id_turma', axis = 1)
 
  notas_avaliacao = df_final.groupby(by = ['nome_docente'])[['atuacao_profissional_media','postura_profissional_media']].mean().reset_index()
  df_media_avaliacao = notas_medias.merge(notas_avaliacao, how= 'inner', on = 'nome_docente')
  df_media_avaliacao = df_media_avaliacao.groupby('nome_docente')[['media_final','atuacao_profissional_media','postura_profissional_media']].mean().reset_index()
  m_nota_formacao_corr = df_media_avaliacao.corr(method = 'pearson')

  fig3 = go.Figure(data=go.Heatmap(
                   z=m_nota_formacao_corr.values.astype('float64'),
                   x = ['media_final', 'atuacao_profissional_media' ,'postura_profissional_media'],
                   y = ['media_final', 'atuacao_profissional_media' ,'postura_profissional_media'],
                   hoverongaps = False, colorscale='Viridis'))
  fig3.update_xaxes(side="top")
  fig3.update_layout(title = 'Correlação entre média geral de alunos de todas as turmas com as avaliações dos docentes')
  st.markdown('## Correlacao')
  st.plotly_chart(fig3)

  
  
  
else:
  st.title('Nada')

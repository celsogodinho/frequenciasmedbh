import streamlit as st
from helpers import obtem_conexao, meses
from streamlit_apexjs import st_apexcharts
from streamlit_extras.metric_cards import style_metric_cards

@st.cache_data
def busca_resultados(regional_id, dias_letivos, ano):
    conn = obtem_conexao()
    sql_10 = '''
        select e.cod_escl cod_escl, count(fa.cod_aluno) _0_10
        from faltas_acumuladas fa, aluno a , escola e
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and e.regional = %s
        and 100*(cast(fa.total_sem_jus as float)/%s) <= 10.0
        group by e.cod_escl 
    '''%(ano, regional_id, dias_letivos)

    data_menor_10 = conn.query(sql_10)

    sql_10_20 = '''
        select e.cod_escl cod_escl, count(fa.cod_aluno) _10_20
        from faltas_acumuladas fa, aluno a , escola e
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and e.regional = %s
        and 100*(cast(fa.total_sem_jus as float)/%s) > 10.0
        and 100*(cast(fa.total_sem_jus as float)/%s) <= 20.0
        group by e.cod_escl
    '''%(ano, regional_id, dias_letivos, dias_letivos)
    data_10_20 = conn.query(sql_10_20)

    sql_20_25 = '''
        select e.cod_escl cod_escl, count(fa.cod_aluno) _20_25
        from faltas_acumuladas fa, aluno a , escola e
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and e.regional = %s
        and 100*(cast(fa.total_sem_jus as float)/%s) > 20.0
        and 100*(cast(fa.total_sem_jus as float)/%s) < 25.0
        group by e.cod_escl
    '''%(ano, regional_id, dias_letivos, dias_letivos)
    data_20_25 = conn.query(sql_20_25)

    sql_maior_25 = '''
        select e.cod_escl cod_escl, count(fa.cod_aluno) _25_100
        from faltas_acumuladas fa, aluno a , escola e
        where ano = %s
        and a.cod_aluno = fa.cod_aluno 
        and e.cod_escl = a.cod_escl_atua
        and e.regional = %s
        and 100*(cast(fa.total_sem_jus as float)/%s) >= 25.0
        group by e.cod_escl
    '''%(ano, regional_id, dias_letivos)

    data_maior_25 = conn.query(sql_maior_25)


    sql_escola = 'select cod_escl, nome from escola where regional=%s order by nome'%regional_id
    escolas = conn.query(sql_escola)

    result = escolas.merge(data_menor_10, on='cod_escl', how='left')
    result = result.merge(data_10_20, on='cod_escl', how='left')
    result = result.merge(data_20_25, on='cod_escl', how='left')
    result = result.merge(data_maior_25, on='cod_escl', how='left')

    result.fillna(0, inplace=True)

    result['total'] = result['_0_10'] + result['_10_20'] + result['_20_25'] + result['_25_100']
    result['p_0_10'] = 100*result['_0_10']/result['total']
    result['p_10_20'] = 100*result['_10_20']/result['total']
    result['p_20_25'] = 100*result['_20_25']/result['total']
    result['p_25_100'] = 100*result['_25_100']/result['total']


    return result


def regional(nome_regional, regional_id, dias_letivos, ano, mes):
    st.header("Secretaria Municipal de Educação - PBH", divider='rainbow')
    st.subheader('Percentual de Alunos por Taxa de Infrequência na %s'%nome_regional)
    st.write('Acumulado de Fevereiro à  %s de %s - Dias Letivos no período: %s'%(meses[mes], ano, dias_letivos))

    resultado = busca_resultados(regional_id, dias_letivos, ano)

    total_0_10 = resultado['_0_10'].sum(axis=0)
    total_10_20 = resultado['_10_20'].sum(axis=0)
    total_20_25 = resultado['_20_25'].sum(axis=0)
    total_25_100 = resultado['_25_100'].sum(axis=0)
    total = resultado['total'].sum(axis=0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label='Menor ou igual à 10%', value= str(round(100*(total_0_10/total), 1))+'%')
    col2.metric(label='Entre 10% e 20%', value=str(round(100*(total_10_20/total), 1))+'%')
    col3.metric(label='Entre 20% e 25%', value=str(round(100*(total_20_25/total), 1))+'%')
    col4.metric(label='Maior ou igual à 25%', value=str(round(100*(total_25_100/total), 1))+'%')
    style_metric_cards()


    options = {
        'chart': {
          'type': 'bar',
          'stacked': True,
          'stackType': '100%'
        },
        'colors': ['#1ED0DF', '#fde910','#ffa500', "#ff0000"],
        'plotOptions': {
          'bar': {
            'horizontal': True,
          },
        },
        'stroke': {
          'width': 1,
          'colors': ['#fff']
        },
        'title': {
                'text': 'Percentual de Alunos por Taxa de Infrequência nas escolas da %s'%nome_regional,
                'horizontalAlign': 'center',
        },
        'subtitle': {
                'text': 'Acumulado de Fevereiro à  %s de %s - Dias Letivos no período: %s'%(meses[mes], ano, dias_letivos),
        },  
        'yaxis': {
            'labels': {
                'maxWidth': 500,
            }            
        },      
        'xaxis': {
          'categories':  resultado['nome'].tolist(),
        },
        'fill': {
          'opacity': 1
        },
        'legend': {
          'position': 'top',
          'horizontalAlign': 'center',
          'offsetX': 50
        }
    }
    series = [dict(name='Menor ou igual à 10%',data=resultado['p_0_10'].tolist()),
              dict(name='Entre 10% e 20%',data=resultado['p_10_20'].tolist()),
              dict(name='Entre 20% e 25%',data=resultado['p_20_25'].tolist()),
              dict(name='Maior ou igual à 25%',data=resultado['p_25_100'].tolist())]

    st_apexcharts(options, series, 'bar', 1100)    

    rename = {
        'nome':'Local', 
        '_0_10':'Menor ou igual à 10%', 
        '_10_20':'Entre 10% e 20%', 
        '_20_25':'Entre 20% e 25%', 
        '_25_100':'Maior ou igual à 25%', 
        'total':'Total'
    }
    
    df=resultado[['nome', '_0_10', '_10_20', '_20_25', '_25_100', 'total']].rename(columns=rename)

    st.write('Total de Alunos por Taxa de Infrequência nas escolas da %s'%nome_regional)
    st.dataframe(df, hide_index=True, use_container_width=True)


import streamlit as st
import pandas as pd
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from oniz_client import OnizClient
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Dashboard de Produtividade", layout="wide")

st_autorefresh(
    interval=900000,
    key="prod_refresh"
)

st.markdown("""
<style>

/* remove header */
header[data-testid="stHeader"] {
    background: transparent;
}

/* remove espaço extra acima dos elementos */
[data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}

/* remove footer */
footer {
    visibility: hidden;
}

/* remove espaços do topo */
.main .block-container {
    max-width: 90% !important;
    padding-top: 0rem;
    padding-bottom: 0rem;
}

/* remove margem do título */
h3 {
    margin-top: 0rem !important;
    margin-bottom: 0.5rem !important;
}

.block-container {
    padding-top: 3rem !important;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100%;
}

</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=900)
def carregar_dados_oniz():
    
    client = OnizClient(
        usuario="311048",
        senha="Kthl22010804*"
    )
    
    client.login()
    
    return client.extrair_gaiolas()
    
def transformar_dados(df):
    df["Valor contabil"] = (
        df["Valor R$"]
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .astype(float)
    )
    
    df["Valor R$"] = "R$ " + df["Valor R$"]
    
    df["Status"] = "Em andamento"    
    
    df.loc[
        (df["Box separado"] == 0) &
        (df["Ilha separado"] == 0),
        "Status",
    ] = "Não iniciado"
    
    df.loc [
        (df["% Separação Box"] == 100) &
        (df["% Separação Ilha"] == 100),
        "Status"
    ] = "Finalizado"
    
    df["Saida datetime"] = pd.to_datetime(df["Saida"], format="%d/%m/%Y")
    
    df["Itens separados carga"] = df["Box separado"] + df["Ilha separado"]
    df["Total itens da carga"] = df["Box Total"] + df["Ilha Total"]
    df["Itens Carga"] =  df["Itens separados carga"].astype(int).astype(str) + " / " + df["Total itens da carga"].astype(int).astype(str)
    df["% Separação Carga"] = (df["Itens separados carga"] / df["Total itens da carga"]) * 100
    return df
    
def aplicar_filtros(df):
    
   col1, col2, col3, col4 = st.columns(4)
   
   with col1:
        data_selecionada = st.date_input("Selecione uma data de saída: ")
        df_filtrado = df[df["Saida datetime"].dt.date == data_selecionada]
        return df_filtrado

def exibir_analise(df):
        
    # Valores financeiros
        
    valor_total_financeiro = df["Valor contabil"].sum()
    valor_financeiro_a_separar = df.loc[
        (df["Status"] == "Não iniciado") |
        (df["Status"] == "Em andamento"),
        "Valor contabil"
    ].sum()
    valor_financeiro_separado = df.loc[
        df["Status"] == "Finalizado",
        "Valor contabil"
    ].sum()
    
    if valor_total_financeiro == 0:
        perc_financeiro_separado = 100
    else:
        perc_financeiro_separado = (
            (valor_financeiro_separado / valor_total_financeiro) * 100
            if valor_total_financeiro > 0
            else 0
        )
        
    # Valores em box
            
    total_itens_box = df["Box Total"].sum()
    separado_box = df["Box separado"].sum()
    pendente_box = total_itens_box - separado_box
    
    if total_itens_box == 0:
        perc_box = 100
    else:
        perc_box = (
            (separado_box / total_itens_box) * 100
            if total_itens_box > 0
            else 0
        )
    
    # Valores em ilha
    
    total_itens_ilha = df["Ilha Total"].sum()
    separado_ilha = df["Ilha separado"].sum()
    pendente_ilha = total_itens_ilha - separado_ilha
    
    if total_itens_ilha == 0:
        perc_ilha = 100
    else:
        perc_ilha = (
            (separado_ilha / total_itens_ilha) * 100
            if total_itens_ilha > 0
            else 0
        )
        
    # Valores em cargas
    
    total_cargas = len(df["Carga"])
    cargas_a_separar = (df["Status"] != "Finalizado").sum()
    cargas_separadas = (df["Status"] == "Finalizado").sum()
    
    if total_cargas == 0:
        perc_cargas_finalizadas = 100
    else:
        perc_cargas_finalizadas = (
            (cargas_separadas / total_cargas) * 100
            if total_cargas > 0
            else 0
        )
    
    col1, col2, col3, col4 = st.columns([1,1,1,1], gap="xxsmall", vertical_alignment="center")
    
    st.markdown("""
        <style>
            .card {
                border-radius: 15px;
                margin-bottom: 14px;
                margin-left: 0.5px;
                margin-right: 0.5px;
                padding: 10px;
                min-height: 90px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                text-align: center;
            }

            .card-valor {
                font-size: 15px;
                font-weight: 600;
                color: white;
                line-height: 1;
                margin-bottom: 10px;
            }

            .card-legenda {
                font-weight: 500;
                font-size: 12px;
                margin-top: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

        </style>
        """, unsafe_allow_html=True)
    
    def criar_card(legenda, valor, fundo="#323232;", cor_valor="white", cor_legenda="#b2b2b2", borda_baixo="#666666", borda_esquerda="#666666"): 
        st.markdown(f"""
            <div class="card" style="background-color:{fundo}; border-bottom: 5px solid {borda_baixo}; border-left: 3px solid {borda_esquerda};"> 
                <div class="card-valor" style="color:{cor_valor}";">{valor}</div>
                <div class="card-legenda" style="color: {cor_legenda}";">{legenda}</div> 
            </div> """, unsafe_allow_html=True)
        
    # Resumo valores
    with col1:
        with st.container(border=True):
            
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #946b2d 0%, #5d5d5d 100%);                    
                    color:white;
                    padding:8px 12px;
                    border-radius:8px;
                    font-weight:600;
                    text-align:center;
                    margin-bottom:20px;
                ">
                    Resumo Valores
                </div>
                """, unsafe_allow_html=True)
            
            col5, col6, col7 = st.columns(3, gap="small")
            
            with col5:
                criar_card(legenda="Total", 
                    valor=f"R$ {valor_total_financeiro:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")                    
                )
            with col6:
                criar_card(legenda="A Separar", valor=f"R$ {valor_financeiro_a_separar:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
            with col7:
                criar_card(legenda="Separado", valor=f"R$ {valor_financeiro_separado:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

            if perc_financeiro_separado >= 80:
                criar_card(legenda="% Separado", valor=f"{perc_financeiro_separado:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#14532D",
                        cor_valor="#5ce488",
                        cor_legenda="#A7F3D0",
                        borda_baixo="#6EE7B7",
                        borda_esquerda="#6EE7B7"
                    )
            elif perc_financeiro_separado>=50:
                criar_card(legenda="% Separado", valor=f"{perc_financeiro_separado:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#854D0E",
                        cor_valor="#FDE68A",
                        cor_legenda="#FEF3C7",
                        borda_baixo="#FCD34D",
                        borda_esquerda="#FCD34D"
                    )
            else:
                criar_card(legenda="% Separado", valor=f"{perc_financeiro_separado:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#7F1D1D",
                        cor_valor="#FCA5A5",
                        cor_legenda="#FECACA",
                        borda_baixo="#F87171",
                        borda_esquerda="#F87171"
                    )
    
    # Resumo Box    
    with col2:
        with st.container(border=True):
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 100%);
                    color:white;
                    padding:8px 12px;
                    border-radius:8px;
                    font-weight:600;
                    text-align:center;
                    margin-bottom:20px;
                ">
                    Resumo Ilha
                </div>
                """, unsafe_allow_html=True)
            
            col5, col6, col7 = st.columns(3, gap="small")
            
            with col5:
                criar_card(legenda="Total", valor=total_itens_box)
            
            with col6:
                criar_card(legenda="A Separar", valor=pendente_box)
                
            with col7:
                criar_card(legenda="Separado", valor=separado_box)
            
            if perc_box >= 80:
                criar_card(legenda="% Separado", valor=f"{perc_box:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#14532D",
                        cor_valor="#5ce488",
                        cor_legenda="#A7F3D0",
                        borda_baixo="#6EE7B7",
                        borda_esquerda="#6EE7B7"
                    )
            elif perc_box>=50:
                criar_card(legenda="% Separado", valor=f"{perc_box:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#854D0E",
                        cor_valor="#FDE68A",
                        cor_legenda="#FEF3C7",
                        borda_baixo="#FCD34D",
                        borda_esquerda="#FCD34D"
                    )
            else:
                criar_card(legenda="% Separado", valor=f"{perc_box:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#7F1D1D",
                        cor_valor="#FCA5A5",
                        cor_legenda="#FECACA",
                        borda_baixo="#F87171",
                        borda_esquerda="#F87171"
                    )
        
    # Resumo Ilha         
    with col3:
        with st.container(border=True):
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #0066B3 0%, #0F766E 100%);
                    color: white;
                    padding:8px 12px;
                    border-radius:8px;
                    font-weight:600;
                    text-align:center;
                    margin-bottom:20px;
                ">
                    Resumo Box
                </div>
                """, unsafe_allow_html=True)
            
            col5, col6, col7 = st.columns(3, gap="small")
            
            with col5:
                criar_card(legenda="Total", valor=total_itens_ilha)
            
            with col6:
                criar_card(legenda="A Separar", valor=pendente_ilha)
                
            with col7:
                criar_card(legenda="Separado", valor=separado_ilha)
            
            if perc_ilha >= 80:
                criar_card(legenda="% Separado", valor=f"{perc_ilha:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#14532D",
                        cor_valor="#5ce488",
                        cor_legenda="#A7F3D0",
                        borda_baixo="#6EE7B7",
                        borda_esquerda="#6EE7B7"
                    )
            elif perc_ilha>=50:
                criar_card(legenda="% Separado", valor=f"{perc_ilha:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#854D0E",
                        cor_valor="#FDE68A",
                        cor_legenda="#FEF3C7",
                        borda_baixo="#FCD34D",
                        borda_esquerda="#FCD34D"
                    )
            else:
                criar_card(legenda="% Separado", valor=f"{perc_ilha:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#7F1D1D",
                        cor_valor="#FCA5A5",
                        cor_legenda="#FECACA",
                        borda_baixo="#F87171",
                        borda_esquerda="#F87171"
                    )
        
    # Resumo cargas    
    with col4:
        with st.container(border=True):
            st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #374151 0%, #1E3A8A 100%);
                    color: white;
                    padding:8px 12px;
                    border-radius:8px;
                    font-weight:600;
                    text-align:center;
                    margin-bottom:20px;
                ">
                    Resumo Carga
                </div>
                """, unsafe_allow_html=True)
            
            col5, col6, col7 = st.columns(3, gap="small")
            
            with col5:
                criar_card(legenda="Total", valor=total_cargas)
            
            with col6:
                criar_card(legenda="A Separar", valor=cargas_a_separar)
                
            with col7:
                criar_card(legenda="Separado", valor=cargas_separadas)
            
            if perc_cargas_finalizadas >= 80:
                criar_card(legenda="% Separado", valor=f"{perc_cargas_finalizadas:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#14532D",
                        cor_valor="#5ce488",
                        cor_legenda="#A7F3D0",
                        borda_baixo="#6EE7B7",
                        borda_esquerda="#6EE7B7"
                    )
            elif perc_cargas_finalizadas>=50:
                criar_card(legenda="% Separado", valor=f"{perc_cargas_finalizadas:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#854D0E",
                        cor_valor="#FDE68A",
                        cor_legenda="#FEF3C7",
                        borda_baixo="#FCD34D",
                        borda_esquerda="#FCD34D"
                    )
            else:
                criar_card(legenda="% Separado", valor=f"{perc_cargas_finalizadas:,.2f}%"
                        .replace(",", "X")
                        .replace(".", ",")
                        .replace("X", "."),
                        fundo="#7F1D1D",
                        cor_valor="#FCA5A5",
                        cor_legenda="#FECACA",
                        borda_baixo="#F87171",
                        borda_esquerda="#F87171"
                    )
    
    # Criação de progress bar
    cell_renderer = JsCode("""
    class ProgressCellRenderer {
        init(params) {

            let value = Number(params.value) || 0;

            let color = '#f05656';

            if (value >= 100)
                color = '#10b981';
            else if (value >= 50)
                color = '#f59e0b';

            let texto = `${value.toFixed(0)}%`;
            
            let textoStyle = '';
            
            if (value <= 5)
                textoStyle = 'padding-left: 6px; text-align: left;';
            
            this.eGui = document.createElement('div');
            
            this.eGui.style.height = '100%';
            this.eGui.style.display = 'flex';
            this.eGui.style.alignItems = 'center';

            this.eGui.innerHTML = `
                <div style="
                    width:100%;
                    background:#ced4da;
                    border-radius:5px;
                    height:20px;
                ">
                    <div style="
                        width:${value}%;
                        background:${color};
                        height:20px;
                        border-radius:5px;
                        text-align:center;
                        font-size:12px;
                        line-height:20px;
                        color: black;
                        font-weight: bold;
                        ${textoStyle}
                    ">
                        ${(value).toFixed(0)}%
                    </div>
                </div>
            `;
        }

        getGui() {
            return this.eGui;
        }
    }
    """)
    
    df_carga = df[["Nr.", "Carga", "Rota", "Saida", "Entregas", "Prioridade", "Valor R$"]]
    df_box = df[["Itens Gaiola", "% Separação Box"]]
    df_ilha = df[["Itens Flow Rack", "% Separação Ilha"]]
    df_vl_carga = df[["Itens Carga", "% Separação Carga"]]
    
    col4, col5, col6, col7 = st.columns([3,1,1,1])
    
    # Tabela de dados da carga
    with col4:
        gb_carga = GridOptionsBuilder.from_dataframe(df_carga)

        gb_carga.configure_column(
            "Rota",
            minWidth = 200,
        )
        
        for col in df_carga.columns:
            gb_carga.configure_column(
                col,
                filter=False,
                sortable=False,
                suppressMenu=True
            )
        
        gb_carga.configure_default_column(
            headerClass="ag-center-header",
            cellStyle={"textAlign": "center"},
            flex=1,
            resizable=True,
            sortable=False,
            minWidth=80,
            supressMenu=True
        )
        
        gb_carga.configure_grid_options(domLayout="autoHeight")
            
        AgGrid(
            df_carga,
            gridOptions=gb_carga.build(),
            columns_auto_size_mode= "FIT_CONTENTS",
            allow_unsafe_jscode=True,
            custom_css= {
                ".ag-header-cell-label": {
                    "justify-content": "center",
                    "width": "100%"
                },
                ".ag-header-cell-text": {
                    "width": "100%",
                    "text-align": "center"
                }
            }
        )
    
    # Tabela de valores do Box
    with col5:        
        gb_box = GridOptionsBuilder.from_dataframe(df_box)
        
        gb_box.configure_default_column(
            headerClass="ag-center-header",
            cellStyle={"textAlign": "center"},
            flex=1,
            resizable=True,
            sortable=False
        )
        
        for col in df_box.columns:
            gb_box.configure_column(
                col,
                filter=False,
                sortable=False,
                suppressMenu=True
            )
            
        gb_box.configure_column(
            "Itens Gaiola",
            header_name="Itens Box"
        )
        
        gb_box.configure_column(
            "% Separação Box",
            cellRenderer=cell_renderer
        )
        
        gb_box.configure_grid_options(domLayout="autoHeight")
        
        AgGrid(
            df_box,
            gridOptions=gb_box.build(),
            allow_unsafe_jscode=True,
            custom_css= {
                ".ag-header-cell-label": {
                    "justify-content": "center",
                    "width": "100%"
                },
                ".ag-header-cell-text": {
                    "width": "100%",
                    "text-align": "center"
                }
            }
        )
    
    # Tabela de valores da Ilha
    with col6:        
        gb_ilha = GridOptionsBuilder.from_dataframe(df_ilha)
        
        gb_ilha.configure_default_column(
            cellStyle={"textAlign": "center"},
            flex=1,
            resizable=True,
            sortable=False
        )
        
        for col in df_ilha.columns:
            gb_ilha.configure_column(
            col,
            filter=False,
            sortable=False,
            suppressMenu=True
        )
            
        gb_ilha.configure_column(
            "Itens Flow Rack",
            header_name="Itens Ilha"
        )
        
        gb_ilha.configure_column(
            "% Separação Ilha",
            cellRenderer=cell_renderer
        )
        
        gb_ilha.configure_grid_options(domLayout="autoHeight")
        
        AgGrid(
            df_ilha,
            gridOptions=gb_ilha.build(),
            allow_unsafe_jscode=True,
            custom_css= {
                ".ag-header-cell-label": {
                    "justify-content": "center",
                    "width": "100%"
                },
                ".ag-header-cell-text": {
                    "width": "100%",
                    "text-align": "center"
                }
            }
    )
        
    # Tabela de valores de carga    
    with col7:
        gb_tot_carga = GridOptionsBuilder.from_dataframe(df_vl_carga)
        
        gb_tot_carga.configure_default_column(
            cellStyle={"textAlign": "center"},
            flex=1,
            resizable=True,
            sortable=False
        )
        
        for col in df_vl_carga.columns:
            gb_tot_carga.configure_column(
            col,
            filter=False,
            sortable=False,
            suppressMenu=True
        )
        
        gb_tot_carga.configure_column(
            "% Separação Carga",
            cellRenderer=cell_renderer
        )
        
        gb_tot_carga.configure_grid_options(domLayout="autoHeight")
        
        AgGrid(
            df_vl_carga,
            gridOptions=gb_tot_carga.build(),
            allow_unsafe_jscode=True,
            custom_css= {
                ".ag-header-cell-label": {
                    "justify-content": "center",
                    "width": "100%"
                },
                ".ag-header-cell-text": {
                    "width": "100%",
                    "text-align": "center"
                }
            }
        )     
        
def main():
    
    df = carregar_dados_oniz()
    st.write("Última atualização:", pd.Timestamp.now())
    
    st.markdown(
        """
        <h2 style="
            text-align:center;
            margin-top:0px;
            margin-bottom:15px;
        ">
            Acompanhamento de produção de cargas
        </h2>
        """,
        unsafe_allow_html=True
    )    
    
    df = transformar_dados(df)
    df = aplicar_filtros(df)
    exibir_analise(df)

if __name__ == "__main__":
    main()

import hashlib
import requests
import pandas as pd
from io import StringIO
import numpy as np


class OnizClient:
    def __init__(self, usuario, senha):
        self.base_url = "https://sys.oniz.com.br"
        self.login_url = f"{self.base_url}/login.php"

        self.usuario = usuario
        self.senha = senha
        self.session = requests.Session()

        self.headers = {
            "User-Agent": "Mozilla/5.0",
        }
    
    def _gerar_senha_md5(self):
        return hashlib.md5(self.senha.encode()).hexdigest()

    def login(self):
        login_data = {
            "f_login_submitted": "1",
            "f_ds_apelido": self.usuario,
            "f_ds_senha": self._gerar_senha_md5(),
            "f_submit": "Enviar"
        }

        response = self.session.post(
            self.login_url,
            data=login_data,
            headers=self.headers
        )

        if response.status_code != 200:
            raise Exception("Erro ao fazer login")

    def extrair_gaiolas(self):
        
        url = f"{self.base_url}/fil_analise_separacao_gaiolas.php"
        
        response = self.session.get(
            url,
            headers=self.headers
        )
        
        dfs = pd.read_html(StringIO(response.text))
        
        df = dfs[1]
        
        df = df.dropna(how="all")
        df = df.reset_index(drop=True)
        df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
        
        df = df[pd.to_numeric(df["Carga"], errors="coerce").notna()]
        df["Carga"] = df["Carga"].astype(int)
        
        # Separando produzido de total Box
        
        df[["Box separado", "Box Total"]] = (
            df["Itens Gaiola"].astype(str).str.split("/", expand=True).astype(int)
        )
        
        df["% Separação Box"] = np.where(
            df["Box Total"] == 0,
            100,
            (df["Box separado"] / df["Box Total"]) * 100
        )
        
        # Separando produzido de total Ilha
        
        df[["Ilha separado", "Ilha Total"]] = (
            df["Itens Flow Rack"].astype(str).str.split("/", expand=True).astype(int)
        )
        
        df["% Separação Ilha"] = np.where(
            df["Ilha Total"] == 0,
            100,
            (df["Ilha separado"] / df["Ilha Total"]) * 100
        )
        
        return df

if __name__ == "__main__":
    
    client = OnizClient(usuario="311048", senha="Kthl22010804*")

    client.login()
    
    df = client.extrair_gaiolas()
    
    df.to_excel(
        r"C:\Users\marcio.junior\OneDrive - Oniz Distribuidora\Arquivos de Patrick Schaffer - Logística - CD SUL - CCH\2025\05 - Armazém\08 - Produtividade\Acompanhamento producao\producao_gaiolas.xlsx",
        index=False
    )
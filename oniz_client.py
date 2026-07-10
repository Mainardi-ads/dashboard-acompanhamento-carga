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
            headers=self.headers,
            timeout=30
        )

        if response.status_code != 200:

            raise Exception(
                f"Erro ao fazer login ({response.status_code})"
            )

        return response

    def extrair_gaiolas(self):

        url = f"{self.base_url}/fil_analise_separacao_gaiolas.php"

        response = self.session.get(
            url,
            headers=self.headers,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(
                f"Erro ao acessar a página ({response.status_code})"
            )

        try:

            dfs = pd.read_html(StringIO(response.text))

        except ValueError:

            raise Exception(
                "Nenhuma tabela foi encontrada na página."
            )

        # Procurar a tabela correta
        df = None

        for tabela in dfs:

            if isinstance(tabela.columns, pd.MultiIndex):
                tabela.columns = tabela.columns.get_level_values(0)

            if "Carga" in tabela.columns:
                df = tabela.copy()
                break

        if df is None:

            raise Exception(
                f"Tabela de gaiolas não encontrada. "
                f"Tabelas encontradas: {len(dfs)}"
            )

        # Limpeza
        df = df.dropna(how="all")
        
        if df.empty:
            return df

        df = df.reset_index(drop=True)

        # Garante que os nomes das colunas sejam strings
        df.columns = df.columns.map(str)

        # Remove colunas Unnamed
        df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

        # Remove linhas sem carga
        df = df[
            pd.to_numeric(
                df["Carga"],
                errors="coerce"
            ).notna()
        ]

        df["Carga"] = df["Carga"].astype(int)

        # -------- BOX --------

        if "Itens Gaiola" not in df.columns:

            raise Exception(
                "Coluna 'Itens Gaiola' não encontrada."
            )

        if df.empty:

            df["Box separado"] = 0
            df["Box Total"] = 0

        else:

            split = (
                df["Itens Gaiola"]
                .astype(str)
                .str.split("/", expand=True)
            )

            if split.shape[1] >= 2:

                df[["Box separado", "Box Total"]] = (

                    split.iloc[:, :2]

                    .apply(lambda x: x.str.strip())

                    .replace("", "0")

                    .astype(int)

                )

            else:

                df["Box separado"] = 0
                df["Box Total"] = 0

        df["% Separação Box"] = np.where(

            df["Box Total"] == 0,

            100,

            (df["Box separado"] / df["Box Total"]) * 100

        )

        # -------- ILHA --------

        if "Itens Flow Rack" not in df.columns:

            raise Exception(
                "Coluna 'Itens Flow Rack' não encontrada."
            )

        if df.empty:

            df["Ilha separado"] = 0
            df["Ilha Total"] = 0

        else:

            split = (
                df["Itens Flow Rack"]
                .astype(str)
                .str.split("/", expand=True)
            )

            if split.shape[1] >= 2:

                df[["Ilha separado", "Ilha Total"]] = (

                    split.iloc[:, :2]

                    .apply(lambda x: x.str.strip())

                    .replace("", "0")

                    .astype(int)

                )

            else:

                df["Ilha separado"] = 0
                df["Ilha Total"] = 0

        df["% Separação Ilha"] = np.where(

            df["Ilha Total"] == 0,

            100,

            (df["Ilha separado"] / df["Ilha Total"]) * 100

        )

        return df
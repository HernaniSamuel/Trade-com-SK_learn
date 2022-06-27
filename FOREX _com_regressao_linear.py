import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from sklearn.metrics import r2_score
from iqoptionapi.stable_api import IQ_Option
from time import time,  sleep
from datetime import datetime
from dateutil import tz

API = IQ_Option('<e-mail>', '<senha>')
API.connect()
API.change_balance('PRACTICE')
while True:
    if API.check_connect() == False:
        API.connect()
        conectar = 'Desconectado'
    else:
        conectar = 'Conectado'
        break

    sleep(1)


def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]


velas = []
tempo = time()
t = 3600

for i in range(3):
    X = API.get_candles('EURUSD', t, 1000, tempo)
    velas = X+velas
    tempo = int(X[0]['from'])-1

for c in range(0, len(velas)):
    velas[c]['from'] = timestamp_converter(velas[c]['from'])
df = pd.DataFrame(velas)
df.rename(columns={'max': 'maxima', 'min': 'minima', 'open': 'abertura', 'close': 'fechamento', 'from': 'tempo', }, inplace=True)

df['tempo'] = pd.to_datetime(df['tempo'], format='%Y-%m-%d')

df['mm5d'] = df['fechamento'].rolling(5).mean()
df['mm21d'] = df['fechamento'].rolling(21).mean()
df['mm50d'] = df['fechamento'].rolling(50).mean()

df['fechamento'] = df['fechamento'].shift(-1)

df.dropna(inplace=True)

df = df.reset_index(drop=True)

qtd_linhas = len(df)

qtd_linhas_treino = round(.70 * qtd_linhas)
qtd_linhas_teste = qtd_linhas - qtd_linhas_treino
qtd_linhas_validacao = qtd_linhas - 1

info = (
    f"linhas treino= 0:{qtd_linhas_treino}"
    f" linhas teste= {qtd_linhas_treino}:{qtd_linhas_treino + qtd_linhas_teste -1}"
    f" linhas validação= {qtd_linhas_validacao}"
)

features = df.drop(['tempo', 'fechamento'], 1)
labels = df['fechamento']

features_list = ('abertura', 'maxima', 'minima', 'volume', 'mm5d', 'mm21d', 'mm50d')

features = df.loc[:, ['mm50d', 'mm21d', 'mm5d', 'minima', 'maxima', 'volume', 'abertura']]

X_train = features[:qtd_linhas_treino]
X_test = features[qtd_linhas_treino:qtd_linhas_treino + qtd_linhas_teste - 1]

y_train = labels[:qtd_linhas_treino]
y_test = labels[qtd_linhas_treino:qtd_linhas_treino + qtd_linhas_teste - 1]


scaler = MinMaxScaler()
X_train_scale = scaler.fit_transform(X_train)
X_test_scale = scaler.transform(X_test)
print(len(X_train), len(y_train))
print(len(X_test), len(y_test))
lr = linear_model.LinearRegression()
lr.fit(X_train_scale, y_train)
pred = lr.predict(X_test_scale)


acerto = 0
erro = 0
for c in range(len(pred)):
    a = X_test[c]['abertura']-pred[c]
    b = X_test[c]['abertura']-y_test[c]
    if a < 0 and b < 0 or a > 0 and b > 0:
        acerto += 1

print(f'Taxa de acertos de {acerto/884}%')

cd = r2_score(y_test, pred)



print(f'Coeficiente de determinação:{cd * 100:.2f}%')

valor_novo = features.tail(1)

previsao = scaler.transform(valor_novo)

pred = lr.predict(previsao)

print(pred, velas[-1]['close'])

if pred > velas[-1]['close']:
    print('\033[1;32mCIMA!')
if pred < velas[-1]['close']:
    print('\033[1;31mBAIXO!')

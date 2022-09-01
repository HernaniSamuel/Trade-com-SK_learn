from iqoptionapi.stable_api import IQ_Option
from time import time,  sleep
from datetime import datetime
from dateutil import tz
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from sklearn.metrics import r2_score


def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]


def operacao(par, entrada, direcao, timeframe):
    global l, w
    _, id = API.buy_digital_spot(par, entrada, direcao, timeframe)

    if isinstance(id, int):
        while True:
            status, lucro = API.check_win_digital_v2(id)

            if status:
                if lucro > 0:
                    return 1
                else:
                    return -1
                break


def calcular_direcao():
    global velas, paridade, op

    labels = []
    minima = []
    volume = []
    mm5 = []

    c = 0
    while True:
        if c >= 4:
            media5 = (velas[c]['close'] + velas[c - 1]['close'] + velas[c - 2]['close'] + velas[c - 3]['close'] +
                      velas[c - 4]['close']) / 5
            minima.append(velas[c]['min'])
            volume.append(velas[c]['volume'])
            mm5.append(media5)
            labels.append(velas[c]['close'])
        if c == 2999:
            break
        c += 1

    features = []
    for i in range(0, 2996):
        a = [minima[i], volume[i], mm5[i]]
        features.append(a)

    # separando listas de dados de treinamentos e listas de dados de teste
    xtrain = []
    ytrain = []
    xtest = []
    ytest = []

    for c in range(0, 2089):
        xtrain.append(features[c])
        ytrain.append(labels[c])

    for c in range(0, 907):
        xtest.append(features[2089 + c])
        ytest.append(labels[2089 + c])

    # transformando dados
    scaler = MinMaxScaler()
    X_train_scale = scaler.fit_transform(xtrain)
    X_test_scale = scaler.transform(xtest)

    # criando, treinando e testando modelo de regressão linear
    lr = linear_model.LinearRegression()
    lr.fit(X_train_scale, ytrain)
    pred = lr.predict(X_test_scale)
    prev = pred[-1]
    cd = r2_score(ytest, pred)
    print(f'Coeficiente de determinação em {cd*100:.2f}%')

    if prev > velas[-1]['close']:
        op = 1
    if prev < velas[-1]['close']:
        op = -1


def pegar_velas(paridade):
    global velas
    tempo = time()
    t = 60
    for i in range(3):
        X = API.get_candles(paridade, t, 1000, tempo)
        velas = X + velas
        tempo = int(X[0]['from']) - 1


if __name__ == '__main__':
    API = IQ_Option('email', 'senha')
    API.connect()
    API.change_balance('PRACTICE')
    paridade = 'EURUSD'
    op = 0
    resultado = 0
    valor_inicial = API.get_balance()
    while True:
        if not API.check_connect():
            API.connect()
            print('Desconectado')
        else:
            print('Conectado')
            break
        sleep(1)

    velas = []
    pegar_velas(paridade)

    while True:
        del velas[0]
        X = API.get_candles(paridade, 60, 1, time())
        velas = velas + X
        calcular_direcao()
        if op == 1:
            resultado = operacao(paridade, 4, 'call', 1)
        if op == -1:
            resultado = operacao(paridade, 4, 'put', 1)

        if resultado == 1:
            print(f'\033[1;32m{timestamp_converter(X[0]["from"])}')
        if resultado == -1:
            print(f'\033[1;31m{timestamp_converter(X[0]["from"])}')

        if not API.check_connect():
            print('\n\033[1;31mConexão perdida!')
            break
        if API.get_balance() >= valor_inicial:
            print('\n\033[1;32mTake Profit atingido!')
            break

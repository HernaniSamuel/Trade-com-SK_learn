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

    scaler = MinMaxScaler()
    X_train_scale = scaler.fit_transform(xtrain)
    X_test_scale = scaler.transform(xtest)

    lr = linear_model.LinearRegression()
    lr.fit(X_train_scale, ytrain)
    pred = lr.predict(X_test_scale)
    prev = pred[-1]
    cd = r2_score(ytest, pred)
    print(f'Coeficiente de determinação [traduzido] em {(cd*100-99)*100}%')

    if prev > velas[-1]['close']:
        op = 1
    if prev < velas[-1]['close']:
        op = -1


def pegar_velas(paridade):
    global velas
    tempo = time()
    t = 3600
    for i in range(3):
        X = API.get_candles(paridade, t, 1000, tempo)
        velas = X + velas
        tempo = int(X[0]['from']) - 1


def operar(instrument_type, instrument_id, valor, side, take_profit, stop_lose, multiplicador):
    type = "market"
    limit_price = None
    stop_price = None
    stop_lose_kind = "percent"
    stop_lose_value = stop_lose
    take_profit_kind = "percent"
    take_profit_value = take_profit
    use_trail_stop = False
    auto_margin_call = False
    use_token_for_commission = False

    check, order_id = API.buy_order(instrument_type=instrument_type, instrument_id=instrument_id,
                                             side=side, amount=valor, leverage=multiplicador,
                                             type=type, limit_price=limit_price, stop_price=stop_price,
                                             stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
                                             take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
                                             use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
                                             use_token_for_commission=use_token_for_commission)


if __name__ == '__main__':
    API = IQ_Option('email', 'senha')
    API.connect()
    API.change_balance('PRACTICE')

    instrument_type = "forex"
    paridade = 'EURUSD'
    op = 0

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

    del velas[0]
    X = API.get_candles(paridade, 3600, 1, time())
    velas = velas + X
    calcular_direcao()
    if op == 1:
        operar(instrument_type, paridade, API.get_balance(), 'buy', 1, 95, 100)#('forex', paridade, valor de operação, direção, take profit, stop loss, multiplicador)
        print('comprar')
    if op == -1:
        operar(instrument_type, paridade, API.get_balance(), 'sell', 1, 95, 100)
        print('vender')

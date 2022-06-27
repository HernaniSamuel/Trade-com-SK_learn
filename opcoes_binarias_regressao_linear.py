from iqoptionapi.stable_api import IQ_Option
from time import time,  sleep
from datetime import datetime
from dateutil import tz
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model
from sklearn.metrics import r2_score


#Conversor de tempo
def timestamp_converter(x):
    hora = datetime.strptime(datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return str(hora.astimezone(tz.gettz('America/Sao Paulo')))[:-6]


#função de operação automática
def operacao(par, entrada, direcao, timeframe):
    global l, w
    _, id = API.buy_digital_spot(par, entrada, direcao, timeframe)

    if isinstance(id, int):
        while True:
            status, lucro = API.check_win_digital_v2(id)

            if status:
                if lucro > 0:
                    pass
                else:
                    pass
                break


#informações para login
API = IQ_Option('<e-mail>', '<senha>')
API.connect()
API.change_balance('PRACTICE')

#conectando na API
while True:
    if API.check_connect() == False:
        API.connect()
        print('Desconectado')
    else:
        print('Conectado')
        break
    sleep(1)

#definições de mercado e preço de operações
valor_operacao = 4
paridade = 'EURUSD-OTC'

#Pegando valor em conta antes do inicio das operações e definindo variáveis para pegar o valor mínimo e o valor máximo atingidos
valor_inicial = API.get_balance()
minimo = 0
maximo = 0

#inicio do processo
for contador in range(100):
    #listas para fornecimento de informação para a regressão linear
    labels = []
    minima = []
    volume = []
    mm5 = []

    #Pegando dados das velas
    velas = []
    tempo = time()
    t = 60

    for i in range(3):
        X = API.get_candles(paridade, t, 1000, tempo)
        velas = X+velas
        tempo = int(X[0]['from'])-1

    #Adicionando dados às listas
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

    #separando listas de dados de treinamentos e listas de dados de teste
    xtrain = []
    ytrain = []
    xtest = []
    ytest = []

    for c in range(0, 2089):
        xtrain.append(features[c])
        ytrain.append(labels[c])

    for c in range(0, 907):
        xtest.append(features[2089+c])
        ytest.append(labels[2089+c])

    #transformando dados
    scaler = MinMaxScaler()
    X_train_scale = scaler.fit_transform(xtrain)
    X_test_scale = scaler.transform(xtest)

    #criando, treinando e testando modelo de regressão linear
    lr = linear_model.LinearRegression()
    lr.fit(X_train_scale, ytrain)
    pred = lr.predict(X_test_scale)
    prev = pred[-1]
    cd = r2_score(ytest, pred)

    #fazendo as operações com base na última previsão
    if prev > velas[-1]['close']:
        operacao(paridade, valor_operacao, 'call', 1)
    if prev < velas[-1]['close']:
        operacao(paridade, valor_operacao, 'put', 1)

    valor_atual = API.get_balance()
    print(contador+1, end=' ')

    #pegando valor máximo e minimo atingidos durante as repetições
    if valor_atual < minimo:
        minimo = valor_atual
    if valor_atual > maximo:
        maximo = valor_atual

    #Condicionais que freiam a repetição
    if API.check_connect() == False:
        print('\n\033[1;31mConexão perdida!')
        break
    if valor_atual >= valor_inicial + 20:
        print('\n\033[1;32mTake Profit atingido!')
        break
    if valor_atual <= valor_inicial-valor_operacao*10:
        print('\n\033[1;31mStop Loss!\033[m')
        break

#informações obtidas das operações feitas
print(f'Número de operações feitas: {contador + 1}')
print(f'Valor de início: R${valor_inicial}')
print(f'mínima de R${minimo}, máxima de R${maximo}')
print(f'Valor após as operações: R${valor_atual}')

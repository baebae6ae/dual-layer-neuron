#앞에서 만들었던거 사용함
import numpy as np
import matplotlib.pyplot as plt

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

cancer = load_breast_cancer()
x = cancer.data
y = cancer.target
x_train_all, x_test, y_train_all, y_test = train_test_split(x, y, stratify=y, test_size=0.2, random_state=42)
x_train, x_val, y_train, y_val = train_test_split(x_train_all, y_train_all, stratify=y_train_all, test_size=0.2, random_state=42)

print(x_train.shape, x_val.shape) #훈련 전 데이터의 크기를 확인하는 습관을 가지자.

class SingleLayer:

  def __init__(self, learning_rate=0.1, l1=0, l2=0):
    self.w = None
    self.b = None
    self.losses = []
    self.val_losses = []
    self.w_history = []
    self.lr = learning_rate
    self.l1 = l1
    self.l2 = l2

  def forpass(self, x):
    z=np.dot(x,self.w) + self.b #np.sum말고 np.dot으로 행렬의 곱셈을 함.
    return z

  def backprop(self, x, err):
    m = len(x)
    w_grad = np.dot(x.T, err)/m #x.T는 x행렬을 전치시킨 것(행과 열을 뒤바꿈)으로 err과 곱하고 x 갯수로 나누어 w행렬에 곱할 수 있는 모양으로 만듦.
    b_grad = np.sum(err)/m
    return w_grad, b_grad

  def activation(self, z):
    a = 1/(1+np.exp(-z))
    return a

#배치경사하강법에서는 전체 샘플을 한꺼번에 계산하므로 for문이 사라짐
  def fit(self, x, y, epochs=100, x_val=None, y_val=None):
    y = y.reshape(-1, 1) #타깃을 열벡터로 바꿈
    y_val = y_val.reshape(-1, 1)
    m = len(x)
    self.w = np.ones((x.shape[1], 1)) #가중치 초기화
    self.b = 0
    self.w_history.append(self.w.copy()) #가중치 기록

    for i in range(epochs):
      z = self.forpass(x)
      a = self.activation(z)
      err = -(y-a)
      w_grad, b_grad = self.backprop(x,err)
      w_grad += (self.l1*np.sign(self.w) + self.l2*self.w) / m
      self.w -= self.lr * w_grad
      self.b -= self.lr*b_grad
      self.w_history.append(self.w.copy())
      a = np.clip(a, 1e-10, 1-1e-10)
      loss = np.sum(-(y*np.log(a) + (1-y)*np.log(1-a)))
      self.losses.append((loss + self.reg_loss()) / m)
      self.update_val_loss(x_val, y_val)

  def predict(self, x):
    z = self.forpass(x)
    return z>0

  def score(self, x, y):
    return np.mean(self.predict(x) == y.reshape(-1, 1))

  def reg_loss(self):
    return self.l1*np.sum(np.abs(self.w)) + self.l2/2*np.sum(self.w**2)

  def update_val_loss(self, x_val, y_val):
    z = self.forpass(x_val)
    a = self.activation(z)
    a = np.clip(a, 1e-10, 1-1e-10)
    val_loss = np.sum(-(y_val*np.log(a) + (1-y_val)*np.log(1-a)))
    self.val_losses.append((val_loss + self.reg_loss()) / len(y_val))

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(x_train) #fit을 이용해 변환규칙을 익힘
x_train_scaled = scaler.transform(x_train)
x_val_scaled = scaler.transform(x_val)

class DualLayer(SingleLayer):
  def __init__(self, units=10, learning_rate=0.1, l1=0, l2=0):
    self.units = units #은닉층의 뉴런 개수
    self.w1 = None
    self.b1 = None
    self.w2 = None
    self.b2 = None
    self.a1 = None
    self.losses = []
    self.val_losses = []
    self.lr = learning_rate
    self.l1 = l1
    self.l2 = l2

  def forpass(self, x):
    z1 = np.dot(x, self.w1) + self.b1
    self.a1 = self.activation(z1)
    z2 = np.dot(self.a1, self.w2) + self.b2
    return z2

  def backprop(self, x, err):
    m = len(x)
    w2_grad = np.dot(self.a1.T, err)/m
    b2_grad = np.sum(err)/m
    #출력층의 가중치와 절편에 대한 그레디언트 계산했음.
    err_to_hidden = np.dot(err, self.w2.T)*self.a1*(1-self.a1)
    #시그모이드함수의 그레디언트 계산
    w1_grad = np.dot(x.T, err_to_hidden)/m
    b1_grad = np.sum(err_to_hidden, axis=0)/m
    #은닉층의 가중치와 절편에 대한 그레디언트 계산했음.
    return w1_grad, b1_grad, w2_grad, b2_grad

  #이제 fit 매서드 만들건데 세개의 메서드로 나누어서 만듦.
  def init_weights(self, n_features): #가중치 초기화 매서드. n_features는 입력 특성의 개수를 지정하는 매개변수
    self.w1 = np.ones((n_features, self.units)) #(특성 개수, 은닉층의 개수)행렬 만들고 전부 1로 채운것
    self.b1 = np.zeros(self.units) #(은닉층의 개수) 행렬 만들고 전부 0으로 채운것
    self.w2 = np.ones((self.units, 1))
    self.b2 = 0

  def fit(self, x, y, epochs=100, x_val=None, y_val=None):
    y = y.reshape(-1, 1)
    y_val = y_val.reshape(-1,1)
    m=len(x)
    self.init_weights(x.shape[1])
    for i in range(epochs):
      a=self.training(x, y, m) #트레이닝 매서드로 따로 나눌거임
      a=np.clip(a, 1e-10, 1-1e-10)
      loss = np.sum(-(y*np.log(a) + (1-y)*np.log(1-a)))
      self.losses.append((loss + self.reg_loss()) / m)
      self.update_val_loss(x_val, y_val)

  def training(self, x, y, m):
    z = self.forpass(x)
    a = self.activation(z)
    err = -(y-a)
    w1_grad, b1_grad, w2_grad, b2_grad = self.backprop(x,err)
    w1_grad += (self.l1*np.sign(self.w1) + self.l2*self.w1) / m
    w2_grad += (self.l1*np.sign(self.w2) + self.l2*self.w2) / m
    self.w1 -= self.lr * w1_grad
    self.b1 -= self.lr * b1_grad
    self.w2 -= self.lr * w2_grad
    self.b2 -= self.lr * b2_grad
    return a

  def reg_loss(self):
    return self.l1*(np.sum(np.abs(self.w1)) + np.sum(np.abs(self.w2))) + self.l2/2*(np.sum(self.w1**2) + np.sum(self.w2**2))

  #나머지 메서드는 싱글레이어와 동일하기 때문에 상속받았으니 생략


#훈련하고 평가하기
dual_layer = DualLayer(l2=0.01)
dual_layer.fit(x_train_scaled, y_train, x_val=x_val_scaled, y_val=y_val, epochs=20000)
dual_layer.score(x_val_scaled, y_val)

#근데 이제 가중치 초기화를 랜덤으로 해야 더 매끄럽게 훈련할 수 있으니 다시 상속받아서 랜덤으로 가중치 초기화하게 만들어보자
class RandomInitNetwork(DualLayer):
  def init_weights(self, n_features):
    self.w1 = np.random.normal(0,1,(n_features, self.units))
    self.b1 = np.zeros(self.units)
    self.w2 = np.random.normal(0,1,(self.units,1))
    self.b2 = 0

random_init_net = RandomInitNetwork(l2=0.01)
random_init_net.fit(x_train_scaled, y_train, x_val=x_val, y_val=y_val, epochs=500)

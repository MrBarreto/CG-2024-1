import numpy as np
import matplotlib.pyplot as plt

# Verifica se houve interseção da esfera com o raio de luz
def intersecao_esfera(centro, raio, origem_raio, direcao_raio):
    b = 2 * np.dot(direcao_raio, origem_raio - centro)
    c = np.linalg.norm(origem_raio - centro) ** 2 - raio ** 2
    delta = b ** 2 - 4 * c
    if delta > 0:
        t1 = (-b + np.sqrt(delta)) / 2
        t2 = (-b - np.sqrt(delta)) / 2
        if t1 > 0 and t2 > 0:
            return min(t1, t2)
    return None

#Define a interseçao do plano com um raio de luz
def intersecao_plano(ponto_plano, normal_plano, origem_raio, direcao_raio):
    denom = np.dot(direcao_raio, normal_plano)
    if np.abs(denom) > 1e-6:  # Verifica se o denominador não é zero
        t = np.dot(ponto_plano - origem_raio, normal_plano) / denom
        if t >= 0:
            return t
    return None

#Percorre todos os elementos da cena e procura por aqule mais próximo
def encontrar_objeto_mais_proximo(objetos, origem_raio, direcao_raio):
    distancias = []
    for obj in objetos:
        if obj['tipo'] == 'esfera':
            distancias.append(intersecao_esfera(obj['centro'], obj['raio'], origem_raio, direcao_raio))
        elif obj['tipo'] == 'plano':
            distancias.append(intersecao_plano(obj['ponto'], obj['normal'], origem_raio, direcao_raio))
    
    objeto_mais_proximo = None
    distancia_minima = np.inf
    for indice, distancia in enumerate(distancias):
        if distancia and distancia < distancia_minima:
            distancia_minima = distancia
            objeto_mais_proximo = objetos[indice]
    return objeto_mais_proximo, distancia_minima

def normalizar(vetor):
    return vetor / np.linalg.norm(vetor)
#calcular a reflexão em relação a normal
def refletido(vetor, eixo):
    return vetor - 2 * np.dot(vetor, eixo) * eixo

def ray_tracing(origem_raio, direcao_raio, objetos, luz, camera, profundidade=0, profundidade_maxima=3):
    #Verifica se houve um estouro do número máximo de reflexsões se sim retorna preto
    if profundidade >= profundidade_maxima:
        return np.zeros((3))
    
    #Se não foi encontrado um objeto próximo ao raio, retorna preto
    objeto_mais_proximo, distancia_minima = encontrar_objeto_mais_proximo(objetos, origem_raio, direcao_raio)
    if objeto_mais_proximo is None:
        return np.zeros((3)) 

    intersecao = origem_raio + distancia_minima * direcao_raio
    #Verifica o tipo de objeto, se for uma esfera, a nomral é calculada, se for um plano a normal é inerente a ele
    if objeto_mais_proximo['tipo'] == 'esfera':
        normal_superficie = normalizar(intersecao - objeto_mais_proximo['centro'])
    elif objeto_mais_proximo['tipo'] == 'plano':
        normal_superficie = objeto_mais_proximo['normal']
    
    #Move um infinitésimo o ponto de interseção na direção da normal, com o intuito de evitar que o ponto seja sombreado pelo próprio objeto, gerando uma cena incorreta
    ponto_deslocado = intersecao + 1e-5 * normal_superficie
    intersecao_para_luz = normalizar(luz['posicao'] - ponto_deslocado)

    _, distancia_minima = encontrar_objeto_mais_proximo(objetos, ponto_deslocado, intersecao_para_luz)
    distancia_intersecao_luz = np.linalg.norm(luz['posicao'] - intersecao)
    #verifica se tem um objeto entre a luz e o ponto de intersecção
    esta_sombreado = distancia_minima < distancia_intersecao_luz

    #Se estiver sombreado retorna preto
    if esta_sombreado:
        return np.zeros((3))  

    iluminacao = np.zeros((3))

    #Calcula a contribuição de cada luz para a iluminação do ponto
    iluminacao += objeto_mais_proximo['ambiente'] * luz['ambiente']

    iluminacao += objeto_mais_proximo['difusa'] * luz['difusa'] * np.dot(intersecao_para_luz, normal_superficie)

    intersecao_para_camera = normalizar(camera - intersecao)
    H = normalizar(intersecao_para_luz + intersecao_para_camera)
    iluminacao += objeto_mais_proximo['especular'] * luz['especular'] * np.dot(normal_superficie, H) ** (objeto_mais_proximo['brilho'] / 4)

    # Se o objeto possui a propriedade de reflexão, então ele faz uma recursão chamando a função tendo como origem o ponto de intersseção deslocado e incrementando o número de 'pulos' que o raio faz 
    if 'reflexao' in objeto_mais_proximo:
        direcao_refletida = refletido(direcao_raio, normal_superficie)
        reflexao = objeto_mais_proximo['reflexao'] * ray_tracing(ponto_deslocado, direcao_refletida, objetos, luz, camera, profundidade + 1, profundidade_maxima)
        iluminacao += reflexao

    return iluminacao

largura = 600
altura = 400
#Posiciona a câmera em 1 no eixo z
camera = np.array([0, 0, 1])
proporcao = float(largura) / altura
# Define os limites da tela, e deforma os limites inferiores e superiores conforme a proporção da imagem
tela = (-1, 1 / proporcao, 1, -1 / proporcao)
#Define a luz da cena
luz = {
    'posicao': np.array([0, 5, 3]),
    'ambiente': np.array([1, 1, 1]),
    'difusa': np.array([1, 1, 1]),
    'especular': np.array([1, 1, 1])
}
#Define os objetos da cena
objetos = [
    {'tipo': 'esfera', 'centro': np.array([-0.3, -0.3, -0.5]), 'raio': 0.1, 'ambiente': np.array([0.3, 0.3, 0.1]), 'difusa': np.array([0.8, 0.6, 0.2]), 'especular': np.array([1, 1, 1]), 'brilho': 100, 'reflexao': 0.5},
    {'tipo': 'esfera', 'centro': np.array([0.3, -0.3, -0.5]), 'raio': 0.1, 'ambiente': np.array([0.3, 0.3, 0.1]), 'difusa': np.array([0.8, 0.6, 0.2]), 'especular': np.array([1, 1, 1]), 'brilho': 100, 'reflexao': 0.5},
    {'tipo': 'esfera', 'centro': np.array([0, 0, -1]), 'raio': 0.5, 'ambiente': np.array([0.1, 0.1, 0.3]), 'difusa': np.array([0.2, 0.2, 0.8]), 'especular': np.array([1, 1, 1]), 'brilho': 100, 'reflexao': 0.5},
    {'tipo': 'plano', 'ponto': np.array([0, -0.5, 0]), 'normal': np.array([0, 1, 0]), 'ambiente': np.array([0.1, 0.1, 0.1]), 'difusa': np.array([0.5, 0.5, 0.5]), 'especular': np.array([0.5, 0.5, 0.5]), 'brilho': 50}
]

imagem = np.zeros((altura, largura, 3)) #Define uma imagem com cada pixel tendo 3 dimensões, RGB
#Percore todos os pixels da imagem, define os mesmos e inicia a função de ray tracing
for i, y in enumerate(np.linspace(tela[1], tela[3], altura)):
    for j, x in enumerate(np.linspace(tela[0], tela[2], largura)):
        pixel = np.array([x, y, 0])
        origem = camera
        direcao = normalizar(pixel - origem)
        cor = ray_tracing(origem, direcao, objetos, luz, camera)
        imagem[i, j] = np.clip(cor, 0, 1)

plt.imsave('cena.png', imagem)

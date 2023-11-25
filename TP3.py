import argparse
import heapq
from collections import defaultdict
from math import log2

def obtener_frecuencias(texto):
    frecuencias = defaultdict(int)
    for caracter in texto:
        frecuencias[caracter] += 1
    return frecuencias

def construir_arbol_huffman(frecuencias):
    heap = [[frecuencia, [caracter, ""]] for caracter, frecuencia in frecuencias.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    return heap[0][1:]

def construir_diccionario_codigos(arbol_huffman):
    return {caracter: codigo for caracter, codigo in arbol_huffman}

def guardar_diccionario_codigos(diccionario_codigos, archivo):
    with open(archivo, 'wb') as f:
        # Guardar la cantidad de elementos en el diccionario
        f.write(len(diccionario_codigos).to_bytes(4, byteorder='big'))
        for caracter, codigo in diccionario_codigos.items():
            # Guardar caracter, longitud de código y código en el archivo
            f.write(bytes([ord(caracter), len(codigo)]) + codigo.encode('utf-8'))

def cargar_diccionario_codigos(archivo):
    diccionario_codigos = {}
    with open(archivo, 'rb') as f:
        # Leer la cantidad de elementos en el diccionario
        num_elementos = int.from_bytes(f.read(4), byteorder='big')
        for _ in range(num_elementos):
            # Leer caracter, longitud de código y código del archivo
            caracter = chr(f.read(1)[0])
            longitud_codigo = f.read(1)[0]
            codigo = f.read(longitud_codigo).decode('utf-8')
            diccionario_codigos[caracter] = codigo
    return diccionario_codigos

def comprimir(texto, diccionario_codigos):
    return ''.join(diccionario_codigos[caracter] for caracter in texto)

def descomprimir(bits_comprimidos, diccionario_codigos):
    texto_descomprimido = ''
    codigo_actual = ''
    for bit in bits_comprimidos:
        codigo_actual += bit
        for caracter, codigo in diccionario_codigos.items():
            if codigo == codigo_actual:
                texto_descomprimido += caracter
                codigo_actual = ''
                break
    return texto_descomprimido

def calcular_tasa_compresion(longitud_original, longitud_comprimida):
    return longitud_comprimida / longitud_original

def calcular_entropia(frecuencias):
    total = sum(frecuencias.values())
    return -sum((frecuencia / total) * log2(frecuencia / total) for frecuencia in frecuencias.values() if frecuencia > 0)

def calcular_longitud_media(frecuencias, diccionario_codigos):
    total = sum(frecuencias.values())
    longitud_media = sum((frecuencia / total) * len(codigo) for caracter, frecuencia in frecuencias.items() for _, codigo in diccionario_codigos.items() if caracter == _)
    return longitud_media

def calcular_rendimiento(entropia, longitud_media):
    return entropia / longitud_media

parser = argparse.ArgumentParser(description="Programa de compresión y descompresión utilizando Huffman")
parser.add_argument('archivo_original', type=str, help="Nombre del archivo de texto original")
parser.add_argument('archivo_comprimido', type=str, help="Nombre del archivo binario comprimido")
parser.add_argument('-c', action='store_true', help="Realizar compresión")
parser.add_argument('-d', action='store_true', help="Realizar descompresión")

args = parser.parse_args()

if not (args.c or args.d):
    print("Error: Debes especificar una de las opciones -c o -d.")
else:
    if args.c:
        with open(args.archivo_original, 'r') as f:
            texto_original = f.read()

        frecuencias = obtener_frecuencias(texto_original)
        arbol_huffman = construir_arbol_huffman(frecuencias)
        diccionario_codigos = construir_diccionario_codigos(arbol_huffman)

        bits_comprimidos = comprimir(texto_original, diccionario_codigos)

        # Guardar el diccionario de códigos en el archivo binario
        guardar_diccionario_codigos(diccionario_codigos, args.archivo_comprimido)

        # Append los bits comprimidos al archivo binario
        with open(args.archivo_comprimido, 'ab') as f:
            f.write(int(bits_comprimidos, 2).to_bytes((len(bits_comprimidos) + 7) // 8, byteorder='big'))

        tasa_compresion = calcular_tasa_compresion(len(texto_original) * 8, len(bits_comprimidos))
        entropia = calcular_entropia(frecuencias)
        longitud_media = calcular_longitud_media(frecuencias, diccionario_codigos)
        rendimiento = calcular_rendimiento(entropia, longitud_media)
        redundancia = 1 - rendimiento

        print(f"Compresión exitosa. Tasa de Compresión: {tasa_compresion:.2%}, Rendimiento: {rendimiento:.2%}, Redundancia: {redundancia:.2%}")

    elif args.d:
        # Cargar el diccionario de códigos desde el archivo binario
        diccionario_codigos = cargar_diccionario_codigos(args.archivo_comprimido)

        # Abrir el archivo comprimido en modo binario ('rb') para leer los bits comprimidos
        with open(args.archivo_comprimido, 'rb') as f:
            # Leer los bits comprimidos y convertirlos a una cadena binaria
            bits_comprimidos = ''.join(format(byte, '08b') for byte in f.read())

        # Descomprimir los bits comprimidos utilizando el diccionario de códigos
        texto_descomprimido = descomprimir(bits_comprimidos, diccionario_codigos)

        # Escribir el texto descomprimido en el archivo original
        with open(args.archivo_original, 'w') as f:
            f.write(texto_descomprimido)
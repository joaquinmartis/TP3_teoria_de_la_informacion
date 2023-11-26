import os
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
    return longitud_original/longitud_comprimida

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
parser.usage = "TP3.py original.txt archivo_comprimido.bin {-c|-d}"
parser.add_argument('archivo_original', type=str, help="Nombre del archivo de texto original")
parser.add_argument('archivo_comprimido', type=str, help="Nombre del archivo binario comprimido")
parser.add_argument('-c', action='store_true', help="Realizar compresión")
parser.add_argument('-d', action='store_true', help="Realizar descompresión")

args = parser.parse_args()

if (args.c and args.d):
    print("Error: debe seleccionar uno de los dos flags")
elif not (args.c or args.d):
    print("Error: Debes especificar una de las opciones -c o -d.")

elif args.c:
    with open(args.archivo_original, 'r') as f:
        texto_original = f.read()

    frecuencias = obtener_frecuencias(texto_original)
    arbol_huffman = construir_arbol_huffman(frecuencias)
    diccionario_codigos = construir_diccionario_codigos(arbol_huffman)

    bits_comprimidos = comprimir(texto_original, diccionario_codigos)
    import math

    with open(args.archivo_comprimido, 'wb') as f:
        # Escribir la longitud del diccionario_codigos en 1 byte
        f.write(len(diccionario_codigos).to_bytes(1, byteorder='big'))
    
        # Escribir la cantidad de bytes necesarios para representar los bits comprimidos
        bytes_necesarios = math.ceil(len(bits_comprimidos) / 8)
        f.write(bytes_necesarios.to_bytes(4, byteorder='big'))
    
        # Escribir el residuo de la división por 8 (cantidad de bits adicionales necesarios)
        f.write( (len(bits_comprimidos) % 8).to_bytes(1, byteorder='big'))

        # Escribir caracteres y frecuencias
        for caracter, frecuencia in frecuencias.items():
            f.write(ord(caracter).to_bytes(1, byteorder='big'))
            f.write(frecuencia.to_bytes(2, byteorder='big'))  # Puedes ajustar el número de bytes según tus necesidades.

        # Escribir bits comprimidos
        i = 0
        j = 0
        byte = 0
        while i < len(bits_comprimidos):
            byte = (byte << 1)
            if bits_comprimidos[i] == '1':
                byte = byte | 1
            i = i + 1
            j = j + 1
            if j == 8:
                j = 0
                f.write(byte.to_bytes(1, byteorder='big'))
                byte = 0

        # Escribir el último byte si es necesario
        if j > 0:
            byte = byte << (8 - j)
            f.write(byte.to_bytes(1, byteorder='big'))
    f.close()
    tasa_compresion = calcular_tasa_compresion(os.path.getsize(args.archivo_original),os.path.getsize(args.archivo_comprimido) )
    entropia = calcular_entropia(frecuencias)
    longitud_media = calcular_longitud_media(frecuencias, diccionario_codigos)
    rendimiento = calcular_rendimiento(entropia, longitud_media)
    redundancia = 1 - rendimiento

    print(f"Compresión exitosa. Tasa de Compresión: {tasa_compresion:.2}:1, Rendimiento: {rendimiento:.2%}, Redundancia: {redundancia:.2%}")

elif args.d:
    frecuencias = {}
    with open(args.archivo_comprimido, 'rb') as f:
        
        longitud_diccionario = int.from_bytes(f.read(1), byteorder='big')
        
        bytes_necesarios = int.from_bytes(f.read(4), byteorder='big')
        
        residuo_division = int.from_bytes(f.read(1), byteorder='big')
        
        for _ in range(longitud_diccionario):
            caracter = chr(int.from_bytes(f.read(1), byteorder='big'))
            frecuencia = int.from_bytes(f.read(2), byteorder='big')
            frecuencias[caracter] = frecuencia
        
        i = 0
        codificacion = ""
        while i < bytes_necesarios:
            byte = int.from_bytes(f.read(1), byteorder='big')
            bits = 8
            codAux = ""
    
            if i == bytes_necesarios - 1:
                bits = residuo_division
                byte = byte >> (8 - residuo_division)

            for j in range(bits):
                if (byte & 1) == 1:
                    codAux = codAux + "1"
                else:
                    codAux = codAux + "0"
                byte = byte >> 1

            # Invierte la cadena codAux antes de agregarla a codificacion
            codificacion = codificacion + codAux[::-1]
            i = i + 1
    f.close()
    arbol_huffman = construir_arbol_huffman(frecuencias)
    diccionario_codigos = construir_diccionario_codigos(arbol_huffman)
    # Descomprimir los bits comprimidos utilizando el diccionario de códigos
    texto_descomprimido = descomprimir(codificacion, diccionario_codigos)

    # Escribir el texto descomprimido en el archivo original
    with open(args.archivo_original, 'w') as f:
        f.write(texto_descomprimido)
    f.close()
    tasa_compresion = calcular_tasa_compresion(os.path.getsize(args.archivo_original),os.path.getsize(args.archivo_comprimido) )
    entropia = calcular_entropia(frecuencias)
    longitud_media = calcular_longitud_media(frecuencias, diccionario_codigos)
    rendimiento = calcular_rendimiento(entropia, longitud_media)
    redundancia = 1 - rendimiento
    print(f"Descompresión exitosa. Tasa de Compresión: {tasa_compresion:}:1, Rendimiento: {rendimiento:.2%}, Redundancia: {redundancia:.2%}")
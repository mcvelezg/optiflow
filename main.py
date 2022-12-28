# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 12:23:25 2022

@author: marvelez
"""

import streamlit as st
from pulp import *

def nombre_var(nombre, *indices):
    return nombre+'_'+'_'.join(str(x) for x in indices)  

def resuelve_modelo(archivo_plano):
    if archivo_plano:
        # 0. Crer modelo
        SW = LpProblem('MinCostoTotal', LpMinimize)
        
        # 1. Cargar datos
        datos = [linea.decode('utf-8').split() for linea in archivo_plano]
        requerimiento = 45*'='+'\n'
        requerimiento += "{:<10} {:<10} {:<12} {:^10} \n".format('Shipper', 'Origin', 'Destination', 'Quantity')
        requerimiento += 45*'='+'\n'
        for linea in datos:
            requerimiento +="{:<10} {:<10} {:<12} {:^10} \n".format(linea[0], linea[1], linea[2], linea[3])
        requerimiento += 45*'='+'\n'
        
        # 2. Definir conjuntos
        S  = sorted(list(set([i[0] for i in datos]))) # Shippers
        T  = sorted(list(set([i[1] for i in datos]+[i[2] for i in datos])))
        
        Shp_from_j, Shp_to_j = {}, {} # Shippers pumping {from terminal j}, {to terminal j}
        for line in datos:
            if line[1] in Shp_from_j:
                Shp_from_j[line[1]].add(line[0])
            else:
                Shp_from_j[line[1]] = set()
                Shp_from_j[line[1]].add(line[0])
            
            if line[2] in Shp_to_j:
                Shp_to_j[line[2]].add(line[0])
            else:
                Shp_to_j[line[2]] = set()
                Shp_to_j[line[2]].add(line[0])

        Trmnls_i_from_j,Trmnls_i_to_j = {}, {} # Terminals getting (pumping) oil of shipper i coming from (towards) j
        for line in datos:
            
            if line[0] in Trmnls_i_from_j:
                if line[1] in Trmnls_i_from_j[line[0]]:
                    Trmnls_i_from_j[line[0]][line[1]].add(line[2])
                else:
                    Trmnls_i_from_j[line[0]][line[1]] = set()
                    Trmnls_i_from_j[line[0]][line[1]].add(line[2])
            else:
                Trmnls_i_from_j[line[0]] = {line[1]:set()}
                Trmnls_i_from_j[line[0]][line[1]].add(line[2])

            if line[0] in Trmnls_i_to_j:
                if line[2] in Trmnls_i_to_j[line[0]]:
                    Trmnls_i_to_j[line[0]][line[2]].add(line[1])
                else:
                    Trmnls_i_to_j[line[0]][line[2]] = set()
                    Trmnls_i_to_j[line[0]][line[2]].add(line[1])
            else:
                Trmnls_i_to_j[line[0]] = {line[2]:set()}
                Trmnls_i_to_j[line[0]][line[2]].add(line[1])
        
        # 3. Parámetros
        c, v = {i:{} for i in S}, {i:{} for i in S}
        for line in datos:
            if line[1] in v[line[0]]:
                v[line[0]][line[1]][line[2]] = float(line[3])
                c[line[0]][line[1]][line[2]] = float(line[4])
            else:
                v[line[0]][line[1]] = {line[2]:float(line[3])}
                c[line[0]][line[1]] = {line[2]:float(line[4])}
        
        # 4. Variables
        x = {i:{} for i in S}
        for line in datos:
            if line[1] in x[line[0]]:
                x[line[0]][line[1]][line[2]] = LpVariable(nombre_var('x',line[0],line[1],line[2]), 0, None, cat=LpContinuous)
            else:
                x[line[0]][line[1]] = {line[2]:LpVariable(nombre_var('x',line[0],line[1],line[2]), 0, None, cat=LpContinuous)}
        
        # 5. Objetivo
        SW += lpSum(c[i][j][k]*x[i][j][k] for i in x for j in x[i] for k in x[i][j])

        # 6. Restricciones

        for j in T:
            SW += lpSum(v[i][j][k] for i in Shp_from_j[j] for k in Trmnls_i_from_j[i][j]) \
                - lpSum(v[i][k][j] for i in Shp_to_j[j]   for k in Trmnls_i_to_j[i][j]) \
               == lpSum(x[i][j][k] for i in Shp_from_j[j] for k in Trmnls_i_from_j[i][j]) \
                - lpSum(x[i][k][j] for i in Shp_to_j[j]   for k in Trmnls_i_to_j[i][j])

        for i in x:
            for j in x[i]:
                for k in x[i][j]:
                    SW +=  x[i][j][k] <= v[i][j][k]
        
        
        # 7. Resolver
        SW.solve()
        
        # 8. Imprimir resultado
        separador = 45*'='+'\n'
        resultado = separador
        resultado+="{:<10} {:<10} {:<12} {:^10} \n".format('Shipper', 'Origin', 'Destination', 'Quantity')
        resultado+=separador
        for i in x:
            for j in x[i]:
                for k in x[i][j]:
                    if x[i][j][k].value() > 0:
                        resultado+="{:<10} {:<10} {:<12} {:^10} \n".format(i, j, k, x[i][j][k].value())
        resultado+=separador
        return(requerimiento, resultado)
        
# ====================================
# APLICACIÓN WEB
# ====================================

header = st.container()
input_data =st.container()
solucion=''

with header:
    st.title('Modelo de Simplicación de Flujos')

with input_data:
    archivo = st.file_uploader('Subir archivo de requerimientos', type='txt', label_visibility='hidden')
    st.header('Datos de Entrada')
    if archivo:
        original, solucion = resuelve_modelo(archivo)
        st.text(original)
        
        result_summary = st.container()
        with result_summary:
            st.header('Resultado')
            st.text(solucion)
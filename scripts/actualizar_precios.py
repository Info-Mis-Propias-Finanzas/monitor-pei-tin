#!/usr/bin/env python3
"""Agrega a data/precios.json los cierres de PEI y TIN que falten, tomados de la BVC.

Uso:
    python3 scripts/actualizar_precios.py                 # actualiza data/precios.json
    python3 scripts/actualizar_precios.py ruta/precios.json

Correrlo cada día hábil en la mañana (hora Colombia). Solo agrega días ya cerrados:
el día en curso se ignora porque el precio todavía puede cambiar. Usa solo la librería
estándar de Python 3.9 o superior. Si la BVC no responde, termina con código 1 y no
modifica el archivo.
"""
import base64
import datetime
import json
import os
import random
import sys
import time
import urllib.request

RUTA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'data', 'precios.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36'
H = {'User-Agent': UA, 'Accept': 'application/json, text/plain, */*',
     'Origin': 'https://www.bvc.com.co', 'Referer': 'https://www.bvc.com.co/'}
# TIN pasó a negociación continua el 21 de enero de 2026; antes su precio era de referencia.
INICIO_CONTINUA = {'PEI': '2022-08-22', 'TIN': '2026-01-21'}


def get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def consulta(simbolo, desde, hasta):
    # La BVC entrega un token de un solo uso por consulta.
    tok = get(f'https://www.bvc.com.co/api/handshake?ts={int(time.time() * 1000)}&r={random.randint(10**8, 10**9)}', H)['token']
    q = (f'filters[market]=rv&filters[segment]=undefined&filters[nemotenic]={simbolo}'
         f'&filters[startDate]={desde}&filters[endDate]={hasta}')
    datos = get('https://rest.bvc.com.co/market-history?' + q,
                {**H, 'token': tok, 'k': base64.b64encode(q.encode()).decode()})
    return datos['data']['marketHistory']


def historico(simbolo, desde, hasta, intentos=3):
    # La BVC a veces corta la conexión: se repite la consulta completa (con token nuevo).
    for n in range(intentos):
        try:
            return consulta(simbolo, desde, hasta)
        except Exception:  # noqa: BLE001
            if n == intentos - 1:
                raise
            time.sleep(5 * (n + 1))


def num(v):
    return float(v) if v not in (None, '') else None


def main():
    rows = json.load(open(RUTA, encoding='utf-8'))
    hoy = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).date().isoformat()
    nuevos, resumen = 0, {}
    for f in ('PEI', 'TIN'):
        ult = max(r['fecha'] for r in rows if r['fondo'] == f)
        desde = (datetime.date.fromisoformat(ult) - datetime.timedelta(days=10)).isoformat()
        for x in historico(f, desde, hoy):
            d, c = x.get('tradeDate'), x.get('close_price')
            if not d or not c or float(c) < 1000 or d >= hoy:
                continue
            row = {'fondo': f, 'fecha': d, 'cierre': float(c),
                   'maximo': num(x.get('price_max')), 'minimo': num(x.get('price_min')),
                   'cantidad': num(x.get('contratos')) or 0, 'volumen_cop': num(x.get('volumen')) or 0,
                   'negociacion_continua': d >= INICIO_CONTINUA[f],
                   'fuente': 'BVC, históricos renta variable'}
            i = next((k for k, r in enumerate(rows) if r['fondo'] == f and r['fecha'] == d), None)
            if i is None:
                rows.append(row)
                nuevos += 1
            else:
                rows[i] = row
        ultimo = max((r for r in rows if r['fondo'] == f), key=lambda r: r['fecha'])
        resumen[f] = {'fecha': ultimo['fecha'], 'cierre': ultimo['cierre']}
    rows.sort(key=lambda r: (r['fondo'], r['fecha']))
    tmp = RUTA + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, separators=(',', ':'), ensure_ascii=False)
    os.replace(tmp, RUTA)
    print(json.dumps({'filas_nuevas': nuevos, 'total': len(rows), 'ultimo': resumen}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f'Error actualizando precios: {e}', file=sys.stderr)
        sys.exit(1)

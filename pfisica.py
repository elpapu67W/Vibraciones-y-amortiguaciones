import numpy as np
from scipy.integrate import solve_ivp

import csv

ms, ks, zs = 2.0, 800.0, 0.02
mb, kb, zb = 1.0, 100.0, 0.15
A = 0.01
F = 2.0
T_TOTAL = 30.0
Tnomas = 10.0

cs = 2*zs*np.sqrt(ks*ms)
cb = 2*zb*np.sqrt(kb*(mb + ms))

def fijo(t, s, f):
    w = 2*np.pi*f
    xg = A*np.sin(w*t)
    vg = A*w*np.cos(w*t)
    xs, vs = s
    return [vs, (-ks*(xs - xg) - cs*(vs - vg))/ms]

def aislado(t, s, f):
    w = 2*np.pi*f
    xg = A*np.sin(w*t)
    vg = A*w*np.cos(w*t)
    xb, vb, xs, vs = s
    fb = -kb*(xb - xg) - cb*(vb - vg)
    fs = -ks*(xs - xb) - cs*(vs - vb)
    return [vb, (fb - fs)/mb, vs, fs/ms]

def simular(f=F, t_total=T_TOTAL, paso=0.002):
    t_eval = np.arange(0, t_total, paso)
    rf = solve_ivp(fijo, (0, t_total), [0, 0], args=(f,), t_eval=t_eval,
                   method="DOP853", rtol=1e-8, atol=1e-10, max_step=0.01)
    ri = solve_ivp(aislado, (0, t_total), [0, 0, 0, 0], args=(f,), t_eval=t_eval,
                   method="DOP853", rtol=1e-8, atol=1e-10, max_step=0.01)
    t = rf.t
    w = 2*np.pi*f
    xg = A*np.sin(w*t)
    vg = A*w*np.cos(w*t)
    xs_f, vs_f = rf.y
    xb, vb, xs_i, vs_i = ri.y
    a_f = (-ks*(xs_f - xg) - cs*(vs_f - vg))/ms
    a_i = (-ks*(xs_i - xb) - cs*(vs_i - vb))/ms
    d_f = xs_f - xg
    d_i = xs_i - xb
    E_f = 0.5*ms*vs_f**2 + 0.5*ks*d_f**2
    E_i = 0.5*ms*vs_i**2 + 0.5*ks*d_i**2
    return dict(t=t, xg=xg, xb=xb, xs_f=xs_f, xs_i=xs_i,
                d_f=d_f, d_i=d_i, a_f=a_f, a_i=a_i, E_f=E_f, E_i=E_i)

def resultado(d, a, E, m):
    cruces = np.sum((d[m][:-1] < 0) & (d[m][1:] >= 0))
    return dict(amp=(d[m].max() - d[m].min())/2, amax=np.abs(a[m]).max(),
                Emax=E[m].max(), f=cruces/Tnomas)

def medir(r):
    m = r["t"] > r["t"][-1] - Tnomas
    return (resultado(r["d_f"], r["a_f"], r["E_f"], m),
            resultado(r["d_i"], r["a_i"], r["E_i"], m))

def barrido(freqs):
    TF, TI = [], []
    for f in freqs:
        r = simular(f, 30.0, 0.004)
        m = r["t"] > 20
        ag = A*(2*np.pi*f)**2
        TF.append(np.abs(r["a_f"][m]).max()/ag)
        TI.append(np.abs(r["a_i"][m]).max()/ag)
    return np.array(TF), np.array(TI)

r = simular()
a, b = medir(r)
error = lambda x, y: 100*(1 - y/x)

print()
print(f"Fuente: {F} Hz")
print(f"{'':24}{'Fija':>10}{'Aislada':>10}{'Error relativo':>12}")
print(f"{'Amplitud (mm)':24}{a['amp']*1e3:10.2f}{b['amp']*1e3:10.2f}{error(a['amp'], b['amp']):10.1f} %")
print(f"{'Aceleracion max (m/s2)':24}{a['amax']:10.2f}{b['amax']:10.2f}{error(a['amax'], b['amax']):10.1f} %")
print(f"{'Energia max (mJ)':24}{a['Emax']*1e3:10.2f}{b['Emax']*1e3:10.2f}{error(a['Emax'], b['Emax']):10.1f} %")

freqs = np.arange(0.3, 8.01, 0.1)
TFs, TIs = barrido(freqs[::5])

##################
def exportar_csv(r, ruta="respuesta.csv", fps=60, duracion=12.0):
    t_ini = r["t"][-1] - duracion
    tt = np.arange(t_ini, t_ini + duracion, 1/fps)
    cols = ["xg", "xb", "xs_f", "xs_i"]
    with open(ruta, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t"] + cols)
        for t in tt:
            w.writerow([round(t - t_ini, 5)] + [float(np.interp(t, r["t"], r[c])) for c in cols])
    print(f"CSV exportado: {ruta} ({len(tt)} fotogramas a {fps} fps)")
###############
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def exportar_excel(r, freqs_sim, TFs, TIs, ruta="Resultados_Simulacion.xlsx", duracion=4.0):
    # 1. Preparar datos de Respuesta en el Tiempo
    t_ini = r["t"][-1] - duracion
    m = r["t"] >= t_ini
    df_tiempo = pd.DataFrame({
        'Tiempo (s)': r["t"][m],
        'Suelo (mm)': r["xg"][m] * 1000,
        'Estructura, base fija (mm)': r["xs_f"][m] * 1000,
        'Estructura, base aislada (mm)': r["xs_i"][m] * 1000
    })
    
    # 2. Preparar datos de Transmisibilidad Simulada
    df_trans = pd.DataFrame({
        'Frecuencia (Hz)': freqs_sim,
        'Base fija (simulada)': TFs,
        'Base aislada (simulada)': TIs
    })
    
    # Escribir a Excel creando dos hojas distintas
    with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
        df_tiempo.to_excel(writer, sheet_name='Respuesta_Tiempo', index=False)
        df_trans.to_excel(writer, sheet_name='Transmisibilidad', index=False)
        
        # --- Aplicar estilos visuales a ambas hojas ---
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="36454F", end_color="36454F", fill_type="solid")
        border = Border(left=Side(style='thin', color="D3D3D3"),
                        right=Side(style='thin', color="D3D3D3"),
                        top=Side(style='thin', color="D3D3D3"),
                        bottom=Side(style='thin', color="D3D3D3"))
                        
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                    cell.border = border
                ws.column_dimensions[column].width = max_length + 2
                
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
    print(f"Excel exportado correctamente con 2 hojas: {ruta}")


print("Iniciando simulación en el tiempo...")
r = simular()
a, b = medir(r)
error = lambda x, y: 100*(1 - y/x)

print()
print(f"Fuente: {F} Hz")
print(f"{'':24}{'Fija':>10}{'Aislada':>10}{'Error relativo':>12}")
print(f"{'Amplitud (mm)':24}{a['amp']*1e3:10.2f}{b['amp']*1e3:10.2f}{error(a['amp'], b['amp']):10.1f} %")
print(f"{'Aceleracion max (m/s2)':24}{a['amax']:10.2f}{b['amax']:10.2f}{error(a['amax'], b['amax']):10.1f} %")
print(f"{'Energia max (mJ)':24}{a['Emax']*1e3:10.2f}{b['Emax']*1e3:10.2f}{error(a['Emax'], b['Emax']):10.1f} %")
print()

print("Calculando barrido de frecuencias para transmisibilidad (esto puede tomar unos segundos)...")
freqs = np.arange(0.3, 8.01, 0.1)
freqs_simulacion = freqs[::5] 
TFs, TIs = barrido(freqs_simulacion)

exportar_csv(r)
exportar_excel(r, freqs_simulacion, TFs, TIs) 
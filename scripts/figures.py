"""gera figuras a partir dos resultados medidos, sem valores desenhados à mão."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[1]
metrics = json.loads((root/'reports/metrics.json').read_text())
with (root/'reports/risk_coverage.csv').open() as source:
    curve = list(csv.DictReader(source))
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, ax = plt.subplots(figsize=(7.5, 3.2), layout='constrained')
ax.plot([float(r['coverage'])*100 for r in curve], [float(r['error_rate'])*100 for r in curve], color='#164d80')
p = metrics['test']['policy']
ax.scatter([p['coverage']*100], [p['error_rate']*100], color='#222222', zorder=3)
ax.annotate('limiar escolhido na validação: 0,81', (p['coverage']*100,p['error_rate']*100), xytext=(-215,20), textcoords='offset points', arrowprops={'arrowstyle':'->','color':'#555'})
ax.set(xlabel='Textos aceitos automaticamente (%)', ylabel='Erro entre os aceitos (%)', title='O custo de classificar mais textos · teste B2W')
ax.grid(alpha=.2)
fig.savefig(root/'docs/images/cobertura.png', dpi=160)
plt.close(fig)
fig, ax = plt.subplots(figsize=(4.6,3.6),layout='constrained')
m = metrics['test']['forced']['confusion_matrix_negative_positive']
ax.imshow(m,cmap='Blues')
for y,row in enumerate(m):
    for x,value in enumerate(row):
        ax.text(x,y,f'{value:,}'.replace(',','.'),ha='center',va='center',color='white' if value>6000 else 'black',fontsize=14)
ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Negativa','Positiva'],yticklabels=['Negativa','Positiva'],xlabel='Predição',ylabel='Rótulo pelas estrelas',title='Classificando todo o teste · 16.988 textos')
fig.savefig(root/'docs/images/confusao.png',dpi=160)

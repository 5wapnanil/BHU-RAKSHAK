with open('frontend/src/app/alerts/page.tsx', 'r') as f:
    code = f.read()

code = code.replace('rgba(255,255,255,0.03)', 'rgba(0,0,0,0.02)')
code = code.replace('rgba(255,255,255,0.02)', 'rgba(0,0,0,0.02)')
code = code.replace('rgba(255,255,255,0.05)', 'rgba(0,0,0,0.05)')
code = code.replace('rgba(255,255,255,0.1)', 'rgba(0,0,0,0.08)')
code = code.replace('rgba(0,0,0,0.2)', 'rgba(0,0,0,0.04)')

with open('frontend/src/app/alerts/page.tsx', 'w') as f:
    f.write(code)

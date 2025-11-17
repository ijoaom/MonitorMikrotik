📊 Monitor MikroTik - Dashboard em Tempo Real

Sobre o Projeto
Aplicação web para monitoramento em tempo real do tráfego de rede em dispositivos MikroTik. Desenvolvida em Python com Flask e Socket.IO, oferece visualização gráfica do consumo de banda.

🚀 Funcionalidades
- Monitoramento em tempo real de upload/download
- Gráficos dinâmicos com atualização automática
- Histórico de consumo (últimos 30 pontos)
- Estatísticas (média e pico de tráfego)
- Interface responsiva e intuitiva
- Conexão direta com API RouterOS

🛠️ Tecnologias
- Backend: Python, Flask, Flask-SocketIO
- Frontend: HTML, CSS, JavaScript, Chart.js
- API:routeros-api (MikroTik)
- Tempo real: WebSockets

⚙️ Configuração
```python
HOST = '192.168.56.102'    # IP do MikroTik
USUARIO = 'admin'          # Usuário RouterOS
SENHA = '1234'             # Senha do dispositivo
```

Como Usar
1. Configure o IP e credenciais do MikroTik
2. Execute `python app.py`
3. Acesse `http://127.0.0.1:5000`
4. Visualize o tráfego em tempo real

📈 Métricas Monitoradas
- Download (Rx): Tráfego de entrada
- Upload (Tx): Tráfego de saída  
- Médias: Consumo médio por período
- Picos: Máximo de utilização

Ideal para administradores de rede monitorarem o desempenho de links e identificar padrões de uso.
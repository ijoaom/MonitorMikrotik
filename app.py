import time
from flask import Flask, render_template
from flask_socketio import SocketIO
import routeros_api

# --- Configuração do Roteador ---
HOST = '192.168.56.102'
USUARIO = 'admin'
SENHA = '1234'
# ----------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu_segredo_super_secreto'
socketio = SocketIO(app)

thread_iniciada = False
historico_dados = []
MAX_HISTORICO = 120

def conectar_mikrotik():
    """Conecta ao MikroTik e retorna a API"""
    try:
        connection = routeros_api.RouterOsApiPool(
            host=HOST,
            username=USUARIO, 
            password=SENHA,
            plaintext_login=True,
            use_ssl=False,
            port=8728
        )
        api = connection.get_api()
        return api, connection
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None, None

def monitor_bandwidth():
    """Função principal que busca os dados IGUAIS ao WinBox"""
    global thread_iniciada, historico_dados
    
    print("📊 Iniciando monitoramento de banda (Modo Real-Time)...")
    
    rx_historico = []
    tx_historico = []
    historico_medias = 10 # Para calcular média móvel rápida
    
    while True:
        try:
            api, conexao = conectar_mikrotik()
            
            if not api:
                socketio.emit('update_status', {
                    'status': 'Desconectado', 
                    'last_read': '--:--:--'
                })
                time.sleep(3)
                continue
            
            # Pegamos o recurso de interface
            interface_resource = api.get_resource('/interface')

            while True: # Loop interno para manter a conexão ativa
                try:
                    # --- A MÁGICA ESTÁ AQUI ---
                    # Usamos 'monitor-traffic' igual ao WinBox
                    # duration=1 faz ele calcular a média exata do último segundo
                    trafego = interface_resource.call(
                        'monitor-traffic',
                        {'interface': 'ether1', 'duration': '1'}
                    )
                    
                    if trafego:
                        dados = trafego[0]
                        
                        # O RouterOS já devolve a velocidade em bits por segundo (bps)
                        rx_bps = int(dados.get('rx-bits-per-second', 0))
                        tx_bps = int(dados.get('tx-bits-per-second', 0))
                        
                        # Converter para Mbps
                        rx_mbps = round(rx_bps / 1_000_000, 2)
                        tx_mbps = round(tx_bps / 1_000_000, 2)
                        
                        tempo_atual = time.strftime('%H:%M:%S')
                        
                        # Atualizar listas para médias
                        rx_historico.append(rx_mbps)
                        tx_historico.append(tx_mbps)
                        if len(rx_historico) > historico_medias:
                            rx_historico.pop(0)
                            tx_historico.pop(0)
                        
                        # Calcular Estatísticas
                        avg_rx = round(sum(rx_historico) / len(rx_historico), 2)
                        avg_tx = round(sum(tx_historico) / len(tx_historico), 2)
                        peak_rx = max(rx_historico)
                        peak_tx = max(tx_historico)

                        # Salvar histórico global
                        ponto = {
                            'rx': rx_mbps,
                            'tx': tx_mbps,
                            'time': tempo_atual
                        }
                        historico_dados.append(ponto)
                        if len(historico_dados) > MAX_HISTORICO:
                            historico_dados.pop(0)

                        print(f"📡 WinBox Data -> Rx: {rx_mbps} Mbps | Tx: {tx_mbps} Mbps")

                        # Enviar para o Frontend
                        socketio.emit('new_data', {
                            'rx': rx_mbps,
                            'tx': tx_mbps, 
                            'time': tempo_atual,
                            'avg_rx': avg_rx,
                            'avg_tx': avg_tx,
                            'peak_rx': peak_rx,
                            'peak_tx': peak_tx
                        })
                        
                        socketio.emit('update_status', {
                            'status': 'Monitorando',
                            'last_read': tempo_atual
                        })
                    
                except Exception as e:
                    print(f"Erro na leitura: {e}")
                    break # Sai do loop interno para reconectar
                
        except Exception as e:
            print(f"💥 Erro fatal: {e}")
            time.sleep(3)
        
        # Garante desconexão limpa antes de tentar reconectar
        try:
            if 'conexao' in locals():
                conexao.disconnect()
        except:
            pass

def obter_historico():
    return historico_dados

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global thread_iniciada
    print("👤 Cliente conectado")
    
    # Enviar interfaces (simples)
    socketio.emit('interfaces', {'interfaces': ['ether1']})
    
    if not thread_iniciada:
        socketio.start_background_task(monitor_bandwidth)
        thread_iniciada = True

@socketio.on('request_history')
def handle_request_history():
    socketio.emit('history', {'history': obter_historico()})

if __name__ == '__main__':
    print("🚀 Servidor iniciando em http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000, debug=False)
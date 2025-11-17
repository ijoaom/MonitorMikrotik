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
MAX_HISTORICO = 100

def testar_conexao_mikrotik():
    """Testa a conexão de forma mais robusta"""
    try:
        print(f"🔌 Testando conexão com {HOST}...")
        
        connection = routeros_api.RouterOsApiPool(
            host=HOST,
            username=USUARIO, 
            password=SENHA,
            plaintext_login=True,
            use_ssl=False,
            port=8728
        )
        
        api = connection.get_api()
        test = api.get_resource('/system/identity').get()
        if test:
            print("✅ Conexão estabelecida com sucesso!")
            return api, connection
        else:
            print("❌ Conexão falhou no teste")
            return None, None
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return None, None

def coletar_dados_bandwidth(api):
    """Coleta dados de bandwidth de forma segura"""
    try:
        # Método direto com interface
        interface_resource = api.get_resource('/interface')
        interface_data = interface_resource.get(name='ether1')
        
        if interface_data and len(interface_data) > 0:
            data = interface_data[0]
            rx_bytes = int(data.get('rx-byte', 0))
            tx_bytes = int(data.get('tx-byte', 0))
            
            # Converter bytes para bits
            rx_bps = rx_bytes * 8
            tx_bps = tx_bytes * 8
            return rx_bps, tx_bps
            
        return 0, 0
        
    except Exception as e:
        print(f"❌ Erro na coleta de dados: {e}")
        return 0, 0

def monitor_bandwidth():
    """Função principal de monitoramento"""
    global thread_iniciada, historico_dados
    
    print("📊 Iniciando monitoramento de banda...")
    
    # ✅ CORREÇÃO: Inicializar listas vazias
    rx_historico = []
    tx_historico = []
    historico_max = 10
    
    while True:
        try:
            # Estabelecer conexão
            api, conexao = testar_conexao_mikrotik()
            
            if not api:
                print("❌ Falha na conexão, tentando novamente em 3 segundos...")
                socketio.emit('update_status', {
                    'status': 'Desconectado', 
                    'last_read': time.strftime('%H:%M:%S')
                })
                time.sleep(3)
                continue
            
            # Coletar dados
            rx_bps, tx_bps = coletar_dados_bandwidth(api)
            
            # Fechar conexão após uso
            try:
                conexao.disconnect()
            except:
                pass
            
            # Converter para Mbps
            rx_mbps = round(rx_bps / 1_000_000, 2)
            tx_mbps = round(tx_bps / 1_000_000, 2)
            
            print(f"📊 Dados coletados - Rx: {rx_mbps} Mbps, Tx: {tx_mbps} Mbps")
            
            # ✅ CORREÇÃO: Adicionar valores corretos às listas
            rx_historico.append(rx_mbps)
            tx_historico.append(tx_mbps)  # ✅ CORRIGIDO: era tx_historico.append(tx_historico)
            
            if len(rx_historico) > historico_max:
                rx_historico.pop(0)
                tx_historico.pop(0)
            
            # ✅ SALVAR NO HISTÓRICO GLOBAL (para o botão)
            tempo_atual = time.strftime('%H:%M:%S')
            ponto_historico = {
                'rx': rx_mbps,
                'tx': tx_mbps,
                'time': tempo_atual
            }
            historico_dados.append(ponto_historico)
            
            # Manter histórico limitado
            if len(historico_dados) > MAX_HISTORICO:
                historico_dados.pop(0)
            
            # Calcular estatísticas
            avg_rx = round(sum(rx_historico) / len(rx_historico), 2) if rx_historico else 0
            avg_tx = round(sum(tx_historico) / len(tx_historico), 2) if tx_historico else 0
            peak_rx = round(max(rx_historico), 2) if rx_historico else 0
            peak_tx = round(max(tx_historico), 2) if tx_historico else 0
            
            # Emitir dados para o frontend
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
                'status': 'Conectado',
                'last_read': tempo_atual
            })
            
            time.sleep(1)
            
        except Exception as e:
            print(f"💥 Erro no loop principal: {e}")
            time.sleep(3)

def obter_historico():
    """Retorna o histórico de dados para o frontend"""
    return historico_dados[-30:]  # Retorna últimos 30 pontos

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect(auth):
    global thread_iniciada
    print("👤 Cliente conectado via SocketIO")
    
    # Enviar interfaces disponíveis
    try:
        api_temp, conn_temp = testar_conexao_mikrotik()
        if api_temp:
            interfaces = api_temp.get_resource('/interface').get()
            interface_names = [interface['name'] for interface in interfaces]
            socketio.emit('interfaces', {'interfaces': interface_names})
            conn_temp.disconnect()
    except Exception as e:
        print(f"Erro ao obter interfaces: {e}")
    
    socketio.emit('update_status', {
        'status': 'Iniciando...',
        'last_read': time.strftime('%H:%M:%S')
    })
    
    if not thread_iniciada:
        print("🚀 Iniciando thread de monitoramento...")
        socketio.start_background_task(monitor_bandwidth)
        thread_iniciada = True

@socketio.on('change_interface')
def handle_change_interface(data):
    print(f"🔧 Interface alterada: {data.get('interface')}")

@socketio.on('pause')
def handle_pause(data):
    estado = "pausado" if data.get('pause') else "retomado"
    print(f"⏸️  Monitoramento {estado}")

# ✅ BOTÃO CARREGAR HISTÓRICO FUNCIONANDO
@socketio.on('request_history')
def handle_request_history():
    print("📋 Histórico solicitado - enviando dados...")
    try:
        historico = obter_historico()
        socketio.emit('history', {
            'history': historico,
            'total_pontos': len(historico),
            'mensagem': f'Carregados {len(historico)} pontos de histórico'
        })
        print(f"✅ Histórico enviado: {len(historico)} pontos")
    except Exception as e:
        print(f"❌ Erro ao enviar histórico: {e}")
        socketio.emit('history_error', {
            'erro': 'Falha ao carregar histórico'
        })

if __name__ == '__main__':
    print("🚀 Servidor iniciando em http://127.0.0.1:5000")
    
    # Teste inicial
    api_test, conn_test = testar_conexao_mikrotik()
    if api_test:
        print("✅ Conectividade OK - Servidor pronto!")
        try:
            conn_test.disconnect()
        except:
            pass
    else:
        print("⚠️  Aviso: Não foi possível conectar ao MikroTik")
    
    socketio.run(app, host='127.0.0.1', port=5000, debug=False)
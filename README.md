# 📊 Mikrotik Bandwidth Monitor

Este projeto é uma aplicação web para monitoramento de tráfego de rede em tempo real de um roteador MikroTik. Desenvolvido como parte da disciplina de **Projeto e Administração de Redes**.

O sistema utiliza **Python (Flask)** no backend para comunicar-se com a API do MikroTik e **WebSockets (Socket.IO)** para enviar dados em tempo real para um frontend dinâmico com **Chart.js**.

---

## 🚀 Tecnologias Utilizadas

* **Backend:** Python 3, Flask, Flask-SocketIO, routeros-api
* **Frontend:** HTML5, CSS3, JavaScript, Chart.js
* **Infraestrutura:** VirtualBox, MikroTik Cloud Hosted Router (CHR)
* **Ferramentas:** WinBox, Bandwidth Test Tool (btest.exe)

---

## ⚙️ Pré-requisitos

Antes de começar, você precisará ter instalado:

1.  [Python 3.x](https://www.python.org/)
2.  [Oracle VirtualBox](https://www.virtualbox.org/)
3.  Imagem do [MikroTik CHR (OVA)](https://mikrotik.com/download)
4.  [WinBox](https://mikrotik.com/download) (para configuração)
5.  **Bandwidth Test Tool for Windows** (para gerar tráfego de teste)

---

## 🛠️ Configuração do Ambiente

### 1. Configurar a VM MikroTik (VirtualBox)
1.  Importe a imagem `.ova` do CHR no VirtualBox.
2.  Nas configurações de **Rede**, certifique-se de que o **Adaptador 1** esteja configurado como **"Placa de Rede Exclusiva de Hospedeiro" (Host-only Adapter)**.
3.  Inicie a VM.
4.  No terminal do MikroTik, configure o IP e ative a API:
    ```bash
    # Adicionar IP (exemplo)
    /ip address add address=192.168.56.102/24 interface=ether1
    
    # Habilitar serviço de API
    /ip service enable api
    ```

### 2. Configurar o Firewall (MikroTik)
Para permitir que o PC e o teste de banda se comuniquem com o roteador, adicione uma regra de firewall via WinBox:
* Vá em **IP > Firewall > Filter Rules**.
* Adicione uma nova regra (`+`):
    * **Chain:** `input`
    * **Src. Address:** `192.168.56.0/24` (Sua rede Host-Only)
    * **Action:** `accept`
* **Importante:** Arraste esta regra para o topo da lista (posição 0).

---

## 📥 Instalação e Execução

### 1. Clonar e Instalar Dependências

Abra o terminal na pasta do projeto:

```bash
# 1. Crie um ambiente virtual (recomendado)
python -m venv venv

# 2. Ative o ambiente virtual
# No Windows:
.\venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# 3. Instale as bibliotecas necessárias
pip install flask flask-socketio routeros-api

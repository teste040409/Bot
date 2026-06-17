from flask import Flask, request, render_template_string, jsonify
import subprocess
import os
import time
import sys
import signal
import threading
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_process = None

# Template HTML (embutido para facilitar)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Self-Bot Discord Launcher</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 600px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        .logo { text-align: center; margin-bottom: 30px; color: #ffffff; }
        .logo h1 { font-size: 28px; }
        .logo span { color: #7289da; }
        .logo p { color: #b9bbbe; font-size: 14px; margin-top: 5px; }
        .form-group { margin-bottom: 20px; }
        label { color: #b9bbbe; display: block; margin-bottom: 8px; font-size: 14px; font-weight: 500; }
        textarea {
            width: 100%;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: #ffffff;
            font-size: 13px;
            min-height: 80px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        textarea:focus { outline: none; border-color: #7289da; box-shadow: 0 0 0 2px rgba(114, 137, 218, 0.2); }
        textarea::placeholder { color: #6a6a7a; }
        .btn {
            width: 100%;
            padding: 14px;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-success { background: #2ecc71; }
        .btn-success:hover { background: #27ae60; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #e67e22; }
        .button-group { display: flex; gap: 10px; }
        .button-group .btn { flex: 1; }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            display: none;
            text-align: center;
            font-weight: 500;
        }
        .status.success { display: block; background: rgba(46, 204, 113, 0.2); border: 1px solid #2ecc71; color: #2ecc71; }
        .status.error { display: block; background: rgba(231, 76, 60, 0.2); border: 1px solid #e74c3c; color: #e74c3c; }
        .status.info { display: block; background: rgba(52, 152, 219, 0.2); border: 1px solid #3498db; color: #3498db; }
        .status.running { display: block; background: rgba(46, 204, 113, 0.2); border: 1px solid #2ecc71; color: #2ecc71; }
        .console-output {
            background: rgba(0, 0, 0, 0.6);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            max-height: 250px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #00ff00;
            display: none;
            white-space: pre-wrap;
            word-break: break-all;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .console-output.active { display: block; }
        .console-output .error { color: #ff4444; }
        .console-output .success { color: #44ff44; }
        .console-output .info { color: #4488ff; }
        .console-output .warning { color: #ffaa44; }
        .info-box {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            border-left: 3px solid #f39c12;
        }
        .info-box h4 { color: #f39c12; margin-bottom: 8px; }
        .info-box p { color: #b9bbbe; font-size: 13px; line-height: 1.6; }
        .info-box code { background: rgba(0, 0, 0, 0.3); padding: 2px 8px; border-radius: 4px; color: #7289da; font-size: 12px; }
        .security-note { color: #e74c3c; font-size: 12px; margin-top: 15px; text-align: center; font-weight: bold; }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @media (max-width: 600px) { .container { padding: 20px; } .button-group { flex-direction: column; } }
        
        /* Estilo para o status do servidor */
        .server-status {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 10px;
            margin-top: 15px;
            text-align: center;
            color: #b9bbbe;
            font-size: 12px;
        }
        .server-status .online { color: #2ecc71; }
        .server-status .offline { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Self-Bot <span>Launcher</span></h1>
            <p>Cole o token e inicie seu self-bot</p>
        </div>

        <div class="form-group">
            <label>Token da sua conta:</label>
            <textarea id="tokenInput" placeholder="Cole o token da sua conta Discord aqui..."></textarea>
        </div>

        <div class="button-group">
            <button class="btn btn-success" id="startBtn">Iniciar Self-Bot</button>
            <button class="btn btn-danger" id="stopBtn" disabled>Parar</button>
            <button class="btn btn-warning" id="clearBtn">Limpar</button>
        </div>

        <div class="status" id="status"></div>
        <div class="console-output" id="consoleOutput"></div>
        
        <div class="server-status">
            Status do Servidor: <span class="online" id="serverStatus">● Online</span>
        </div>

        <div class="info-box">
            <h4>ATENCAO:</h4>
            <p>
                * Isso eh um SELF-BOT (usa sua propria conta)<br>
                * O bot roda no servidor remoto<br>
                * Seu token NUNCA eh compartilhado<br>
                * Use por sua conta e risco (viola os ToS do Discord)
            </p>
        </div>

        <div class="security-note">
            NUNCA COMPARTILHE SEU TOKEN! ELE DA ACESSO TOTAL A SUA CONTA!
        </div>
    </div>

    <script>
        let checkInterval = null;
        let logInterval = null;
        const API_URL = window.location.origin;

        document.addEventListener('DOMContentLoaded', function() {
            const tokenInput = document.getElementById('tokenInput');
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const clearBtn = document.getElementById('clearBtn');
            const statusDiv = document.getElementById('status');
            const consoleOutput = document.getElementById('consoleOutput');

            // Carregar token salvo
            const savedToken = localStorage.getItem('discord_token');
            if (savedToken) {
                tokenInput.value = savedToken;
                showStatus('info', 'Token carregado do navegador');
            }

            // Verificar status inicial
            checkBotStatus();

            startBtn.addEventListener('click', async function() {
                const token = tokenInput.value.trim();
                
                if (!token) {
                    showStatus('error', 'Cole o token da sua conta!');
                    return;
                }

                if (token.length < 20) {
                    showStatus('error', 'Token invalido!');
                    return;
                }

                try {
                    startBtn.disabled = true;
                    startBtn.innerHTML = '<span class="loading"></span> Iniciando...';
                    showStatus('info', 'Iniciando self-bot...');
                    consoleOutput.classList.add('active');
                    appendConsole('Iniciando self-bot...', 'info');

                    const response = await fetch(API_URL + '/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: token })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        showStatus('running', data.status);
                        appendConsole(data.status, 'success');
                        startBtn.disabled = true;
                        stopBtn.disabled = false;
                        localStorage.setItem('discord_token', token);
                        startLogCheck();
                    } else {
                        showStatus('error', data.error);
                        appendConsole(data.error, 'error');
                        startBtn.disabled = false;
                        startBtn.innerHTML = 'Iniciar Self-Bot';
                    }
                } catch (error) {
                    showStatus('error', 'Erro: ' + error.message);
                    appendConsole('Erro: ' + error.message, 'error');
                    startBtn.disabled = false;
                    startBtn.innerHTML = 'Iniciar Self-Bot';
                }
            });

            stopBtn.addEventListener('click', async function() {
                try {
                    const response = await fetch(API_URL + '/stop', { method: 'POST' });
                    const data = await response.json();

                    if (response.ok) {
                        showStatus('info', data.status);
                        appendConsole(data.status, 'info');
                        startBtn.disabled = false;
                        startBtn.innerHTML = 'Iniciar Self-Bot';
                        stopBtn.disabled = true;
                        clearInterval(checkInterval);
                        clearInterval(logInterval);
                    }
                } catch (error) {
                    showStatus('error', 'Erro: ' + error.message);
                }
            });

            clearBtn.addEventListener('click', function() {
                tokenInput.value = '';
                localStorage.removeItem('discord_token');
                showStatus('info', 'Token removido');
                consoleOutput.classList.remove('active');
                consoleOutput.innerHTML = '';
            });

            function showStatus(type, message) {
                statusDiv.className = 'status ' + type;
                statusDiv.textContent = message;
                statusDiv.style.display = 'block';
            }

            function appendConsole(text, type = 'info') {
                const className = type === 'error' ? 'error' : type === 'success' ? 'success' : 'info';
                consoleOutput.innerHTML += `<div class="${className}">${text}</div>`;
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }

            function startLogCheck() {
                clearInterval(logInterval);
                logInterval = setInterval(async function() {
                    try {
                        const response = await fetch(API_URL + '/logs');
                        const data = await response.json();
                        
                        if (data.logs && data.logs.length > 0) {
                            data.logs.forEach(log => {
                                appendConsole(log, 'info');
                            });
                        }
                    } catch (e) {}
                }, 2000);
            }

            async function checkBotStatus() {
                try {
                    const response = await fetch(API_URL + '/status');
                    const data = await response.json();
                    
                    if (data.running) {
                        showStatus('running', 'Bot esta rodando!');
                        startBtn.disabled = true;
                        stopBtn.disabled = false;
                        startLogCheck();
                    }
                } catch (e) {}
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start', methods=['POST'])
def start_bot():
    global bot_process
    
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token nao fornecido'}), 400
    
    if bot_process and bot_process.poll() is None:
        return jsonify({'error': 'Bot ja esta rodando'}), 400
    
    try:
        # Configurar ambiente com o token
        env = os.environ.copy()
        env['BOT_TOKEN'] = token  # ← Token como variável de ambiente
        
        bot_process = subprocess.Popen(
            ['python', 'bot.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace',
            env=env  # ← Passa o ambiente com o token
        )
        
        # Aguardar 3 segundos para ver se inicia
        time.sleep(3)
        
        if bot_process.poll() is not None:
            output, _ = bot_process.communicate()
            return jsonify({'error': f'Falha ao iniciar: {output[:500]}'}), 500
        
        logger.info(f"Bot iniciado com sucesso! PID: {bot_process.pid}")
        return jsonify({'status': 'Self-bot iniciado com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao iniciar bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_bot():
    global bot_process
    
    if bot_process:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
            logger.info("Bot finalizado com sucesso")
        except:
            try:
                bot_process.kill()
                logger.info("Bot finalizado com kill")
            except:
                pass
        finally:
            bot_process = None
        return jsonify({'status': 'Self-bot parado'})
    
    return jsonify({'error': 'Nenhum bot rodando'}), 400

@app.route('/status', methods=['GET'])
def status_bot():
    global bot_process
    
    if bot_process and bot_process.poll() is None:
        return jsonify({'running': True})
    return jsonify({'running': False})

@app.route('/logs', methods=['GET'])
def get_logs():
    global bot_process
    
    logs = []
    if bot_process and bot_process.poll() is None:
        try:
            for _ in range(5):
                line = bot_process.stdout.readline()
                if line:
                    logs.append(line.strip())
                else:
                    break
        except:
            pass
    
    return jsonify({'logs': logs})

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para health check do Render"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

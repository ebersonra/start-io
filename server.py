from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json
import urllib.request
import urllib.parse
from io import BytesIO
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectGenerator:
    INITIALIZR_URL = "https://start.spring.io/starter.zip"

    @staticmethod
    def generate_project(data):
        # Mapeamento de IDs de dependências para os valores do Spring Initializr
        dependency_mapping = {
            'web': 'web',
            'data-jpa': 'data-jpa',
            'security': 'security',
            'devtools': 'devtools',
            'lombok': 'lombok',
            'mysql': 'mysql',
            'postgresql': 'postgresql',
            'mongodb': 'data-mongodb',
            'data-redis': 'data-redis',
            'thymeleaf': 'thymeleaf'
        }

        # Converter o tipo de projeto para o formato correto
        project_type = 'maven-project' if data.get('project') == 'maven' else 'gradle-project'

        params = {
            'type': project_type,
            'language': data.get('language', 'java'),
            'bootVersion': data.get('version', '3.5.0'),
            'baseDir': data.get('artifact', 'demo'),
            'groupId': data.get('group', 'com.example'),
            'artifactId': data.get('artifact', 'demo'),
            'name': data.get('name', 'demo'),
            'description': data.get('description', 'Demo project'),
            'packageName': f"{data.get('group', 'com.example')}.{data.get('artifact', 'demo')}",
            'packaging': data.get('packaging', 'jar'),
            'javaVersion': data.get('javaVersion', '17')
        }

        # Processar dependências
        if 'dependencies' in data and data['dependencies']:
            mapped_deps = [dependency_mapping.get(dep, dep) for dep in data['dependencies']]
            params['dependencies'] = ','.join(mapped_deps)

        # Construir URL com parâmetros
        url = f"{ProjectGenerator.INITIALIZR_URL}?{urllib.parse.urlencode(params)}"
        
        logger.info(f"Gerando projeto com URL: {url}")

        try:
            # Configurar a requisição com um User-Agent apropriado
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/zip'
            }
            request = urllib.request.Request(url, headers=headers)
            
            # Buscar o projeto gerado
            with urllib.request.urlopen(request) as response:
                return response.read()
        except Exception as e:
            logger.error(f"Erro ao gerar projeto: {str(e)}")
            raise Exception(f"Falha ao gerar projeto: {str(e)}")

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions_map.update({
            '.css': 'text/css',
            '.js': 'application/javascript',
        })

    def do_GET(self):
        # Se a requisição começar com /api, proxy para start.spring.io
        if self.path.startswith('/api/'):
            self.proxy_request()
        else:
            if self.path == '/':
                self.path = '/index.html'
            return SimpleHTTPRequestHandler.do_GET(self)

    def proxy_request(self):
        try:
            # Remove /api do caminho e adiciona https://start.spring.io
            target_url = 'https://start.spring.io' + self.path[4:]
            logger.info(f"Proxying request to: {target_url}")

            # Configurar headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/zip'
            }

            # Criar requisição
            req = urllib.request.Request(target_url, headers=headers)

            # Fazer a requisição
            with urllib.request.urlopen(req) as response:
                # Copiar status code
                self.send_response(response.status)
                
                # Copiar headers relevantes
                for header, value in response.getheaders():
                    if header.lower() not in ['server', 'date', 'transfer-encoding']:
                        self.send_header(header, value)
                
                # Adicionar headers CORS
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                
                self.end_headers()
                
                # Copiar o corpo da resposta
                self.wfile.write(response.read())

        except Exception as e:
            logger.error(f"Proxy error: {str(e)}")
            self.send_error(500, f"Proxy error: {str(e)}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse dos dados JSON
                project_data = json.loads(post_data.decode('utf-8'))
                logger.info(f"Dados recebidos: {project_data}")
                
                # Gerar o projeto
                zip_content = ProjectGenerator.generate_project(project_data)
                
                # Enviar resposta
                self.send_response(200)
                self.send_header('Content-Type', 'application/zip')
                self.send_header('Content-Disposition', 'attachment; filename="project.zip"')
                self.end_headers()
                self.wfile.write(zip_content)
                logger.info("Projeto gerado com sucesso")
            
            except Exception as e:
                logger.error(f"Erro no servidor: {str(e)}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'error': str(e)}).encode('utf-8')
                self.wfile.write(error_response)
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8080):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, CustomHandler)
    logger.info(f"Servidor rodando em http://localhost:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nDesligando servidor...")
        httpd.server_close()

if __name__ == '__main__':
    run_server() 
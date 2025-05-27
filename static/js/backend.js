document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('projectForm');
    const dependencyItems = document.querySelectorAll('.dependency-item');
    const searchInput = document.getElementById('dependency-search');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorMessage = document.getElementById('error-message');

    // Handle dependency item clicks
    dependencyItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (e.target.type !== 'checkbox') {
                const checkbox = this.querySelector('.checkbox');
                checkbox.checked = !checkbox.checked;
                this.classList.toggle('selected', checkbox.checked);
            } else {
                this.classList.toggle('selected', e.target.checked);
            }
        });
    });

    // Handle dependency search
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        dependencyItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        errorMessage.style.display = 'none';
        loadingOverlay.style.display = 'flex';

        try {
            // Validar campos obrigatórios
            const artifactId = document.getElementById('artifact').value;
            const groupId = document.getElementById('group').value;
            
            if (!artifactId) {
                throw new Error('Artifact ID é obrigatório');
            }
            if (!groupId) {
                throw new Error('Group ID é obrigatório');
            }

            // Preparar os parâmetros para a URL
            const params = new URLSearchParams({
                type: document.getElementById('project').value === 'maven' ? 'maven-project' : 'gradle-project',
                language: document.getElementById('language').value,
                bootVersion: document.getElementById('version').value,
                baseDir: artifactId,
                groupId: groupId,
                artifactId: artifactId,
                name: document.getElementById('name').value || artifactId,
                description: document.getElementById('description').value || `Projeto ${artifactId}`,
                packageName: `${groupId}.${artifactId}`,
                packaging: document.getElementById('packaging').value,
                javaVersion: document.getElementById('java-version').value
            });

            // Adicionar dependências selecionadas
            const dependencies = Array.from(document.querySelectorAll('.dependency-item .checkbox:checked'))
                .map(checkbox => checkbox.closest('.dependency-item').dataset.id);
            
            if (dependencies.length > 0) {
                params.append('dependencies', dependencies.join(','));
            }

            // Construir URL final usando a base URL apropriada
            const baseUrl = getApiBaseUrl();
            const url = `${baseUrl}/starter.zip?${params.toString()}`;
            console.log('URL de requisição:', url);

            // Fazer o download usando Fetch API com headers específicos
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/zip',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Resposta do servidor:', response.status, errorText);
                throw new Error(`Erro ao gerar projeto: ${response.status} - ${errorText || response.statusText}`);
            }

            const blob = await response.blob();
            if (blob.size === 0) {
                throw new Error('O arquivo gerado está vazio');
            }

            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `${artifactId}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();

            // Limpar mensagem de erro se tudo der certo
            errorMessage.style.display = 'none';

        } catch (error) {
            console.error('Erro detalhado:', error);
            errorMessage.textContent = error.message || 'Erro ao gerar projeto. Por favor, tente novamente.';
            errorMessage.style.display = 'block';
        } finally {
            loadingOverlay.style.display = 'none';
        }
    });
}); 
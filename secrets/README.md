# secrets/

Este diretório contém arquivos de segredos usados pelo Docker em produção.

**NUNCA commite arquivos de senha aqui.** O `.gitignore` já ignora `*.txt` neste diretório.

## Setup inicial no servidor

```bash
# Gera uma senha forte e salva no arquivo de secret
openssl rand -base64 32 > secrets/mongo_password.txt
chmod 600 secrets/mongo_password.txt
```

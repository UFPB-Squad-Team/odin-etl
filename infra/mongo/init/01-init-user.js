db = db.getSiblingDB('odin');

db.createUser({
  user: 'odin_user',
  pwd: cat('/run/secrets/mongo_password').trim(),
  roles: [
    {
      role: 'readWrite',
      db: 'odin'
    }
  ]
});

db.municipio_indicadores.createIndex({ municipioIdIbge: 1 }, { unique: true, sparse: true });
db.setor_indicadores.createIndex({ cd_setor: 1 }, { unique: true, sparse: true });
db.bairro_indicadores.createIndex({ cd_bairro: 1 }, { unique: true, sparse: true });
db.escolas.createIndex({ escolaIdInep: 1 }, { unique: true, sparse: true });

print('✅ Usuário odin_user criado e índices inicializados.');

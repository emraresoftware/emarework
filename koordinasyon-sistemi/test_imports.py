#!/usr/bin/env python3
"""Test imports - tüm modülleri import ederek test et"""

print('🔍 Testing imports...\n')

modules_to_test = [
    ('src.config', 'settings'),
    ('src.cache', 'get_cached'),
    ('src.celery_app', 'app'),
    ('src.db.models', 'Node'),
    ('src.db.repository', 'NodeRepository'),
    ('src.tasks', 'check_node_health'),
]

success_count = 0
fail_count = 0

for module_name, item_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=[item_name])
        getattr(module, item_name)
        print(f'✅ {module_name} - OK')
        success_count += 1
    except Exception as e:
        print(f'❌ {module_name} - {e}')
        fail_count += 1

print(f'\n{"="*50}')
print(f'✨ Test Sonucu: {success_count}/{len(modules_to_test)} başarılı')
if fail_count == 0:
    print('🎉 Tüm modüller çalışıyor!')
else:
    print(f'⚠️  {fail_count} modülde hata var')

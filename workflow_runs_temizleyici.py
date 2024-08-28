import requests

# Parametreler
owner = 'alitekdemir'  # GitHub kullanıcı adınız
repo = 'biruni-randevucu'  # Repository adınız
token = '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'  # GitHub personal access token

# API URL'leri
runs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs'

# Auth header
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_runs(url):
    """Workflow runs'larını getirir."""
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # HTTP hatası olursa exception fırlat
    return response.json()

def delete_run(run_id):
    """Belirtilen ID'ye sahip workflow run'ı siler."""
    delete_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}'
    response = requests.delete(delete_url, headers=headers)
    response.raise_for_status()  # HTTP hatası olursa exception fırlat
    print(f'Run ID {run_id} silindi.')

# Workflow runs'larını getir
runs_data = get_runs(runs_url)

# Tüm runs'ları ID'ye göre sıralayın
runs = sorted(runs_data['workflow_runs'], key=lambda x: x['created_at'])
total = runs_data['total_count']
print(f'Toplam {total} workflow_runs bulundu.')

#! İlk ve son run hariç tüm runs'ları sil
for run in runs[1:-1]:
    total -= 1
    delete_run(run['id'])

print(f'Toplam {total} workflow_runs kaldı.')

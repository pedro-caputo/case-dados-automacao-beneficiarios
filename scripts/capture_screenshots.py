"""
Script automatizado para capturar screenshots reais em alta resolução de todas as páginas da aplicação.
Utiliza navegação SPA oficial do Streamlit via Playwright com Microsoft Edge.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Remover teste anterior
test_file = OUTPUT_DIR / "test.png"
if test_file.exists():
    test_file.unlink()

PAGE_CONFIGS = [
    ("app", "01_central_operacoes.png"),
    ("Nova Solicitacao", "02_nova_solicitacao.png"),
    ("Fila Operacional", "03_fila_operacional.png"),
    ("Analise Humana", "04_analise_humana.png"),
    ("Dashboard", "05_dashboard.png"),
    ("Laboratorio", "06_laboratorio.png"),
]

def main():
    print("[*] Iniciando captura de screenshots em alta fidelidade...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960}, device_scale_factor=1.25)
        page = context.new_page()

        # Abre a página principal
        page.goto("http://localhost:8501")
        page.wait_for_timeout(4000)

        for link_text, filename in PAGE_CONFIGS:
            print(f"[*] Navegando para '{link_text}'...")
            link = page.locator(f"a[data-testid='stSidebarNavLink']:has-text('{link_text}')")
            if link.count() > 0:
                link.first.click()
                page.wait_for_timeout(4500)
            else:
                print(f"[-] Link '{link_text}' não encontrado, tentando URL direta...")
                page.goto(f"http://localhost:8501/{link_text.replace(' ', '_')}")
                page.wait_for_timeout(4500)

            out_path = OUTPUT_DIR / filename
            page.screenshot(path=str(out_path), full_page=False)
            print(f"[+] Captura gravada: {out_path.name} ({out_path.stat().st_size} bytes)")

        browser.close()
    print("[✓] Todas as 6 páginas foram capturadas com sucesso!")

if __name__ == "__main__":
    main()

Repozytorium zostało stworzone na potrzeby projektu końcowego z kursu Python. 

Pojekt jest aplikacją portalu społecznościowego stworzoną przy użyciu frameworka Flask.
Aplikacja umożliwia użytkownikom wykonywanie operacji CRUD, dodawania postów, komentarzy, profili oraz ich edycji, ponadto u


Instalacja

1. Sklonuj repozytorium:

    git clone https://github.com/cezjar/projekt_koncowy_flask.git

2. Przejdź do katalogu projektu:

    cd projekt_koncowy_flask

3. Utwórz i aktywuj wirtualne środowisko:
    
    python -m venv venv
    source venv/bin/activate  # Na Windows: venv\Scripts\activate
    
4. Zainstaluj wymagane pakiety:
    
    pip install -r requirements.txt
    

## Uruchomienie aplikacji

1. Upewnij się, że wirtualne środowisko jest aktywne.
2. Uruchom aplikację poprzez plik run.py
3. Otwórz przeglądarkę i przejdź do `http://127.0.0.1:5000`.

## Struktura projektu

- `app/` - katalog z kodem aplikacji
- `templates/` - katalog z szablonami HTML
- `static/` - katalog z plikami statycznymi (CSS)
- `requirements.txt` - plik z listą zależności
- `instance/` - katalog z plikiem konfiguracji
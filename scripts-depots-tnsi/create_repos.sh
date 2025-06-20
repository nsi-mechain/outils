#!/bin/bash

CSV_FILE="eleves.csv"
GITHUB_ORG="nsi-mechain"

tail -n +2 "$CSV_FILE" | while IFS="," read -r nom prenom githubusername; do
    if [[ -z "$nom" || -z "$prenom" || -z "$githubusername" ]]; then
        echo "Ligne ignorée : ligne vide ou incomplète"
        continue
    fi

    repo_name=$(echo "$nom" | iconv -f utf8 -t ascii//TRANSLIT | tr '[:upper:]' '[:lower:]' | tr -d "'" | sed 's/ /-/g')
    full_repo_name="tnsi2526-$repo_name"

    echo "Création du dépôt : $full_repo_name pour $prenom $nom ($githubusername)"

    gh repo create "$GITHUB_ORG/$full_repo_name" --private
    git clone "git@github.com:$GITHUB_ORG/$full_repo_name.git"
    cd "$full_repo_name" || exit

    echo "# Dépôt de $prenom $nom" > README.md

    cat << EOF > .gitignore
# Fichiers Python
__pycache__/
*.py[cod]
*$py.class

# Environnements virtuels
venv/
.env/

# Distribution / packaging
build/
dist/
*.egg-info/

# Cache Pytest
.pytest_cache/

# Fichiers de configuration sensibles
*.ini
*.cfg
*.secret
*.key

# IDE
.vscode/
.idea/

# Notebooks checkpoints
.ipynb_checkpoints/

# Jupyter runtime
*.nbconvert.ipynb

EOF

    git add .
    git commit -m "Initialisation du dépôt de $prenom $nom"
    git push origin main

    cd ..
    rm -rf "$full_repo_name"

    gh api -X PUT "repos/$GITHUB_ORG/$full_repo_name/collaborators/$githubusername" \
      -f permission=push

done


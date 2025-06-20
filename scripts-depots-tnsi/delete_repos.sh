#!/bin/bash

# Organisation GitHub
GITHUB_ORG="nsi-mechain"

# Récupérer tous les dépôts commençant par "tnsi"
repos=$(gh repo list "$GITHUB_ORG" --limit 1000 --json name --jq '.[] | select(.name | startswith("tnsi")) | .name')

for repo in $repos; do
    echo "Suppression du dépôt : $repo"
    gh repo delete "$GITHUB_ORG/$repo" --yes
done

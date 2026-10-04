#!/usr/bin/env bash
# Fetch the text of the OpenStax algebra books: Prealgebra 2e,
# Elementary Algebra 2e and Intermediate Algebra 2e.
#
# Only the CNXML is checked out. The full repository is ~300 MB, nearly
# all of it images we don't use.
#
# Licence: CC BY-NC-SA 4.0. The text is not committed to this repository;
# this script fetches it, so anything derived from it stays local.
set -euo pipefail

DEST="$(cd "$(dirname "$0")/.." && pwd)/data/raw/openstax-algebra"

if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --quiet
else
  mkdir -p "$(dirname "$DEST")"
  git clone --quiet --depth 1 --filter=blob:none --sparse \
    https://github.com/openstax/osbooks-prealgebra-bundle.git "$DEST"
  git -C "$DEST" sparse-checkout set collections modules
fi

echo "$(ls "$DEST/modules" | wc -l | tr -d ' ') modules in $DEST"
